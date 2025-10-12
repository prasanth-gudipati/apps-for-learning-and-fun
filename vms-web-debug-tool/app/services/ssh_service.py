"""
SSH Service - Handles SSH connections to VMS servers
"""

import paramiko
import threading
import time
import re
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class SSHService:
    def __init__(self):
        self.connections = {}
        self.connection_lock = threading.Lock()
    
    def connect(self, host, username, password, sudo_password=None):
        """Establish SSH connection"""
        try:
            connection_id = str(uuid.uuid4())
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            ssh.connect(host, username=username, password=password, look_for_keys=False)
            
            # Create interactive shell
            shell = ssh.invoke_shell()
            time.sleep(1)
            shell.recv(10000)  # Clear banner
            
            # Perform sudo if password provided
            if sudo_password:
                shell.send("sudo su\n")
                buff = ""
                timeout = 10
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if shell.recv_ready():
                        resp = shell.recv(1000).decode()
                        buff += resp
                        if "password for" in buff.lower():
                            break
                    time.sleep(0.2)
                
                shell.send(sudo_password + "\n")
                time.sleep(2)
                output = shell.recv(10000).decode()
                
                # Set kubectl alias
                shell.send("alias k=kubectl\n")
                time.sleep(0.5)
                shell.recv(10000)
            
            # Store connection
            with self.connection_lock:
                self.connections[connection_id] = {
                    'ssh': ssh,
                    'shell': shell,
                    'host': host,
                    'username': username,
                    'connected_at': datetime.utcnow(),
                    'last_used': datetime.utcnow()
                }
            
            logger.info(f"SSH connection established: {connection_id} to {host}")
            return connection_id
            
        except Exception as e:
            logger.error(f"SSH connection failed: {str(e)}")
            return None
    
    def disconnect(self, connection_id):
        """Disconnect SSH connection"""
        try:
            with self.connection_lock:
                if connection_id in self.connections:
                    conn = self.connections[connection_id]
                    
                    # Send exit command
                    try:
                        conn['shell'].send("exit\n")
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # Close SSH connection
                    try:
                        conn['ssh'].close()
                    except:
                        pass
                    
                    # Remove from connections
                    del self.connections[connection_id]
                    logger.info(f"SSH connection closed: {connection_id}")
                    
        except Exception as e:
            logger.error(f"SSH disconnect error: {str(e)}")
    
    def get_connection(self, connection_id):
        """Get SSH connection by ID"""
        with self.connection_lock:
            if connection_id in self.connections:
                self.connections[connection_id]['last_used'] = datetime.utcnow()
                return self.connections[connection_id]
        return None
    
    def get_connection_status(self, connection_id):
        """Check if connection is active"""
        with self.connection_lock:
            if connection_id in self.connections:
                try:
                    # Test connection by sending a simple command
                    conn = self.connections[connection_id]
                    shell = conn['shell']
                    
                    # Check if shell is still responsive
                    shell.send("echo test\n")
                    time.sleep(0.5)
                    
                    if shell.recv_ready():
                        shell.recv(1000)  # Clear buffer
                        return True
                    return False
                except:
                    return False
        return False
    
    def execute_command(self, connection_id, command, timeout=30):
        """Execute command on SSH connection"""
        try:
            conn = self.get_connection(connection_id)
            if not conn:
                raise Exception("SSH connection not found")
            
            shell = conn['shell']
            
            # Send command
            shell.send(f"{command}\n")
            
            # Collect output
            output = ""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if shell.recv_ready():
                    chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                    output += chunk
                    
                    # Check for shell prompt (indicating command completion)
                    if chunk.endswith('# ') or chunk.endswith('$ '):
                        break
                time.sleep(0.1)
            
            # Clean output
            cleaned_output = self._clean_command_output(output, command)
            return cleaned_output
            
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            raise
    
    def _clean_command_output(self, output, command):
        """Clean SSH command output"""
        # Remove ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        output = ansi_escape.sub('', output)
        
        # Split into lines
        lines = output.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip command echo, prompts, and empty lines
            if (line == command or 
                line.startswith('echo ') or
                line.endswith('# ') or 
                line.endswith('$ ') or 
                line.startswith('[root@') or
                not line):
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def cleanup_old_connections(self, max_age_minutes=60):
        """Cleanup old unused connections"""
        try:
            cutoff_time = datetime.utcnow()
            cutoff_time = cutoff_time.replace(minute=cutoff_time.minute - max_age_minutes)
            
            to_remove = []
            
            with self.connection_lock:
                for conn_id, conn in self.connections.items():
                    if conn['last_used'] < cutoff_time:
                        to_remove.append(conn_id)
                
                for conn_id in to_remove:
                    logger.info(f"Cleaning up old SSH connection: {conn_id}")
                    self.disconnect(conn_id)
                    
        except Exception as e:
            logger.error(f"Connection cleanup error: {str(e)}")
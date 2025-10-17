#!/usr/bin/env python3
"""
VMS Debug Tool - SSH Service Microservice
Handles SSH connections and session management.
"""

from flask import Flask, request, jsonify
import paramiko
import redis
import json
import os
import time
import threading
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Service configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8001))
SESSION_REDIS_URL = os.getenv('SESSION_REDIS_URL', 'redis://localhost:6379')

# Redis client for session management
try:
    redis_client = redis.from_url(SESSION_REDIS_URL)
    redis_client.ping()
    logger.info("Connected to Redis successfully")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# SSH connection storage
ssh_connections = {}

class SSHConnectionManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.ssh_client = None
        self.shell = None
        self.connected = False
        self.host = ""
        self.username = ""
        self.ssh_password = ""
        self.admin_password = ""
        
    def connect(self, host, username, ssh_password, admin_password):
        """Establish SSH connection with sudo elevation"""
        try:
            self.host = host
            self.username = username
            self.ssh_password = ssh_password
            self.admin_password = admin_password
            
            logger.info(f"Session {self.session_id}: Attempting SSH connection to {host}")
            
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            self.ssh_client.connect(
                hostname=host,
                username=username,
                password=ssh_password,
                look_for_keys=False,
                timeout=10
            )
            
            logger.info(f"Session {self.session_id}: SSH connection successful")
            
            # Create shell
            self.shell = self.ssh_client.invoke_shell()
            time.sleep(1)
            self.shell.recv(10000)  # Clear banner
            
            # Execute sudo su
            logger.info(f"Session {self.session_id}: Executing sudo su")
            self.shell.send("sudo su\n")
            
            # Wait for password prompt
            buff = ""
            start_time = time.time()
            while time.time() - start_time < 10:  # 10 second timeout
                if self.shell.recv_ready():
                    resp = self.shell.recv(1000).decode('utf-8', errors='ignore')
                    buff += resp
                    if "password for" in buff.lower():
                        break
                time.sleep(0.2)
            
            if "password for" not in buff.lower():
                raise Exception("Sudo password prompt not found")
            
            # Send admin password
            self.shell.send(admin_password + "\n")
            time.sleep(1.5)
            
            # Check if sudo was successful
            output = self.shell.recv(10000).decode('utf-8', errors='ignore')
            
            # Set kubectl alias
            logger.info(f"Session {self.session_id}: Setting kubectl alias")
            self.shell.send("alias k=kubectl\n")
            time.sleep(0.5)
            self.shell.recv(10000).decode('utf-8', errors='ignore')  # Clear response
            
            self.connected = True
            
            # Save connection info to Redis
            if redis_client:
                connection_info = {
                    'connected': True,
                    'host': host,
                    'username': username,
                    'timestamp': datetime.now().isoformat()
                }
                redis_client.setex(f"ssh_session:{self.session_id}", 3600, json.dumps(connection_info))
            
            logger.info(f"Session {self.session_id}: SSH connection and sudo elevation successful")
            return True
            
        except Exception as e:
            logger.error(f"Session {self.session_id}: SSH connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect SSH connection"""
        try:
            if self.connected:
                logger.info(f"Session {self.session_id}: Disconnecting SSH connection")
                
                if self.shell:
                    self.shell.send("exit\n")
                    time.sleep(0.5)
                if self.ssh_client:
                    self.ssh_client.close()
                
                self.connected = False
                self.ssh_client = None
                self.shell = None
                
                # Clear connection info from Redis
                if redis_client:
                    redis_client.delete(f"ssh_session:{self.session_id}")
                
                logger.info(f"Session {self.session_id}: SSH disconnected successfully")
        except Exception as e:
            logger.error(f"Session {self.session_id}: Error during disconnect: {e}")
    
    def execute_command(self, command, timeout=10):
        """Execute command via SSH shell"""
        if not self.connected or not self.shell:
            return None
        
        try:
            logger.info(f"Session {self.session_id}: Executing command: {command}")
            self.shell.send(f"{command}\n")
            time.sleep(2)  # Wait for command to execute
            
            # Collect output
            output = self._collect_command_output(timeout)
            return output
        except Exception as e:
            logger.error(f"Session {self.session_id}: Error executing command: {e}")
            return None
    
    def _collect_command_output(self, timeout=10):
        """Collect output from shell command"""
        output = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.shell.recv_ready():
                chunk = self.shell.recv(4096).decode('utf-8', errors='ignore')
                output += chunk
                if chunk.endswith('# ') or chunk.endswith('$ '):
                    break
            time.sleep(0.1)
        
        return output

def get_ssh_manager(session_id):
    """Get or create SSH connection manager"""
    if session_id not in ssh_connections:
        ssh_connections[session_id] = SSHConnectionManager(session_id)
    return ssh_connections[session_id]

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ssh-service',
        'timestamp': datetime.now().isoformat(),
        'redis_connected': redis_client is not None,
        'active_connections': len(ssh_connections)
    })

@app.route('/connect', methods=['POST'])
def connect_ssh():
    """Connect to SSH server"""
    try:
        data = request.get_json()
        session_id = request.headers.get('X-Session-ID') or data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        host = data.get('host')
        username = data.get('username')
        ssh_password = data.get('ssh_password')
        admin_password = data.get('admin_password')
        
        if not all([host, username, ssh_password, admin_password]):
            return jsonify({'error': 'Missing connection parameters'}), 400
        
        ssh_manager = get_ssh_manager(session_id)
        
        # Connect in a separate thread to avoid blocking
        def connect_thread():
            ssh_manager.connect(host, username, ssh_password, admin_password)
        
        thread = threading.Thread(target=connect_thread)
        thread.start()
        thread.join(timeout=30)  # Wait up to 30 seconds
        
        if ssh_manager.connected:
            return jsonify({
                'success': True, 
                'connected': True,
                'message': 'SSH connection successful'
            })
        else:
            return jsonify({
                'error': 'SSH connection failed',
                'connected': False
            }), 400
            
    except Exception as e:
        logger.error(f"Connect SSH error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/disconnect', methods=['POST'])
def disconnect_ssh():
    """Disconnect from SSH server"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if session_id in ssh_connections:
            ssh_manager = ssh_connections[session_id]
            ssh_manager.disconnect()
            del ssh_connections[session_id]
        
        return jsonify({'success': True, 'message': 'Disconnected successfully'})
        
    except Exception as e:
        logger.error(f"Disconnect SSH error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute_command():
    """Execute command via SSH"""
    try:
        data = request.get_json()
        session_id = request.headers.get('X-Session-ID')
        command = data.get('command')
        timeout = data.get('timeout', 10)
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if not command:
            return jsonify({'error': 'Command required'}), 400
        
        if session_id not in ssh_connections:
            return jsonify({'error': 'No SSH connection found'}), 400
        
        ssh_manager = ssh_connections[session_id]
        
        if not ssh_manager.connected:
            return jsonify({'error': 'SSH not connected'}), 400
        
        output = ssh_manager.execute_command(command, timeout)
        
        if output is not None:
            return jsonify({
                'success': True,
                'output': output,
                'command': command
            })
        else:
            return jsonify({'error': 'Command execution failed'}), 500
            
    except Exception as e:
        logger.error(f"Execute command error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_connection_status():
    """Get SSH connection status"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if session_id in ssh_connections:
            ssh_manager = ssh_connections[session_id]
            return jsonify({
                'connected': ssh_manager.connected,
                'host': ssh_manager.host,
                'username': ssh_manager.username,
                'session_id': session_id
            })
        else:
            return jsonify({
                'connected': False,
                'session_id': session_id
            })
            
    except Exception as e:
        logger.error(f"Get status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/sessions', methods=['GET'])
def get_active_sessions():
    """Get list of active SSH sessions"""
    try:
        sessions = []
        for session_id, ssh_manager in ssh_connections.items():
            sessions.append({
                'session_id': session_id,
                'connected': ssh_manager.connected,
                'host': ssh_manager.host,
                'username': ssh_manager.username
            })
        
        return jsonify({
            'sessions': sessions,
            'total': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("VMS Debug Tool - SSH Service")
    logger.info("=" * 60)
    logger.info("SSH Connection Management Microservice")
    logger.info("")
    logger.info("Features:")
    logger.info("  • SSH connection management")
    logger.info("  • Automatic sudo elevation")
    logger.info("  • Command execution")
    logger.info("  • Session persistence with Redis")
    logger.info("")
    logger.info(f"Server starting on http://0.0.0.0:{SERVICE_PORT}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
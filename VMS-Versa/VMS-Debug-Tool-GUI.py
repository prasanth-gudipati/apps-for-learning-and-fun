#!/usr/bin/env python3
"""
VMS Debug Tool - GUI Version
A GUI application for connecting to VMS servers and executing kubectl commands
with real-time command execution display.

Features:
- GUI connection interface with default values
- SSH connection management
- Real-time command execution display
- Tenant data collection and visualization
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import paramiko
import json
import re
from datetime import datetime

class VMSDebugGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VMS Debug Tool - GUI")
        self.root.geometry("1200x800")
        
        # SSH connection variables
        self.ssh_client = None
        self.shell = None
        self.connected = False
        
        # Queue for thread communication
        self.output_queue = queue.Queue()
        
        # Initialize GUI
        self.setup_gui()
        
        # Start the output processor
        self.process_output()
    
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Main container with two sections
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Connection and controls
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Right panel - Command output display
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_connection_panel(left_frame)
        self.setup_output_panel(right_frame)
    
    def setup_connection_panel(self, parent):
        """Setup the connection configuration panel"""
        # Connection Configuration
        conn_frame = ttk.LabelFrame(parent, text="Server Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Server IP
        ttk.Label(conn_frame, text="Server IP:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ip_var = tk.StringVar(value="vms1-tb163.versa-test.net")
        self.ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=30)
        self.ip_entry.grid(row=0, column=1, pady=2, padx=(5, 0))
        
        # Username
        ttk.Label(conn_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.username_var = tk.StringVar(value="admin")
        self.username_entry = ttk.Entry(conn_frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        # SSH Password
        ttk.Label(conn_frame, text="SSH Password:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ssh_password_var = tk.StringVar(value="THS!5V3r5@vmsP@55")
        self.ssh_password_entry = ttk.Entry(conn_frame, textvariable=self.ssh_password_var, 
                                          show="*", width=30)
        self.ssh_password_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        # Admin Password (for sudo su)
        ttk.Label(conn_frame, text="Admin Password:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.admin_password_var = tk.StringVar(value="THS!5V3r5@vmsP@55")
        self.admin_password_entry = ttk.Entry(conn_frame, textvariable=self.admin_password_var, 
                                            show="*", width=30)
        self.admin_password_entry.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        # Connection button
        self.connect_button = ttk.Button(conn_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Connection status
        self.status_label = ttk.Label(conn_frame, text="Status: Not Connected", 
                                    foreground="red")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=5)
        
        # Operations Panel
        ops_frame = ttk.LabelFrame(parent, text="Operations", padding="10")
        ops_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Kubectl commands button
        self.kubectl_button = ttk.Button(ops_frame, text="Run Kubectl Commands", 
                                       command=self.run_kubectl_commands, state=tk.DISABLED)
        self.kubectl_button.pack(fill=tk.X, pady=5)
        
        # Build tenant data button
        self.tenant_button = ttk.Button(ops_frame, text="Build Tenant Data", 
                                      command=self.build_tenant_data, state=tk.DISABLED)
        self.tenant_button.pack(fill=tk.X, pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(ops_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Clear output button
        self.clear_button = ttk.Button(ops_frame, text="Clear Output", 
                                     command=self.clear_output)
        self.clear_button.pack(fill=tk.X, pady=5)
        
        # Disconnect button
        self.disconnect_button = ttk.Button(ops_frame, text="Disconnect", 
                                          command=self.disconnect_from_server, state=tk.DISABLED)
        self.disconnect_button.pack(fill=tk.X, pady=5)
    
    def setup_output_panel(self, parent):
        """Setup the command output display panel"""
        output_frame = ttk.LabelFrame(parent, text="Command Execution Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrolled text widget for output
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=30,
            font=('Consolas', 10)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for different types of output
        self.output_text.tag_config("command", foreground="blue", font=('Consolas', 10, 'bold'))
        self.output_text.tag_config("success", foreground="green")
        self.output_text.tag_config("error", foreground="red")
        self.output_text.tag_config("info", foreground="purple")
        self.output_text.tag_config("timestamp", foreground="gray")
    
    def log_output(self, message, tag="normal"):
        """Add message to output display with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to queue for thread-safe GUI updates
        self.output_queue.put((message, tag, timestamp))
    
    def process_output(self):
        """Process queued output messages (runs in main thread)"""
        try:
            while True:
                message, tag, timestamp = self.output_queue.get_nowait()
                
                # Insert timestamp
                self.output_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                
                # Insert message with appropriate tag
                self.output_text.insert(tk.END, f"{message}\n", tag)
                
                # Auto-scroll to bottom
                self.output_text.see(tk.END)
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_output)
    
    def clear_output(self):
        """Clear the output display"""
        self.output_text.delete(1.0, tk.END)
    
    def connect_to_server(self):
        """Connect to the SSH server in a separate thread"""
        if self.connected:
            messagebox.showwarning("Already Connected", "Already connected to server")
            return
        
        # Validate inputs
        if not all([self.ip_var.get(), self.username_var.get(), 
                   self.ssh_password_var.get(), self.admin_password_var.get()]):
            messagebox.showerror("Input Error", "Please fill in all connection fields")
            return
        
        # Start connection in separate thread
        self.connect_button.config(state=tk.DISABLED)
        self.progress.start()
        
        thread = threading.Thread(target=self._connect_thread, daemon=True)
        thread.start()
    
    def _connect_thread(self):
        """SSH connection thread"""
        try:
            self.log_output("Attempting SSH connection...", "info")
            
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            self.ssh_client.connect(
                hostname=self.ip_var.get(),
                username=self.username_var.get(),
                password=self.ssh_password_var.get(),
                look_for_keys=False,
                timeout=10
            )
            
            self.log_output(f"SSH connection successful to {self.ip_var.get()}", "success")
            
            # Create shell
            self.shell = self.ssh_client.invoke_shell()
            time.sleep(1)
            self.shell.recv(10000)  # Clear banner
            
            self.log_output("Shell session established", "success")
            
            # Execute sudo su
            self.log_output("Executing 'sudo su' command...", "command")
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
            self.shell.send(self.admin_password_var.get() + "\n")
            time.sleep(1.5)
            
            # Check if sudo was successful
            output = self.shell.recv(10000).decode('utf-8', errors='ignore')
            self.log_output("Sudo elevation successful", "success")
            
            # Set kubectl alias
            self.log_output("Setting kubectl alias...", "info")
            self.shell.send("alias k=kubectl\n")
            time.sleep(0.5)
            self.shell.recv(10000).decode('utf-8', errors='ignore')  # Clear response
            
            # Update GUI state
            self.connected = True
            self.root.after(0, self._connection_success)
            
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.log_output(error_msg, "error")
            self.root.after(0, self._connection_failed)
    
    def _connection_success(self):
        """Handle successful connection (main thread)"""
        self.progress.stop()
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        self.kubectl_button.config(state=tk.NORMAL)
        self.tenant_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Connected", foreground="green")
        
        # Disable editing of connection fields
        for entry in [self.ip_entry, self.username_entry, self.ssh_password_entry, self.admin_password_entry]:
            entry.config(state=tk.DISABLED)
    
    def _connection_failed(self):
        """Handle failed connection (main thread)"""
        self.progress.stop()
        self.connect_button.config(state=tk.NORMAL)
        self.connected = False
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
            self.ssh_client = None
            self.shell = None
    
    def disconnect_from_server(self):
        """Disconnect from SSH server"""
        if not self.connected:
            return
        
        try:
            self.log_output("Disconnecting from server...", "info")
            if self.shell:
                self.shell.send("exit\n")
                time.sleep(0.5)
            if self.ssh_client:
                self.ssh_client.close()
        except Exception as e:
            self.log_output(f"Error during disconnect: {str(e)}", "error")
        
        # Reset connection state
        self.connected = False
        self.ssh_client = None
        self.shell = None
        
        # Update GUI
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.kubectl_button.config(state=tk.DISABLED)
        self.tenant_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Not Connected", foreground="red")
        
        # Re-enable connection fields
        for entry in [self.ip_entry, self.username_entry, self.ssh_password_entry, self.admin_password_entry]:
            entry.config(state=tk.NORMAL)
        
        self.log_output("Disconnected from server", "info")
    
    def run_kubectl_commands(self):
        """Run basic kubectl commands"""
        if not self.connected:
            messagebox.showerror("Not Connected", "Please connect to server first")
            return
        
        self.progress.start()
        thread = threading.Thread(target=self._run_kubectl_thread, daemon=True)
        thread.start()
    
    def _run_kubectl_thread(self):
        """Run kubectl commands in separate thread"""
        commands = [
            ("kubectl get ns", "Get all namespaces"),
            ("kubectl get pods -A", "Get all pods across all namespaces"),
            ("kubectl get svc -A", "Get all services across all namespaces"),
            ("kubectl get pv", "Get persistent volumes"),
            ("kubectl get pvc -A", "Get persistent volume claims"),
            ("kubectl get cm -A", "Get config maps"),
            ("kubectl get svc -A | grep redis", "Get Redis services")
        ]
        
        try:
            self.log_output("Starting kubectl commands execution...", "info")
            
            for command, description in commands:
                self.log_output(f"Running: {command}", "command")
                self.log_output(f"Description: {description}", "info")
                
                # Execute command
                self.shell.send(f"{command}\n")
                time.sleep(3)
                
                # Collect output
                output = self._collect_command_output()
                
                # Clean and display output
                cleaned_output = self._clean_ansi_codes(output)
                lines = cleaned_output.split('\n')
                
                line_count = 0
                for line in lines:
                    line = line.strip()
                    if (line and not line.startswith('kubectl') and 
                        not line.endswith('# ') and not line.endswith('$ ') and
                        not line.startswith('[root@')):
                        self.log_output(f"  {line}", "normal")
                        line_count += 1
                
                self.log_output(f"-> Collected {line_count} lines of output", "success")
                self.log_output("", "normal")  # Empty line for separation
            
            self.log_output("All kubectl commands completed successfully!", "success")
            
        except Exception as e:
            self.log_output(f"Error running kubectl commands: {str(e)}", "error")
        
        finally:
            self.root.after(0, lambda: self.progress.stop())
    
    def build_tenant_data(self):
        """Build comprehensive tenant data"""
        if not self.connected:
            messagebox.showerror("Not Connected", "Please connect to server first")
            return
        
        self.progress.start()
        thread = threading.Thread(target=self._build_tenant_thread, daemon=True)
        thread.start()
    
    def _build_tenant_thread(self):
        """Build tenant data in separate thread"""
        try:
            self.log_output("Building comprehensive tenant data structure...", "info")
            
            # Step 1: Get all services
            self.log_output("Step 1: Getting all services...", "command")
            self.shell.send("kubectl get svc -A\n")
            time.sleep(2)
            kubectl_output = self._collect_command_output()
            
            # Parse tenant services
            tenant_data = self._parse_kubectl_output(kubectl_output)
            service_count = len(tenant_data)
            self.log_output(f"-> Found {service_count} tenant namespaces", "success")
            
            # Step 2: Get Redis information
            self.log_output("Step 2: Getting Redis information...", "command")
            redis_info = self._extract_redis_ips()
            redis_count = len(redis_info)
            self.log_output(f"-> Found {redis_count} Redis services", "success")
            
            # Step 3: Integrate Redis information
            self.log_output("Step 3: Integrating Redis information with tenant data...", "info")
            for tenant, redis_details in redis_info.items():
                if tenant in tenant_data:
                    tenant_data[tenant]['redis_info'] = redis_details
                else:
                    tenant_data[tenant] = {
                        'services': ['redis'],
                        'redis_info': redis_details
                    }
            
            # Display results
            self.log_output("", "normal")
            self.log_output("=== TENANT DATA SUMMARY ===", "success")
            
            for tenant, data in tenant_data.items():
                services = ', '.join(data.get('services', []))
                redis_ip = data.get('redis_info', {}).get('cluster_ip', 'N/A')
                self.log_output(f"Tenant: {tenant}", "info")
                self.log_output(f"  Services: {services}", "normal")
                self.log_output(f"  Redis IP: {redis_ip}", "normal")
                self.log_output("", "normal")
            
            # Save to file
            filename = f"tenant_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                with open(filename, 'w') as f:
                    json.dump(tenant_data, f, indent=2)
                self.log_output(f"Tenant data saved to: {filename}", "success")
            except Exception as e:
                self.log_output(f"Error saving tenant data: {str(e)}", "error")
            
            self.log_output("Tenant data building completed successfully!", "success")
            
        except Exception as e:
            self.log_output(f"Error building tenant data: {str(e)}", "error")
        
        finally:
            self.root.after(0, lambda: self.progress.stop())
    
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
    
    def _clean_ansi_codes(self, text):
        """Remove ANSI escape codes from text"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def _parse_kubectl_output(self, output):
        """Parse kubectl get svc -A output and extract tenant information"""
        tenant_services = {}
        cleaned_output = self._clean_ansi_codes(output)
        lines = cleaned_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('NAMESPACE') or line.startswith('kubectl'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                namespace = parts[0]
                service = parts[1]
                
                # Skip system namespaces
                if namespace in ['kube-system', 'kube-public', 'kube-node-lease', 'default']:
                    continue
                
                if namespace not in tenant_services:
                    tenant_services[namespace] = {
                        'services': [],
                        'redis_info': None
                    }
                
                if service not in tenant_services[namespace]['services']:
                    tenant_services[namespace]['services'].append(service)
        
        return tenant_services
    
    def _extract_redis_ips(self):
        """Extract Redis service IPs for each tenant/namespace"""
        self.shell.send("kubectl get svc -A | grep redis\n")
        time.sleep(2)
        
        output = self._collect_command_output()
        cleaned_output = self._clean_ansi_codes(output)
        
        redis_info = {}
        lines = cleaned_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('kubectl') or line.endswith('# ') or line.endswith('$ '):
                continue
            
            parts = line.split()
            if len(parts) >= 4 and 'redis' in line.lower():
                namespace = parts[0]
                service_name = parts[1]
                service_type = parts[2]
                cluster_ip = parts[3]
                external_ip = parts[4] if len(parts) > 4 else "N/A"
                ports = parts[5] if len(parts) > 5 else "N/A"
                age = parts[6] if len(parts) > 6 else "N/A"
                
                redis_info[namespace] = {
                    'service_name': service_name,
                    'service_type': service_type,
                    'cluster_ip': cluster_ip,
                    'external_ip': external_ip,
                    'ports': ports,
                    'age': age
                }
        
        return redis_info

def main():
    """Main function to start the GUI application"""
    root = tk.Tk()
    app = VMSDebugGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.connected:
            app.disconnect_from_server()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
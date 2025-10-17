#!/usr/bin/env python3

import paramiko
import sys

def test_ssh_connection(host, username, password):
    """Test SSH connection with detailed error reporting"""
    try:
        print(f"Testing SSH connection to {host}")
        print(f"Username: {username}")
        
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print("Attempting to connect...")
        
        # Connect with detailed timeout and error handling
        ssh.connect(
            host,
            username=username, 
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )
        
        print("✅ SSH connection successful!")
        
        # Test a simple command
        stdin, stdout, stderr = ssh.exec_command('whoami')
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if output:
            print(f"✅ Command test successful: {output}")
        if error:
            print(f"⚠️  Command stderr: {error}")
        
        ssh.close()
        print("✅ Connection closed successfully")
        return True
        
    except paramiko.AuthenticationException as e:
        print(f"❌ Authentication failed: {str(e)}")
        print("   - Check username and password")
        return False
        
    except paramiko.SSHException as e:
        print(f"❌ SSH Error: {str(e)}")
        return False
        
    except paramiko.socket.timeout as e:
        print(f"❌ Connection timeout: {str(e)}")
        print("   - Check if host is reachable")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print(f"   - Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    # Test the connection with your credentials
    host = "10.70.188.169"  # Replace with your VMS IP
    username = "admin"
    password = "THS!5V3r5@vmsP@55"
    
    print("VMS SSH Connection Test")
    print("=" * 50)
    
    success = test_ssh_connection(host, username, password)
    
    if success:
        print("\n🎉 SSH connection is working correctly!")
    else:
        print("\n❌ SSH connection failed. Please check the output above for details.")
    
    sys.exit(0 if success else 1)
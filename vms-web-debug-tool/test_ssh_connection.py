#!/usr/bin/env python3
"""
Standalone VMS SSH Connection Tester
Run this script to test SSH connectivity to your VMS server before starting the application
"""

import paramiko
import socket
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vms_ssh_connection():
    """Test SSH connection to VMS server with detailed diagnostics"""
    
    host = '10.70.188.171'
    username = 'admin'
    password = 'THS!5V3r5@vmsP@55'
    port = 22
    timeout = 10
    
    print("=" * 70)
    print("VMS SSH Connection Diagnostic Test")
    print("=" * 70)
    print(f"Target Server: {host}:{port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print("-" * 70)
    
    success_count = 0
    total_tests = 4
    
    try:
        # Test 1: Network connectivity
        print("🔍 Test 1: Network Connectivity")
        print(f"   Checking if {host}:{port} is reachable...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("   ✅ Network connectivity: SUCCESS")
            success_count += 1
        else:
            print(f"   ❌ Network connectivity: FAILED (Error code: {result})")
            print("      Possible issues:")
            print("      - VMS server is down")
            print("      - Wrong IP address")
            print("      - Firewall blocking connection")
            print("      - Network routing issues")
        
        # Test 2: SSH service availability
        print("\n🔍 Test 2: SSH Service Detection")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            sock.connect((host, port))
            banner = sock.recv(1024).decode().strip()
            sock.close()
            
            if 'SSH' in banner:
                print(f"   ✅ SSH service detected: {banner}")
                success_count += 1
            else:
                print(f"   ❌ Unexpected service response: {banner}")
        except Exception as e:
            print(f"   ❌ SSH service detection failed: {str(e)}")
        
        # Test 3: SSH authentication
        print("\n🔍 Test 3: SSH Authentication")
        print("   Attempting SSH login...")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                host,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                look_for_keys=False,
                allow_agent=False,
                auth_timeout=timeout
            )
            print("   ✅ SSH authentication: SUCCESS")
            success_count += 1
            
            # Test 4: Command execution
            print("\n🔍 Test 4: Command Execution")
            print("   Executing test command 'whoami'...")
            
            stdin, stdout, stderr = ssh.exec_command('whoami', timeout=5)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if output:
                print(f"   ✅ Command execution: SUCCESS")
                print(f"      Logged in as: {output}")
                success_count += 1
            else:
                print("   ⚠️  Command executed but no output")
            
            if error:
                print(f"   ⚠️  Command stderr: {error}")
            
            ssh.close()
            
        except paramiko.AuthenticationException as e:
            print(f"   ❌ SSH authentication: FAILED - {str(e)}")
            print("      Possible issues:")
            print("      - Wrong username or password")
            print("      - Account locked or disabled")
            print("      - SSH server denying password authentication")
            
        except Exception as e:
            print(f"   ❌ SSH connection error: {str(e)}")
    
    except KeyboardInterrupt:
        print("\n   ⚠️  Test interrupted by user")
        return False
    
    except Exception as e:
        print(f"\n   ❌ Unexpected error: {str(e)}")
        return False
    
    # Results summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED - VMS SSH connection is ready!")
        print("   You can start the VMS Debug Tool application.")
        return True
    elif success_count >= 3:
        print("⚠️  MOSTLY SUCCESSFUL - Minor issues detected")
        print("   The application should work but may have some limitations.")
        return True
    elif success_count >= 1:
        print("❌ PARTIAL FAILURE - Significant issues detected")
        print("   Please fix the connection issues before starting the application.")
        return False
    else:
        print("❌ COMPLETE FAILURE - SSH connection not working")
        print("   Please check all connection parameters and try again.")
        return False

def main():
    """Main function"""
    print("VMS SSH Connection Tester")
    print("This tool will test SSH connectivity to your VMS server\n")
    
    success = test_vms_ssh_connection()
    
    print("\nNext steps:")
    if success:
        print("✅ You can now start the VMS Debug Tool application:")
        print("   python app/app.py")
    else:
        print("❌ Please fix the SSH connection issues first:")
        print("   1. Verify VMS server IP address")
        print("   2. Check username and password")
        print("   3. Ensure SSH service is running")
        print("   4. Check network connectivity")
        print("   5. Run this test again")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
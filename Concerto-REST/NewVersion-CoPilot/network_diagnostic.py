#!/usr/bin/env python3
"""
Network Diagnostic Tool for Concerto ECP Server
Helps identify connectivity issues before running the main script.
"""

import socket
import subprocess
import sys
import requests
import time
from urllib.parse import urlparse

def test_ping(host):
    """Test basic ping connectivity."""
    print(f"🏓 Testing ping to {host}...")
    try:
        # Use ping command (works on both Windows and Linux)
        result = subprocess.run(['ping', '-n', '3', host], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f"✅ Ping successful to {host}")
            return True
        else:
            print(f"❌ Ping failed to {host}")
            print(f"Output: {result.stdout}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Ping timeout to {host}")
        return False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False

def test_port_connectivity(host, port):
    """Test if a specific port is open and accepting connections."""
    print(f"🔌 Testing port connectivity to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is open on {host}")
            return True
        else:
            print(f"❌ Port {port} is closed or filtered on {host}")
            return False
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed for {host}: {e}")
        return False
    except Exception as e:
        print(f"❌ Port test error: {e}")
        return False

def test_https_response(host, port):
    """Test HTTPS response from the server."""
    print(f"🔐 Testing HTTPS response from {host}:{port}...")
    try:
        url = f"https://{host}:{port}/"
        response = requests.get(url, timeout=10, verify=False)
        print(f"✅ HTTPS response received: HTTP {response.status_code}")
        return True
    except requests.exceptions.ConnectTimeout:
        print(f"⏰ HTTPS connection timeout to {host}:{port}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTPS connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ HTTPS test error: {e}")
        return False

def get_network_info():
    """Get basic network information."""
    print("🌐 Network Information:")
    try:
        # Get default gateway
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Default Gateway' in line and '.' in line:
                gateway = line.split(':')[-1].strip()
                if gateway:
                    print(f"   Default Gateway: {gateway}")
                    break
        
        # Get current IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"   Local IP: {local_ip}")
        print(f"   Hostname: {hostname}")
        
    except Exception as e:
        print(f"   Could not get network info: {e}")

def main():
    """Run comprehensive network diagnostics."""
    print("=" * 70)
    print("🔧 Concerto ECP Server - Network Diagnostics")
    print("=" * 70)
    
    # Configuration
    ECP_IP = "10.73.70.70"
    ECP_PORT = 9182
    
    print(f"Target Server: {ECP_IP}:{ECP_PORT}")
    print("-" * 70)
    
    # Get network info
    get_network_info()
    print("-" * 70)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Ping
    if test_ping(ECP_IP):
        tests_passed += 1
    
    print("-" * 70)
    
    # Test 2: Port connectivity
    if test_port_connectivity(ECP_IP, ECP_PORT):
        tests_passed += 1
    
    print("-" * 70)
    
    # Test 3: HTTPS response
    if test_https_response(ECP_IP, ECP_PORT):
        tests_passed += 1
    
    print("-" * 70)
    
    # Summary
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == 0:
        print("\n❌ COMPLETE CONNECTIVITY FAILURE")
        print("Possible causes:")
        print("  • Server is down or not running")
        print("  • Network firewall blocking connection")
        print("  • Incorrect IP address")
        print("  • VPN or network routing issues")
        print("  • Different network segment (server not accessible from here)")
        
    elif tests_passed == 1:
        print("\n⚠️  PARTIAL CONNECTIVITY")
        print("  • Basic network connectivity exists (ping works)")
        print("  • But specific port 9182 is not accessible")
        print("  • Server may not be running Concerto service")
        print("  • Port may be blocked by firewall")
        
    elif tests_passed == 2:
        print("\n🟡 PORT ACCESSIBLE BUT HTTPS ISSUES")
        print("  • Network and port connectivity work")
        print("  • HTTPS service may have certificate issues")
        print("  • Service may not be fully started")
        
    else:
        print("\n✅ ALL TESTS PASSED!")
        print("  • Server appears to be accessible")
        print("  • The authentication issue may be credentials-related")
        print("  • Try running the main script again")
    
    print("\n" + "=" * 70)
    
    # Offer to test different IP
    test_other = input("\nWould you like to test a different IP address? (y/n): ").strip().lower()
    if test_other == 'y':
        new_ip = input("Enter IP address to test: ").strip()
        if new_ip:
            print(f"\n🔄 Testing {new_ip}:{ECP_PORT}...")
            test_ping(new_ip)
            test_port_connectivity(new_ip, ECP_PORT)
            test_https_response(new_ip, ECP_PORT)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced error handling with popups
"""

import sys
import os
import importlib.util

# Load the module
spec = importlib.util.spec_from_file_location("vms_debug_web", "/home/versa/pgudipati/SAMBA-70-188-169/apps-for-learning-and-fun/VMS-Versa/VMS-Debug-Tool-Web.py")
vms_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vms_module)

def test_error_analysis():
    """Test the error analysis functionality"""
    print("Testing Enhanced Error Analysis...")
    
    # Create a VMS instance
    vms = vms_module.VMSDebugWeb()
    
    # Test different types of errors
    test_cases = [
        {
            'name': 'DNS Resolution Error',
            'error': Exception("[Errno -2] Name or service not known"),
            'host': 'invalid-host.example.com',
            'username': 'testuser'
        },
        {
            'name': 'Connection Refused',
            'error': Exception("Connection refused"),
            'host': '192.168.1.100',
            'username': 'admin'
        },
        {
            'name': 'Connection Timeout',
            'error': Exception("Connection timed out"),
            'host': '10.1.1.1',
            'username': 'admin'
        },
        {
            'name': 'Authentication Failed',
            'error': Exception("Authentication failed. permission denied"),
            'host': 'server.example.com',
            'username': 'wronguser'
        },
        {
            'name': 'SSH Protocol Error',
            'error': Exception("SSH protocol version 1.5 not supported"),
            'host': 'old-server.com',
            'username': 'admin'
        },
        {
            'name': 'Unknown Error',
            'error': Exception("Some unexpected error occurred"),
            'host': 'server.com',
            'username': 'user'
        }
    ]
    
    print(f"{'='*80}")
    print("ERROR ANALYSIS RESULTS")
    print(f"{'='*80}")
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"   Error: {test_case['error']}")
        print(f"   Host: {test_case['host']}")
        print(f"   Username: {test_case['username']}")
        
        # Analyze the error
        result = vms._analyze_connection_error(
            test_case['error'], 
            test_case['host'], 
            test_case['username']
        )
        
        print(f"\n   📊 Analysis Result:")
        print(f"   Type: {result['type']}")
        print(f"   Title: {result['title']}")
        print(f"   Message: {result['simple_message']}")
        print(f"   Suggestions: {len(result['suggestions'])} available")
        
        # Show first suggestion as example
        if result['suggestions']:
            print(f"   First suggestion: {result['suggestions'][0]}")
        
        print(f"   {'-'*60}")
    
    print(f"\n✅ All error types analyzed successfully!")
    print(f"\n📝 Summary of Features:")
    print(f"   • DNS Resolution errors → Clear hostname troubleshooting")
    print(f"   • Network errors → Connectivity and firewall guidance") 
    print(f"   • Timeout errors → Performance and load suggestions")
    print(f"   • Auth errors → Credential and permission help")
    print(f"   • SSH errors → Protocol and configuration advice")
    print(f"   • Unknown errors → General troubleshooting steps")
    print(f"\n🎯 When connection fails, users will see:")
    print(f"   • Descriptive popup window with error details")
    print(f"   • Specific troubleshooting suggestions")
    print(f"   • Copy-to-clipboard functionality")
    print(f"   • Expandable technical details")

if __name__ == "__main__":
    test_error_analysis()
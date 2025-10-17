#!/usr/bin/env python3
"""
Test script to demonstrate the new persistent logging functionality
"""

import os
import sys
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the VMSDebugWeb class
# Load the module by executing the file
import importlib.util
spec = importlib.util.spec_from_file_location("vms_debug_web", "/home/versa/pgudipati/SAMBA-70-188-169/apps-for-learning-and-fun/VMS-Versa/VMS-Debug-Tool-Web.py")
vms_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vms_module)
VMSDebugWeb = vms_module.VMSDebugWeb

def test_logging():
    """Test the new persistent logging functionality"""
    print("Testing VMS Debug Tool Persistent Logging...")
    
    # Create an instance (this will initialize the log file)
    vms_tool = VMSDebugWeb()
    
    print(f"Log file created at: {vms_tool.persistent_log_file}")
    
    # Test session start logging
    vms_tool.start_new_session_log()
    
    # Test various log operations
    vms_tool.log_output("This is a test connection message", "info")
    vms_tool.log_output("Test kubectl command executed", "command")
    vms_tool.log_output("Operation completed successfully", "success")
    
    # Test operation start logging
    vms_tool.start_new_operation_log("Test Tenant Data Building")
    vms_tool.log_output("Building tenant database...", "info")
    vms_tool.log_output("Found 5 tenants", "success")
    
    # Test another operation
    vms_tool.start_new_operation_log("Test Redis Key Extraction")
    vms_tool.log_output("Extracting Redis keys for tenant: test-tenant", "info")
    vms_tool.log_output("Found 25 Redis keys", "success")
    
    # Test error logging
    vms_tool.log_output("This is a test error message", "error")
    
    print("\nLogging test completed!")
    print(f"Check the log file: {vms_tool.persistent_log_file}")
    
    # Display the log file content
    if os.path.exists(vms_tool.persistent_log_file):
        print(f"\n{'='*80}")
        print("LOG FILE CONTENT:")
        print(f"{'='*80}")
        
        with open(vms_tool.persistent_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        
        print(f"{'='*80}")
        print(f"Log file size: {os.path.getsize(vms_tool.persistent_log_file)} bytes")

if __name__ == "__main__":
    test_logging()
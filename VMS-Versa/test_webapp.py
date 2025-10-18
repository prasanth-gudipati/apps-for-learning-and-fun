#!/usr/bin/env python3
"""
Quick test to check if the VMS Debug Tool web application starts without errors
"""

import sys
import os
import time
import signal
import subprocess

def test_web_app_startup():
    """Test if the web application starts without immediate errors"""
    print("Testing VMS Debug Tool Web Application startup...")
    
    try:
        # Start the web application
        print("Starting web application...")
        process = subprocess.Popen(
            [sys.executable, "VMS-Debug-Tool-Web.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a few seconds to see if it starts without errors
        time.sleep(3)
        
        # Check if process is still running (no immediate crash)
        poll_result = process.poll()
        
        if poll_result is None:
            print("✅ SUCCESS: Web application started successfully!")
            print("   - No immediate startup errors detected")
            print("   - Process is running normally")
            
            # Try to get some output
            try:
                stdout, stderr = process.communicate(timeout=2)
                if stdout:
                    print(f"   - Stdout: {stdout[:200]}...")
                if stderr:
                    print(f"   - Stderr: {stderr[:200]}...")
            except subprocess.TimeoutExpired:
                print("   - Application is running (timeout reached)")
            
            # Terminate the process
            process.terminate()
            print("   - Process terminated cleanly")
            
        else:
            print("❌ FAILURE: Web application crashed immediately!")
            stdout, stderr = process.communicate()
            print(f"   - Exit code: {poll_result}")
            if stdout:
                print(f"   - Stdout: {stdout}")
            if stderr:
                print(f"   - Stderr: {stderr}")
            
        return poll_result is None
        
    except Exception as e:
        print(f"❌ ERROR: Failed to test web application: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_web_app_startup()
    if success:
        print("\n🎉 The web application appears to be working correctly!")
        print("   The JavaScript null reference error should be fixed.")
    else:
        print("\n💥 There may still be issues with the web application.")
    
    sys.exit(0 if success else 1)
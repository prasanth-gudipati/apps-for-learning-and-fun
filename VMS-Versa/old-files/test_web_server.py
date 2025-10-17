#!/usr/bin/env python3
"""
Simple test to start the web server and check for any immediate errors
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the web app (using importlib since filename has hyphens)
    import importlib.util
    spec = importlib.util.spec_from_file_location("vms_web", "VMS-Debug-Tool-Web.py")
    vms_web = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vms_web)
    
    app = vms_web.app
    socketio = vms_web.socketio
    print("✅ Successfully imported web application modules")
    
    # Test if templates directory exists
    if os.path.exists('templates'):
        print("✅ Templates directory exists")
        if os.path.exists('templates/index.html'):
            print("✅ HTML template file exists")
        else:
            print("❌ HTML template file missing")
    else:
        print("❌ Templates directory missing")
    
    print("🚀 Starting web server on http://localhost:5000")
    print("📋 Use Ctrl+C to stop the server")
    print("🔧 Debug mode enabled - check console for debug messages")
    
    # Start the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all required packages are installed:")
    print("   pip install flask flask-socketio paramiko")
except Exception as e:
    print(f"❌ Error starting web server: {e}")
    import traceback
    traceback.print_exc()
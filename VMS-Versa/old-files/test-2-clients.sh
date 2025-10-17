#!/bin/bash

# VMS Debug Tool - Multi-Session Test Script
# This script helps you test the multi-session functionality with 2 clients

echo "=================================================================="
echo "VMS Debug Tool - Multi-Session Test with 2 Clients"
echo "=================================================================="
echo ""
echo "Server Status: ✅ Running at http://localhost:5000"
echo ""
echo "🧪 TEST INSTRUCTIONS:"
echo ""
echo "1. OPEN CLIENT 1:"
echo "   Open your web browser and go to: http://localhost:5000"
echo "   This will be your first client session."
echo ""
echo "2. OPEN CLIENT 2:"
echo "   Open a NEW browser window/tab (or use a different browser)"
echo "   Go to: http://localhost:5000"
echo "   This will be your second client session."
echo ""
echo "3. TEST SCENARIOS:"
echo ""
echo "   📋 Scenario A: Basic Session Isolation"
echo "   - In Client 1: Fill in connection details but DON'T connect yet"
echo "   - In Client 2: Check that it shows 'Not Connected' (independent state)"
echo "   - In Client 1: Click Connect"
echo "   - In Client 2: Verify it still shows 'Not Connected'"
echo ""
echo "   📋 Scenario B: Independent Connections" 
echo "   - In Client 1: Connect to server and run 'Run Kubectl Commands'"
echo "   - In Client 2: Connect to the SAME or DIFFERENT server"
echo "   - Verify both sessions work independently"
echo ""
echo "   📋 Scenario C: Tenant Data Isolation"
echo "   - In Client 1: Build tenant data"
echo "   - In Client 2: Check that tenant dropdown is empty until it builds its own data"
echo "   - In Client 2: Build tenant data"
echo "   - Verify each session has its own tenant data"
echo ""
echo "   📋 Scenario D: Command Output Isolation"
echo "   - In both clients: Run kubectl commands simultaneously"
echo "   - Verify outputs appear only in their respective sessions"
echo ""
echo "4. EXPECTED RESULTS:"
echo "   ✅ Each browser window maintains separate connection status"
echo "   ✅ Command outputs don't mix between sessions"
echo "   ✅ Tenant data is session-specific"
echo "   ✅ Closing one session doesn't affect the other"
echo ""
echo "5. MONITOR SERVER LOGS:"
echo "   Watch the terminal where the server is running to see:"
echo "   - Different session IDs being created"
echo "   - Debug messages showing session isolation"
echo "   - Cleanup messages when sessions disconnect"
echo ""
echo "=================================================================="
echo "🚀 QUICK TEST LINKS:"
echo ""
echo "Client 1: http://localhost:5000"
echo "Client 2: http://localhost:5000"
echo ""
echo "Or use the test page: file://$(pwd)/test-multi-session.html"
echo "=================================================================="

# Check if the server is actually running
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo "✅ Server is running and responding"
else
    echo "❌ Server is not responding. Please check if it's running."
fi

echo ""
echo "Press any key to open test page in browser..."
read -n 1 -s

# Try to open the test page in browser
if command -v xdg-open > /dev/null 2>&1; then
    xdg-open "file://$(pwd)/test-multi-session.html"
elif command -v open > /dev/null 2>&1; then
    open "file://$(pwd)/test-multi-session.html"
else
    echo "Please manually open: file://$(pwd)/test-multi-session.html in your browser"
fi
# VMS Debug Tool - Web Interface

A comprehensive web-based application for connecting to VMS servers and executing kubectl commands with real-time display and tenant management capabilities.

## Features

### Core Functionality
- **SSH Connection Management**: Secure connection to VMS servers with automatic sudo elevation
- **Real-time Command Execution**: Live streaming of kubectl command output via WebSocket
- **Tenant Data Management**: Comprehensive tenant discovery and data visualization
- **Interactive UI**: Progressive disclosure of features based on connection state
- **Automatic Reset**: Complete UI cleanup on disconnect for fresh user experience

### Supported Operations

#### 1. Basic kubectl Commands
- Get namespaces (`kubectl get ns`)
- Get pods across all namespaces (`kubectl get pods -A`)
- Get services across all namespaces (`kubectl get svc -A`) 
- Get persistent volumes (`kubectl get pv`)
- Get persistent volume claims (`kubectl get pvc -A`)
- Get config maps (`kubectl get cm -A`)
- Filter Redis services (`kubectl get svc -A | grep redis`)

#### 2. Tenant Database Building
- Discovers all tenant namespaces from services
- Extracts Redis service information per tenant
- Collects ConfigMaps information per tenant
- Builds comprehensive tenant database with relationships
- Saves data to timestamped JSON files

#### 3. Redis Key Management
- Lists all Redis keys per tenant using `redis-cli keys "*"`
- Displays key values using `redis-cli hgetall "<key>"`
- Handles JSON parsing and escaping in Redis values
- Interactive key selection and viewing

#### 4. ConfigMap Management
- Lists all ConfigMaps per tenant
- Shows ConfigMap metadata (name, data count, age)
- Displays raw ConfigMap output using `kubectl get configmap <name> -n <tenant>`
- Clean, unprocessed kubectl output display

## UI Components

### Connection Panel
- **Server IP**: Pre-configured with default VMS server
- **Username**: Default admin username
- **SSH Password**: SSH authentication credentials  
- **Admin Password**: Sudo elevation password
- **Connect/Disconnect**: Connection management buttons
- **Status Indicator**: Real-time connection status display

### Operations Panel
- **Run Kubectl Commands**: Execute basic kubectl discovery commands
- **Build Tenant Data**: Comprehensive tenant database building
- **Show Tenant Database**: Display complete tenant database in JSON format

### Dynamic Sections (Appear After Tenant Data Building)

#### Tenant Selection
- **Tenant Dropdown**: Select from discovered tenants
- **Refresh List**: Update tenant list from current data

#### Redis Keys Section
- **Key Dropdown**: Select from discovered Redis keys for chosen tenant
- **Refresh Keys**: Re-scan Redis keys for current tenant
- **View Key Value**: Display formatted Redis key value

#### ConfigMaps Section  
- **ConfigMap Dropdown**: Select from available ConfigMaps for chosen tenant
- **Refresh ConfigMaps**: Re-scan ConfigMaps for current tenant
- **Show Config-Map**: Display raw kubectl ConfigMap output

### Output Panels

#### Command Execution Output
- **Real-time Streaming**: Live command output with timestamps
- **Color-coded Messages**: Different colors for commands, success, errors, info
- **Auto-scrolling**: Automatic scroll to latest output
- **Clear Function**: Clear output history

#### Tenant Details Panel
- **Structured Data Display**: Formatted tenant information
- **Redis Key Values**: Pretty-printed JSON and text values
- **ConfigMap Raw Output**: Clean kubectl command output
- **Debug Information**: Raw command output when needed

## Technical Architecture

### Backend (Python Flask-SocketIO)
- **Flask-SocketIO**: Real-time WebSocket communication
- **Paramiko**: SSH client for secure server connections
- **Threading**: Background command execution to prevent UI blocking
- **JSON Processing**: Data parsing and validation
- **ANSI Cleaning**: Remove terminal escape codes for clean output

### Frontend (HTML/JavaScript)
- **Socket.IO Client**: Real-time communication with backend
- **Progressive UI**: Dynamic show/hide based on application state
- **Event-driven**: Responsive to user actions and server events
- **State Management**: Automatic UI reset and cleanup

### Key Classes and Methods

#### VMSDebugWeb Class
- `connect_to_server()`: Establish SSH connection with sudo elevation
- `disconnect_from_server()`: Clean disconnect and state reset
- `run_kubectl_commands()`: Execute basic kubectl discovery commands
- `build_tenant_data()`: Comprehensive tenant database building
- `extract_redis_keys_for_tenant()`: Get Redis keys for specific tenant
- `get_redis_key_value()`: Retrieve and parse Redis key values
- `get_configmap_json_details()`: Get raw ConfigMap output
- `_extract_configmaps_for_all_tenants()`: Discover all ConfigMaps

#### Socket Event Handlers
- `ssh_connect`: Handle connection requests
- `ssh_disconnect`: Handle disconnection requests
- `run_kubectl`: Execute kubectl commands
- `build_tenant_data`: Build comprehensive tenant database
- `get_redis_keys`: Get Redis keys for tenant
- `get_redis_key_value`: Get specific Redis key value
- `get_configmaps`: Get ConfigMaps for tenant
- `get_configmap_json_details`: Get raw ConfigMap details

## Usage Workflow

### 1. Initial Connection
1. Enter server credentials (defaults provided)
2. Click "Connect" button
3. Wait for SSH connection and sudo elevation
4. Connection status updates in real-time

### 2. Basic Operations
1. Click "Run Kubectl Commands" for basic discovery
2. View real-time output in command panel
3. Click "Build Tenant Data" for comprehensive tenant discovery
4. Wait for tenant database building completion

### 3. Tenant Management
1. Select tenant from dropdown (appears after building data)
2. View Redis keys section and ConfigMaps section (auto-populated)
3. Select and view Redis key values
4. Select and view raw ConfigMap output

### 4. Clean Disconnect
1. Click "Disconnect" button
2. UI automatically resets to initial state
3. All sections hidden and dropdowns cleared
4. Ready for new connection

## Configuration

### Default Values
- **Server**: `vms1-tb163.versa-test.net`
- **Username**: `admin`
- **Passwords**: Pre-configured (update as needed)
- **Port**: `5000` (Flask server)
- **Host**: `0.0.0.0` (accessible from network)

### Customization
- Update default server credentials in HTML template
- Modify SSH connection parameters in `connect_to_server()`
- Adjust command timeouts in `_collect_command_output()`
- Customize UI colors and styling in CSS

## Security Considerations

### SSH Security
- Password-based authentication (consider key-based for production)
- Automatic sudo elevation with stored credentials
- SSH client with auto-accept host keys (verify for production)

### Network Security  
- Flask server runs on all interfaces (`0.0.0.0`)
- No HTTPS encryption (add SSL for production)
- No authentication on web interface (add auth for production)

### Credential Management
- Passwords stored in HTML template (externalize for production)
- SSH credentials transmitted via WebSocket (encrypt for production)

## Installation and Running

### Prerequisites
```bash
pip install flask flask-socketio paramiko
```

### Running
```bash
python VMS-Debug-Tool-Web.py
```

### Access
Open web browser to: `http://localhost:5000`

## File Structure
```
VMS-Versa/
├── VMS-Debug-Tool-Web.py          # Main application file
├── templates/                      # Auto-generated template directory
│   └── index.html                 # Auto-generated HTML template
├── tenant_data_*.json             # Generated tenant database files
└── README-VMS-Debug-Tool-Web.md   # This documentation file
```

## Troubleshooting

### Connection Issues
- Verify server IP and credentials
- Check network connectivity to VMS server
- Ensure SSH service is running on target server
- Verify sudo privileges for admin user

### Command Execution Issues
- Check kubectl is available on target server
- Verify kubernetes cluster is accessible
- Ensure proper namespace permissions
- Check command syntax and parameters

### UI Issues
- Refresh browser page to reset state
- Check browser console for JavaScript errors
- Verify WebSocket connection in browser dev tools
- Clear browser cache if needed

### Performance Issues
- Reduce command timeouts for faster responses
- Limit output collection for large datasets
- Use filters in kubectl commands to reduce output
- Consider pagination for large tenant lists

## Development Notes

### Code Structure
- Main application logic in `VMSDebugWeb` class
- Socket event handlers at module level
- HTML template embedded as string (auto-generated file)
- CSS and JavaScript inline in HTML template

### Extension Points
- Add new kubectl commands in `run_kubectl_commands()`
- Add new tenant data collection in `build_tenant_data()`
- Add new UI sections by extending HTML template
- Add new socket events for additional functionality

### Testing
- Test with different VMS server configurations
- Verify with various tenant setups
- Test error handling and recovery
- Performance testing with large datasets

## License and Support

This tool is part of the VMS debugging utilities suite. For support or questions, refer to the development team documentation or issue tracking system.
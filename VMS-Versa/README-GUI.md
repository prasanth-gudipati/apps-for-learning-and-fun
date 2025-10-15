# VMS Debug Tool - GUI Version

A GUI application for connecting to VMS servers and executing kubectl commands with real-time display of command execution and output.

## Features

### Current Implementation (v1.0)

✅ **GUI Connection Interface**
- Easy-to-use connection form with default values (same as original script)
- Editable fields for Server IP, Username, SSH Password, and Admin Password
- Connection status indicator
- Input validation

✅ **SSH Connection Management** 
- Secure SSH connection with paramiko
- Automatic sudo elevation
- Connection status monitoring
- Clean disconnect functionality

✅ **Real-time Command Execution Display**
- Right-side panel showing each command being executed
- Real-time output display with timestamps
- Color-coded output (commands in blue, success in green, errors in red)
- Auto-scrolling output window

✅ **Kubectl Commands Execution**
- Run comprehensive kubectl commands (namespaces, pods, services, etc.)
- Display command descriptions and execution status
- Line count reporting for each command output

✅ **Tenant Data Collection**
- Build comprehensive tenant data structure
- Extract services and Redis information
- Integration of Redis IPs with tenant namespaces
- JSON export functionality with timestamps

## Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements-gui.txt
   ```

2. **Run the Application:**
   ```bash
   python VMS-Debug-Tool-GUI.py
   ```

## Usage

### 1. Server Connection
- Fill in the connection details (default values are pre-populated from original script)
- Click "Connect" to establish SSH connection
- The application will automatically perform sudo elevation
- Connection status will be displayed

### 2. Command Execution
- **"Run Kubectl Commands"**: Executes basic kubectl commands for system overview
- **"Build Tenant Data"**: Builds comprehensive tenant data with Redis information

### 3. Real-time Monitoring
- The right panel shows each command being executed in real-time
- Commands are color-coded for easy identification
- Timestamps are added to each log entry
- Output can be cleared using the "Clear Output" button

## Default Values

The application uses the same default values as the original VMS-Debug-Tool.py:

- **Server IP**: `vms1-tb163.versa-test.net`
- **Username**: `admin`
- **SSH Password**: `THS!5V3r5@vmsP@55`
- **Admin Password**: `THS!5V3r5@vmsP@55`

## GUI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                         VMS Debug Tool - GUI                        │
├─────────────────┬───────────────────────────────────────────────────┤
│   Connection    │                                                   │
│   Panel         │             Command Execution Output              │
│                 │                                                   │
│ ┌─────────────┐ │  [10:30:15] Attempting SSH connection...          │
│ │Server IP    │ │  [10:30:16] SSH connection successful             │
│ │Username     │ │  [10:30:17] Running: kubectl get ns              │
│ │SSH Password │ │  [10:30:17] Description: Get all namespaces      │
│ │Admin Pass   │ │    default                                        │
│ └─────────────┘ │    kube-system                                    │
│                 │    tenant-abc                                     │
│ [Connect]       │    tenant-xyz                                     │
│                 │  [10:30:18] -> Collected 25 lines of output      │
│ Operations:     │  [10:30:19] Running: kubectl get pods -A         │
│ [Run Kubectl]   │  ...                                             │
│ [Build Tenant]  │                                                   │
│ [Clear Output]  │                                                   │
│ [Disconnect]    │                                                   │
└─────────────────┴───────────────────────────────────────────────────┘
```

## Thread Safety

The application uses proper thread management:
- SSH connections run in separate threads to avoid GUI freezing
- Command execution happens in background threads
- Thread-safe queue system for updating GUI with command output
- Progress indicators during long-running operations

## File Outputs

- **Tenant Data**: Saved as JSON files with timestamps (`tenant_data_YYYYMMDD_HHMMSS.json`)
- **Real-time Logs**: Displayed in GUI with color coding and timestamps

## Planned Features (Next Increments)

🔄 **Upcoming Features:**
- Redis key exploration GUI
- Interactive tenant selection interface
- Export functionality for command outputs
- Configuration save/load for connection settings
- Enhanced error handling and recovery
- Command history and replay functionality

## Requirements

- Python 3.6+
- tkinter (usually included with Python)
- paramiko 2.7.0+

## Error Handling

- Connection timeout handling
- SSH authentication error reporting
- Command execution error logging
- GUI state management during failures
- Clean resource cleanup on application exit
# Concerto REST API Client

A simple, incremental REST API client for Concerto ECP operations.

## Current Features (Version 0.1)

✅ **Tenant UUID Lookup** - Get the UUID of a tenant by its name  
✅ **List All Tenants** - Display all available tenants with their UUIDs  
✅ **Interactive Mode** - User-friendly command-line interface  

## Setup

1. **Activate Virtual Environment**
   
   **Option A: Using batch file (Recommended for Windows)**
   ```cmd
   activate_env.bat
   ```
   
   **Option B: Using PowerShell script**
   ```powershell
   .\activate_env.ps1
   ```
   
   **Option C: Manual activation**
   ```cmd
   "C:\Users\Prasanth Gudipati\Documents\Zoom\.venv\Scripts\activate"
   ```

2. **Install Dependencies** (if not already installed)
   ```cmd
   pip install -r requirements.txt
   ```

3. **Update Configuration**
   Edit the following variables in `tenant_uuid.py`:
   ```python
   ECP_IP = "10.73.70.70"    # Your ECP server IP
   USERNAME = "admin"        # Your username
   PASSWORD = "versa123"     # Your password
   ```

## Usage

Run the script:
```cmd
python tenant_uuid.py
```

### Interactive Options

1. **Get UUID for specific tenant** - Enter a tenant name to get its UUID
2. **List all tenants** - Display all available tenants
3. **Exit** - Close the program

### Example Output

```
🎯 Concerto REST API - Tenant UUID Lookup
============================================================
Authenticating with ECP server at 10.73.70.70...
✓ Authentication successful

============================================================
Options:
1. Get UUID for specific tenant
2. List all tenants
3. Exit
============================================================
Select option (1-3): 1
Enter tenant name: MyTenant
Searching for tenant: MyTenant
✓ Found tenant 'MyTenant' with UUID: 12345678-1234-1234-1234-123456789abc

🎯 Result: Tenant 'MyTenant' has UUID: 12345678-1234-1234-1234-123456789abc
```

## Features

- ✅ Simple, focused functionality
- ✅ Error handling for common issues
- ✅ SSL certificate verification disabled (for self-signed certs)
- ✅ Session management with authentication tokens
- ✅ User-friendly output with status indicators
- ✅ Interactive command-line interface

## Roadmap

This is version 0.1 - more features will be added incrementally:
- [ ] Tenant creation operations
- [ ] Tenant modification operations
- [ ] Device management
- [ ] Configuration management
- [ ] Bulk operations
- [ ] Configuration file support
- [ ] Logging capabilities

## File Structure

```
Concerto-REST/
├── tenant_uuid.py      # Main script for tenant UUID operations
├── requirements.txt    # Python dependencies
├── activate_env.bat    # Batch file to activate virtual environment
├── activate_env.ps1    # PowerShell script to activate virtual environment
└── README.md          # This documentation
```

## Dependencies

- **requests** - HTTP library for API calls
- **urllib3** - HTTP client (used to disable SSL warnings)

---
**Created:** October 10, 2025  
**Version:** 0.1 - Tenant UUID Lookup
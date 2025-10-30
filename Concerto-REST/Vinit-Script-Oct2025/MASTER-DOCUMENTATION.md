# Master Documentation - Concerto REST Scripts

---

## Delete and Clean-and-Delete Tenant Operations

### Overview

The script `rest-Oct2025.py` supports two types of tenant deletion operations:
- **Standard Delete**: Removes a tenant by name (UUID lookup required)
- **Clean-and-Delete**: Performs a cleanup and then deletes the tenant, requiring password confirmation

### Delete Tenants by Name

#### Usage
```bash
python3 rest-Oct2025.py --action delete_tenants --tenant-names "Script-Tenant-144,Script-Tenant-143"
```
- Accepts a comma-separated list of tenant names
- For each name, the script fetches the UUID and issues a DELETE request:
  - `DELETE /portalapi/v1/tenants/tenant/{uuid}`
- Summary of successes and failures is printed

### Clean-and-Delete Tenants by Name

#### Usage
```bash
python3 rest-Oct2025.py --action clean_and_delete_tenants --tenant-names "Script-Tenant-101"
```

#### Delete a Range of Tenants Example
```bash
python3 rest-Oct2025.py --action clean_and_delete_tenants --tenant-names "$(python3 -c 'print(",".join([f"Script-Tenant-{i}" for i in range(102, 122)]))')"
```
- Accepts a comma-separated list of tenant names
- For each name, the script fetches the UUID and issues a DELETE request with password in the body:
  - `DELETE /portalapi/v1/tenants/tenant/cleanup-delete/{uuid}`
  - Request body: `{ "password": "<your_password>" }`
- The password is taken from the `--password` CLI argument
- Summary of successes and failures is printed

#### Example curl Equivalent
```bash
curl -X DELETE "https://<ECP-IP>/portalapi/v1/tenants/tenant/cleanup-delete/<uuid>" \
  -H "accept: application/json" -H "Content-Type: application/json" \
  -d '{ "password": "<your_password>" }'
```

### Notes
- Both operations require valid ECP credentials
- Clean-and-delete is recommended for full cleanup before tenant removal
- If a tenant cannot be found, or the API returns an error, the script will report the failure

### Exit Codes
- `0`: All deletions succeeded
- `1`: One or more deletions failed

---

## Parallel Tenant Creation Script - rest-Oct2025.py

### Overview

This enhanced REST API script now supports creating multiple Versa tenants in parallel, significantly improving efficiency when deploying multiple tenants simultaneously.

### New Features

#### 🚀 Parallel Processing
- Create multiple tenants simultaneously using ThreadPoolExecutor
- Configurable number of worker threads (default: 5)
- Thread-safe logging with per-tenant identification
- Comprehensive progress tracking and summary reporting

#### 🔢 Flexible Global ID Input
The script accepts various formats for specifying multiple Global IDs:
- **Single number**: `50`
- **Range with dash**: `50-55` (creates IDs 50, 51, 52, 53, 54, 55)
- **Range with colon**: `50:55` (same as above)
- **List**: `50,52,54,56` (creates specific IDs)
- **Mixed**: `50-52,55,60-62` (combines ranges and individual IDs)

### Usage Examples

#### Basic Parallel Creation
```bash
# Create tenants with Global IDs 50-55 using 3 workers
python3 rest-Oct2025.py --action create_tenant --global-ids "50-55" --max-workers 3

# Create specific tenants
python3 rest-Oct2025.py --action create_tenant --global-ids "100,102,105,108"

# Mixed ranges and lists
python3 rest-Oct2025.py --action create_tenant --global-ids "50-52,55,60-62"
```

#### Advanced Configuration
```bash
# Parallel creation with custom ECP settings
python3 rest-Oct2025.py \
  -ip 10.73.70.70 \
  -user Script1 \
  -password 'scr1@Versa123' \
  --action create_tenant \
  --global-ids "100-105" \
  --max-workers 5 \
  --bandwidth 2000 \
  --license-year 2024
```

#### Static JSON Mode (Parallel)
```bash
python3 rest-Oct2025.py \
  --action create_tenant \
  --global-ids "50-52" \
  --use-static-json \
  --payload StaticTenant.json \
  --max-workers 2
```

### Command Line Options

#### Core Options
- `-ip IP`: ECP server IP address (default: 10.73.70.70)
- `-user USER`: Username (default: Script1)  
- `-password PASSWORD`: Password (default: scr1@Versa123)
- `-payload PAYLOAD`: JSON template file (default: TenantTemplate-Oct2025.json)

#### Parallel Processing Options
- `--global-ids GLOBAL_IDS`: Multiple Global IDs (enables parallel mode)
- `--max-workers MAX_WORKERS`: Number of parallel workers (default: 5)

#### Single Tenant Options (Backward Compatible)
- `--global-id GLOBAL_ID`: Single Global ID (default: 49)
- `--tenant-name TENANT_NAME`: Custom tenant name
- `--description DESCRIPTION`: Custom description

#### Template Variables
- `--bandwidth BANDWIDTH`: SASE bandwidth (default: 1000)
- `--max-tunnels MAX_TUNNELS`: Maximum tunnels (default: "5")
- `--license-year LICENSE_YEAR`: License year (default: "2019")
- `--sdwan-enabled / --no-sdwan-enabled`: SDWAN functionality
- `--sase-enabled / --no-sase-enabled`: SASE functionality

### Automatic Naming Convention

When using parallel mode, tenants are automatically named:
- **Name**: `Script-Tenant-{GLOBAL_ID}`
- **Description**: `Script-Tenant-{GLOBAL_ID} description`

Examples:
- Global ID 50 → Name: "Script-Tenant-50"
- Global ID 101 → Name: "Script-Tenant-101"

### Output and Logging

#### Console Output
```
=== PARALLEL TENANT CREATION MODE ===
Global IDs to create: [50, 51, 52, 53, 54, 55]
Total tenants: 6
Max workers: 3

[ID:50] Creating tenant: Script-Tenant-50 (Global ID: 50)
[ID:51] Creating tenant: Script-Tenant-51 (Global ID: 51)
[ID:52] Creating tenant: Script-Tenant-52 (Global ID: 52)
...

=== PARALLEL CREATION SUMMARY ===
Total tenants processed: 6
Successful: 5
Failed: 1

✓ Successfully created tenants:
  - ID 50: Script-Tenant-50
  - ID 51: Script-Tenant-51
  - ID 52: Script-Tenant-52
  - ID 53: Script-Tenant-53
  - ID 55: Script-Tenant-55

✗ Failed tenants:
  - ID 54: API Failed: 409 - Conflict
```

#### Log Files
- Detailed per-tenant logs with `[ID:XX]` prefixes
- Individual payload logs for each tenant
- Error tracking and debugging information

### Error Handling

- **Individual Failures**: If some tenants fail, others continue processing
- **Summary Report**: Complete success/failure breakdown at the end  
- **Exit Codes**: Script exits with error code 1 if any tenant fails
- **Thread Safety**: Each worker thread has its own REST API session

### Performance Considerations

#### Optimal Worker Count
- **Default**: 5 workers (good balance for most scenarios)
- **Conservative**: 2-3 workers for sensitive environments
- **Aggressive**: 8-10 workers for high-capacity systems

#### Resource Usage
- Each worker maintains its own HTTP session
- Memory usage scales with worker count
- API server load increases with parallelization

### Migration from Single Mode

The script remains 100% backward compatible:

```bash
# Old way (still works)
python3 rest-Oct2025.py --action create_tenant --global-id 50

# New parallel way
python3 rest-Oct2025.py --action create_tenant --global-ids "50-55"
```

### Testing

Run the included test to verify Global ID parsing:
```bash
python3 test-global-id-parsing.py
```

View usage examples:
```bash
./parallel-tenant-examples.sh
```

### Troubleshooting

#### Common Issues
1. **Authentication Failures**: Check ECP credentials and connectivity
2. **Resource Conflicts**: Reduce `--max-workers` if seeing conflicts
3. **Template Errors**: Verify JSON template file exists and is valid
4. **Global ID Conflicts**: Ensure Global IDs don't already exist

#### Debug Tips
- Check log files for detailed per-tenant error messages
- Use fewer workers initially to isolate issues
- Test with a small range first (e.g., `--global-ids "50-52"`)

### File Structure

```
Vinit-Script-Oct2025/
├── rest-Oct2025.py                    # Main enhanced script
├── parallel-tenant-examples.sh       # Usage examples
├── test-global-id-parsing.py         # Parsing validation
├── TenantTemplate-Oct2025.json       # Template file (required)
└── README-Parallel.md               # This documentation
```

### Requirements

- Python 3.6+
- Required modules: `requests`, `jsonpath_ng`, `jinja2`, `concurrent.futures`
- Valid ECP server access and credentials
- JSON template file for tenant creation

---

*Enhanced by adding parallel processing capabilities while maintaining full backward compatibility with existing workflows.*

# Delete and Clean-and-Delete Tenant Operations

## Overview

The script `rest-Oct2025.py` supports two types of tenant deletion operations:
- **Standard Delete**: Removes a tenant by name (UUID lookup required)
- **Clean-and-Delete**: Performs a cleanup and then deletes the tenant, requiring password confirmation

## Delete Tenants by Name

### Usage
```bash
python3 rest-Oct2025.py --action delete_tenants --tenant-names "Script-Tenant-144,Script-Tenant-143"
```
- Accepts a comma-separated list of tenant names
- For each name, the script fetches the UUID and issues a DELETE request:
  - `DELETE /portalapi/v1/tenants/tenant/{uuid}`
- Summary of successes and failures is printed

## Clean-and-Delete Tenants by Name

### Usage
```bash
python3 rest-Oct2025.py --action clean_and_delete_tenants --tenant-names "Script-Tenant-101"
```
- Accepts a comma-separated list of tenant names
- For each name, the script fetches the UUID and issues a DELETE request with password in the body:
  - `DELETE /portalapi/v1/tenants/tenant/cleanup-delete/{uuid}`
  - Request body: `{ "password": "<your_password>" }`
- The password is taken from the `--password` CLI argument
- Summary of successes and failures is printed

### Example curl Equivalent
```bash
curl -X DELETE "https://<ECP-IP>/portalapi/v1/tenants/tenant/cleanup-delete/<uuid>" \
  -H "accept: application/json" -H "Content-Type: application/json" \
  -d '{ "password": "<your_password>" }'
```

## Notes
- Both operations require valid ECP credentials
- Clean-and-delete is recommended for full cleanup before tenant removal
- If a tenant cannot be found, or the API returns an error, the script will report the failure

## Exit Codes
- `0`: All deletions succeeded
- `1`: One or more deletions failed

---
*See main README for additional options and parallel creation features.*

# Automate SSH, sudo su, and kubectl commands as described in your manual steps.
# Requires: paramiko (install with `pip install paramiko`)
import paramiko
import getpass
import time
import json
import re

HOST = "vms1-tb163.versa-test.net"
USER = "admin"

def prompt_password(prompt_text, default="THS!5V3r5@vmsP@55"):
    pw = getpass.getpass(f"{prompt_text} (default: {default}): ")
    return pw if pw else default

def parse_kubectl_output(output):
    """Parse kubectl get svc -A output and extract tenant information"""
    tenant_services = {}
    lines = output.strip().split('\n')
    
    # Skip header line and empty lines
    for line in lines:
        line = line.strip()
        if not line or line.startswith('NAMESPACE') or line.startswith('kubectl'):
            continue
        
        # Split by whitespace and get first two columns
        parts = line.split()
        if len(parts) >= 2:
            namespace = parts[0]  # First column is tenant (namespace)
            service = parts[1]    # Second column is service name
            
            # Skip system namespaces (optional filtering)
            if namespace in ['kube-system', 'kube-public', 'kube-node-lease', 'default']:
                continue
            
            if namespace not in tenant_services:
                tenant_services[namespace] = {
                    'services': [],
                    'redis_info': None  # Will be populated later
                }
            
            if service not in tenant_services[namespace]['services']:
                tenant_services[namespace]['services'].append(service)
    
    return tenant_services

def build_comprehensive_tenant_data(shell, include_redis_keys=False):
    """
    Build comprehensive tenant data structure including services, Redis information, and optionally Redis keys
    """
    print("Building comprehensive tenant data...")
    
    # Step 1: Get all services
    print("Getting all services...")
    shell.send("kubectl get svc -A\n")
    time.sleep(2)
    kubectl_output = ""
    try:
        start_time = time.time()
        while time.time() - start_time < 10:
            if shell.recv_ready():
                chunk = shell.recv(65535).decode('utf-8', errors='ignore')
                kubectl_output += chunk
                if chunk.endswith('# ') or chunk.endswith('$ '):
                    break
            time.sleep(0.1)
    except Exception as e:
        print(f"Error getting services: {str(e)}")
        return {}
    
    # Clean ANSI escape codes from kubectl output
    kubectl_output = clean_ansi_codes(kubectl_output)
    
    # Parse basic tenant services
    tenant_data = parse_kubectl_output(kubectl_output)
    
    # Step 2: Get Redis information and integrate it
    print("Getting Redis information...")
    redis_info = extract_redis_ips(shell)
    
    # Integrate Redis information into tenant data
    for tenant, redis_details in redis_info.items():
        if tenant in tenant_data:
            tenant_data[tenant]['redis_info'] = redis_details
        else:
            # Create entry for tenant that only has Redis (shouldn't happen normally)
            tenant_data[tenant] = {
                'services': ['redis'],
                'redis_info': redis_details
            }
    
    # Step 3: Extract Redis keys if requested
    if include_redis_keys:
        print("Extracting Redis keys for each tenant...")
        for tenant, data in tenant_data.items():
            if data.get('redis_info') and data['redis_info'].get('cluster_ip'):
                redis_ip = data['redis_info']['cluster_ip']
                print(f"  Getting keys for {tenant} (Redis IP: {redis_ip})...")
                keys = extract_redis_keys(shell, redis_ip)
                tenant_data[tenant]['redis_info']['keys'] = keys
                tenant_data[tenant]['redis_info']['key_count'] = len(keys)
                print(f"    Found {len(keys)} keys")
            else:
                print(f"  No Redis IP found for {tenant}")
    
    return tenant_data

def clean_ansi_codes(text):
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def extract_redis_keys(shell, redis_ip, redis_port="6379"):
    """
    Extract all Redis keys for a given Redis IP using redis-cli
    """
    print(f"Extracting Redis keys from {redis_ip}:{redis_port}...")
    
    # Execute redis-cli command to get all keys
    command = f"redis-cli -h {redis_ip} -p {redis_port} keys \"*\""
    shell.send(f"{command}\n")
    time.sleep(3)  # Wait a bit longer for Redis response
    
    # Collect output
    output = ""
    try:
        start_time = time.time()
        while time.time() - start_time < 15:  # 15 second timeout for Redis
            if shell.recv_ready():
                chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                output += chunk
                if chunk.endswith('# ') or chunk.endswith('$ '):
                    break
            time.sleep(0.1)
    except Exception as e:
        print(f"Error extracting Redis keys from {redis_ip}: {str(e)}")
        return []
    
    # Clean ANSI codes and parse keys
    output = clean_ansi_codes(output)
    lines = output.strip().split('\n')
    
    keys = []
    for line in lines:
        line = line.strip()
        # Skip command echo, prompts, and empty lines
        if (not line or 
            line.startswith('redis-cli') or 
            line.endswith('# ') or 
            line.endswith('$ ') or
            line.startswith('[root@')):
            continue
        
        # Redis keys are typically numbered like "1) keyname"
        if line and not line.startswith('(error)'):
            # Remove numbering if present (e.g., "1) keyname" -> "keyname")
            if ')' in line and line.split(')')[0].strip().isdigit():
                key = ')'.join(line.split(')')[1:]).strip()
                # Remove quotes if present
                key = key.strip('"\'')
                if key:
                    keys.append(key)
            else:
                # If no numbering, treat the whole line as a key
                key = line.strip('"\'')
                if key and not key.startswith('redis'):  # Avoid command echoes
                    keys.append(key)
    
    return keys

def get_redis_key_value(shell, redis_ip, redis_port, key_name):
    """
    Get the value of a specific Redis key using hgetall command
    """
    print(f"Getting value for Redis key: {key_name}")
    
    # Execute redis-cli hgetall command
    command = f"redis-cli -h {redis_ip} -p {redis_port} hgetall \"{key_name}\""
    shell.send(f"{command}\n")
    time.sleep(2)
    
    # Collect output
    output = ""
    try:
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 second timeout
            if shell.recv_ready():
                chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                output += chunk
                if chunk.endswith('# ') or chunk.endswith('$ '):
                    break
            time.sleep(0.1)
    except Exception as e:
        print(f"Error getting Redis key value: {str(e)}")
        return {}
    
    # Clean ANSI codes and parse output
    output = clean_ansi_codes(output)
    lines = output.strip().split('\n')
    
    # Clean lines and remove Redis CLI numbering
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Skip command echo, prompts, and empty lines
        if (not line or 
            line.startswith('redis-cli') or 
            line.endswith('# ') or 
            line.endswith('$ ') or
            line.startswith('[root@')):
            continue
        
        # Remove Redis CLI numbering format like "1) \"field\"" -> "field"
        if ')' in line and line.split(')')[0].strip().isdigit():
            line = ')'.join(line.split(')')[1:]).strip()
        
        # Remove outer quotes
        line = line.strip('"\'')
        cleaned_lines.append(line)
    
    # Parse field-value pairs
    key_value_pairs = {}
    current_field = None
    
    for line in cleaned_lines:
        if current_field is None:
            current_field = line
        else:
            # Handle escaped JSON strings
            value = line
            # Unescape JSON if it's escaped
            if value.startswith('{') and '\\\"' in value:
                try:
                    # Replace escaped quotes and parse as JSON
                    unescaped_value = value.replace('\\"', '"').replace('\\\\', '\\')
                    # Try to parse as JSON to validate and reformat
                    json_obj = json.loads(unescaped_value)
                    value = json_obj  # Store as object, not string
                except (json.JSONDecodeError, ValueError):
                    # If not valid JSON, keep as string but unescape quotes
                    value = value.replace('\\"', '"').replace('\\\\', '\\')
            
            key_value_pairs[current_field] = value
            current_field = None
    
    return key_value_pairs

def decode_value(value):
    """
    Attempt to decode values that might be encoded (base64, JSON, etc.)
    """
    import base64
    
    # If value is already a parsed object (dict, list), return as-is
    if isinstance(value, (dict, list)):
        return value, "parsed_json"
    
    if not value or not isinstance(value, str):
        return value, "raw"
    
    # Try to decode as JSON
    try:
        decoded_json = json.loads(value)
        return decoded_json, "json"
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try to decode as base64
    try:
        if len(value) > 10 and value.replace('+', '').replace('/', '').replace('=', '').isalnum():
            decoded_b64 = base64.b64decode(value).decode('utf-8')
            # Check if decoded result looks like readable text or JSON
            if decoded_b64.isprintable() and len(decoded_b64) > 0:
                # Try to parse decoded as JSON
                try:
                    decoded_json = json.loads(decoded_b64)
                    return decoded_json, "base64+json"
                except (json.JSONDecodeError, ValueError):
                    return decoded_b64, "base64"
    except Exception:
        pass
    
    # Check if it's a timestamp
    try:
        if value.isdigit() and len(value) == 10:  # Unix timestamp
            import datetime
            dt = datetime.datetime.fromtimestamp(int(value))
            return f"{value} ({dt.strftime('%Y-%m-%d %H:%M:%S')})", "timestamp"
        elif value.isdigit() and len(value) == 13:  # Unix timestamp in milliseconds
            import datetime
            dt = datetime.datetime.fromtimestamp(int(value) / 1000)
            return f"{value} ({dt.strftime('%Y-%m-%d %H:%M:%S')})", "timestamp_ms"
    except Exception:
        pass
    
    return value, "raw"

def display_pretty_json_format(key_name, key_value_pairs):
    """
    Display Redis key-value pairs in pretty JSON format with decoded values
    """
    print(f"\n" + "="*80)
    print(f"REDIS KEY VALUE (PRETTY JSON FORMAT): {key_name}")
    print("="*80)
    
    if not key_value_pairs:
        print("No data found for this Redis key.")
        return
    
    # Process each field for better display
    formatted_data = {}
    decoding_info = {}
    
    for field, value in key_value_pairs.items():
        # Clean field name (remove any Redis numbering artifacts)
        clean_field = field.strip()
        
        # If value is already a JSON object (parsed during extraction), use it directly
        if isinstance(value, (dict, list)):
            formatted_data[clean_field] = value
            decoding_info[clean_field] = "parsed_json"
        else:
            # Try to decode the value
            decoded_value, decode_type = decode_value(value)
            formatted_data[clean_field] = decoded_value
            if decode_type != "raw":
                decoding_info[clean_field] = decode_type
    
    # Display the formatted JSON with proper indentation
    try:
        pretty_json = json.dumps(formatted_data, indent=2, ensure_ascii=False, sort_keys=True)
        print(pretty_json)
    except Exception as e:
        print(f"Error formatting JSON: {e}")
        # Fallback to simple display
        for field, value in formatted_data.items():
            print(f"{field}:")
            if isinstance(value, (dict, list)):
                try:
                    print(json.dumps(value, indent=2, ensure_ascii=False))
                except:
                    print(f"  {value}")
            else:
                print(f"  {value}")
            print()
    
    # Display decoding/processing information
    if decoding_info:
        print(f"\n" + "-"*60)
        print("DATA PROCESSING INFORMATION:")
        print("-"*60)
        for field, process_type in decoding_info.items():
            type_descriptions = {
                "parsed_json": "Parsed from escaped JSON string",
                "json": "Decoded as JSON object", 
                "base64": "Decoded from base64",
                "base64+json": "Decoded from base64-encoded JSON",
                "timestamp": "Converted Unix timestamp to readable date",
                "timestamp_ms": "Converted Unix timestamp (ms) to readable date"
            }
            description = type_descriptions.get(process_type, process_type)
            print(f"  {field}: {description}")
    
    # Show summary
    print(f"\n" + "-"*60)
    print(f"SUMMARY: {len(key_value_pairs)} field(s) found in Redis key")
    print("-"*60)

def display_raw_format(key_name, key_value_pairs):
    """
    Display Redis key-value pairs in raw format with blank lines between entries
    """
    print(f"\n" + "="*80)
    print(f"REDIS KEY VALUE (RAW FORMAT): {key_name}")
    print("="*80)
    
    for field, value in key_value_pairs.items():
        print(f"{field}")
        print(f"{value}")
        print()  # Blank line after each entry

def display_important_fields_table(key_name, key_value_pairs):
    """
    Display important fields in tabular format with decoded values
    """
    print(f"\n" + "="*80)
    print(f"REDIS KEY VALUE (IMPORTANT FIELDS TABLE): {key_name}")
    print("="*80)
    
    # Define important field patterns (customize as needed)
    important_patterns = [
        'id', 'name', 'username', 'email', 'type', 'status', 'state',
        'created', 'updated', 'modified', 'timestamp', 'date',
        'url', 'endpoint', 'address', 'host', 'port',
        'version', 'config', 'metadata', 'data'
    ]
    
    # Find important fields
    important_fields = {}
    other_fields = {}
    
    for field, value in key_value_pairs.items():
        field_lower = field.lower()
        is_important = any(pattern in field_lower for pattern in important_patterns)
        
        decoded_value, decode_type = decode_value(value)
        
        if is_important:
            important_fields[field] = {
                'value': decoded_value,
                'type': decode_type,
                'original': value
            }
        else:
            other_fields[field] = {
                'value': decoded_value,
                'type': decode_type,
                'original': value
            }
    
    # Display important fields table
    if important_fields:
        print("\nIMPORTANT FIELDS:")
        print("-" * 80)
        
        # Calculate column widths
        max_field_width = max(len(field) for field in important_fields.keys()) if important_fields else 15
        field_width = max(max_field_width + 2, 20)
        
        # Header
        header_line = f"| {'Field':<{field_width}} | {'Value':<35} | {'Type':<12} |"
        separator_line = "+" + "-" * (field_width + 2) + "+" + "-" * 37 + "+" + "-" * 14 + "+"
        
        print(separator_line)
        print(header_line)
        print(separator_line)
        
        for field, info in important_fields.items():
            value_str = str(info['value'])
            if len(value_str) > 33:
                value_str = value_str[:30] + "..."
            
            row_line = f"| {field:<{field_width}} | {value_str:<35} | {info['type']:<12} |"
            print(row_line)
        
        print(separator_line)
    
    # Display other fields summary
    if other_fields:
        print(f"\nOTHER FIELDS ({len(other_fields)} total):")
        print("-" * 50)
        for field, info in other_fields.items():
            value_preview = str(info['value'])[:50]
            if len(str(info['value'])) > 50:
                value_preview += "..."
            print(f"  {field} ({info['type']}): {value_preview}")

def display_redis_key_value_with_format_choice(key_name, key_value_pairs):
    """
    Display Redis key-value pairs with user choice of format
    """
    if not key_value_pairs:
        print(f"No data found for Redis key: {key_name}")
        return
    
    while True:
        print(f"\n" + "="*60)
        print(f"DISPLAY FORMAT OPTIONS FOR: {key_name}")
        print("="*60)
        print("Choose display format:")
        print("  a. Pretty JSON format (with decoded values)")
        print("  b. Raw output (with blank lines between entries)")
        print("  c. Important fields table (with decoded values)")
        print("  d. Back to key selection")
        
        format_choice = input("\nEnter your choice (a/b/c/d): ").strip().lower()
        
        if format_choice == 'a':
            display_pretty_json_format(key_name, key_value_pairs)
        elif format_choice == 'b':
            display_raw_format(key_name, key_value_pairs)
        elif format_choice == 'c':
            display_important_fields_table(key_name, key_value_pairs)
        elif format_choice == 'd':
            break
        else:
            print("Invalid choice. Please select a, b, c, or d.")
        
        input("\nPress Enter to continue...")

def display_redis_key_value_table(key_name, key_value_pairs):
    """
    Display Redis key-value pairs in a pretty table format (legacy function for compatibility)
    """
    display_redis_key_value_with_format_choice(key_name, key_value_pairs)
    return key_value_pairs

def interactive_redis_key_explorer(shell, tenant_name, tenant_data):
    """
    Interactive Redis key explorer for a specific tenant
    """
    if tenant_name not in tenant_data:
        print(f"Tenant '{tenant_name}' not found.")
        return
    
    data = tenant_data[tenant_name]
    redis_info = data.get('redis_info')
    
    if not redis_info or not redis_info.get('keys'):
        print(f"No Redis keys found for tenant: {tenant_name}")
        return
    
    redis_ip = redis_info.get('cluster_ip')
    keys = redis_info.get('keys', [])
    
    while True:
        print(f"\n" + "="*80)
        print(f"REDIS KEY EXPLORER - TENANT: {tenant_name}")
        print(f"Redis IP: {redis_ip}")
        print("="*80)
        
        print(f"\nAvailable Redis Keys ({len(keys)} total):")
        key_map = {}
        for i, key in enumerate(keys, 1):
            print(f"  {i:2d}. {key}")
            key_map[str(i)] = key
        
        print(f"\nOptions:")
        print(f"  - Enter key number (1-{len(keys)}) to view key value")
        print(f"  - Enter 'back' to return to tenant selection")
        print(f"  - Enter 'quit' to exit")
        
        choice = input(f"\nEnter your choice: ").strip().lower()
        
        if choice == 'quit':
            return 'quit'
        elif choice == 'back':
            return 'back'
        elif choice in key_map:
            selected_key = key_map[choice]
            print(f"\nFetching data for Redis key: {selected_key}")
            key_values = get_redis_key_value(shell, redis_ip, "6379", selected_key)
            display_redis_key_value_table(selected_key, key_values)
        else:
            print("Invalid choice. Please try again.")

def extract_redis_ips(shell):
    """
    Extract Redis service IPs for each tenant/namespace.
    Runs 'kubectl get svc -A | grep redis' and parses the output.
    """
    print("Extracting Redis IPs for each tenant...")
    
    # Execute the command
    shell.send("kubectl get svc -A | grep redis\n")
    time.sleep(2)
    
    # Collect output
    output = ""
    try:
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 second timeout
            if shell.recv_ready():
                chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                output += chunk
                if chunk.endswith('# ') or chunk.endswith('$ '):  # Shell prompt returned
                    break
            time.sleep(0.1)
    except Exception as e:
        print(f"Error collecting Redis output: {str(e)}")
        return {}
    
    # Clean ANSI escape codes from output
    output = clean_ansi_codes(output)
    
    # Parse the output to extract Redis information
    redis_info = {}
    lines = output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        # Skip empty lines, command echo, and prompts
        if not line or line.startswith('kubectl') or line.endswith('# ') or line.endswith('$ '):
            continue
        
        # Parse Redis service lines
        # Expected format: NAMESPACE  NAME  TYPE  CLUSTER-IP  EXTERNAL-IP  PORT(S)  AGE
        parts = line.split()
        if len(parts) >= 4 and 'redis' in line.lower():
            namespace = clean_ansi_codes(parts[0])          # Tenant/namespace
            service_name = clean_ansi_codes(parts[1])       # Service name (should be 'redis')
            service_type = clean_ansi_codes(parts[2])       # Service type (ClusterIP, etc.)
            cluster_ip = clean_ansi_codes(parts[3])         # Redis IP
            
            # Additional info
            external_ip = clean_ansi_codes(parts[4]) if len(parts) > 4 else "N/A"
            ports = clean_ansi_codes(parts[5]) if len(parts) > 5 else "N/A"
            age = clean_ansi_codes(parts[6]) if len(parts) > 6 else "N/A"
            
            redis_info[namespace] = {
                'service_name': service_name,
                'service_type': service_type,
                'cluster_ip': cluster_ip,
                'external_ip': external_ip,
                'ports': ports,
                'age': age
            }
    
    return redis_info

def display_redis_info(redis_info):
    """Display Redis information in a formatted way"""
    if not redis_info:
        print("No Redis services found.")
        return
    
    print("\n" + "="*70)
    print("REDIS SERVICES - IP INFORMATION")
    print("="*70)
    
    for tenant, info in redis_info.items():
        print(f"\nTenant/Namespace: {tenant}")
        print(f"  Service Name:   {info['service_name']}")
        print(f"  Service Type:   {info['service_type']}")
        print(f"  Cluster IP:     {info['cluster_ip']}")
        print(f"  External IP:    {info['external_ip']}")
        print(f"  Ports:          {info['ports']}")
        print(f"  Age:            {info['age']}")
    
    print("\n" + "="*70)
    print("REDIS IP SUMMARY")
    print("="*70)
    
    for tenant, info in redis_info.items():
        print(f"{tenant:<20} -> {info['cluster_ip']}")
    
    print("\n" + "="*70)
    print("JSON FORMAT - REDIS INFORMATION")
    print("="*70)
    redis_json = json.dumps(redis_info, indent=2)
    print(redis_json)
    
    return redis_json

def display_tenant_list(tenant_data):
    """Display a numbered list of tenant names for selection"""
    if not tenant_data:
        print("No tenant data found.")
        return {}
    
    print("\n" + "="*60)
    print("AVAILABLE TENANTS")
    print("="*60)
    
    tenant_list = list(tenant_data.keys())
    tenant_map = {}
    
    for i, tenant in enumerate(tenant_list, 1):
        data = tenant_data[tenant]
        redis_ip = data['redis_info']['cluster_ip'] if data.get('redis_info') else "No Redis"
        service_count = len(data.get('services', []))
        key_count = data['redis_info'].get('key_count', 0) if data.get('redis_info') else 0
        
        print(f"{i:2d}. {tenant:<25} | Services: {service_count:<2} | Redis IP: {redis_ip:<15} | Keys: {key_count}")
        tenant_map[str(i)] = tenant
    
    print("="*60)
    return tenant_map

def display_tenant_details(tenant_name, tenant_data):
    """Display detailed information for a specific tenant"""
    if tenant_name not in tenant_data:
        print(f"Tenant '{tenant_name}' not found.")
        return
    
    data = tenant_data[tenant_name]
    
    print(f"\n" + "="*80)
    print(f"DETAILED TENANT INFORMATION: {tenant_name}")
    print("="*80)
    
    print(f"\nBasic Information:")
    print(f"  Tenant/Namespace: {tenant_name}")
    print(f"  Total Services:   {len(data.get('services', []))}")
    print(f"  Services:         {', '.join(data.get('services', []))}")
    
    if data.get('redis_info'):
        redis = data['redis_info']
        print(f"\nRedis Service Information:")
        print(f"  Service Name:     {redis.get('service_name', 'N/A')}")
        print(f"  Service Type:     {redis.get('service_type', 'N/A')}")
        print(f"  Cluster IP:       {redis.get('cluster_ip', 'N/A')}")
        print(f"  External IP:      {redis.get('external_ip', 'N/A')}")
        print(f"  Ports:            {redis.get('ports', 'N/A')}")
        print(f"  Age:              {redis.get('age', 'N/A')}")
        
        if 'keys' in redis:
            print(f"  Total Keys:       {len(redis['keys'])}")
            
            if redis['keys']:
                print(f"\nRedis Keys:")
                for i, key in enumerate(redis['keys'], 1):
                    print(f"    {i:2d}. {key}")
            else:
                print(f"\nNo Redis keys found.")
        else:
            print(f"  Redis Keys:       Not extracted")
    else:
        print(f"\nRedis Service:      Not found")
    
    print(f"\n" + "="*80)
    print(f"JSON DATA STRUCTURE FOR: {tenant_name}")
    print("="*80)
    tenant_json = json.dumps({tenant_name: data}, indent=2)
    print(tenant_json)
    
    return tenant_json

def display_comprehensive_tenant_data(tenant_data):
    """Display comprehensive tenant data including services and Redis information"""
    if not tenant_data:
        print("No tenant data found.")
        return
    
    print("\n" + "="*80)
    print("COMPREHENSIVE TENANT INFORMATION")
    print("="*80)
    
    for tenant, data in tenant_data.items():
        print(f"\nTenant/Namespace: {tenant}")
        print(f"  Services: {', '.join(data['services'])}")
        
        if data['redis_info']:
            redis = data['redis_info']
            print(f"  Redis Service:")
            print(f"    - Cluster IP:   {redis['cluster_ip']}")
            print(f"    - Service Type: {redis['service_type']}")
            print(f"    - Ports:        {redis['ports']}")
            print(f"    - Age:          {redis['age']}")
            if 'keys' in redis:
                print(f"    - Keys Count:   {len(redis['keys'])}")
        else:
            print(f"  Redis Service:  Not found")
    
    print("\n" + "="*80)
    print("TENANT SUMMARY WITH REDIS IPS")
    print("="*80)
    
    for tenant, data in tenant_data.items():
        redis_ip = data['redis_info']['cluster_ip'] if data['redis_info'] else "N/A"
        service_count = len(data['services'])
        key_count = data['redis_info'].get('key_count', 0) if data.get('redis_info') else 0
        print(f"{tenant:<25} | Services: {service_count:<3} | Redis IP: {redis_ip:<15} | Keys: {key_count}")
    
    print("\n" + "="*80)
    print("MASTER TENANT DATA STRUCTURE (JSON)")
    print("="*80)
    tenant_json = json.dumps(tenant_data, indent=2)
    print(tenant_json)
    
    return tenant_json

def run_vms_status_check(shell, logfile="vms1_status_pgudipati.log"):
    """
    Run comprehensive VMS status check equivalent to the shell script.
    Executes kubectl commands and logs output to file with newest entries at the top.
    """
    import datetime
    
    kubectl_commands = [
        ("kubectl get ns", "Get all namespaces"),
        ("kubectl get pods -A", "Get all pods across all namespaces"), 
        ("kubectl get pv", "Get persistent volumes"),
        ("kubectl get pvc -A", "Get persistent volume claims across all namespaces"),
        ("kubectl get cm -A", "Get config maps across all namespaces"),
        ("kubectl get svc -A |grep redis ", "Get Redis services across all namespaces")
    ]
    
    # Prepare log content for this run
    current_run_content = []
    current_run_content.append("#------")
    current_run_content.append(f"Run time: {datetime.datetime.now()}")
    current_run_content.append("")
    
    print(f"Running VMS status check automatically... Logging to: {logfile}")
    
    for command, description in kubectl_commands:
        print(f"Running: {command} ({description})")
        
        # Add command header to log
        current_run_content.append("#------")
        current_run_content.append("")
        current_run_content.append(f"{command}")
        current_run_content.append("")
        
        # Execute command via SSH shell
        shell.send(f"{command}\n")
        time.sleep(3)  # Wait for command to complete
        
        # Collect output
        output = ""
        try:
            # Collect output with timeout
            start_time = time.time()
            while time.time() - start_time < 10:  # 10 second timeout
                if shell.recv_ready():
                    chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                    output += chunk
                    if chunk.endswith('# ') or chunk.endswith('$ '):  # Shell prompt returned
                        break
                time.sleep(0.1)
        except Exception as e:
            output = f"Error collecting output: {str(e)}"
        
        # Clean ANSI codes and output
        output = clean_ansi_codes(output)
        
        # Clean up the output (remove command echo and prompt)
        lines = output.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip the command echo line and empty lines at start
            if (line == command or 
                line.startswith('kubectl') or
                line.endswith('# ') or 
                line.endswith('$ ') or 
                line.startswith('[root@') or
                not line):
                continue
            cleaned_lines.append(line)
        
        cleaned_output = '\n'.join(cleaned_lines)
        current_run_content.append(cleaned_output)
        current_run_content.append("")
        
        # Print summary to console
        line_count = len(cleaned_lines)
        print(f"  -> Collected {line_count} lines of output")
    
    # Add end marker for this run
    current_run_content.append("")
    current_run_content.append("#------ End of run ------")
    current_run_content.append("")
    current_run_content.append("")  # Extra space between runs
    
    # Read existing log file content (if it exists)
    existing_content = ""
    try:
        with open(logfile, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    except FileNotFoundError:
        # File doesn't exist yet, that's okay
        pass
    except Exception as e:
        print(f"Warning: Could not read existing log file: {str(e)}")
    
    # Write new content at the top, followed by existing content
    try:
        with open(logfile, 'w', encoding='utf-8') as f:
            # Write current run first (newest at top)
            f.write('\n'.join(current_run_content))
            # Then write existing content (older runs below)
            if existing_content.strip():
                f.write('\n' + existing_content)
        
        print(f"VMS status check completed. Results saved to: {logfile}")
        print(f"  -> Latest run added at the top of the log file")
        return True
    except Exception as e:
        print(f"Error writing to log file {logfile}: {str(e)}")
        return False

def run_configmaps_export(shell, logfile="vms2_configmaps_output_pgudipati.log"):
    """
    Export all configmaps in JSON format equivalent to the shell script.
    Saves output to a separate log file with newest entries at the top.
    """
    import datetime
    
    # Prepare log content for this run
    current_run_content = []
    current_run_content.append("#------")
    current_run_content.append(f"Run time: {datetime.datetime.now()}")
    current_run_content.append("")
    
    print(f"Running ConfigMaps export automatically... Logging to: {logfile}")
    
    # Command to get all configmaps in JSON format
    command = "kubectl get configmaps -A -o json"
    description = "Saving all configmaps in JSON format"
    
    print(f"Running: {command} ({description})")
    
    # Add command header to log
    current_run_content.append("#------")
    current_run_content.append("")
    current_run_content.append("Saving all configmaps in JSON format")
    current_run_content.append("")
    
    # Execute command via SSH shell
    shell.send(f"{command}\n")
    time.sleep(5)  # Wait longer for JSON output (can be large)
    
    # Collect output
    output = ""
    try:
        # Collect output with longer timeout for JSON data
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 second timeout for large JSON
            if shell.recv_ready():
                chunk = shell.recv(8192).decode('utf-8', errors='ignore')  # Larger chunk size
                output += chunk
                if chunk.endswith('# ') or chunk.endswith('$ '):  # Shell prompt returned
                    break
            time.sleep(0.1)
    except Exception as e:
        output = f"Error collecting configmaps output: {str(e)}"
    
    # Clean ANSI codes from output
    output = clean_ansi_codes(output)
    
    # Clean up the output (remove command echo and prompt)
    lines = output.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_stripped = line.rstrip()  # Keep leading spaces for JSON formatting
        # Skip the command echo line and prompts
        if (line_stripped == command or 
            line_stripped.startswith('kubectl') or
            line_stripped.endswith('# ') or 
            line_stripped.endswith('$ ') or 
            line_stripped.startswith('[root@')):
            continue
        if line_stripped:  # Keep non-empty lines (including JSON)
            cleaned_lines.append(line_stripped)
    
    cleaned_output = '\n'.join(cleaned_lines)
    current_run_content.append(cleaned_output)
    current_run_content.append("")
    
    # Add end marker for this run
    current_run_content.append("")
    current_run_content.append("#------ End of run ------")
    current_run_content.append("")
    current_run_content.append("")  # Extra space between runs
    
    # Print summary to console
    line_count = len(cleaned_lines)
    json_size = len(cleaned_output)
    print(f"  -> Collected {line_count} lines of JSON output ({json_size} characters)")
    
    # Read existing log file content (if it exists)
    existing_content = ""
    try:
        with open(logfile, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    except FileNotFoundError:
        # File doesn't exist yet, that's okay
        pass
    except Exception as e:
        print(f"Warning: Could not read existing configmaps log file: {str(e)}")
    
    # Write new content at the top, followed by existing content
    try:
        with open(logfile, 'w', encoding='utf-8') as f:
            # Write current run first (newest at top)
            f.write('\n'.join(current_run_content))
            # Then write existing content (older runs below)
            if existing_content.strip():
                f.write('\n' + existing_content)
        
        print(f"ConfigMaps export completed. Results saved to: {logfile}")
        print(f"  -> Latest JSON data added at the top of the log file")
        return True
    except Exception as e:
        print(f"Error writing to configmaps log file {logfile}: {str(e)}")
        return False

def main():
    ssh_password = prompt_password(f"Enter SSH password for {USER}@{HOST}")
    sudo_password = prompt_password(f"Enter sudo password for {USER}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=ssh_password, look_for_keys=False)

    shell = ssh.invoke_shell()
    time.sleep(1)
    shell.recv(10000)  # Clear banner

    # Step 1: sudo su
    shell.send("sudo su\n")
    buff = ""
    while not buff.strip().endswith("password for admin:"):
        resp = shell.recv(1000).decode()
        buff += resp
        if "password for" in buff:
            break
        time.sleep(0.2)
    shell.send(sudo_password + "\n")
    time.sleep(1.5)
    output = shell.recv(10000).decode()
    print(output)

    # Set alias for kubectl
    shell.send("alias k=kubectl\n")
    time.sleep(0.5)
    shell.recv(10000).decode()  # Clear the response

    # Step 2: Build comprehensive tenant data (services + Redis info + keys) - Automatic
    print(f"\n" + "="*70)
    print("BUILDING COMPREHENSIVE TENANT DATA")
    print("="*70)
    print("✅ Building comprehensive tenant data (services + Redis IPs + keys)...")
    print("✅ Extracting Redis keys for each tenant...")
    print("Processing automatically - no user input required.")
    
    print("\nBuilding comprehensive tenant data structure...")
    comprehensive_data = build_comprehensive_tenant_data(shell, include_redis_keys=True)
    
    if comprehensive_data:
        # Display tenant list for selection
        tenant_map = display_tenant_list(comprehensive_data)
        
        # Interactive tenant selection
        while True:
            # Always show the tenant list before options
            tenant_map = display_tenant_list(comprehensive_data)
            
            print("\nOptions:")
            print("  - Enter tenant number (1-{}) to view details".format(len(tenant_map)))
            print("  - Enter 'redis-X' (e.g., redis-1) to explore Redis keys for tenant X")
            print("  - Enter 'all' to view all tenant data")
            print("  - Enter 'save' to save data to file")
            print("  - Enter 'quit' to exit")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'quit':
                break
            elif choice == 'all':
                tenant_json = display_comprehensive_tenant_data(comprehensive_data)
            elif choice == 'save':
                filename = f"comprehensive_tenant_data_{time.strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    with open(filename, 'w') as f:
                        json.dump(comprehensive_data, f, indent=2)
                    print(f"Comprehensive tenant data saved to: {filename}")
                except Exception as e:
                    print(f"Error saving comprehensive data: {str(e)}")
            elif choice.startswith('redis-'):
                # Handle Redis key exploration
                try:
                    tenant_num = choice.split('-')[1]
                    if tenant_num in tenant_map:
                        tenant_name = tenant_map[tenant_num]
                        result = interactive_redis_key_explorer(shell, tenant_name, comprehensive_data)
                        if result == 'quit':
                            break
                    else:
                        print(f"Invalid tenant number: {tenant_num}")
                except (IndexError, ValueError):
                    print("Invalid redis command format. Use 'redis-X' where X is the tenant number.")
            elif choice in tenant_map:
                tenant_name = tenant_map[choice]
                display_tenant_details(tenant_name, comprehensive_data)
            else:
                print("Invalid choice. Please try again.")
    else:
        print("No tenant data found.")
        
        # Fallback message - if no comprehensive data, show alternative
        print("Attempting fallback to basic tenant collection...")
        print("❌ Unable to collect comprehensive tenant data.")
        print("🔍 Check SSH connection and kubectl access.")

    # Automatically run comprehensive VMS status check
    print(f"\n" + "="*60)
    print("RUNNING COMPREHENSIVE VMS STATUS CHECK")
    print("="*60)
    print("Running VMS status check automatically (no prompt needed)...")
    
    success = run_vms_status_check(shell)
    if success:
        print("✅ VMS status check completed successfully!")
        print("📄 Check the log file 'vms1_status_pgudipati.log' for detailed output")
        print("📌 Latest run data is at the top of the log file")
    else:
        print("❌ VMS status check completed with some errors")
        print("🔍 Check console output and log file for details")

    # Automatically run configmaps export
    print(f"\n" + "="*60)
    print("RUNNING CONFIGMAPS JSON EXPORT")
    print("="*60)
    print("Exporting all configmaps in JSON format automatically...")
    
    configmaps_success = run_configmaps_export(shell)
    if configmaps_success:
        print("✅ ConfigMaps export completed successfully!")
        print("📄 Check the log file 'vms2_configmaps_output_pgudipati.log' for JSON output")
        print("📌 Latest JSON export is at the top of the log file")
    else:
        print("❌ ConfigMaps export completed with some errors")
        print("🔍 Check console output and log file for details")

    shell.send("exit\n")
    time.sleep(0.5)
    ssh.close()

if __name__ == "__main__":
    main()
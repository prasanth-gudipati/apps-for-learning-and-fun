#!/usr/bin/env python3
"""
Decode and display Redis key data in pretty format
"""

import json
import base64
from datetime import datetime

def decode_and_display_data():
    """Decode the provided Redis key data and display in pretty format"""
    
    # Raw data from the user
    raw_data = {
        'TagsAttrValuesList': None, 
        'TenantId': 'provider-org', 
        'EntryKey': 'ObjectID("68b62a73d904820f7f7ef06f")', 
        'SequenceNum': 77, 
        'EntryData': {
            'data': 'eyJ0ZW5hbnROYW1lIjoiTUVUQTE2MyIsInRlbmFudElkIjoiQkU4QzA4Q0NEOUUwNEY5MzhGOTM3NDlEOTZFQ0YzRjgtQTciLCJiYW5kIjoibG93LXJpc2siLCJkZXZpY2VJZCI6IjYxOTEwM2EyZTA3ZDQxZDA4NmZkOWM3OWUwMWMzNDA2Iiwib3ZlcmFsbCI6MzMsImV4dGVybmFsX2lwIjoiNjYuMTYwLjE0Ni45MSIsImludGVybmFsX2lwIjoiMTcyLjMwLjYwLjcxIiwic3lzdGVtX3NlcmlhbF9udW1iZXIiOiI1NVpNMEozIiwiaG9zdG5hbWUiOiJERVNLVE9QLUczRDZRTEYifQo='
        }
    }
    
    print("=" * 80)
    print("REDIS KEY DATA - DECODED AND PRETTY FORMAT")
    print("=" * 80)
    
    # Display raw structure first
    print("\n1. RAW DATA STRUCTURE:")
    print("-" * 40)
    for key, value in raw_data.items():
        if key != 'EntryData':
            print(f"{key:20s}: {value}")
        else:
            print(f"{key:20s}: [Base64 encoded data - see decoded below]")
    
    # Decode the base64 data
    print("\n2. DECODED BASE64 DATA:")
    print("-" * 40)
    
    base64_data = raw_data['EntryData']['data']
    
    try:
        # Decode from base64
        decoded_bytes = base64.b64decode(base64_data)
        decoded_string = decoded_bytes.decode('utf-8')
        
        print("Decoded string:")
        print(decoded_string)
        
        # Try to parse as JSON
        try:
            decoded_json = json.loads(decoded_string)
            
            print("\n3. PARSED JSON DATA (PRETTY FORMAT):")
            print("-" * 40)
            print(json.dumps(decoded_json, indent=2, ensure_ascii=False))
            
            # Display in table format for better readability
            print("\n4. TENANT INFORMATION TABLE:")
            print("-" * 60)
            
            # Calculate column width
            max_key_length = max(len(key) for key in decoded_json.keys())
            
            # Table header
            print(f"| {'Field':<{max_key_length + 2}} | {'Value':<35} |")
            print(f"+{'-' * (max_key_length + 4)}+{'-' * 37}+")
            
            # Table rows
            for key, value in decoded_json.items():
                value_str = str(value)
                if len(value_str) > 33:
                    value_str = value_str[:30] + "..."
                print(f"| {key:<{max_key_length + 2}} | {value_str:<35} |")
            
            print(f"+{'-' * (max_key_length + 4)}+{'-' * 37}+")
            
            # Analysis section
            print("\n5. DATA ANALYSIS:")
            print("-" * 40)
            print(f"• Tenant Name:        {decoded_json.get('tenantName', 'N/A')}")
            print(f"• Tenant ID:          {decoded_json.get('tenantId', 'N/A')}")
            print(f"• Device ID:          {decoded_json.get('deviceId', 'N/A')}")
            print(f"• Risk Band:          {decoded_json.get('band', 'N/A')}")
            print(f"• Overall Score:      {decoded_json.get('overall', 'N/A')}")
            print(f"• External IP:        {decoded_json.get('external_ip', 'N/A')}")
            print(f"• Internal IP:        {decoded_json.get('internal_ip', 'N/A')}")
            print(f"• System Serial:      {decoded_json.get('system_serial_number', 'N/A')}")
            print(f"• Hostname:           {decoded_json.get('hostname', 'N/A')}")
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("The decoded string is not valid JSON")
            
    except Exception as e:
        print(f"Error decoding base64: {e}")
    
    # Complete data structure
    print("\n6. COMPLETE DATA STRUCTURE (WITH DECODED CONTENT):")
    print("-" * 60)
    
    complete_structure = raw_data.copy()
    
    try:
        # Replace encoded data with decoded content
        decoded_content = json.loads(base64.b64decode(base64_data).decode('utf-8'))
        complete_structure['EntryData'] = {
            'data_type': 'JSON (base64 decoded)',
            'decoded_content': decoded_content,
            'original_base64': base64_data[:50] + "..." if len(base64_data) > 50 else base64_data
        }
    except:
        complete_structure['EntryData']['data'] = "[Could not decode]"
    
    print(json.dumps(complete_structure, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("This Redis key contains tenant device information for:")
    print(f"  • Tenant: META163 (ID: BE8C08CCD9E04F938F93749D96ECF3F8-A7)")
    print(f"  • Device: DESKTOP-G3D6QLF (Serial: 55ZM0J3)")
    print(f"  • Risk Assessment: Low-risk with overall score of 33")
    print(f"  • Network: External IP 66.160.146.91, Internal IP 172.30.60.71")
    print("=" * 80)

if __name__ == "__main__":
    decode_and_display_data()
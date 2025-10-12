"""
Redis Service - Handles Redis key operations and value retrieval
"""

import json
import re
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self, db_service):
        self.db = db_service
    
    def get_tenant_keys(self, tenant_name):
        """Get Redis keys for a tenant"""
        try:
            return self.db.get_tenant_redis_keys(tenant_name)
        except Exception as e:
            logger.error(f"Get tenant keys error: {str(e)}")
            return []
    
    def get_key_value(self, connection_id, tenant_name, key_name, format_type='pretty_json'):
        """Get Redis key value via SSH connection"""
        try:
            from .ssh_service import SSHService
            
            # Get tenant Redis IP
            tenant = self.db.get_tenant_by_name(tenant_name)
            if not tenant or not tenant.get('redis_info'):
                raise Exception(f"No Redis info found for tenant: {tenant_name}")
            
            redis_ip = tenant['redis_info'].get('cluster_ip')
            if not redis_ip:
                raise Exception(f"No Redis IP found for tenant: {tenant_name}")
            
            # Get SSH service instance (this would need to be injected)
            # For now, we'll assume it's available through app context
            from app import app
            ssh_service = app.ssh_service
            
            # Execute Redis command
            command = f'redis-cli -h {redis_ip} -p 6379 hgetall "{key_name}"'
            output = ssh_service.execute_command(connection_id, command)
            
            # Parse Redis output
            key_value_pairs = self._parse_redis_output(output)
            
            # Format based on requested type
            formatted_value = self._format_key_value(key_name, key_value_pairs, format_type)
            
            # Save to database
            self.db.save_redis_key(
                tenant_name=tenant_name,
                key_name=key_name,
                key_value=key_value_pairs,
                metadata={
                    'redis_ip': redis_ip,
                    'format_requested': format_type,
                    'field_count': len(key_value_pairs),
                    'accessed_at': datetime.utcnow()
                }
            )
            
            return formatted_value
            
        except Exception as e:
            logger.error(f"Get key value error: {str(e)}")
            raise
    
    def _parse_redis_output(self, output):
        """Parse Redis hgetall output"""
        try:
            lines = output.strip().split('\n')
            key_value_pairs = {}
            current_field = None
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                # Remove Redis CLI numbering format like "1) \"field\"" -> "field"
                if ')' in line and line.split(')')[0].strip().isdigit():
                    line = ')'.join(line.split(')')[1:]).strip()
                
                # Remove outer quotes
                line = line.strip('"\'')
                
                if current_field is None:
                    current_field = line
                else:
                    # Handle escaped JSON strings
                    value = line
                    
                    # Unescape JSON if it's escaped
                    if value.startswith('{') and '\\"' in value:
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
            
        except Exception as e:
            logger.error(f"Parse Redis output error: {str(e)}")
            return {}
    
    def _format_key_value(self, key_name, key_value_pairs, format_type):
        """Format Redis key value based on requested type"""
        try:
            if format_type == 'pretty_json':
                return self._format_pretty_json(key_name, key_value_pairs)
            elif format_type == 'raw':
                return self._format_raw(key_name, key_value_pairs)
            elif format_type == 'table':
                return self._format_table(key_name, key_value_pairs)
            else:
                return self._format_pretty_json(key_name, key_value_pairs)
                
        except Exception as e:
            logger.error(f"Format key value error: {str(e)}")
            return {"error": str(e)}
    
    def _format_pretty_json(self, key_name, key_value_pairs):
        """Format as pretty JSON with decoded values"""
        try:
            formatted_data = {}
            decoding_info = {}
            
            for field, value in key_value_pairs.items():
                clean_field = field.strip()
                
                if isinstance(value, (dict, list)):
                    formatted_data[clean_field] = value
                    decoding_info[clean_field] = "parsed_json"
                else:
                    decoded_value, decode_type = self._decode_value(value)
                    formatted_data[clean_field] = decoded_value
                    if decode_type != "raw":
                        decoding_info[clean_field] = decode_type
            
            return {
                'format': 'pretty_json',
                'key_name': key_name,
                'data': formatted_data,
                'decoding_info': decoding_info,
                'field_count': len(key_value_pairs)
            }
            
        except Exception as e:
            logger.error(f"Format pretty JSON error: {str(e)}")
            return {"error": str(e)}
    
    def _format_raw(self, key_name, key_value_pairs):
        """Format as raw output"""
        try:
            raw_lines = []
            
            for field, value in key_value_pairs.items():
                raw_lines.append(field)
                raw_lines.append(str(value))
                raw_lines.append("")  # Blank line
            
            return {
                'format': 'raw',
                'key_name': key_name,
                'data': '\n'.join(raw_lines),
                'field_count': len(key_value_pairs)
            }
            
        except Exception as e:
            logger.error(f"Format raw error: {str(e)}")
            return {"error": str(e)}
    
    def _format_table(self, key_name, key_value_pairs):
        """Format as table with important fields"""
        try:
            important_patterns = [
                'id', 'name', 'username', 'email', 'type', 'status', 'state',
                'created', 'updated', 'modified', 'timestamp', 'date',
                'url', 'endpoint', 'address', 'host', 'port',
                'version', 'config', 'metadata', 'data'
            ]
            
            important_fields = []
            other_fields = []
            
            for field, value in key_value_pairs.items():
                field_lower = field.lower()
                is_important = any(pattern in field_lower for pattern in important_patterns)
                
                decoded_value, decode_type = self._decode_value(value)
                
                field_info = {
                    'field': field,
                    'value': decoded_value,
                    'type': decode_type,
                    'original': str(value)
                }
                
                if is_important:
                    important_fields.append(field_info)
                else:
                    other_fields.append(field_info)
            
            return {
                'format': 'table',
                'key_name': key_name,
                'important_fields': important_fields,
                'other_fields': other_fields,
                'field_count': len(key_value_pairs)
            }
            
        except Exception as e:
            logger.error(f"Format table error: {str(e)}")
            return {"error": str(e)}
    
    def _decode_value(self, value):
        """Decode values (JSON, base64, timestamps)"""
        try:
            # If value is already a parsed object
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
                    dt = datetime.fromtimestamp(int(value))
                    return f"{value} ({dt.strftime('%Y-%m-%d %H:%M:%S')})", "timestamp"
                elif value.isdigit() and len(value) == 13:  # Unix timestamp in milliseconds
                    dt = datetime.fromtimestamp(int(value) / 1000)
                    return f"{value} ({dt.strftime('%Y-%m-%d %H:%M:%S')})", "timestamp_ms"
            except Exception:
                pass
            
            return value, "raw"
            
        except Exception as e:
            logger.error(f"Decode value error: {str(e)}")
            return value, "raw"
    
    def search_keys(self, tenant_name, search_term):
        """Search Redis keys by name"""
        try:
            keys = self.db.get_tenant_redis_keys(tenant_name)
            
            if search_term:
                filtered_keys = [
                    key for key in keys 
                    if search_term.lower() in key['key_name'].lower()
                ]
                return filtered_keys
            
            return keys
            
        except Exception as e:
            logger.error(f"Search keys error: {str(e)}")
            return []
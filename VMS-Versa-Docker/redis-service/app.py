#!/usr/bin/env python3
"""
VMS Debug Tool - Redis Service Microservice
Handles Redis operations for tenant key management.
"""

from flask import Flask, request, jsonify
import redis
import json
import os
import requests
import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Service configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8003))
SESSION_REDIS_URL = os.getenv('SESSION_REDIS_URL', 'redis://localhost:6379')
SSH_SERVICE_URL = os.getenv('SSH_SERVICE_URL', 'http://ssh-service:8001')

# Redis client for session management
try:
    redis_client = redis.from_url(SESSION_REDIS_URL)
    redis_client.ping()
    logger.info("Connected to Redis successfully")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

def make_ssh_request(endpoint, method='GET', data=None, session_id=None):
    """Make request to SSH service"""
    url = f"{SSH_SERVICE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    if session_id:
        headers['X-Session-ID'] = session_id
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"SSH service request failed: {e}")
        return {'error': str(e)}

def clean_ansi_codes(text):
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_tenant_redis_info(tenant_name, session_id):
    """Get Redis connection info for a tenant"""
    try:
        # Get tenant data from Redis
        if redis_client:
            data = redis_client.get(f"tenant_data:{session_id}")
            if data:
                tenant_data = json.loads(data)
                if tenant_name in tenant_data:
                    return tenant_data[tenant_name].get('redis_info')
        return None
    except Exception as e:
        logger.error(f"Error getting tenant Redis info: {e}")
        return None

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'redis-service',
        'timestamp': datetime.now().isoformat(),
        'redis_connected': redis_client is not None,
        'ssh_service': SSH_SERVICE_URL
    })

@app.route('/get_keys/<tenant_name>', methods=['GET'])
def get_redis_keys(tenant_name):
    """Extract Redis keys for a specific tenant"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        logger.info(f"Session {session_id}: Getting Redis keys for tenant {tenant_name}")
        
        # Get tenant Redis info
        redis_info = get_tenant_redis_info(tenant_name, session_id)
        
        if not redis_info or not redis_info.get('cluster_ip'):
            return jsonify({
                'success': True,
                'keys': [],
                'message': 'No Redis service found for tenant'
            })
        
        redis_ip = redis_info['cluster_ip']
        logger.info(f"Session {session_id}: Using Redis IP {redis_ip} for tenant {tenant_name}")
        
        # Execute redis-cli command to get all keys
        command = f"redis-cli -h {redis_ip} -p 6379 keys \"*\""
        response = make_ssh_request('/execute', 'POST',
                                   {'command': command, 'timeout': 15},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to execute Redis command: {response['error']}"}), 500
        
        output = response.get('output', '')
        cleaned_output = clean_ansi_codes(output)
        lines = cleaned_output.strip().split('\n')
        
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
        
        logger.info(f"Session {session_id}: Found {len(keys)} Redis keys for {tenant_name}")
        
        return jsonify({
            'success': True,
            'keys': keys,
            'total': len(keys),
            'redis_ip': redis_ip
        })
        
    except Exception as e:
        logger.error(f"Get Redis keys error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_key_value/<tenant_name>', methods=['POST'])
def get_redis_key_value(tenant_name):
    """Get the value of a specific Redis key for a tenant"""
    try:
        session_id = request.headers.get('X-Session-ID')
        data = request.get_json()
        key_name = data.get('key')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if not key_name:
            return jsonify({'error': 'Key name required'}), 400
        
        logger.info(f"Session {session_id}: Getting Redis key value: {key_name} from {tenant_name}")
        
        # Get tenant Redis info
        redis_info = get_tenant_redis_info(tenant_name, session_id)
        
        if not redis_info or not redis_info.get('cluster_ip'):
            return jsonify({'error': 'No Redis service found for tenant'}), 400
        
        redis_ip = redis_info['cluster_ip']
        
        # Execute redis-cli hgetall command
        command = f"redis-cli -h {redis_ip} -p 6379 hgetall \"{key_name}\""
        response = make_ssh_request('/execute', 'POST',
                                   {'command': command, 'timeout': 10},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to execute Redis command: {response['error']}"}), 500
        
        output = response.get('output', '')
        cleaned_output = clean_ansi_codes(output)
        lines = cleaned_output.strip().split('\n')
        
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
                value = line
                # Handle escaped JSON strings
                if value.startswith('{') and '\\\"' in value:
                    try:
                        # Replace escaped quotes and parse as JSON
                        unescaped_value = value.replace('\\"', '"').replace('\\\\', '\\')
                        json_obj = json.loads(unescaped_value)
                        value = json_obj
                    except (json.JSONDecodeError, ValueError):
                        value = value.replace('\\"', '"').replace('\\\\', '\\')
                
                key_value_pairs[current_field] = value
                current_field = None
        
        logger.info(f"Session {session_id}: Successfully retrieved Redis key value for {key_name}")
        
        return jsonify({
            'success': True,
            'value': key_value_pairs,
            'key': key_name,
            'tenant': tenant_name,
            'redis_ip': redis_ip
        })
        
    except Exception as e:
        logger.error(f"Get Redis key value error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test_connection/<tenant_name>', methods=['GET'])
def test_redis_connection(tenant_name):
    """Test Redis connection for a tenant"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        logger.info(f"Session {session_id}: Testing Redis connection for tenant {tenant_name}")
        
        # Get tenant Redis info
        redis_info = get_tenant_redis_info(tenant_name, session_id)
        
        if not redis_info or not redis_info.get('cluster_ip'):
            return jsonify({
                'success': False,
                'error': 'No Redis service found for tenant'
            })
        
        redis_ip = redis_info['cluster_ip']
        
        # Execute redis-cli ping command
        command = f"redis-cli -h {redis_ip} -p 6379 ping"
        response = make_ssh_request('/execute', 'POST',
                                   {'command': command, 'timeout': 5},
                                   session_id)
        
        if 'error' in response:
            return jsonify({
                'success': False,
                'error': f"Failed to execute Redis ping: {response['error']}"
            })
        
        output = response.get('output', '')
        cleaned_output = clean_ansi_codes(output).strip().lower()
        
        # Check if Redis responded with PONG
        is_connected = 'pong' in cleaned_output
        
        logger.info(f"Session {session_id}: Redis connection test for {tenant_name}: {'SUCCESS' if is_connected else 'FAILED'}")
        
        return jsonify({
            'success': is_connected,
            'redis_ip': redis_ip,
            'response': cleaned_output
        })
        
    except Exception as e:
        logger.error(f"Test Redis connection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_info/<tenant_name>', methods=['GET'])
def get_redis_info(tenant_name):
    """Get Redis server info for a tenant"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        logger.info(f"Session {session_id}: Getting Redis info for tenant {tenant_name}")
        
        # Get tenant Redis info
        redis_info = get_tenant_redis_info(tenant_name, session_id)
        
        if not redis_info or not redis_info.get('cluster_ip'):
            return jsonify({'error': 'No Redis service found for tenant'}), 400
        
        redis_ip = redis_info['cluster_ip']
        
        # Execute redis-cli info command
        command = f"redis-cli -h {redis_ip} -p 6379 info"
        response = make_ssh_request('/execute', 'POST',
                                   {'command': command, 'timeout': 10},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to get Redis info: {response['error']}"}), 500
        
        output = response.get('output', '')
        cleaned_output = clean_ansi_codes(output)
        
        # Parse Redis info output
        info_data = {}
        current_section = None
        
        for line in cleaned_output.split('\n'):
            line = line.strip()
            
            # Skip command echo and prompts
            if (line.startswith('redis-cli') or 
                line.endswith('# ') or 
                line.endswith('$ ') or
                line.startswith('[root@') or
                not line):
                continue
            
            # Section headers start with #
            if line.startswith('#'):
                current_section = line[1:].strip()
                info_data[current_section] = {}
            elif ':' in line and current_section:
                key, value = line.split(':', 1)
                info_data[current_section][key.strip()] = value.strip()
        
        logger.info(f"Session {session_id}: Successfully retrieved Redis info for {tenant_name}")
        
        return jsonify({
            'success': True,
            'redis_info': info_data,
            'redis_ip': redis_ip,
            'tenant': tenant_name
        })
        
    except Exception as e:
        logger.error(f"Get Redis info error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("VMS Debug Tool - Redis Service")
    logger.info("=" * 60)
    logger.info("Redis Operations Microservice")
    logger.info("")
    logger.info("Features:")
    logger.info("  • Redis key enumeration")
    logger.info("  • Redis key value retrieval")
    logger.info("  • Redis connection testing")
    logger.info("  • Redis server information")
    logger.info("")
    logger.info(f"Server starting on http://0.0.0.0:{SERVICE_PORT}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
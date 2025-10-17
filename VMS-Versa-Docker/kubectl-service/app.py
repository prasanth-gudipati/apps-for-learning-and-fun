#!/usr/bin/env python3
"""
VMS Debug Tool - Kubectl Service Microservice
Handles kubectl operations and tenant management.
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
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8002))
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

# Tenant database storage
tenant_databases = {}

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

def parse_kubectl_output(output):
    """Parse kubectl get svc -A output and extract tenant information"""
    tenant_services = {}
    cleaned_output = clean_ansi_codes(output)
    lines = cleaned_output.strip().split('\n')
    
    logger.info(f"Parsing {len(lines)} lines of kubectl output")
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('NAMESPACE') or line.startswith('kubectl'):
            continue
        
        parts = line.split()
        if len(parts) >= 2:
            namespace = parts[0]
            service = parts[1]
            
            # Skip system namespaces
            if namespace in ['kube-system', 'kube-public', 'kube-node-lease', 'default']:
                continue
            
            if namespace not in tenant_services:
                tenant_services[namespace] = {
                    'services': [],
                    'redis_info': None
                }
                logger.info(f"Found new tenant namespace: {namespace}")
            
            if service not in tenant_services[namespace]['services']:
                tenant_services[namespace]['services'].append(service)
    
    return tenant_services

def extract_redis_ips(session_id):
    """Extract Redis service IPs for each tenant/namespace"""
    response = make_ssh_request('/execute', 'POST', 
                               {'command': 'kubectl get svc -A | grep redis', 'timeout': 15}, 
                               session_id)
    
    if 'error' in response:
        return {}
    
    output = response.get('output', '')
    cleaned_output = clean_ansi_codes(output)
    
    redis_info = {}
    lines = cleaned_output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('kubectl') or line.endswith('# ') or line.endswith('$ '):
            continue
        
        parts = line.split()
        if len(parts) >= 4 and 'redis' in line.lower():
            namespace = parts[0]
            service_name = parts[1]
            service_type = parts[2]
            cluster_ip = parts[3]
            external_ip = parts[4] if len(parts) > 4 else "N/A"
            ports = parts[5] if len(parts) > 5 else "N/A"
            age = parts[6] if len(parts) > 6 else "N/A"
            
            redis_info[namespace] = {
                'service_name': service_name,
                'service_type': service_type,
                'cluster_ip': cluster_ip,
                'external_ip': external_ip,
                'ports': ports,
                'age': age
            }
    
    return redis_info

def extract_configmaps_for_all_tenants(session_id):
    """Extract all configmaps for all tenants/namespaces"""
    logger.info("Extracting ConfigMaps for all tenants...")
    
    response = make_ssh_request('/execute', 'POST',
                               {'command': 'kubectl get configmaps -A', 'timeout': 15},
                               session_id)
    
    if 'error' in response:
        return {}
    
    output = response.get('output', '')
    cleaned_output = clean_ansi_codes(output)
    
    configmaps_data = {}
    lines = cleaned_output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if (not line or 
            line.startswith('NAMESPACE') or 
            line.startswith('kubectl') or 
            line.endswith('# ') or 
            line.endswith('$ ') or
            line.startswith('[root@')):
            continue
        
        parts = line.split()
        if len(parts) >= 3:
            namespace = parts[0]
            configmap_name = parts[1]
            data_count = parts[2]
            age = parts[3] if len(parts) > 3 else "N/A"
            
            # Skip system namespaces
            if namespace in ['kube-system', 'kube-public', 'kube-node-lease', 'default']:
                continue
            
            if namespace not in configmaps_data:
                configmaps_data[namespace] = {
                    'configmaps': [],
                    'total_configmaps': 0
                }
            
            configmap_info = {
                'name': configmap_name,
                'data_count': data_count,
                'age': age
            }
            
            configmaps_data[namespace]['configmaps'].append(configmap_info)
            configmaps_data[namespace]['total_configmaps'] = len(configmaps_data[namespace]['configmaps'])
    
    total_tenants_with_configmaps = len(configmaps_data)
    total_configmaps = sum(data['total_configmaps'] for data in configmaps_data.values())
    logger.info(f"Found {total_configmaps} configmaps across {total_tenants_with_configmaps} tenants")
    
    return configmaps_data

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'kubectl-service',
        'timestamp': datetime.now().isoformat(),
        'redis_connected': redis_client is not None,
        'ssh_service': SSH_SERVICE_URL,
        'tenant_databases': len(tenant_databases)
    })

@app.route('/run_commands', methods=['POST'])
def run_kubectl_commands():
    """Run basic kubectl commands"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        commands = [
            ("kubectl get ns", "Get all namespaces"),
            ("kubectl get pods -A", "Get all pods across all namespaces"),
            ("kubectl get svc -A", "Get all services across all namespaces"),
            ("kubectl get pv", "Get persistent volumes"),
            ("kubectl get pvc -A", "Get persistent volume claims"),
            ("kubectl get cm -A", "Get config maps"),
            ("kubectl get svc -A | grep redis", "Get Redis services")
        ]
        
        results = []
        for command, description in commands:
            logger.info(f"Session {session_id}: Running {command}")
            
            response = make_ssh_request('/execute', 'POST',
                                       {'command': command, 'timeout': 15},
                                       session_id)
            
            if 'error' in response:
                results.append({
                    'command': command,
                    'description': description,
                    'error': response['error']
                })
            else:
                output = response.get('output', '')
                cleaned_output = clean_ansi_codes(output)
                lines = [line.strip() for line in cleaned_output.split('\n') 
                        if line.strip() and not line.strip().startswith('kubectl') 
                        and not line.strip().endswith('# ') 
                        and not line.strip().endswith('$ ')
                        and not line.strip().startswith('[root@')]
                
                results.append({
                    'command': command,
                    'description': description,
                    'output': lines,
                    'line_count': len(lines)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_commands': len(commands)
        })
        
    except Exception as e:
        logger.error(f"Run kubectl commands error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/build_tenant_data', methods=['POST'])
def build_tenant_data():
    """Build comprehensive tenant data"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        logger.info(f"Session {session_id}: Building comprehensive tenant data")
        
        # Step 1: Get all services
        response = make_ssh_request('/execute', 'POST',
                                   {'command': 'kubectl get svc -A', 'timeout': 15},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to get services: {response['error']}"}), 500
        
        kubectl_output = response.get('output', '')
        tenant_data = parse_kubectl_output(kubectl_output)
        service_count = len(tenant_data)
        logger.info(f"Session {session_id}: Found {service_count} tenant namespaces")
        
        # Step 2: Get Redis information
        redis_info = extract_redis_ips(session_id)
        redis_count = len(redis_info)
        logger.info(f"Session {session_id}: Found {redis_count} Redis services")
        
        # Step 3: Integrate Redis information
        for tenant, redis_details in redis_info.items():
            if tenant in tenant_data:
                if tenant_data[tenant] is None:
                    tenant_data[tenant] = {'services': [], 'redis_info': None}
                tenant_data[tenant]['redis_info'] = redis_details
            else:
                tenant_data[tenant] = {
                    'services': ['redis'],
                    'redis_info': redis_details
                }
        
        # Step 4: Get ConfigMaps information
        configmaps_info = extract_configmaps_for_all_tenants(session_id)
        
        # Step 5: Integrate ConfigMaps information
        for tenant, configmap_details in configmaps_info.items():
            if tenant in tenant_data:
                if tenant_data[tenant] is None:
                    tenant_data[tenant] = {'services': [], 'redis_info': None, 'configmaps_info': None}
                tenant_data[tenant]['configmaps_info'] = configmap_details
            else:
                tenant_data[tenant] = {
                    'services': [],
                    'redis_info': None,
                    'configmaps_info': configmap_details
                }
        
        # Save tenant database
        tenant_databases[session_id] = tenant_data
        
        # Save to Redis
        if redis_client:
            redis_client.setex(f"tenant_data:{session_id}", 3600, json.dumps(tenant_data))
        
        filename = f"tenant_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        logger.info(f"Session {session_id}: Tenant data building completed successfully")
        
        return jsonify({
            'success': True,
            'tenant_data': tenant_data,
            'filename': filename,
            'summary': {
                'total_tenants': len(tenant_data),
                'tenants_with_redis': len([t for t in tenant_data.values() if t.get('redis_info')]),
                'tenants_with_configmaps': len([t for t in tenant_data.values() if t.get('configmaps_info')])
            }
        })
        
    except Exception as e:
        logger.error(f"Build tenant data error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_tenants', methods=['GET'])
def get_tenant_list():
    """Get list of tenants"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if session_id in tenant_databases:
            tenants = list(tenant_databases[session_id].keys())
        else:
            # Try to get from Redis
            if redis_client:
                data = redis_client.get(f"tenant_data:{session_id}")
                if data:
                    tenant_data = json.loads(data)
                    tenant_databases[session_id] = tenant_data
                    tenants = list(tenant_data.keys())
                else:
                    tenants = []
            else:
                tenants = []
        
        return jsonify({
            'success': True,
            'tenants': tenants,
            'total': len(tenants)
        })
        
    except Exception as e:
        logger.error(f"Get tenant list error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_tenant_info/<tenant_name>', methods=['GET'])
def get_tenant_info(tenant_name):
    """Get information for a specific tenant"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if session_id not in tenant_databases:
            # Try to get from Redis
            if redis_client:
                data = redis_client.get(f"tenant_data:{session_id}")
                if data:
                    tenant_databases[session_id] = json.loads(data)
        
        if session_id in tenant_databases and tenant_name in tenant_databases[session_id]:
            tenant_info = tenant_databases[session_id][tenant_name]
            return jsonify({
                'success': True,
                'tenant_info': tenant_info
            })
        else:
            return jsonify({'error': 'Tenant not found'}), 404
        
    except Exception as e:
        logger.error(f"Get tenant info error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_tenant_database', methods=['GET'])
def get_tenant_database():
    """Get complete tenant database"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if session_id not in tenant_databases:
            # Try to get from Redis
            if redis_client:
                data = redis_client.get(f"tenant_data:{session_id}")
                if data:
                    tenant_databases[session_id] = json.loads(data)
        
        database = tenant_databases.get(session_id, {})
        
        return jsonify({
            'success': True,
            'database': database,
            'total_tenants': len(database)
        })
        
    except Exception as e:
        logger.error(f"Get tenant database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_configmaps/<tenant_name>', methods=['GET'])
def get_configmaps_for_tenant(tenant_name):
    """Get ConfigMaps for a specific tenant"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if session_id not in tenant_databases:
            # Try to get from Redis
            if redis_client:
                data = redis_client.get(f"tenant_data:{session_id}")
                if data:
                    tenant_databases[session_id] = json.loads(data)
        
        if (session_id in tenant_databases and 
            tenant_name in tenant_databases[session_id] and
            tenant_databases[session_id][tenant_name].get('configmaps_info')):
            
            configmaps_info = tenant_databases[session_id][tenant_name]['configmaps_info']
            configmaps = configmaps_info.get('configmaps', [])
            
            return jsonify({
                'success': True,
                'configmaps': configmaps
            })
        else:
            return jsonify({
                'success': True,
                'configmaps': []
            })
        
    except Exception as e:
        logger.error(f"Get configmaps error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_configmap_details/<tenant_name>', methods=['POST'])
def get_configmap_details(tenant_name):
    """Get ConfigMap details using kubectl describe and kubectl get + jq"""
    try:
        session_id = request.headers.get('X-Session-ID')
        data = request.get_json()
        configmap_name = data.get('configmap')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if not configmap_name:
            return jsonify({'error': 'ConfigMap name required'}), 400
        
        logger.info(f"Session {session_id}: Getting ConfigMap details: {configmap_name} in {tenant_name}")
        
        # Execute raw format command
        raw_command = f"kubectl describe configmap {configmap_name} -n {tenant_name}"
        response = make_ssh_request('/execute', 'POST',
                                   {'command': raw_command, 'timeout': 15},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to get raw format: {response['error']}"}), 500
        
        raw_output = response.get('output', '')
        cleaned_raw_output = clean_ansi_codes(raw_output)
        
        # Parse raw output
        raw_lines = [line.strip() for line in cleaned_raw_output.split('\n')
                    if line.strip() and not line.strip().startswith('kubectl')
                    and not line.strip().endswith('# ') 
                    and not line.strip().endswith('$ ')
                    and not line.strip().startswith('[root@')]
        
        raw_format_output = '\n'.join(raw_lines)
        
        # Execute pretty format command
        pretty_command = f"kubectl get configmap {configmap_name} -n {tenant_name} -o json | jq \".data.config | fromjson\""
        response = make_ssh_request('/execute', 'POST',
                                   {'command': pretty_command, 'timeout': 15},
                                   session_id)
        
        pretty_format_output = ""
        parsed_json = None
        
        if 'error' not in response:
            pretty_output = response.get('output', '')
            cleaned_pretty_output = clean_ansi_codes(pretty_output)
            
            # Parse pretty output
            pretty_lines = [line.strip() for line in cleaned_pretty_output.split('\n')
                           if line.strip() and not line.strip().startswith('kubectl')
                           and not line.strip().endswith('# ') 
                           and not line.strip().endswith('$ ')
                           and not line.strip().startswith('[root@')
                           and 'jq:' not in line.lower()]
            
            pretty_format_output = '\n'.join(pretty_lines)
            
            # Try to parse as JSON
            try:
                if pretty_format_output.strip():
                    parsed_json = json.loads(pretty_format_output)
                    pretty_format_output = json.dumps(parsed_json, indent=2)
            except json.JSONDecodeError:
                pass
        
        configmap_details = {
            'name': configmap_name,
            'namespace': tenant_name,
            'raw_format': raw_format_output,
            'pretty_format': pretty_format_output,
            'parsed_json': parsed_json,
            'raw_command': raw_command,
            'pretty_command': pretty_command,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Session {session_id}: Successfully retrieved ConfigMap details")
        
        return jsonify({
            'success': True,
            'details': configmap_details
        })
        
    except Exception as e:
        logger.error(f"Get configmap details error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("VMS Debug Tool - Kubectl Service")
    logger.info("=" * 60)
    logger.info("Kubectl Operations and Tenant Management Microservice")
    logger.info("")
    logger.info("Features:")
    logger.info("  • Kubectl command execution")
    logger.info("  • Tenant data building and management")
    logger.info("  • ConfigMap operations")
    logger.info("  • Service discovery")
    logger.info("")
    logger.info(f"Server starting on http://0.0.0.0:{SERVICE_PORT}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
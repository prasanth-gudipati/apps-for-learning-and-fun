#!/usr/bin/env python3
"""
VMS Debug Tool - Web Frontend Microservice
Handles the web interface and coordinates with backend services.
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
import redis
import json
import uuid
import os
import threading
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vms-debug-tool-frontend-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Service URLs from environment
SSH_SERVICE_URL = os.getenv('SSH_SERVICE_URL', 'http://localhost:8001')
KUBECTL_SERVICE_URL = os.getenv('KUBECTL_SERVICE_URL', 'http://localhost:8002')
REDIS_SERVICE_URL = os.getenv('REDIS_SERVICE_URL', 'http://localhost:8003')
LOGS_SERVICE_URL = os.getenv('LOGS_SERVICE_URL', 'http://localhost:8004')
SESSION_REDIS_URL = os.getenv('SESSION_REDIS_URL', 'redis://localhost:6379')

# Redis client for session management
try:
    redis_client = redis.from_url(SESSION_REDIS_URL)
    redis_client.ping()
    logger.info("Connected to Redis successfully")
    
    # Set up progress monitoring
    def monitor_progress():
        """Monitor Redis for progress updates"""
        pubsub = redis_client.pubsub()
        pubsub.psubscribe('progress:*')
        
        for message in pubsub.listen():
            if message['type'] == 'pmessage':
                try:
                    channel = message['channel'].decode('utf-8')
                    session_id = channel.split(':')[1]
                    progress_data = json.loads(message['data'])
                    
                    # Emit progress to specific session
                    socketio.emit('connection_progress', progress_data, room=session_id)
                except Exception as e:
                    logger.error(f"Error processing progress message: {e}")
    
    # Start progress monitoring in background thread
    progress_thread = threading.Thread(target=monitor_progress, daemon=True)
    progress_thread.start()
    
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# Session management
active_sessions = {}

class SessionManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.connected = False
        
    def save_session_data(self, data):
        """Save session data to Redis"""
        if redis_client:
            try:
                redis_client.setex(f"session:{self.session_id}", 3600, json.dumps(data))
            except Exception as e:
                logger.error(f"Failed to save session data: {e}")
    
    def get_session_data(self):
        """Get session data from Redis"""
        if redis_client:
            try:
                data = redis_client.get(f"session:{self.session_id}")
                return json.loads(data) if data else {}
            except Exception as e:
                logger.error(f"Failed to get session data: {e}")
        return {}
    
    def clear_session_data(self):
        """Clear session data from Redis"""
        if redis_client:
            try:
                redis_client.delete(f"session:{self.session_id}")
            except Exception as e:
                logger.error(f"Failed to clear session data: {e}")

def get_session_manager(session_id=None):
    """Get or create session manager"""
    if not session_id:
        session_id = request.sid if hasattr(request, 'sid') else str(uuid.uuid4())
    
    if session_id not in active_sessions:
        active_sessions[session_id] = SessionManager(session_id)
    
    return active_sessions[session_id]

def emit_log(message, tag="normal", session_id=None):
    """Emit log message to client"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    emit_data = {
        'message': message,
        'tag': tag,
        'timestamp': timestamp
    }
    
    if session_id:
        socketio.emit('log_output', emit_data, room=session_id)
    else:
        emit('log_output', emit_data)

def make_service_request(service_url, endpoint, method='GET', data=None, session_id=None):
    """Make request to backend service"""
    url = f"{service_url}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    if session_id:
        headers['X-Session-ID'] = session_id
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Service request failed: {e}")
        return {'error': str(e)}

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'redis': redis_client is not None,
            'ssh_service': SSH_SERVICE_URL,
            'kubectl_service': KUBECTL_SERVICE_URL,
            'redis_service': REDIS_SERVICE_URL,
            'logs_service': LOGS_SERVICE_URL
        }
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    session_id = request.sid
    logger.info(f'Client connected with session ID: {session_id}')
    
    # Create session manager
    session_manager = get_session_manager(session_id)
    join_room(session_id)
    
    # Check session data for existing connection
    session_data = session_manager.get_session_data()
    if session_data.get('connected', False):
        emit('connection_status', {'connected': True, 'message': 'Connected to SSH server'})
    else:
        emit('connection_status', {'connected': False, 'message': 'Not Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    session_id = request.sid
    logger.info(f'Client disconnected with session ID: {session_id}')
    
    # Clean up session
    if session_id in active_sessions:
        # Disconnect from SSH if connected
        make_service_request(SSH_SERVICE_URL, '/disconnect', 'POST', session_id=session_id)
        
        # Clear session data
        session_manager = active_sessions[session_id]
        session_manager.clear_session_data()
        del active_sessions[session_id]
    
    leave_room(session_id)

@socketio.on('ssh_connect')
def handle_ssh_connect(data):
    """Handle SSH connection request"""
    session_id = request.sid
    session_manager = get_session_manager(session_id)
    
    # Add session_id to data
    data['session_id'] = session_id
    
    # Call SSH service
    response = make_service_request(SSH_SERVICE_URL, '/connect', 'POST', data, session_id)
    
    if 'error' in response:
        emit('connection_status', {'connected': False, 'message': f'Connection failed: {response["error"]}'})
        emit_log(f"Connection failed: {response['error']}", "error", session_id)
    else:
        session_manager.connected = response.get('connected', False)
        session_manager.save_session_data({'connected': session_manager.connected})
        
        if session_manager.connected:
            emit('connection_status', {'connected': True, 'message': 'Connected successfully'})
            emit_log("SSH connection successful", "success", session_id)
            
            # Automatically start building tenant data
            emit_log("🔄 Automatically building tenant data...", "info", session_id)
            handle_build_tenant_data()
        else:
            emit('connection_status', {'connected': False, 'message': 'Connection failed'})

@socketio.on('ssh_disconnect')
def handle_ssh_disconnect():
    """Handle SSH disconnection request"""
    session_id = request.sid
    session_manager = get_session_manager(session_id)
    
    # Call SSH service
    response = make_service_request(SSH_SERVICE_URL, '/disconnect', 'POST', session_id=session_id)
    
    session_manager.connected = False
    session_manager.save_session_data({'connected': False})
    emit('connection_status', {'connected': False, 'message': 'Disconnected'})
    emit_log("Disconnected from server", "info", session_id)

@socketio.on('run_kubectl')
def handle_run_kubectl():
    """Handle kubectl commands execution"""
    session_id = request.sid
    session_manager = get_session_manager(session_id)
    
    if not session_manager.connected:
        emit_log('Error: Not connected to server', 'error', session_id)
        return
    
    # Call kubectl service
    response = make_service_request(KUBECTL_SERVICE_URL, '/run_commands', 'POST', session_id=session_id)
    
    if 'error' in response:
        emit_log(f"Error running kubectl commands: {response['error']}", "error", session_id)
    else:
        emit_log("Kubectl commands completed successfully!", "success", session_id)

@socketio.on('build_tenant_data')
def handle_build_tenant_data():
    """Handle tenant data building"""
    session_id = request.sid
    session_manager = get_session_manager(session_id)
    
    if not session_manager.connected:
        emit_log('Error: Not connected to server', 'error', session_id)
        return
    
    # Call kubectl service for tenant data
    response = make_service_request(KUBECTL_SERVICE_URL, '/build_tenant_data', 'POST', session_id=session_id)
    
    if 'error' in response:
        emit_log(f"Error building tenant data: {response['error']}", "error", session_id)
    else:
        # Emit tenant data to client
        if 'tenant_data' in response:
            emit('tenant_data', {
                'data': response['tenant_data'], 
                'filename': response.get('filename', 'tenant_data.json')
            })
            emit('tenant_database_updated', {
                'tenants': list(response['tenant_data'].keys())
            })
        
        # Get log files
        logs_response = make_service_request(LOGS_SERVICE_URL, '/scan_log_files', 'GET', session_id=session_id)
        if 'log_files' in logs_response:
            emit('log_files_response', {'log_files': logs_response['log_files']})
        
        emit_log("✓ Tenant data building completed! All operations are now available.", "success", session_id)

@socketio.on('clear_output')
def handle_clear_output():
    """Handle clear output request"""
    emit('clear_output_response', {})

@socketio.on('get_tenant_list')
def handle_get_tenant_list():
    """Handle request for tenant list"""
    session_id = request.sid
    
    response = make_service_request(KUBECTL_SERVICE_URL, '/get_tenants', 'GET', session_id=session_id)
    
    if 'tenants' in response:
        emit('tenant_list_response', {'tenants': response['tenants']})
    else:
        emit('tenant_list_response', {'tenants': []})

@socketio.on('select_tenant')
def handle_select_tenant(data):
    """Handle tenant selection"""
    session_id = request.sid
    tenant_name = data.get('tenant', '')
    
    if not tenant_name:
        emit('tenant_info_response', {'tenant': '', 'info': None, 'error': 'No tenant specified'})
        return
    
    response = make_service_request(KUBECTL_SERVICE_URL, f'/get_tenant_info/{tenant_name}', 'GET', session_id=session_id)
    
    if 'error' in response:
        emit('tenant_info_response', {'tenant': tenant_name, 'info': None, 'error': response['error']})
    else:
        emit('tenant_info_response', {'tenant': tenant_name, 'info': response.get('tenant_info')})

@socketio.on('show_tenant_database')
def handle_show_tenant_database():
    """Handle request to show complete tenant database"""
    session_id = request.sid
    
    response = make_service_request(KUBECTL_SERVICE_URL, '/get_tenant_database', 'GET', session_id=session_id)
    
    if 'database' in response:
        emit('show_database_response', {'database': response['database']})
    else:
        emit('show_database_response', {'database': {}})

@socketio.on('get_redis_keys')
def handle_get_redis_keys(data):
    """Handle request to get Redis keys for a tenant"""
    session_id = request.sid
    tenant_name = data.get('tenant', '')
    
    if not tenant_name:
        emit('redis_keys_response', {'tenant': '', 'keys': [], 'error': 'No tenant specified'})
        return
    
    response = make_service_request(REDIS_SERVICE_URL, f'/get_keys/{tenant_name}', 'GET', session_id=session_id)
    
    if 'error' in response:
        emit('redis_keys_response', {'tenant': tenant_name, 'keys': [], 'error': response['error']})
    else:
        emit('redis_keys_response', {'tenant': tenant_name, 'keys': response.get('keys', [])})

@socketio.on('get_redis_key_value')
def handle_get_redis_key_value(data):
    """Handle request to get Redis key value"""
    session_id = request.sid
    tenant_name = data.get('tenant', '')
    key_name = data.get('key', '')
    
    if not tenant_name or not key_name:
        emit('redis_key_value_response', {
            'tenant': tenant_name, 
            'key': key_name, 
            'value': None, 
            'error': 'Missing tenant or key name'
        })
        return
    
    response = make_service_request(REDIS_SERVICE_URL, f'/get_key_value/{tenant_name}', 'POST', 
                                   {'key': key_name}, session_id)
    
    if 'error' in response:
        emit('redis_key_value_response', {
            'tenant': tenant_name, 
            'key': key_name, 
            'value': None, 
            'error': response['error']
        })
    else:
        emit('redis_key_value_response', {
            'tenant': tenant_name,
            'key': key_name, 
            'value': response.get('value')
        })

@socketio.on('get_configmaps')
def handle_get_configmaps(data):
    """Handle request to get ConfigMaps for a tenant"""
    session_id = request.sid
    tenant_name = data.get('tenant', '')
    
    if not tenant_name:
        emit('configmaps_response', {'tenant': '', 'configmaps': [], 'error': 'Missing tenant name'})
        return
    
    response = make_service_request(KUBECTL_SERVICE_URL, f'/get_configmaps/{tenant_name}', 'GET', session_id=session_id)
    
    if 'error' in response:
        emit('configmaps_response', {'tenant': tenant_name, 'configmaps': [], 'error': response['error']})
    else:
        emit('configmaps_response', {'tenant': tenant_name, 'configmaps': response.get('configmaps', [])})

@socketio.on('get_configmap_json_details')
def handle_get_configmap_json_details(data):
    """Handle request to get ConfigMap JSON details"""
    session_id = request.sid
    tenant_name = data.get('tenant', '')
    configmap_name = data.get('configmap', '')
    
    if not tenant_name or not configmap_name:
        emit('configmap_json_details_response', {
            'tenant': tenant_name, 
            'configmap': configmap_name, 
            'details': {}, 
            'error': 'Missing tenant or configmap name'
        })
        return
    
    response = make_service_request(KUBECTL_SERVICE_URL, f'/get_configmap_details/{tenant_name}', 'POST',
                                   {'configmap': configmap_name}, session_id)
    
    if 'error' in response:
        emit('configmap_json_details_response', {
            'tenant': tenant_name, 
            'configmap': configmap_name, 
            'details': {}, 
            'error': response['error']
        })
    else:
        emit('configmap_json_details_response', {
            'tenant': tenant_name,
            'configmap': configmap_name,
            'details': response.get('details', {})
        })

@socketio.on('scan_log_files')
def handle_scan_log_files():
    """Handle request to scan for log files"""
    session_id = request.sid
    
    response = make_service_request(LOGS_SERVICE_URL, '/scan_log_files', 'GET', session_id=session_id)
    
    if 'error' in response:
        emit('log_files_response', {'log_files': {}, 'error': response['error']})
    else:
        emit('log_files_response', {'log_files': response.get('log_files', {})})

@socketio.on('get_log_file_content')
def handle_get_log_file_content(data):
    """Handle request to get log file content"""
    session_id = request.sid
    log_file_path = data.get('path', '')
    lines = data.get('lines', 250)
    log_filter = data.get('filter', 'all')
    
    if not log_file_path:
        emit('log_file_content_response', {
            'path': log_file_path, 
            'content': {}, 
            'error': 'Missing log file path'
        })
        return
    
    response = make_service_request(LOGS_SERVICE_URL, '/get_log_content', 'POST',
                                   {'path': log_file_path, 'lines': lines, 'filter': log_filter}, 
                                   session_id)
    
    if 'error' in response:
        emit('log_file_content_response', {
            'path': log_file_path, 
            'content': {}, 
            'error': response['error']
        })
    else:
        emit('log_file_content_response', {
            'path': log_file_path,
            'content': response.get('content', {}),
            'lines': lines,
            'filter': log_filter
        })

if __name__ == '__main__':
    # Create templates directory and files
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('shared-logs', exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("VMS Debug Tool - Web Frontend Microservice")
    logger.info("=" * 60)
    logger.info("Microservices Architecture with Docker")
    logger.info("")
    logger.info("Services:")
    logger.info(f"  • Web Frontend: Port 5000")
    logger.info(f"  • SSH Service: {SSH_SERVICE_URL}")
    logger.info(f"  • Kubectl Service: {KUBECTL_SERVICE_URL}")
    logger.info(f"  • Redis Service: {REDIS_SERVICE_URL}")
    logger.info(f"  • Logs Service: {LOGS_SERVICE_URL}")
    logger.info(f"  • Session Redis: {SESSION_REDIS_URL}")
    logger.info("")
    logger.info("Server starting on http://0.0.0.0:5000")
    logger.info("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
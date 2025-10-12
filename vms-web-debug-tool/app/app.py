#!/usr/bin/env python3
"""
VMS Web Debug Tool - Flask Application
A web-based interface for VMS debugging and tenant management
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import logging
from datetime import datetime
import json

# Import our custom services
from services.ssh_service import SSHService
from services.tenant_service import TenantService
from services.redis_service import RedisService
from services.database_service import DatabaseService
from services.vms_service import VMSService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'vms-debug-tool-secret-key-2025')
    app.config['MONGODB_URL'] = os.getenv('MONGODB_URL', 'mongodb://mongo:27017/vms_debug')
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://redis:6379')
    
    # Enable CORS
    CORS(app)
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize services
    db_service = DatabaseService(app.config['MONGODB_URL'])
    ssh_service = SSHService()
    tenant_service = TenantService(db_service)
    redis_service = RedisService(db_service)
    vms_service = VMSService(db_service, ssh_service)
    
    # Store services in app context
    app.db_service = db_service
    app.ssh_service = ssh_service
    app.tenant_service = tenant_service
    app.redis_service = redis_service
    app.vms_service = vms_service
    app.socketio = socketio
    
    return app, socketio

# Create app instance
app, socketio = create_app()

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        return jsonify({"error": "Failed to load application"}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": app.db_service.test_connection(),
            "ssh": "ready",
            "redis_cache": "ready"
        }
    })

# SSH Connection Routes
@app.route('/api/ssh/connect', methods=['POST'])
def ssh_connect():
    """Establish SSH connection to VMS server"""
    try:
        data = request.get_json()
        host = data.get('host', 'vms1-tb163.versa-test.net')
        username = data.get('username', 'admin')
        password = data.get('password')
        sudo_password = data.get('sudo_password')
        
        if not password:
            return jsonify({"error": "SSH password is required"}), 400
        
        # Establish connection
        connection_id = app.ssh_service.connect(host, username, password, sudo_password)
        
        if connection_id:
            # Store connection info in session
            session['ssh_connection_id'] = connection_id
            
            return jsonify({
                "success": True,
                "connection_id": connection_id,
                "message": f"Connected to {host} as {username}"
            })
        else:
            return jsonify({"error": "Failed to establish SSH connection"}), 500
            
    except Exception as e:
        logger.error(f"SSH connection error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ssh/disconnect', methods=['POST'])
def ssh_disconnect():
    """Disconnect SSH connection"""
    try:
        connection_id = session.get('ssh_connection_id')
        if connection_id:
            app.ssh_service.disconnect(connection_id)
            session.pop('ssh_connection_id', None)
            
        return jsonify({"success": True, "message": "Disconnected from VMS server"})
    except Exception as e:
        logger.error(f"SSH disconnect error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ssh/status')
def ssh_status():
    """Get SSH connection status"""
    try:
        connection_id = session.get('ssh_connection_id')
        if connection_id:
            status = app.ssh_service.get_connection_status(connection_id)
            return jsonify({"connected": status, "connection_id": connection_id})
        else:
            return jsonify({"connected": False, "connection_id": None})
    except Exception as e:
        logger.error(f"SSH status error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Tenant Management Routes
@app.route('/api/tenants/scan', methods=['POST'])
def scan_tenants():
    """Scan and collect comprehensive tenant data"""
    try:
        connection_id = session.get('ssh_connection_id')
        if not connection_id:
            return jsonify({"error": "No SSH connection established"}), 400
        
        include_redis_keys = request.json.get('include_redis_keys', True)
        
        # Start background task for tenant scanning
        socketio.start_background_task(
            target=scan_tenants_background,
            connection_id=connection_id,
            include_redis_keys=include_redis_keys
        )
        
        return jsonify({"success": True, "message": "Tenant scan started in background"})
        
    except Exception as e:
        logger.error(f"Tenant scan error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def scan_tenants_background(connection_id, include_redis_keys=True):
    """Background task for scanning tenants"""
    try:
        socketio.emit('scan_progress', {'status': 'Starting tenant scan...'})
        
        # Collect comprehensive tenant data
        tenant_data = app.vms_service.collect_comprehensive_tenant_data(
            connection_id, 
            include_redis_keys=include_redis_keys,
            progress_callback=lambda msg: socketio.emit('scan_progress', {'status': msg})
        )
        
        if tenant_data:
            # Save to database
            app.tenant_service.save_tenant_data(tenant_data)
            socketio.emit('scan_complete', {
                'success': True,
                'tenant_count': len(tenant_data),
                'message': 'Tenant scan completed successfully'
            })
        else:
            socketio.emit('scan_complete', {
                'success': False,
                'message': 'No tenant data found'
            })
            
    except Exception as e:
        logger.error(f"Background tenant scan error: {str(e)}")
        socketio.emit('scan_complete', {
            'success': False,
            'message': f'Tenant scan failed: {str(e)}'
        })

@app.route('/api/tenants')
def get_tenants():
    """Get all tenants"""
    try:
        tenants = app.tenant_service.get_all_tenants()
        return jsonify({"tenants": tenants})
    except Exception as e:
        logger.error(f"Get tenants error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tenants/<tenant_name>')
def get_tenant_details(tenant_name):
    """Get detailed information for a specific tenant"""
    try:
        tenant = app.tenant_service.get_tenant_by_name(tenant_name)
        if tenant:
            return jsonify({"tenant": tenant})
        else:
            return jsonify({"error": "Tenant not found"}), 404
    except Exception as e:
        logger.error(f"Get tenant details error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Redis Key Management Routes
@app.route('/api/redis/keys/<tenant_name>')
def get_redis_keys(tenant_name):
    """Get Redis keys for a specific tenant"""
    try:
        keys = app.redis_service.get_tenant_keys(tenant_name)
        return jsonify({"keys": keys})
    except Exception as e:
        logger.error(f"Get Redis keys error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/redis/key-value', methods=['POST'])
def get_redis_key_value():
    """Get value for a specific Redis key"""
    try:
        data = request.get_json()
        tenant_name = data.get('tenant_name')
        key_name = data.get('key_name')
        format_type = data.get('format', 'pretty_json')
        
        connection_id = session.get('ssh_connection_id')
        if not connection_id:
            return jsonify({"error": "No SSH connection established"}), 400
        
        key_value = app.redis_service.get_key_value(
            connection_id, tenant_name, key_name, format_type
        )
        
        return jsonify({"key_value": key_value})
    except Exception as e:
        logger.error(f"Get Redis key value error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# VMS Status and Logs Routes
@app.route('/api/vms/status-check', methods=['POST'])
def run_vms_status_check():
    """Run VMS status check"""
    try:
        connection_id = session.get('ssh_connection_id')
        if not connection_id:
            return jsonify({"error": "No SSH connection established"}), 400
        
        # Start background task
        socketio.start_background_task(
            target=vms_status_check_background,
            connection_id=connection_id
        )
        
        return jsonify({"success": True, "message": "VMS status check started"})
    except Exception as e:
        logger.error(f"VMS status check error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def vms_status_check_background(connection_id):
    """Background task for VMS status check"""
    try:
        socketio.emit('status_check_progress', {'status': 'Running VMS status check...'})
        
        result = app.vms_service.run_status_check(
            connection_id,
            progress_callback=lambda msg: socketio.emit('status_check_progress', {'status': msg})
        )
        
        socketio.emit('status_check_complete', {
            'success': True,
            'message': 'VMS status check completed',
            'log_entries': result.get('log_entries', 0)
        })
    except Exception as e:
        logger.error(f"Background VMS status check error: {str(e)}")
        socketio.emit('status_check_complete', {
            'success': False,
            'message': f'VMS status check failed: {str(e)}'
        })

@app.route('/api/logs/system')
def get_system_logs():
    """Get system logs"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        log_type = request.args.get('type')
        
        logs = app.db_service.get_system_logs(page=page, limit=limit, log_type=log_type)
        return jsonify({"logs": logs})
    except Exception as e:
        logger.error(f"Get system logs error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/vms-status')
def get_vms_status_logs():
    """Get VMS status check logs"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        logs = app.db_service.get_vms_status_logs(page=page, limit=limit)
        return jsonify({"logs": logs})
    except Exception as e:
        logger.error(f"Get VMS status logs error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to VMS Debug Tool'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('/app/logs', exist_ok=True)
    
    logger.info("Starting VMS Web Debug Tool...")
    logger.info(f"Flask version: {Flask.__version__}")
    
    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', '0') == '1',
        allow_unsafe_werkzeug=True
    )
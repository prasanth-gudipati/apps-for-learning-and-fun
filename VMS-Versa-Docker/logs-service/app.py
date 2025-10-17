#!/usr/bin/env python3
"""
VMS Debug Tool - Logs Service Microservice
Handles log file operations and management.
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
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8004))
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

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'logs-service',
        'timestamp': datetime.now().isoformat(),
        'redis_connected': redis_client is not None,
        'ssh_service': SSH_SERVICE_URL
    })

@app.route('/scan_log_files', methods=['GET'])
def scan_log_files():
    """Scan for all log files in /var/log/versa/vms/apps directory and subdirectories, plus vms-admin.log"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        logger.info(f"Session {session_id}: Scanning for log files")
        
        # Execute find command to get all files in the apps directory, excluding .gz files
        command = "find /var/log/versa/vms/apps -type f -name '*.log*' ! -name '*.gz' | sort"
        response = make_ssh_request('/execute', 'POST',
                                   {'command': command, 'timeout': 15},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to scan log files: {response['error']}"}), 500
        
        output = response.get('output', '')
        cleaned_output = clean_ansi_codes(output)
        lines = cleaned_output.strip().split('\n')
        
        log_files = {}
        
        # Process apps directory files
        for line in lines:
            line = line.strip()
            # Skip command echo, prompts, and empty lines
            if (not line or 
                line.startswith('find') or 
                line.endswith('# ') or 
                line.endswith('$ ') or
                line.startswith('[root@')):
                continue
            
            # Check if it's a valid log file path and exclude .gz files
            if (line.startswith('/var/log/versa/vms/apps/') and 
                ('log' in line.lower()) and 
                not line.endswith('.gz')):
                # Extract directory and filename
                path_parts = line.split('/')
                if len(path_parts) >= 6:  # /var/log/versa/vms/apps/[directory]/[filename]
                    directory = path_parts[6] if len(path_parts) > 6 else 'root'
                    filename = path_parts[-1]
                    
                    if directory not in log_files:
                        log_files[directory] = []
                    
                    log_files[directory].append({
                        'name': filename,
                        'path': line,
                        'directory': directory
                    })
        
        # Check for vms-admin.log
        logger.info(f"Session {session_id}: Checking for vms-admin.log file")
        vms_admin_command = "ls -la /var/log/versa/vms/vms-admin.log 2>/dev/null"
        vms_admin_response = make_ssh_request('/execute', 'POST',
                                            {'command': vms_admin_command, 'timeout': 10},
                                            session_id)
        
        # Check if vms-admin.log exists
        vms_admin_exists = False
        if 'error' not in vms_admin_response:
            vms_admin_output = vms_admin_response.get('output', '')
            cleaned_vms_admin_output = clean_ansi_codes(vms_admin_output)
            
            for line in cleaned_vms_admin_output.split('\n'):
                line = line.strip()
                if (line and 
                    'vms-admin.log' in line and 
                    not line.startswith('ls ') and
                    not line.endswith('# ') and 
                    not line.endswith('$ ') and
                    not line.startswith('[root@')):
                    vms_admin_exists = True
                    break
        
        if vms_admin_exists:
            if "VMS Admin" not in log_files:
                log_files["VMS Admin"] = []
            
            log_files["VMS Admin"].append({
                'name': 'vms-admin.log',
                'path': '/var/log/versa/vms/vms-admin.log',
                'directory': 'VMS Admin'
            })
            logger.info(f"Session {session_id}: Found vms-admin.log file")
        else:
            logger.info(f"Session {session_id}: vms-admin.log file not found or not accessible")
        
        # Sort files within each directory
        for directory in log_files:
            log_files[directory].sort(key=lambda x: x['name'])
        
        total_files = sum(len(files) for files in log_files.values())
        total_dirs = len(log_files)
        logger.info(f"Session {session_id}: Found {total_files} log files across {total_dirs} directories (excluding .gz files)")
        
        return jsonify({
            'success': True,
            'log_files': log_files,
            'summary': {
                'total_files': total_files,
                'total_directories': total_dirs
            }
        })
        
    except Exception as e:
        logger.error(f"Scan log files error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_log_content', methods=['POST'])
def get_log_file_content():
    """Get the last N lines of a log file with filtering options"""
    try:
        session_id = request.headers.get('X-Session-ID')
        data = request.get_json()
        
        log_file_path = data.get('path')
        lines = data.get('lines', 250)
        log_filter = data.get('filter', 'all')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if not log_file_path:
            return jsonify({'error': 'Log file path required'}), 400
        
        logger.info(f"Session {session_id}: Getting last {lines} lines from: {log_file_path} (filter: {log_filter})")
        
        # Build command based on filter type
        if log_filter == 'all':
            # Show last N lines as raw format
            command = f"tail -n {lines} \"{log_file_path}\""
        elif log_filter == 'errors':
            # Show only ERROR messages in last N lines with 2 spaces before each error
            command = f"tail -n {lines} \"{log_file_path}\" | grep -i error | sed 's/^/  /'"
        elif log_filter == 'pretty':
            # Show all N logs but highlight errors with empty line before each error
            command = f"tail -n {lines} \"{log_file_path}\" | sed '/[Ee][Rr][Rr][Oo][Rr]/i\\\\'"
        else:
            command = f"tail -n {lines} \"{log_file_path}\""
        
        response = make_ssh_request('/execute', 'POST',
                                   {'command': command, 'timeout': 20},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to get log content: {response['error']}"}), 500
        
        output = response.get('output', '')
        cleaned_output = clean_ansi_codes(output)
        lines_output = cleaned_output.strip().split('\n')
        
        # Clean lines and remove command echo/prompts
        cleaned_lines = []
        for line in lines_output:
            line = line.rstrip()
            # Skip command echo, prompts, and empty continuation
            if (line.startswith('tail ') or 
                line.endswith('# ') or 
                line.endswith('$ ') or
                line.startswith('[root@')):
                continue
            
            cleaned_lines.append(line)
        
        # Join lines back together
        log_content = '\n'.join(cleaned_lines)
        
        logger.info(f"Session {session_id}: Successfully retrieved {len(cleaned_lines)} lines from log file")
        
        return jsonify({
            'success': True,
            'content': {
                'path': log_file_path,
                'lines_requested': lines,
                'lines_retrieved': len(cleaned_lines),
                'content': log_content,
                'command': command,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Get log file content error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search_logs', methods=['POST'])
def search_logs():
    """Search for patterns in log files"""
    try:
        session_id = request.headers.get('X-Session-ID')
        data = request.get_json()
        
        log_file_path = data.get('path')
        search_pattern = data.get('pattern')
        lines = data.get('lines', 1000)
        case_sensitive = data.get('case_sensitive', False)
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if not log_file_path or not search_pattern:
            return jsonify({'error': 'Log file path and search pattern required'}), 400
        
        logger.info(f"Session {session_id}: Searching for pattern '{search_pattern}' in {log_file_path}")
        
        # Build grep command
        grep_flags = "-n"  # Show line numbers
        if not case_sensitive:
            grep_flags += "i"  # Case insensitive
        
        command = f"tail -n {lines} \"{log_file_path}\" | grep {grep_flags} \"{search_pattern}\""
        
        response = make_ssh_request('/execute', 'POST',
                                   {'command': command, 'timeout': 20},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to search logs: {response['error']}"}), 500
        
        output = response.get('output', '')
        cleaned_output = clean_ansi_codes(output)
        lines_output = cleaned_output.strip().split('\n')
        
        # Parse search results
        search_results = []
        for line in lines_output:
            line = line.strip()
            # Skip command echo and prompts
            if (not line or
                line.startswith('tail ') or
                line.startswith('grep ') or
                line.endswith('# ') or 
                line.endswith('$ ') or
                line.startswith('[root@')):
                continue
            
            search_results.append(line)
        
        logger.info(f"Session {session_id}: Found {len(search_results)} matches for pattern '{search_pattern}'")
        
        return jsonify({
            'success': True,
            'results': {
                'path': log_file_path,
                'pattern': search_pattern,
                'matches': search_results,
                'total_matches': len(search_results),
                'command': command,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Search logs error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_log_stats', methods=['POST'])
def get_log_file_stats():
    """Get statistics about a log file"""
    try:
        session_id = request.headers.get('X-Session-ID')
        data = request.get_json()
        
        log_file_path = data.get('path')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if not log_file_path:
            return jsonify({'error': 'Log file path required'}), 400
        
        logger.info(f"Session {session_id}: Getting statistics for {log_file_path}")
        
        # Get file size, line count, and modification time
        stats_command = f"ls -lh \"{log_file_path}\" && wc -l \"{log_file_path}\""
        
        response = make_ssh_request('/execute', 'POST',
                                   {'command': stats_command, 'timeout': 10},
                                   session_id)
        
        if 'error' in response:
            return jsonify({'error': f"Failed to get log stats: {response['error']}"}), 500
        
        output = response.get('output', '')
        cleaned_output = clean_ansi_codes(output)
        lines = cleaned_output.strip().split('\n')
        
        file_info = {}
        line_count = 0
        
        for line in lines:
            line = line.strip()
            # Skip command echo and prompts
            if (not line or
                line.startswith('ls ') or
                line.startswith('wc ') or
                line.endswith('# ') or 
                line.endswith('$ ') or
                line.startswith('[root@')):
                continue
            
            # Parse ls output (file size and date)
            if line.startswith('-') and log_file_path in line:
                parts = line.split()
                if len(parts) >= 9:
                    file_info['permissions'] = parts[0]
                    file_info['size'] = parts[4]
                    file_info['date'] = ' '.join(parts[5:8])
            
            # Parse wc output (line count)
            elif line.strip().isdigit() or (line.split()[0].isdigit() and log_file_path in line):
                try:
                    line_count = int(line.split()[0])
                except ValueError:
                    pass
        
        file_info['line_count'] = line_count
        file_info['path'] = log_file_path
        
        logger.info(f"Session {session_id}: Successfully retrieved statistics for {log_file_path}")
        
        return jsonify({
            'success': True,
            'stats': file_info
        })
        
    except Exception as e:
        logger.error(f"Get log file stats error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("VMS Debug Tool - Logs Service")
    logger.info("=" * 60)
    logger.info("Log File Operations Microservice")
    logger.info("")
    logger.info("Features:")
    logger.info("  • Log file scanning and discovery")
    logger.info("  • Log content retrieval with filtering")
    logger.info("  • Log search functionality")
    logger.info("  • Log file statistics")
    logger.info("")
    logger.info(f"Server starting on http://0.0.0.0:{SERVICE_PORT}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
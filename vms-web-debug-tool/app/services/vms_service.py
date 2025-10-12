"""
VMS Service - Handles VMS operations and status checks
"""

import re
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VMSService:
    def __init__(self, db_service, ssh_service):
        self.db = db_service
        self.ssh = ssh_service
    
    def collect_comprehensive_tenant_data(self, connection_id, include_redis_keys=True, progress_callback=None):
        """Collect comprehensive tenant data including Redis keys"""
        try:
            if progress_callback:
                progress_callback("Starting comprehensive tenant data collection...")
            
            # Step 1: Get all services
            if progress_callback:
                progress_callback("Getting all services across namespaces...")
            
            kubectl_output = self.ssh.execute_command(connection_id, "kubectl get svc -A")
            tenant_data = self._parse_kubectl_output(kubectl_output)
            
            # Step 2: Get Redis information
            if progress_callback:
                progress_callback("Extracting Redis service information...")
            
            redis_info = self._extract_redis_ips(connection_id)
            
            # Integrate Redis information
            for tenant, redis_details in redis_info.items():
                if tenant in tenant_data:
                    tenant_data[tenant]['redis_info'] = redis_details
                else:
                    tenant_data[tenant] = {
                        'services': ['redis'],
                        'redis_info': redis_details
                    }
            
            # Step 3: Extract Redis keys if requested
            if include_redis_keys:
                if progress_callback:
                    progress_callback("Extracting Redis keys for each tenant...")
                
                for tenant, data in tenant_data.items():
                    if data.get('redis_info') and data['redis_info'].get('cluster_ip'):
                        redis_ip = data['redis_info']['cluster_ip']
                        
                        if progress_callback:
                            progress_callback(f"Getting Redis keys for {tenant} ({redis_ip})...")
                        
                        keys = self._extract_redis_keys(connection_id, redis_ip)
                        tenant_data[tenant]['redis_info']['keys'] = keys
                        tenant_data[tenant]['redis_info']['key_count'] = len(keys)
            
            if progress_callback:
                progress_callback(f"Tenant data collection completed. Found {len(tenant_data)} tenants.")
            
            return tenant_data
            
        except Exception as e:
            logger.error(f"Collect comprehensive tenant data error: {str(e)}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            raise
    
    def _parse_kubectl_output(self, output):
        """Parse kubectl get svc -A output"""
        try:
            tenant_services = {}
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('NAMESPACE') or line.startswith('kubectl'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    namespace = parts[0]  # Tenant/namespace
                    service = parts[1]    # Service name
                    
                    # Skip system namespaces
                    if namespace in ['kube-system', 'kube-public', 'kube-node-lease', 'default']:
                        continue
                    
                    if namespace not in tenant_services:
                        tenant_services[namespace] = {
                            'services': [],
                            'redis_info': None
                        }
                    
                    if service not in tenant_services[namespace]['services']:
                        tenant_services[namespace]['services'].append(service)
            
            return tenant_services
            
        except Exception as e:
            logger.error(f"Parse kubectl output error: {str(e)}")
            return {}
    
    def _extract_redis_ips(self, connection_id):
        """Extract Redis service IPs"""
        try:
            output = self.ssh.execute_command(connection_id, "kubectl get svc -A | grep redis")
            redis_info = {}
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or 'redis' not in line.lower():
                    continue
                
                parts = line.split()
                if len(parts) >= 4:
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
            
        except Exception as e:
            logger.error(f"Extract Redis IPs error: {str(e)}")
            return {}
    
    def _extract_redis_keys(self, connection_id, redis_ip, redis_port="6379"):
        """Extract Redis keys for a given IP"""
        try:
            command = f"redis-cli -h {redis_ip} -p {redis_port} keys \"*\""
            output = self.ssh.execute_command(connection_id, command, timeout=15)
            
            lines = output.strip().split('\n')
            keys = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('(error)'):
                    continue
                
                # Remove numbering if present
                if ')' in line and line.split(')')[0].strip().isdigit():
                    key = ')'.join(line.split(')')[1:]).strip()
                    key = key.strip('"\'')
                    if key:
                        keys.append(key)
                else:
                    key = line.strip('"\'')
                    if key and not key.startswith('redis'):
                        keys.append(key)
            
            return keys
            
        except Exception as e:
            logger.error(f"Extract Redis keys error for {redis_ip}: {str(e)}")
            return []
    
    def run_status_check(self, connection_id, progress_callback=None):
        """Run comprehensive VMS status check"""
        try:
            if progress_callback:
                progress_callback("Starting VMS status check...")
            
            kubectl_commands = [
                ("kubectl get ns", "Get all namespaces"),
                ("kubectl get pods -A", "Get all pods across all namespaces"),
                ("kubectl get pv", "Get persistent volumes"),
                ("kubectl get pvc -A", "Get persistent volume claims across all namespaces"),
                ("kubectl get cm -A", "Get config maps across all namespaces"),
                ("kubectl get svc -A | grep redis", "Get Redis services across all namespaces")
            ]
            
            run_time = datetime.utcnow()
            log_entries = 0
            
            for command, description in kubectl_commands:
                if progress_callback:
                    progress_callback(f"Running: {command}")
                
                try:
                    output = self.ssh.execute_command(connection_id, command)
                    
                    # Save to database
                    self.db.save_vms_status_log(
                        command=command,
                        output=output,
                        run_time=run_time,
                        metadata={
                            'description': description,
                            'output_lines': len(output.split('\n')) if output else 0
                        }
                    )
                    
                    log_entries += 1
                    
                except Exception as cmd_e:
                    logger.error(f"Command execution error for {command}: {str(cmd_e)}")
                    
                    # Save error to database
                    self.db.save_vms_status_log(
                        command=command,
                        output=f"ERROR: {str(cmd_e)}",
                        run_time=run_time,
                        metadata={
                            'description': description,
                            'error': True
                        }
                    )
            
            if progress_callback:
                progress_callback(f"VMS status check completed. Saved {log_entries} log entries.")
            
            return {
                'success': True,
                'log_entries': log_entries,
                'run_time': run_time
            }
            
        except Exception as e:
            logger.error(f"VMS status check error: {str(e)}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            raise
    
    def run_configmaps_export(self, connection_id, progress_callback=None):
        """Export all configmaps in JSON format"""
        try:
            if progress_callback:
                progress_callback("Starting ConfigMaps JSON export...")
            
            command = "kubectl get configmaps -A -o json"
            output = self.ssh.execute_command(connection_id, command, timeout=30)
            
            run_time = datetime.utcnow()
            
            # Save to database
            self.db.save_vms_status_log(
                command=command,
                output=output,
                run_time=run_time,
                metadata={
                    'description': 'Export all configmaps in JSON format',
                    'export_type': 'configmaps_json',
                    'output_size': len(output) if output else 0
                }
            )
            
            if progress_callback:
                progress_callback("ConfigMaps export completed successfully.")
            
            return {
                'success': True,
                'output_size': len(output) if output else 0,
                'run_time': run_time
            }
            
        except Exception as e:
            logger.error(f"ConfigMaps export error: {str(e)}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            raise
    
    def get_system_overview(self, connection_id):
        """Get system overview information"""
        try:
            overview = {}
            
            # Get namespace count
            ns_output = self.ssh.execute_command(connection_id, "kubectl get ns --no-headers | wc -l")
            overview['namespace_count'] = int(ns_output.strip()) if ns_output.strip().isdigit() else 0
            
            # Get pod count
            pod_output = self.ssh.execute_command(connection_id, "kubectl get pods -A --no-headers | wc -l")
            overview['pod_count'] = int(pod_output.strip()) if pod_output.strip().isdigit() else 0
            
            # Get service count
            svc_output = self.ssh.execute_command(connection_id, "kubectl get svc -A --no-headers | wc -l")
            overview['service_count'] = int(svc_output.strip()) if svc_output.strip().isdigit() else 0
            
            # Get PV count
            pv_output = self.ssh.execute_command(connection_id, "kubectl get pv --no-headers | wc -l")
            overview['pv_count'] = int(pv_output.strip()) if pv_output.strip().isdigit() else 0
            
            return overview
            
        except Exception as e:
            logger.error(f"Get system overview error: {str(e)}")
            return {
                'namespace_count': 0,
                'pod_count': 0,
                'service_count': 0,
                'pv_count': 0
            }
"""
Tenant Service - Handles tenant data operations
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TenantService:
    def __init__(self, db_service):
        self.db = db_service
    
    def save_tenant_data(self, tenant_data_dict):
        """Save comprehensive tenant data"""
        try:
            saved_count = 0
            
            for tenant_name, data in tenant_data_dict.items():
                # Prepare tenant document
                tenant_doc = {
                    'name': tenant_name,
                    'services': data.get('services', []),
                    'redis_info': data.get('redis_info'),
                    'service_count': len(data.get('services', [])),
                    'has_redis': bool(data.get('redis_info')),
                    'redis_key_count': 0,
                    'created_at': datetime.utcnow(),
                    'scan_metadata': {
                        'scan_time': datetime.utcnow(),
                        'source': 'vms_web_debug_tool'
                    }
                }
                
                # Add Redis key count if available
                if data.get('redis_info') and data['redis_info'].get('keys'):
                    tenant_doc['redis_key_count'] = len(data['redis_info']['keys'])
                
                # Save tenant
                if self.db.save_tenant(tenant_doc):
                    saved_count += 1
                    
                    # Save Redis keys separately for better querying
                    if data.get('redis_info') and data['redis_info'].get('keys'):
                        self._save_tenant_redis_keys(tenant_name, data['redis_info']['keys'])
            
            logger.info(f"Saved {saved_count} tenants to database")
            return saved_count
            
        except Exception as e:
            logger.error(f"Save tenant data error: {str(e)}")
            return 0
    
    def _save_tenant_redis_keys(self, tenant_name, keys):
        """Save Redis keys for a tenant"""
        try:
            for key in keys:
                self.db.save_redis_key(
                    tenant_name=tenant_name,
                    key_name=key,
                    key_value=None,  # Will be populated when key is accessed
                    metadata={
                        'discovered_at': datetime.utcnow(),
                        'source': 'tenant_scan'
                    }
                )
        except Exception as e:
            logger.error(f"Save tenant Redis keys error: {str(e)}")
    
    def get_all_tenants(self):
        """Get all tenants with summary information"""
        try:
            tenants = self.db.get_all_tenants()
            
            # Add summary information
            for tenant in tenants:
                tenant['_id'] = str(tenant['_id'])  # Convert ObjectId to string
                
                # Calculate summary stats
                tenant['summary'] = {
                    'service_count': tenant.get('service_count', 0),
                    'has_redis': tenant.get('has_redis', False),
                    'redis_key_count': tenant.get('redis_key_count', 0),
                    'redis_ip': None
                }
                
                # Extract Redis IP if available
                if tenant.get('redis_info') and tenant['redis_info'].get('cluster_ip'):
                    tenant['summary']['redis_ip'] = tenant['redis_info']['cluster_ip']
            
            return tenants
        except Exception as e:
            logger.error(f"Get all tenants error: {str(e)}")
            return []
    
    def get_tenant_by_name(self, name):
        """Get detailed tenant information"""
        try:
            tenant = self.db.get_tenant_by_name(name)
            if tenant:
                tenant['_id'] = str(tenant['_id'])
                
                # Get Redis keys
                redis_keys = self.db.get_tenant_redis_keys(name)
                tenant['redis_keys'] = [
                    {
                        'key_name': key['key_name'],
                        'has_value': bool(key.get('key_value')),
                        'last_accessed': key.get('updated_at')
                    }
                    for key in redis_keys
                ]
                
            return tenant
        except Exception as e:
            logger.error(f"Get tenant by name error: {str(e)}")
            return None
    
    def update_tenant_metadata(self, tenant_name, metadata):
        """Update tenant metadata"""
        try:
            tenant = self.db.get_tenant_by_name(tenant_name)
            if tenant:
                tenant['metadata'] = tenant.get('metadata', {})
                tenant['metadata'].update(metadata)
                tenant['updated_at'] = datetime.utcnow()
                
                return self.db.save_tenant(tenant)
            return False
        except Exception as e:
            logger.error(f"Update tenant metadata error: {str(e)}")
            return False
    
    def delete_tenant(self, tenant_name):
        """Delete tenant and associated data"""
        try:
            # Delete tenant
            tenant_deleted = self.db.delete_tenant(tenant_name)
            
            # Delete Redis keys
            # Note: This would need to be implemented in database_service
            # self.db.delete_tenant_redis_keys(tenant_name)
            
            if tenant_deleted:
                logger.info(f"Deleted tenant: {tenant_name}")
                
            return tenant_deleted
        except Exception as e:
            logger.error(f"Delete tenant error: {str(e)}")
            return False
    
    def get_tenant_statistics(self):
        """Get tenant statistics"""
        try:
            all_tenants = self.db.get_all_tenants()
            
            stats = {
                'total_tenants': len(all_tenants),
                'tenants_with_redis': 0,
                'total_services': 0,
                'total_redis_keys': 0,
                'latest_scan': None
            }
            
            for tenant in all_tenants:
                if tenant.get('has_redis'):
                    stats['tenants_with_redis'] += 1
                
                stats['total_services'] += tenant.get('service_count', 0)
                stats['total_redis_keys'] += tenant.get('redis_key_count', 0)
                
                # Track latest scan
                scan_time = None
                if tenant.get('scan_metadata') and tenant['scan_metadata'].get('scan_time'):
                    scan_time = tenant['scan_metadata']['scan_time']
                elif tenant.get('created_at'):
                    scan_time = tenant['created_at']
                
                if scan_time and (not stats['latest_scan'] or scan_time > stats['latest_scan']):
                    stats['latest_scan'] = scan_time
            
            return stats
        except Exception as e:
            logger.error(f"Get tenant statistics error: {str(e)}")
            return {
                'total_tenants': 0,
                'tenants_with_redis': 0,
                'total_services': 0,
                'total_redis_keys': 0,
                'latest_scan': None
            }
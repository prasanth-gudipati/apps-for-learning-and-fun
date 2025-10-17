"""
Database Service - Handles MongoDB operations
"""

from pymongo import MongoClient, DESCENDING
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, mongodb_url):
        self.mongodb_url = mongodb_url
        self.client = None
        self.db = None
        self.connected = False
        
        try:
            self.client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
            self.db = self.client.vms_debug
            
            # Collections
            self.tenants = self.db.tenants
            self.redis_keys = self.db.redis_keys
            self.system_logs = self.db.system_logs
            self.ssh_connections = self.db.ssh_connections
            self.vms_status_logs = self.db.vms_status_logs
            
            # Test connection
            self.client.admin.command('ping')
            self.connected = True
            logger.info("MongoDB connection established successfully")
            
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {str(e)}")
            logger.info("Application will continue without database functionality")
            self.connected = False
    
    def test_connection(self):
        """Test MongoDB connection"""
        if not self.connected:
            return False
            
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {str(e)}")
            self.connected = False
            return False
    
    # Tenant operations
    def save_tenant(self, tenant_data):
        """Save or update tenant data"""
        try:
            tenant_data['updated_at'] = datetime.utcnow()
            
            result = self.tenants.replace_one(
                {'name': tenant_data['name']},
                tenant_data,
                upsert=True
            )
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Save tenant error: {str(e)}")
            return False
    
    def get_tenant_by_name(self, name):
        """Get tenant by name"""
        try:
            return self.tenants.find_one({'name': name})
        except Exception as e:
            logger.error(f"Get tenant error: {str(e)}")
            return None
    
    def get_all_tenants(self):
        """Get all tenants"""
        if not self.connected:
            logger.debug("Database not connected, returning empty tenant list")
            return []
            
        try:
            return list(self.tenants.find().sort('name', 1))
        except Exception as e:
            logger.error(f"Get all tenants error: {str(e)}")
            self.connected = False
            return []
    
    def delete_tenant(self, name):
        """Delete tenant"""
        try:
            result = self.tenants.delete_one({'name': name})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Delete tenant error: {str(e)}")
            return False
    
    # Redis key operations
    def save_redis_key(self, tenant_name, key_name, key_value, metadata=None):
        """Save Redis key data"""
        try:
            doc = {
                'tenant_name': tenant_name,
                'key_name': key_name,
                'key_value': key_value,
                'metadata': metadata or {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = self.redis_keys.replace_one(
                {'tenant_name': tenant_name, 'key_name': key_name},
                doc,
                upsert=True
            )
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Save Redis key error: {str(e)}")
            return False
    
    def get_tenant_redis_keys(self, tenant_name):
        """Get Redis keys for tenant"""
        try:
            return list(self.redis_keys.find(
                {'tenant_name': tenant_name}
            ).sort('key_name', 1))
        except Exception as e:
            logger.error(f"Get tenant Redis keys error: {str(e)}")
            return []
    
    def get_redis_key_value(self, tenant_name, key_name):
        """Get specific Redis key value"""
        try:
            return self.redis_keys.find_one({
                'tenant_name': tenant_name,
                'key_name': key_name
            })
        except Exception as e:
            logger.error(f"Get Redis key value error: {str(e)}")
            return None
    
    # System log operations
    def log_system_event(self, level, message, log_type=None, metadata=None):
        """Log system event"""
        try:
            doc = {
                'level': level,
                'message': message,
                'log_type': log_type or 'general',
                'metadata': metadata or {},
                'timestamp': datetime.utcnow()
            }
            
            result = self.system_logs.insert_one(doc)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Log system event error: {str(e)}")
            return False
    
    def get_system_logs(self, page=1, limit=50, log_type=None):
        """Get system logs with pagination"""
        try:
            query = {}
            if log_type:
                query['log_type'] = log_type
            
            skip = (page - 1) * limit
            
            logs = list(self.system_logs.find(query)
                       .sort('timestamp', DESCENDING)
                       .skip(skip)
                       .limit(limit))
            
            total = self.system_logs.count_documents(query)
            
            return {
                'logs': logs,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            }
        except Exception as e:
            logger.error(f"Get system logs error: {str(e)}")
            return {'logs': [], 'total': 0, 'page': 1, 'limit': limit, 'pages': 0}
    
    # VMS status log operations
    def save_vms_status_log(self, command, output, run_time, metadata=None):
        """Save VMS status check log"""
        try:
            doc = {
                'command': command,
                'output': output,
                'run_time': run_time,
                'metadata': metadata or {},
                'created_at': datetime.utcnow()
            }
            
            result = self.vms_status_logs.insert_one(doc)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Save VMS status log error: {str(e)}")
            return False
    
    def get_vms_status_logs(self, page=1, limit=20):
        """Get VMS status logs with pagination"""
        try:
            skip = (page - 1) * limit
            
            logs = list(self.vms_status_logs.find()
                       .sort('run_time', DESCENDING)
                       .skip(skip)
                       .limit(limit))
            
            total = self.vms_status_logs.count_documents({})
            
            return {
                'logs': logs,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            }
        except Exception as e:
            logger.error(f"Get VMS status logs error: {str(e)}")
            return {'logs': [], 'total': 0, 'page': 1, 'limit': limit, 'pages': 0}
    
    # SSH connection tracking
    def log_ssh_connection(self, host, username, status, connection_id=None):
        """Log SSH connection event"""
        try:
            doc = {
                'host': host,
                'username': username,
                'status': status,
                'connection_id': connection_id,
                'created_at': datetime.utcnow()
            }
            
            result = self.ssh_connections.insert_one(doc)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Log SSH connection error: {str(e)}")
            return False
    
    # Cleanup operations
    def cleanup_old_logs(self, days_to_keep=30):
        """Clean up old logs"""
        try:
            cutoff_date = datetime.utcnow()
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
            
            # Clean system logs
            result1 = self.system_logs.delete_many({
                'timestamp': {'$lt': cutoff_date}
            })
            
            # Clean SSH connection logs
            result2 = self.ssh_connections.delete_many({
                'created_at': {'$lt': cutoff_date}
            })
            
            logger.info(f"Cleaned up {result1.deleted_count} system logs and {result2.deleted_count} SSH logs")
            return True
        except Exception as e:
            logger.error(f"Log cleanup error: {str(e)}")
            return False
// Initialize MongoDB with collections and indexes
db = db.getSiblingDB('vms_debug');

// Create collections
db.createCollection('tenants');
db.createCollection('redis_keys');
db.createCollection('system_logs');
db.createCollection('ssh_connections');
db.createCollection('vms_status_logs');

// Create indexes for better performance
db.tenants.createIndex({ "name": 1 }, { unique: true });
db.tenants.createIndex({ "redis_info.cluster_ip": 1 });
db.tenants.createIndex({ "created_at": -1 });

db.redis_keys.createIndex({ "tenant_name": 1 });
db.redis_keys.createIndex({ "key_name": 1 });
db.redis_keys.createIndex({ "created_at": -1 });

db.system_logs.createIndex({ "timestamp": -1 });
db.system_logs.createIndex({ "log_type": 1 });
db.system_logs.createIndex({ "level": 1 });

db.ssh_connections.createIndex({ "host": 1 });
db.ssh_connections.createIndex({ "status": 1 });
db.ssh_connections.createIndex({ "created_at": -1 });

db.vms_status_logs.createIndex({ "run_time": -1 });
db.vms_status_logs.createIndex({ "command": 1 });

print('MongoDB initialized with VMS Debug Tool collections and indexes');
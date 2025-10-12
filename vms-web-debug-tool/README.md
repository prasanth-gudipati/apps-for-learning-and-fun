# VMS Web Debug Tool

A comprehensive web-based containerized application for managing and debugging VMS (Virtual Management System) environments. This tool provides a modern GUI interface to perform SSH connections, kubectl operations, tenant management, Redis exploration, and system monitoring.

## 🚀 Features

### Core Functionality
- **SSH Connection Management**: Secure SSH connections to VMS servers with connection pooling
- **kubectl Integration**: Execute kubectl commands remotely for Kubernetes management
- **Tenant Data Collection**: Comprehensive tenant information gathering with Redis key extraction
- **Redis Explorer**: Browse, analyze, and manage Redis keys across all tenants
- **System Status Monitoring**: Real-time VMS system health and resource monitoring
- **ConfigMaps Export**: Export Kubernetes ConfigMaps in JSON format for analysis

### Web Interface
- **Modern Responsive Design**: Bootstrap 5-based UI with mobile support
- **Real-time Updates**: WebSocket integration for live progress tracking
- **Interactive Dashboard**: System overview with key metrics and statistics
- **Advanced Filtering**: Search and filter capabilities across all data views
- **Data Export**: Export functionality for all collected data (JSON format)

### Architecture
- **Containerized Deployment**: Docker-based multi-service architecture
- **Database Persistence**: MongoDB for data storage with indexing
- **Caching Layer**: Redis for session management and performance optimization
- **Service-Oriented Design**: Clean separation of concerns with dedicated service classes
- **API-First Approach**: RESTful API with comprehensive error handling

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  Flask Web App  │────│   MongoDB       │
│   (Port 80)     │    │   (Port 5000)   │    │   (Port 27017) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                          
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Redis Cache    │    │ Mongo Express   │
                       │  (Port 6379)    │    │   (Port 8081)   │
                       └─────────────────┘    └─────────────────┘
```

## 📋 Requirements

### System Requirements
- **Operating System**: Ubuntu 22.04.5 LTS (or compatible Linux distribution)
- **Docker**: Version 28.3.3 or higher
- **Docker Compose**: Version 2.0 or higher
- **Memory**: Minimum 4GB RAM recommended
- **Storage**: Minimum 10GB free disk space

### Network Requirements
- Port 80 (HTTP web interface)
- Port 8081 (Mongo Express - optional)
- SSH access to target VMS servers
- Internet connection for downloading dependencies

## 🛠️ Installation & Setup

### 1. Clone and Prepare
```bash
# Navigate to your applications directory
cd /path/to/your/apps

# The project structure should be available at:
# vms-web-debug-tool/
```

### 2. Environment Configuration
```bash
# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

Example `.env` configuration:
```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DEBUG=False

# MongoDB Configuration
MONGODB_HOST=mongo
MONGODB_PORT=27017
MONGODB_DB=vms_debug_tool

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=5000

# Security
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### 3. Build and Deploy
```bash
# Build and start all services
docker-compose up --build -d

# Verify all services are running
docker-compose ps

# View logs
docker-compose logs -f web
```

### 4. Access the Application
- **Main Interface**: http://localhost (or your server IP)
- **Database Admin**: http://localhost:8081 (Mongo Express)

## 📚 Usage Guide

### Getting Started

1. **Access the Web Interface**
   - Open your browser to `http://localhost`
   - You'll see the VMS Debug Tool dashboard

2. **Establish SSH Connection**
   - Click "New Connection" in the navigation
   - Enter your VMS server credentials:
     - Hostname/IP address
     - Username and password
     - Port (default: 22)
   - Click "Connect"

3. **Verify Connection**
   - Check the connection status indicator
   - System overview cards should populate with data

### Core Operations

#### System Status Check
```bash
# Performs comprehensive system analysis
- kubectl get ns (namespaces)
- kubectl get pods -A (all pods)
- kubectl get pv (persistent volumes)
- kubectl get pvc -A (persistent volume claims)
- kubectl get cm -A (config maps)
- kubectl get svc -A | grep redis (Redis services)
```

#### Tenant Data Collection
- Discovers all tenant namespaces
- Extracts service information
- Identifies Redis instances
- Collects Redis keys (optional)
- Stores data in MongoDB for analysis

#### Redis Exploration
- Browse Redis keys across all tenants
- Filter by tenant, key type, or search term
- View key values with proper formatting
- Export individual keys or complete datasets

#### System Logs Management
- View all executed commands and outputs
- Filter logs by date, command, or content
- Export logs for external analysis
- Auto-refresh capabilities

### API Endpoints

#### SSH Management
```http
POST   /api/ssh/connect          # Establish SSH connection
POST   /api/ssh/disconnect/{id}  # Close SSH connection
GET    /api/ssh/status/{id}      # Check connection status
```

#### VMS Operations
```http
POST   /api/vms/status-check/{connection_id}         # Run system status check
POST   /api/vms/collect-tenant-data/{connection_id}  # Collect tenant data
POST   /api/vms/export-configmaps/{connection_id}    # Export ConfigMaps
GET    /api/vms/system-overview/{connection_id}      # Get system overview
```

#### Data Management
```http
GET    /api/tenant/list          # List all tenants
GET    /api/tenant/stats         # Get tenant statistics
POST   /api/tenant/export        # Export tenant data

GET    /api/redis/keys           # List all Redis keys
GET    /api/redis/key-value/{key} # Get specific key value
POST   /api/redis/export         # Export Redis data

GET    /api/logs/system          # Get system logs
POST   /api/logs/export          # Export logs
DELETE /api/logs/clear           # Clear all logs
```

## 🔧 Configuration

### Docker Services Configuration

#### Web Application (Flask)
- **Image**: Python 3.11-slim
- **Port**: 5000
- **Environment**: Production optimized
- **Dependencies**: See `requirements.txt`

#### MongoDB Database
- **Image**: mongo:7.0
- **Port**: 27017
- **Storage**: Persistent volume mounted
- **Configuration**: Optimized for performance

#### Redis Cache
- **Image**: redis:7.2-alpine
- **Port**: 6379
- **Configuration**: Memory optimized
- **Persistence**: Optional (configured for session storage)

#### Nginx Reverse Proxy
- **Image**: nginx:alpine
- **Port**: 80
- **Configuration**: Optimized for web traffic
- **Features**: Gzip compression, static file serving

### Database Schema

#### Tenants Collection
```javascript
{
  _id: ObjectId,
  name: String,
  services: [String],
  redis_info: {
    service_name: String,
    cluster_ip: String,
    ports: String,
    keys: [String],
    key_count: Number
  },
  created_at: Date,
  updated_at: Date
}
```

#### Redis Keys Collection
```javascript
{
  _id: ObjectId,
  tenant: String,
  key_name: String,
  key_type: String,
  value: Mixed,
  size: Number,
  ttl: Number,
  created_at: Date
}
```

#### System Logs Collection
```javascript
{
  _id: ObjectId,
  command: String,
  output: String,
  timestamp: Date,
  run_time: Date,
  metadata: {
    description: String,
    output_lines: Number,
    error: Boolean,
    export_type: String
  }
}
```

## 🛡️ Security Considerations

### Authentication & Authorization
- SSH connections use standard authentication
- Web interface supports session management
- API endpoints include error handling
- Input validation and sanitization

### Network Security
- SSH connections are encrypted
- Web traffic can be secured with HTTPS
- Internal service communication on isolated network
- Database access restricted to application services

### Data Protection
- Sensitive data (passwords) not stored in logs
- SSH credentials managed in memory only
- Database connections use authentication
- Regular security updates via container images

## 🔍 Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Check SSH connectivity
docker-compose exec web python -c "
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('your-vms-host', username='your-user', password='your-pass')
print('Connection successful')
client.close()
"

# Verify network connectivity
docker-compose exec web ping your-vms-host
```

#### Database Issues
```bash
# Check MongoDB connection
docker-compose exec web python -c "
from pymongo import MongoClient
client = MongoClient('mongo', 27017)
print(client.server_info())
"

# Restart database service
docker-compose restart mongo
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check service logs
docker-compose logs web
docker-compose logs mongo
docker-compose logs redis
```

### Log Locations
```bash
# Application logs
docker-compose logs web

# Database logs  
docker-compose logs mongo

# Nginx access logs
docker-compose logs nginx
```

## 📊 Monitoring & Maintenance

### Health Checks
- Application health endpoint: `/health`
- Database connection monitoring
- Redis connectivity checks
- SSH connection status tracking

### Performance Monitoring
- Response time tracking
- Database query optimization
- Memory usage monitoring
- Connection pool management

### Backup Procedures
```bash
# Database backup
docker-compose exec mongo mongodump --db vms_debug_tool --out /backup

# Export configuration
docker-compose exec web python -c "
from app.services.database_service import DatabaseService
db = DatabaseService()
# Export procedures here
"
```

## 🚀 Deployment in Production

### Production Checklist
- [ ] Configure environment variables
- [ ] Set up HTTPS/SSL certificates  
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Configure resource limits
- [ ] Test disaster recovery procedures

### Scaling Considerations
- Use Docker Swarm or Kubernetes for orchestration
- Implement load balancing for multiple instances
- Configure database clustering for high availability
- Use external Redis cluster for session storage
- Implement caching strategies for better performance

## 📝 Development

### Local Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run in development mode
export FLASK_ENV=development
export DEBUG=True
python app.py
```

### Code Structure
```
vms-web-debug-tool/
├── app/
│   ├── app.py              # Main Flask application
│   ├── services/           # Service layer classes
│   ├── static/             # CSS, JS, images
│   └── templates/          # HTML templates
├── docker-compose.yml      # Service orchestration
├── Dockerfile             # Web application container
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support, please:
1. Check the troubleshooting section
2. Review the logs for error details
3. Open an issue with detailed information
4. Include system information and error messages

## 🔄 Version History

### v1.0.0 (Current)
- Initial release
- Complete web interface
- Docker containerization
- Full VMS debug functionality
- Comprehensive documentation

---

**Built with ❤️ for VMS system administrators and DevOps engineers**
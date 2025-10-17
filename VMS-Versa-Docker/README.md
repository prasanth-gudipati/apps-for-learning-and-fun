# VMS Debug Tool - Docker Microservices Architecture

A containerized microservices version of the VMS Debug Tool for enhanced scalability, maintainability, and deployment flexibility.

## Architecture Overview

This application transforms the monolithic VMS-Debug-Tool-Web into a microservices architecture with the following components:

### Services Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Web Frontend  │
│     (NGINX)     │◄───┤   (Flask+WS)    │
│   Port: 80      │    │   Port: 5000    │
└─────────────────┘    └─────────────────┘
         │                       │
         │              ┌────────┼────────┐
         │              │        │        │
         ▼              ▼        ▼        ▼
┌─────────────┐  ┌─────────┐ ┌─────────┐ ┌─────────┐
│SSH Service  │  │Kubectl  │ │Redis    │ │Logs     │
│Port: 8001   │  │Service  │ │Service  │ │Service  │
│             │  │Port:8002│ │Port:8003│ │Port:8004│
└─────────────┘  └─────────┘ └─────────┘ └─────────┘
         │              │        │        │
         └──────────────┼────────┼────────┘
                        │        │
                ┌───────▼────────▼───────┐
                │   Session Redis        │
                │   Port: 6379           │
                └────────────────────────┘
```

### Service Descriptions

1. **Web Frontend** (`web-frontend/`)
   - Main user interface with Flask and SocketIO
   - Handles WebSocket connections for real-time updates
   - Orchestrates calls to backend microservices
   - Session management and user authentication

2. **SSH Service** (`ssh-service/`)
   - Manages SSH connections to remote hosts
   - Connection pooling and session management
   - Command execution and output handling
   - Health monitoring of SSH connections

3. **Kubectl Service** (`kubectl-service/`)
   - Kubernetes operations and management
   - Tenant data parsing and ConfigMap operations
   - Pod status monitoring and log retrieval
   - Namespace and resource management

4. **Redis Service** (`redis-service/`)
   - Redis key/value operations
   - Tenant data storage and retrieval
   - Cache management and data persistence
   - Redis CLI command execution

5. **Logs Service** (`logs-service/`)
   - Log file scanning and content analysis
   - File system operations via SSH
   - Search and filtering capabilities
   - Real-time log tailing

6. **Session Redis** (`session-redis`)
   - Distributed session storage
   - Cross-service state management
   - Caching layer for performance
   - Data persistence between restarts

7. **NGINX Load Balancer** (`nginx/`)
   - Reverse proxy and load balancing
   - SSL termination (configurable)
   - WebSocket proxy support
   - Static file serving

## Quick Start

### Prerequisites

- Docker 20.10+ and docker-compose 1.29+
- 4GB+ RAM available for containers
- Network access to target SSH hosts

### Installation & Deployment

1. **Clone and Navigate**
   ```bash
   cd /home/versa/pgudipati/SAMBA-70-188-169/apps-for-learning-and-fun/VMS-Versa/VMS-Versa-Docker
   ```

2. **Build and Start Services**
   ```bash
   # Using the management script (recommended)
   ./vms-docker.sh build
   ./vms-docker.sh start
   
   # Or using docker-compose directly
   docker-compose build
   docker-compose up -d
   ```

3. **Verify Deployment**
   ```bash
   ./vms-docker.sh status
   ```

4. **Access the Application**
   - Main Interface: http://localhost:5000
   - Load Balanced: http://localhost:80
   - Individual Services: http://localhost:800[1-4]

## Management Script Usage

The `vms-docker.sh` script provides comprehensive management capabilities:

```bash
# Build all services
./vms-docker.sh build

# Start all services
./vms-docker.sh start

# Check service health
./vms-docker.sh status

# View logs
./vms-docker.sh logs                    # All services
./vms-docker.sh logs web-frontend       # Specific service

# Scale services
./vms-docker.sh scale web-frontend 3    # Scale to 3 replicas

# Stop services
./vms-docker.sh stop

# Restart services
./vms-docker.sh restart

# Complete cleanup
./vms-docker.sh cleanup
```

## Service Endpoints

| Service | Port | Health Check | Purpose |
|---------|------|--------------|---------|
| Web Frontend | 5000 | `/health` | Main web interface |
| SSH Service | 8001 | `/health` | SSH connection management |
| Kubectl Service | 8002 | `/health` | Kubernetes operations |
| Redis Service | 8003 | `/health` | Redis key/value operations |
| Logs Service | 8004 | `/health` | Log file operations |
| Session Redis | 6379 | `PING` | Session storage |
| NGINX | 80 | `/` | Load balancer |

## Configuration

### Environment Variables

Each service supports environment-based configuration:

**Web Frontend:**
- `FLASK_ENV`: Development/production mode
- `SECRET_KEY`: Session encryption key
- `REDIS_URL`: Session storage connection

**SSH Service:**
- `SSH_TIMEOUT`: Connection timeout (default: 30s)
- `MAX_CONNECTIONS`: Connection pool size (default: 10)

**Kubectl Service:**
- `KUBECTL_TIMEOUT`: Command timeout (default: 60s)
- `DEFAULT_NAMESPACE`: Default Kubernetes namespace

### Volume Mounts

- Logs are stored in `./logs/` directory
- SSH keys can be mounted from `~/.ssh/`
- Configuration files in `./config/`

## Development

### Local Development Setup

1. **Install Dependencies**
   ```bash
   # For each service
   cd [service-directory]
   pip install -r requirements.txt
   ```

2. **Run Individual Services**
   ```bash
   # Terminal 1 - Redis
   docker run -p 6379:6379 redis:7-alpine
   
   # Terminal 2 - SSH Service
   cd ssh-service && python app.py
   
   # Terminal 3 - Web Frontend
   cd web-frontend && python app.py
   ```

### Adding New Services

1. Create service directory with standard structure:
   ```
   new-service/
   ├── app.py
   ├── requirements.txt
   └── Dockerfile
   ```

2. Add service to `docker-compose.yml`
3. Update NGINX configuration if needed
4. Add health checks and monitoring

## Monitoring & Observability

### Health Checks

All services implement health check endpoints:
```bash
curl http://localhost:5000/health    # Web Frontend
curl http://localhost:8001/health    # SSH Service
# ... etc
```

### Logging

Centralized logging with structured output:
- All services log to stdout/stderr
- Docker captures and rotates logs automatically
- Use `docker-compose logs [service]` to view

### Metrics

Basic metrics available through health endpoints:
- Service uptime
- Request counts
- Error rates
- Connection status

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :5000
   
   # Modify ports in docker-compose.yml if needed
   ```

2. **Service Communication Failures**
   ```bash
   # Check network connectivity
   docker-compose exec web-frontend ping ssh-service
   
   # Verify service discovery
   docker-compose exec web-frontend nslookup ssh-service
   ```

3. **Memory Issues**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Adjust memory limits in docker-compose.yml
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:
```bash
# Set debug environment variables
export FLASK_ENV=development
export LOG_LEVEL=DEBUG

# Restart with debug logs
docker-compose down && docker-compose up
```

## Production Deployment

### Security Considerations

1. **SSL/TLS Configuration**
   - Configure SSL certificates in NGINX
   - Use secure session keys
   - Enable HTTPS redirect

2. **Network Security**
   - Use Docker secrets for sensitive data
   - Configure firewall rules
   - Enable container security scanning

3. **Access Control**
   - Implement authentication middleware
   - Use RBAC for Kubernetes access
   - Audit logging for security events

### Performance Tuning

1. **Scaling Guidelines**
   ```bash
   # Scale based on load
   ./vms-docker.sh scale web-frontend 3
   ./vms-docker.sh scale ssh-service 2
   ```

2. **Resource Limits**
   - Set appropriate memory/CPU limits
   - Monitor and adjust based on usage
   - Use resource reservations for critical services

3. **Caching Strategy**
   - Configure Redis persistence
   - Implement application-level caching
   - Use CDN for static assets

## Migration from Monolithic Version

### Data Migration

1. **Export existing configurations**
2. **Convert session data format**
3. **Update connection strings**

### Feature Parity

All features from the original VMS-Debug-Tool-Web are preserved:
- ✅ SSH connection management
- ✅ Kubernetes operations
- ✅ Redis key/value operations
- ✅ Log file analysis
- ✅ Real-time WebSocket updates
- ✅ Multi-session support

## Contributing

### Development Workflow

1. Create feature branch
2. Implement changes in relevant service(s)
3. Add/update tests
4. Update documentation
5. Submit pull request

### Code Standards

- Follow PEP 8 for Python code
- Use type hints where applicable
- Implement proper error handling
- Add comprehensive logging

## License

This project maintains the same license as the original VMS Debug Tool.

## Support

For issues and questions:
1. Check troubleshooting section
2. Review service logs
3. Open GitHub issue with full context
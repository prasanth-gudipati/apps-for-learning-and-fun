# VMS Debug Tool - Quick Deployment Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Prerequisites Check
```bash
# Verify Docker installation
docker --version
docker-compose --version

# Should show:
# Docker version 20.10+ 
# docker-compose version 1.29+
```

### Step 2: Navigate to Project
```bash
cd /home/versa/pgudipati/SAMBA-70-188-169/apps-for-learning-and-fun/VMS-Versa/VMS-Versa-Docker
```

### Step 3: Deploy Application
```bash
# Build and start all services
./vms-docker.sh build
./vms-docker.sh start

# Check deployment status
./health-check.sh
```

### Step 4: Access Application
- **Main Interface**: http://localhost:5000
- **Load Balanced**: http://localhost:80

---

## 📋 Detailed Deployment Steps

### 1. Environment Setup

**Check System Requirements:**
```bash
# Memory: At least 4GB RAM available
free -h

# Disk: At least 2GB free space  
df -h .

# Network: Docker daemon running
docker info
```

**Configure Environment Variables:**
```bash
# Copy and customize environment file
cp .env .env.production

# Edit production settings
nano .env.production

# Key settings to review:
# - SECRET_KEY (change for production)
# - REDIS_PASSWORD (set for security)  
# - SSL settings (if using HTTPS)
```

### 2. Service Deployment

**Build All Services:**
```bash
# Build with specific environment
docker-compose build --no-cache

# Or use management script
./vms-docker.sh build
```

**Start Services in Order:**
```bash
# Option 1: All at once (recommended)
docker-compose up -d

# Option 2: One by one (for troubleshooting)
docker-compose up -d session-redis
docker-compose up -d ssh-service
docker-compose up -d kubectl-service  
docker-compose up -d redis-service
docker-compose up -d logs-service
docker-compose up -d web-frontend
docker-compose up -d nginx
```

### 3. Health Verification

**Quick Health Check:**
```bash
./health-check.sh
```

**Detailed Service Verification:**
```bash
# Check individual services
curl http://localhost:5000/health    # Web Frontend
curl http://localhost:8001/health    # SSH Service  
curl http://localhost:8002/health    # Kubectl Service
curl http://localhost:8003/health    # Redis Service
curl http://localhost:8004/health    # Logs Service

# Check Redis connectivity
docker-compose exec session-redis redis-cli ping

# Check NGINX routing
curl http://localhost:80
```

**Monitor Service Logs:**
```bash
# All services
./vms-docker.sh logs

# Specific service  
./vms-docker.sh logs web-frontend
docker-compose logs -f ssh-service
```

### 4. Application Configuration

**Initial Setup Tasks:**
1. Access web interface at http://localhost:5000
2. Configure SSH connections to target hosts
3. Set up Kubernetes access credentials
4. Test Redis connectivity
5. Verify log file access

**SSH Configuration:**
```bash
# Mount SSH keys (if needed)
mkdir -p ./ssh_keys
cp ~/.ssh/id_rsa ./ssh_keys/
chmod 600 ./ssh_keys/id_rsa

# Restart services to pick up keys
docker-compose restart ssh-service
```

**Kubernetes Configuration:**
```bash
# Mount kubeconfig (if needed)  
mkdir -p ./kube_config
cp ~/.kube/config ./kube_config/
chmod 600 ./kube_config/config

# Restart kubectl service
docker-compose restart kubectl-service
```

---

## 🔧 Production Deployment

### Security Hardening

**1. SSL/TLS Setup:**
```bash
# Generate SSL certificates
mkdir -p ./ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/vms-debug-tool.key \
  -out ./ssl/vms-debug-tool.crt

# Update nginx configuration for HTTPS
# Edit nginx/nginx.conf to enable SSL
```

**2. Secrets Management:**
```bash
# Use Docker secrets instead of environment variables
echo "your-secret-key" | docker secret create vms_secret_key -
echo "redis-password" | docker secret create vms_redis_password -

# Update docker-compose.yml to use secrets
```

**3. Network Security:**
```bash
# Configure firewall rules
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS  
sudo ufw deny 5000/tcp   # Block direct service access
sudo ufw deny 8001:8004/tcp
```

### Performance Optimization

**1. Resource Limits:**
```yaml
# Add to docker-compose.yml for each service
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

**2. Scaling Configuration:**
```bash
# Scale services based on load
./vms-docker.sh scale web-frontend 3
./vms-docker.sh scale ssh-service 2

# Or using docker-compose
docker-compose up -d --scale web-frontend=3
```

**3. Persistent Data:**
```bash
# Create named volumes for persistence
docker volume create vms_redis_data
docker volume create vms_logs_data

# Update docker-compose.yml to use named volumes
```

### Monitoring & Observability

**1. Log Aggregation:**
```bash
# Configure centralized logging
# Add logging driver to docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**2. Health Monitoring:**
```bash
# Set up automated health checks
crontab -e

# Add line for periodic health checks:
# */5 * * * * /path/to/health-check.sh > /var/log/vms-health.log 2>&1
```

**3. Backup Strategy:**
```bash
# Backup Redis data
docker-compose exec session-redis redis-cli BGSAVE

# Backup configuration
tar -czf vms-config-backup-$(date +%Y%m%d).tar.gz \
  .env docker-compose.yml nginx/ ssh_keys/ kube_config/
```

---

## 🛠️ Troubleshooting Guide

### Common Issues

**1. Port Conflicts:**
```bash
# Check what's using ports
netstat -tulpn | grep :5000
netstat -tulpn | grep :80

# Solution: Change ports in docker-compose.yml
ports:
  - "5001:5000"  # Change external port
```

**2. Memory Issues:**
```bash
# Check memory usage
docker stats

# Solution: Add memory limits or increase host memory
# Add to docker-compose.yml:
mem_limit: 512m
```

**3. Service Communication Failures:**
```bash
# Test inter-service connectivity
docker-compose exec web-frontend ping ssh-service
docker-compose exec web-frontend nslookup ssh-service

# Check Docker network
docker network ls
docker network inspect vms-versa-docker_vms-network
```

**4. Permission Issues:**
```bash
# Fix SSH key permissions
chmod 600 ./ssh_keys/*
chown 1000:1000 ./ssh_keys/*

# Fix log directory permissions  
chmod 755 ./logs/
chown 1000:1000 ./logs/
```

### Debug Mode

**Enable Debug Logging:**
```bash
# Set debug environment
export FLASK_ENV=development
export LOG_LEVEL=DEBUG

# Restart with debug
docker-compose down
docker-compose up
```

**Access Service Logs:**
```bash
# Live log tailing
./vms-docker.sh logs web-frontend

# Get specific time range
docker-compose logs --since="1h" web-frontend

# Export logs for analysis
docker-compose logs web-frontend > web-frontend-debug.log
```

### Recovery Procedures

**1. Complete Reset:**
```bash
# Stop and remove everything
./vms-docker.sh cleanup

# Rebuild from scratch  
./vms-docker.sh build
./vms-docker.sh start
```

**2. Service-Specific Recovery:**
```bash
# Restart single service
docker-compose restart web-frontend

# Rebuild single service
docker-compose build web-frontend
docker-compose up -d web-frontend
```

**3. Data Recovery:**
```bash
# Restore Redis data
docker-compose exec session-redis redis-cli FLUSHALL
docker-compose exec session-redis redis-cli < backup.rdb

# Restore configuration
tar -xzf vms-config-backup-YYYYMMDD.tar.gz
docker-compose restart
```

---

## 📊 Performance Monitoring

### Key Metrics to Monitor

**System Metrics:**
- CPU usage per service
- Memory consumption  
- Network I/O
- Disk usage

**Application Metrics:**
- Response times
- Error rates
- Active connections
- Session count

**Monitoring Commands:**
```bash
# Real-time resource monitoring
./health-check.sh monitor

# Generate performance report
./health-check.sh report

# Docker resource usage
docker stats --no-stream

# Service-specific metrics
curl http://localhost:5000/health | jq
```

### Alerting Setup

**Basic Alerting Script:**
```bash
#!/bin/bash
# Simple health alerting
if ! ./health-check.sh services >/dev/null 2>&1; then
  echo "VMS Debug Tool health check failed!" | mail -s "Alert" admin@company.com
fi
```

**Add to Crontab:**
```bash
# Check every 5 minutes
*/5 * * * * /path/to/alert-script.sh
```

---

## 🎯 Next Steps

After successful deployment:

1. **Configure Monitoring**: Set up proper monitoring and alerting
2. **Backup Strategy**: Implement regular backups
3. **Security Review**: Conduct security assessment
4. **Performance Tuning**: Optimize based on usage patterns
5. **Documentation**: Create operational runbooks
6. **Training**: Train team on new microservices architecture

For advanced configuration and custom integrations, refer to the main README.md file.
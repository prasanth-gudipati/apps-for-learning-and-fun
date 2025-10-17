# VMS-Versa-Docker Test Configuration
# This file contains test data and configuration for testing scenarios

# Test SSH Hosts (add your test hosts here)
TEST_SSH_HOSTS=(
    "localhost"
    # "test-server-1.example.com"
    # "test-server-2.example.com"
)

# Test SSH Credentials (for localhost testing)
TEST_SSH_USER="$USER"
TEST_SSH_PORT="22"

# Test Kubernetes Configuration (if available)
TEST_KUBERNETES_NAMESPACE="default"
TEST_KUBERNETES_CONTEXT=""  # Leave empty for default context

# Test Redis Configuration
TEST_REDIS_HOST="localhost"
TEST_REDIS_PORT="6379"
TEST_REDIS_DB="0"

# Sample Test Data for Redis
TEST_REDIS_KEYS=(
    "test:key:1"
    "test:key:2" 
    "test:tenant:sample"
)

# Sample Test Values
TEST_REDIS_VALUES=(
    "test_value_1"
    "test_value_2"
    '{"tenant": "sample", "data": "test_data"}'
)

# Performance Test Configuration
PERFORMANCE_TEST_DURATION=60  # seconds
PERFORMANCE_CONCURRENT_USERS=10
PERFORMANCE_RAMP_UP_TIME=30   # seconds

# Load Test Configuration  
LOAD_TEST_REQUESTS=100
LOAD_TEST_CONCURRENCY=20
LOAD_TEST_TIMEOUT=30

# Test Thresholds
MAX_ACCEPTABLE_RESPONSE_TIME=2.0  # seconds
MIN_SUCCESS_RATE=90              # percentage
MAX_CPU_USAGE=80                 # percentage
MAX_MEMORY_USAGE=85              # percentage

# Test Service Endpoints
TEST_WEB_FRONTEND_URL="http://localhost:5000"
TEST_SSH_SERVICE_URL="http://localhost:8001"
TEST_KUBECTL_SERVICE_URL="http://localhost:8002"
TEST_REDIS_SERVICE_URL="http://localhost:8003"
TEST_LOGS_SERVICE_URL="http://localhost:8004"
TEST_NGINX_URL="http://localhost:80"

# Test File Paths
TEST_LOG_FILE="/var/log/syslog"     # Sample log file for testing
TEST_CONFIG_FILE="/etc/hostname"    # Sample config file for testing

# Expected Service Health Check Responses
EXPECTED_HEALTH_STATUS="200"
EXPECTED_HEALTH_CONTENT="OK"

# Test Scenarios
TEST_SCENARIOS=(
    "basic_connectivity"
    "service_health_checks"
    "ssh_connection_test" 
    "redis_operations_test"
    "web_interface_test"
    "load_balancer_test"
    "scaling_test"
)

# Mock Data for UI Testing
MOCK_TENANT_DATA='[
    {
        "name": "test-tenant-1",
        "namespace": "tenant-1",
        "status": "active"
    },
    {
        "name": "test-tenant-2", 
        "namespace": "tenant-2",
        "status": "inactive"
    }
]'

MOCK_REDIS_KEYS='[
    "tenant:test-tenant-1:config",
    "tenant:test-tenant-1:session",
    "tenant:test-tenant-2:config"
]'

# Test Commands for SSH Testing
TEST_SSH_COMMANDS=(
    "echo 'Hello World'"
    "whoami"
    "pwd"
    "date"
    "uptime"
)

# Expected Command Outputs (for validation)
declare -A EXPECTED_OUTPUTS
EXPECTED_OUTPUTS["echo 'Hello World'"]="Hello World"
EXPECTED_OUTPUTS["whoami"]="$USER"
EXPECTED_OUTPUTS["pwd"]="$HOME"

# Kubernetes Test Objects (if testing with K8s)
TEST_K8S_CONFIGMAP='
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-config
  namespace: default
data:
  test.property: "test-value"
  app.config: |
    debug=true
    log_level=info
'

# Test Environment Variables
export TEST_ENV="testing"
export LOG_LEVEL="DEBUG" 
export HEALTH_CHECK_TIMEOUT="30"
export SERVICE_STARTUP_TIMEOUT="120"
#!/bin/bash

# VMS-Versa-Docker Testing Environment Validation
# Version: 1.0
# Description: Validates that the testing environment is properly set up

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="/home/versa/pgudipati/SAMBA-70-188-169/apps-for-learning-and-fun/VMS-Versa-Docker"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
checks_total=0
checks_passed=0
checks_failed=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

check_item() {
    local description="$1"
    local command="$2"
    local required="$3"  # true/false
    
    ((checks_total++))
    echo -n "Checking $description... "
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((checks_passed++))
        return 0
    else
        if [[ "$required" == "true" ]]; then
            echo -e "${RED}✗ FAIL (REQUIRED)${NC}"
            ((checks_failed++))
            return 1
        else
            echo -e "${YELLOW}⚠ OPTIONAL${NC}"
            return 0
        fi
    fi
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Validation checks
validate_system_requirements() {
    print_header "System Requirements"
    
    check_item "Docker installation" "command -v docker" true
    check_item "docker-compose installation" "command -v docker-compose" true
    check_item "curl installation" "command -v curl" true
    check_item "bash shell (version 4+)" "[[ \${BASH_VERSION%%.*} -ge 4 ]]" true
    check_item "bc calculator" "command -v bc" true
    
    # Optional tools
    check_item "Apache Bench (ab)" "command -v ab" false
    check_item "jq JSON processor" "command -v jq" false
    check_item "netstat network tool" "command -v netstat" false
    
    # Check Docker daemon
    check_item "Docker daemon running" "docker info" true
    
    # Check available resources
    local memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $memory_gb -ge 4 ]]; then
        echo -e "Memory available: ${GREEN}${memory_gb}GB ✓${NC}"
        ((checks_passed++))
    else
        echo -e "Memory available: ${RED}${memory_gb}GB (< 4GB recommended) ✗${NC}"
        ((checks_failed++))
    fi
    ((checks_total++))
}

validate_project_structure() {
    print_header "Project Structure"
    
    check_item "VMS-Versa-Docker project directory" "[[ -d '$PROJECT_DIR' ]]" true
    check_item "docker-compose.yml file" "[[ -f '$PROJECT_DIR/docker-compose.yml' ]]" true
    check_item "vms-docker.sh management script" "[[ -x '$PROJECT_DIR/vms-docker.sh' ]]" true
    
    # Check service directories
    local services=("web-frontend" "ssh-service" "kubectl-service" "redis-service" "logs-service" "nginx")
    for service in "${services[@]}"; do
        check_item "$service directory" "[[ -d '$PROJECT_DIR/$service' ]]" true
    done
}

validate_testing_structure() {
    print_header "Testing Environment Structure"
    
    check_item "Testing root directory" "[[ -d '$TESTING_ROOT' ]]" true
    check_item "test-plans directory" "[[ -d '$TESTING_ROOT/test-plans' ]]" true
    check_item "test-scripts directory" "[[ -d '$TESTING_ROOT/test-scripts' ]]" true
    check_item "test-data directory" "[[ -d '$TESTING_ROOT/test-data' ]]" true
    check_item "test-results directory" "[[ -d '$TESTING_ROOT/test-results' ]]" true
    check_item "logs directory" "[[ -d '$TESTING_ROOT/logs' ]]" true
    
    # Check test scripts
    local scripts=("automated-test-suite.sh" "manual-test-suite.sh" "performance-test.sh")
    for script in "${scripts[@]}"; do
        check_item "$script executable" "[[ -x '$TESTING_ROOT/test-scripts/$script' ]]" true
    done
    
    # Check test plan
    check_item "Test plan document" "[[ -f '$TESTING_ROOT/test-plans/VMS-Docker-Test-Plan.md' ]]" true
    check_item "Test configuration" "[[ -f '$TESTING_ROOT/test-data/test-config.sh' ]]" true
    check_item "README documentation" "[[ -f '$TESTING_ROOT/README.md' ]]" true
}

validate_network_ports() {
    print_header "Network Port Availability"
    
    local ports=(5000 8001 8002 8003 8004 6379 80)
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo -e "Port $port: ${YELLOW}⚠ IN USE${NC}"
            print_warning "Port $port is already in use. You may need to stop other services."
        else
            echo -e "Port $port: ${GREEN}✓ AVAILABLE${NC}"
        fi
    done
}

validate_file_permissions() {
    print_header "File Permissions"
    
    # Check directory permissions
    check_item "Testing directory writable" "[[ -w '$TESTING_ROOT' ]]" true
    check_item "test-results writable" "[[ -w '$TESTING_ROOT/test-results' ]]" true
    check_item "logs writable" "[[ -w '$TESTING_ROOT/logs' ]]" true
    
    # Check script permissions
    local scripts=("$TESTING_ROOT/test-scripts"/*.sh)
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            local script_name=$(basename "$script")
            check_item "$script_name executable" "[[ -x '$script' ]]" true
        fi
    done
}

validate_docker_environment() {
    print_header "Docker Environment"
    
    # Test basic Docker operations
    check_item "Docker pull capability" "docker pull hello-world:latest" true
    check_item "Docker run capability" "docker run --rm hello-world" true
    
    # Check Docker Compose
    check_item "docker-compose version compatibility" "docker-compose --version | grep -E 'version [1-9]\\.[2-9][0-9]|version [2-9]'" true
    
    # Check available space
    local docker_space=$(docker system df --format "table {{.Size}}" 2>/dev/null | tail -1 | head -1 || echo "Unknown")
    print_info "Docker space usage: $docker_space"
}

test_basic_functionality() {
    print_header "Basic Functionality Test"
    
    print_info "Testing basic script functionality..."
    
    # Test logging functions
    echo "Testing logging..." > "/tmp/test_log_$$"
    if [[ -f "/tmp/test_log_$$" ]]; then
        print_success "File creation test passed"
        rm -f "/tmp/test_log_$$"
        ((checks_passed++))
    else
        print_error "File creation test failed"
        ((checks_failed++))
    fi
    ((checks_total++))
    
    # Test network connectivity
    check_item "Internet connectivity" "curl -f -s https://google.com >/dev/null" false
    check_item "Localhost connectivity" "curl -f -s http://localhost >/dev/null || true" false
}

generate_validation_report() {
    print_header "Validation Summary"
    
    echo "Total Checks: $checks_total"
    echo -e "Passed: ${GREEN}$checks_passed${NC}"
    echo -e "Failed: ${RED}$checks_failed${NC}"
    
    local success_rate=0
    if [[ $checks_total -gt 0 ]]; then
        success_rate=$((checks_passed * 100 / checks_total))
    fi
    
    echo "Success Rate: ${success_rate}%"
    
    echo ""
    if [[ $checks_failed -eq 0 ]]; then
        print_success "All critical validation checks passed! ✓"
        print_info "Your testing environment is ready."
        echo ""
        echo "Next steps:"
        echo "1. cd $TESTING_ROOT/test-scripts"
        echo "2. ./manual-test-suite.sh (for interactive testing)"
        echo "3. ./automated-test-suite.sh (for automated testing)"
        return 0
    else
        print_error "Some validation checks failed. ✗"
        print_warning "Please address the failed checks before running tests."
        echo ""
        echo "Common fixes:"
        echo "- Install missing tools (docker, docker-compose, curl, bc)"
        echo "- Start Docker daemon: sudo systemctl start docker"
        echo "- Free up required ports"
        echo "- Fix file permissions: chmod +x test-scripts/*.sh"
        return 1
    fi
}

# Main execution
main() {
    echo "VMS-Versa-Docker Testing Environment Validation"
    echo "=============================================="
    echo ""
    echo "Validating testing environment setup..."
    echo ""
    
    validate_system_requirements
    validate_project_structure
    validate_testing_structure
    validate_file_permissions
    validate_network_ports
    validate_docker_environment
    test_basic_functionality
    
    echo ""
    generate_validation_report
}

# Check if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
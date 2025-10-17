#!/bin/bash

# VMS-Versa-Docker Automated Test Script
# Version: 1.0
# Date: October 17, 2025
# Description: Comprehensive automated testing for VMS-Versa-Docker microservices

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/versa/pgudipati/SAMBA-70-188-169/apps-for-learning-and-fun/VMS-Versa-Docker"
TEST_LOG_DIR="$SCRIPT_DIR/../logs"
TEST_RESULTS_DIR="$SCRIPT_DIR/../test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_LOG="$TEST_LOG_DIR/test_execution_$TIMESTAMP.log"
RESULTS_FILE="$TEST_RESULTS_DIR/test_results_$TIMESTAMP.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
HEALTH_CHECK_TIMEOUT=30
STARTUP_TIMEOUT=120
LOAD_TEST_DURATION=60
CONCURRENT_USERS=10

# Service endpoints
WEB_FRONTEND_URL="http://localhost:5000"
SSH_SERVICE_URL="http://localhost:8001"
KUBECTL_SERVICE_URL="http://localhost:8002"
REDIS_SERVICE_URL="http://localhost:8003"
LOGS_SERVICE_URL="http://localhost:8004"
NGINX_URL="http://localhost:80"

# Initialize logging
init_logging() {
    mkdir -p "$TEST_LOG_DIR" "$TEST_RESULTS_DIR"
    echo "Test execution started at $(date)" | tee "$TEST_LOG"
    echo "Logging to: $TEST_LOG"
}

# Logging functions
log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$TEST_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} [$(date '+%H:%M:%S')] $1" | tee -a "$TEST_LOG"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} [$(date '+%H:%M:%S')] $1" | tee -a "$TEST_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} [$(date '+%H:%M:%S')] $1" | tee -a "$TEST_LOG"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} [$(date '+%H:%M:%S')] $1" | tee -a "$TEST_LOG"
}

# Test results tracking
declare -A test_results
total_tests=0
passed_tests=0
failed_tests=0

# Record test result
record_test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    test_results["$test_name"]="$result"
    total_tests=$((total_tests + 1))
    
    if [[ "$result" == "PASS" ]]; then
        passed_tests=$((passed_tests + 1))
        log_success "TC-$total_tests: $test_name - PASSED"
    else
        failed_tests=$((failed_tests + 1))
        log_error "TC-$total_tests: $test_name - FAILED: $details"
    fi
}

# Utility functions
wait_for_service() {
    local url="$1"
    local timeout="$2"
    local service_name="$3"
    
    log_info "Waiting for $service_name to be ready..."
    
    local count=0
    while [[ $count -lt $timeout ]]; do
        if curl -f -s "$url/health" >/dev/null 2>&1 || curl -f -s "$url" >/dev/null 2>&1; then
            log_success "$service_name is ready"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    
    log_error "$service_name failed to start within $timeout seconds"
    return 1
}

check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found. Please install docker-compose."
        return 1
    fi
    
    if ! docker --version &> /dev/null; then
        log_error "docker not found. Please install Docker."
        return 1
    fi
    
    return 0
}

# Test Phase 1: Infrastructure Tests
test_infrastructure() {
    log_info "=== PHASE 1: Infrastructure Testing ==="
    
    # TC-001: Check prerequisites
    log_info "TC-001: Checking prerequisites..."
    if check_docker_compose; then
        record_test_result "Prerequisites Check" "PASS"
    else
        record_test_result "Prerequisites Check" "FAIL" "Docker/docker-compose not available"
        return 1
    fi
    
    # TC-002: Build containers
    log_info "TC-002: Building containers..."
    cd "$PROJECT_DIR"
    if ./vms-docker.sh build &>> "$TEST_LOG"; then
        record_test_result "Container Build" "PASS"
    else
        record_test_result "Container Build" "FAIL" "Build process failed"
        return 1
    fi
    
    # TC-003: Start services
    log_info "TC-003: Starting services..."
    if ./vms-docker.sh start &>> "$TEST_LOG"; then
        record_test_result "Service Startup" "PASS"
    else
        record_test_result "Service Startup" "FAIL" "Service startup failed"
        return 1
    fi
    
    # TC-004: Wait for services to be ready
    log_info "TC-004: Waiting for services to be ready..."
    sleep 10  # Give services time to initialize
    
    local all_ready=true
    
    if ! wait_for_service "$WEB_FRONTEND_URL" $HEALTH_CHECK_TIMEOUT "Web Frontend"; then
        all_ready=false
    fi
    
    if ! wait_for_service "$SSH_SERVICE_URL" $HEALTH_CHECK_TIMEOUT "SSH Service"; then
        all_ready=false
    fi
    
    if ! wait_for_service "$KUBECTL_SERVICE_URL" $HEALTH_CHECK_TIMEOUT "Kubectl Service"; then
        all_ready=false
    fi
    
    if ! wait_for_service "$REDIS_SERVICE_URL" $HEALTH_CHECK_TIMEOUT "Redis Service"; then
        all_ready=false
    fi
    
    if ! wait_for_service "$LOGS_SERVICE_URL" $HEALTH_CHECK_TIMEOUT "Logs Service"; then
        all_ready=false
    fi
    
    if $all_ready; then
        record_test_result "Service Health Checks" "PASS"
    else
        record_test_result "Service Health Checks" "FAIL" "One or more services failed health check"
    fi
}

# Test Phase 2: Service Integration Tests
test_service_integration() {
    log_info "=== PHASE 2: Service Integration Testing ==="
    
    # TC-005: Test health endpoints
    log_info "TC-005: Testing health endpoints..."
    local health_check_pass=true
    
    for service in "Web Frontend:$WEB_FRONTEND_URL" "SSH Service:$SSH_SERVICE_URL" "Kubectl Service:$KUBECTL_SERVICE_URL" "Redis Service:$REDIS_SERVICE_URL" "Logs Service:$LOGS_SERVICE_URL"; do
        IFS=':' read -r name url <<< "$service"
        log_info "  Checking $name health endpoint..."
        
        response=$(curl -s -w "%{http_code}" "$url/health" -o /tmp/health_response 2>/dev/null || echo "000")
        if [[ "$response" == "200" ]]; then
            log_success "  $name health check passed"
        else
            log_error "  $name health check failed (HTTP $response)"
            health_check_pass=false
        fi
    done
    
    if $health_check_pass; then
        record_test_result "Health Endpoint Tests" "PASS"
    else
        record_test_result "Health Endpoint Tests" "FAIL" "One or more health endpoints failed"
    fi
    
    # TC-006: Test web frontend accessibility
    log_info "TC-006: Testing web frontend accessibility..."
    response=$(curl -s -w "%{http_code}" "$WEB_FRONTEND_URL" -o /tmp/frontend_response 2>/dev/null || echo "000")
    if [[ "$response" == "200" ]]; then
        record_test_result "Web Frontend Access" "PASS"
    else
        record_test_result "Web Frontend Access" "FAIL" "HTTP response code: $response"
    fi
    
    # TC-007: Test NGINX load balancer
    log_info "TC-007: Testing NGINX load balancer..."
    response=$(curl -s -w "%{http_code}" "$NGINX_URL" -o /tmp/nginx_response 2>/dev/null || echo "000")
    if [[ "$response" == "200" ]]; then
        record_test_result "NGINX Load Balancer" "PASS"
    else
        record_test_result "NGINX Load Balancer" "FAIL" "HTTP response code: $response"
    fi
}

# Test Phase 3: Functional Tests
test_functionality() {
    log_info "=== PHASE 3: Functional Testing ==="
    
    # TC-008: Test service status reporting
    log_info "TC-008: Testing service status reporting..."
    cd "$PROJECT_DIR"
    if ./vms-docker.sh status &>> "$TEST_LOG"; then
        record_test_result "Service Status Reporting" "PASS"
    else
        record_test_result "Service Status Reporting" "FAIL" "Status command failed"
    fi
    
    # TC-009: Test log collection
    log_info "TC-009: Testing log collection..."
    if ./vms-docker.sh logs web-frontend | head -10 &>> "$TEST_LOG"; then
        record_test_result "Log Collection" "PASS"
    else
        record_test_result "Log Collection" "FAIL" "Log collection failed"
    fi
    
    # TC-010: Test container inspection
    log_info "TC-010: Testing container inspection..."
    local containers_running=true
    
    for container in "vms-web-frontend" "vms-ssh-service" "vms-kubectl-service" "vms-redis-service" "vms-logs-service"; do
        if docker ps | grep -q "$container"; then
            log_success "  Container $container is running"
        else
            log_error "  Container $container is not running"
            containers_running=false
        fi
    done
    
    if $containers_running; then
        record_test_result "Container Status Check" "PASS"
    else
        record_test_result "Container Status Check" "FAIL" "One or more containers not running"
    fi
}

# Test Phase 4: Performance Tests
test_performance() {
    log_info "=== PHASE 4: Performance Testing ==="
    
    # TC-011: Response time test
    log_info "TC-011: Testing response times..."
    local response_times_good=true
    
    for endpoint in "$WEB_FRONTEND_URL/health" "$SSH_SERVICE_URL/health" "$KUBECTL_SERVICE_URL/health"; do
        response_time=$(curl -o /dev/null -s -w "%{time_total}" "$endpoint" 2>/dev/null || echo "999")
        
        if (( $(echo "$response_time < 2.0" | bc -l) )); then
            log_success "  Response time for $endpoint: ${response_time}s (Good)"
        else
            log_warning "  Response time for $endpoint: ${response_time}s (Slow)"
            response_times_good=false
        fi
    done
    
    if $response_times_good; then
        record_test_result "Response Time Test" "PASS"
    else
        record_test_result "Response Time Test" "FAIL" "Some endpoints have slow response times"
    fi
    
    # TC-012: Resource usage test
    log_info "TC-012: Testing resource usage..."
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" > /tmp/docker_stats
    
    if [[ -s /tmp/docker_stats ]]; then
        log_info "Resource usage captured:"
        cat /tmp/docker_stats | tee -a "$TEST_LOG"
        record_test_result "Resource Usage Capture" "PASS"
    else
        record_test_result "Resource Usage Capture" "FAIL" "Failed to capture resource stats"
    fi
}

# Test Phase 5: Basic Load Test
test_load() {
    log_info "=== PHASE 5: Load Testing ==="
    
    # TC-013: Simple load test
    log_info "TC-013: Running simple load test..."
    
    if command -v ab &> /dev/null; then
        log_info "  Running Apache Bench test (100 requests, 10 concurrent)..."
        ab -n 100 -c 10 "$WEB_FRONTEND_URL/" > /tmp/ab_results 2>&1
        
        if [[ $? -eq 0 ]]; then
            log_success "  Load test completed successfully"
            grep -E "(Requests per second|Time per request)" /tmp/ab_results | tee -a "$TEST_LOG"
            record_test_result "Load Test" "PASS"
        else
            record_test_result "Load Test" "FAIL" "Apache Bench test failed"
        fi
    else
        log_warning "  Apache Bench not available, using curl-based test..."
        
        local concurrent_requests=5
        local total_requests=20
        local success_count=0
        
        for ((i=1; i<=total_requests; i++)); do
            if ((i % concurrent_requests == 0)); then
                wait  # Wait for previous batch to complete
            fi
            
            {
                if curl -f -s "$WEB_FRONTEND_URL" >/dev/null 2>&1; then
                    ((success_count++))
                fi
            } &
        done
        wait  # Wait for all background processes
        
        local success_rate=$((success_count * 100 / total_requests))
        log_info "  Success rate: $success_rate% ($success_count/$total_requests)"
        
        if [[ $success_rate -ge 80 ]]; then
            record_test_result "Simple Load Test" "PASS"
        else
            record_test_result "Simple Load Test" "FAIL" "Success rate below 80%: $success_rate%"
        fi
    fi
}

# Test Phase 6: Service Scaling Test
test_scaling() {
    log_info "=== PHASE 6: Scaling Test ==="
    
    # TC-014: Scale up test
    log_info "TC-014: Testing service scaling..."
    cd "$PROJECT_DIR"
    
    if ./vms-docker.sh scale web-frontend 2 &>> "$TEST_LOG"; then
        sleep 15  # Wait for scaling to complete
        
        local scaled_containers=$(docker ps | grep -c "vms-web-frontend" || echo "0")
        if [[ $scaled_containers -ge 2 ]]; then
            log_success "  Successfully scaled web-frontend to 2 instances"
            
            # Scale back down
            if ./vms-docker.sh scale web-frontend 1 &>> "$TEST_LOG"; then
                sleep 10
                record_test_result "Service Scaling" "PASS"
            else
                record_test_result "Service Scaling" "FAIL" "Failed to scale back down"
            fi
        else
            record_test_result "Service Scaling" "FAIL" "Scaling up failed"
        fi
    else
        record_test_result "Service Scaling" "FAIL" "Scale command failed"
    fi
}

# Cleanup function
cleanup() {
    log_info "=== CLEANUP ==="
    cd "$PROJECT_DIR"
    
    log_info "Stopping services..."
    ./vms-docker.sh stop &>> "$TEST_LOG" || true
    
    log_info "Cleaning up test artifacts..."
    rm -f /tmp/health_response /tmp/frontend_response /tmp/nginx_response /tmp/docker_stats /tmp/ab_results
}

# Generate test report
generate_report() {
    log_info "=== GENERATING TEST REPORT ==="
    
    local report_file="$TEST_RESULTS_DIR/test_summary_$TIMESTAMP.txt"
    
    cat > "$report_file" << EOF
VMS-Versa-Docker Test Execution Report
=====================================
Date: $(date)
Total Tests: $total_tests
Passed: $passed_tests
Failed: $failed_tests
Success Rate: $(( passed_tests * 100 / total_tests ))%

Test Results:
EOF
    
    for test_name in "${!test_results[@]}"; do
        echo "  $test_name: ${test_results[$test_name]}" >> "$report_file"
    done
    
    echo "" >> "$report_file"
    echo "Detailed logs available in: $TEST_LOG" >> "$report_file"
    
    log_info "Test report generated: $report_file"
    
    # Generate JSON results
    cat > "$RESULTS_FILE" << EOF
{
  "timestamp": "$TIMESTAMP",
  "total_tests": $total_tests,
  "passed_tests": $passed_tests,
  "failed_tests": $failed_tests,
  "success_rate": $(( passed_tests * 100 / total_tests )),
  "results": {
EOF
    
    local first=true
    for test_name in "${!test_results[@]}"; do
        if [[ "$first" == true ]]; then
            first=false
        else
            echo "," >> "$RESULTS_FILE"
        fi
        echo -n "    \"$test_name\": \"${test_results[$test_name]}\"" >> "$RESULTS_FILE"
    done
    
    cat >> "$RESULTS_FILE" << EOF

  }
}
EOF
    
    log_info "JSON results saved to: $RESULTS_FILE"
    
    # Display summary
    echo ""
    echo "================================="
    echo "TEST EXECUTION SUMMARY"
    echo "================================="
    echo "Total Tests: $total_tests"
    echo -e "Passed: ${GREEN}$passed_tests${NC}"
    echo -e "Failed: ${RED}$failed_tests${NC}"
    echo "Success Rate: $(( passed_tests * 100 / total_tests ))%"
    echo "================================="
    
    if [[ $failed_tests -gt 0 ]]; then
        echo -e "${RED}Some tests failed. Check the detailed logs for more information.${NC}"
        return 1
    else
        echo -e "${GREEN}All tests passed successfully!${NC}"
        return 0
    fi
}

# Main test execution function
main() {
    echo "VMS-Versa-Docker Automated Test Suite"
    echo "======================================"
    
    init_logging
    
    # Trap to ensure cleanup on exit
    trap cleanup EXIT
    
    # Execute test phases
    test_infrastructure || {
        log_error "Infrastructure tests failed. Aborting test suite."
        generate_report
        exit 1
    }
    
    test_service_integration
    test_functionality
    test_performance
    test_load
    test_scaling
    
    # Generate final report
    generate_report
}

# Command line options
case "${1:-run}" in
    "run"|"")
        main
        ;;
    "infrastructure")
        init_logging
        test_infrastructure
        generate_report
        ;;
    "integration")
        init_logging
        test_service_integration
        generate_report
        ;;
    "functional")
        init_logging
        test_functionality
        generate_report
        ;;
    "performance")
        init_logging
        test_performance
        generate_report
        ;;
    "load")
        init_logging
        test_load
        generate_report
        ;;
    "scaling")
        init_logging
        test_scaling
        generate_report
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  run            Run all test phases (default)"
        echo "  infrastructure Run infrastructure tests only"
        echo "  integration    Run integration tests only"
        echo "  functional     Run functional tests only"
        echo "  performance    Run performance tests only"
        echo "  load           Run load tests only"
        echo "  scaling        Run scaling tests only"
        echo "  help           Show this help message"
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use '$0 help' for usage information."
        exit 1
        ;;
esac
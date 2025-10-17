#!/bin/bash

# VMS-Versa-Docker Performance Test Script
# Version: 1.0
# Date: October 17, 2025
# Description: Performance and load testing for VMS-Versa-Docker

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PERF_LOG="$RESULTS_DIR/performance_test_$TIMESTAMP.log"

# Test configuration
WEB_FRONTEND_URL="http://localhost:5000"
NGINX_URL="http://localhost:80"
TEST_DURATION=60
CONCURRENT_USERS=10
RAMP_UP_TIME=30

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$PERF_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} [$(date '+%H:%M:%S')] $1" | tee -a "$PERF_LOG"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} [$(date '+%H:%M:%S')] $1" | tee -a "$PERF_LOG"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} [$(date '+%H:%M:%S')] $1" | tee -a "$PERF_LOG"
}

# Initialize
init_performance_testing() {
    mkdir -p "$RESULTS_DIR"
    echo "Performance testing started at $(date)" > "$PERF_LOG"
    log_info "Performance test log: $PERF_LOG"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites for performance testing..."
    
    # Check if services are running
    if ! curl -f -s "$WEB_FRONTEND_URL/health" >/dev/null 2>&1 && ! curl -f -s "$WEB_FRONTEND_URL" >/dev/null 2>&1; then
        log_error "Web frontend is not accessible. Please start the services first."
        exit 1
    fi
    
    log_success "Services are accessible"
}

# Basic response time test
test_response_times() {
    log_info "=== Response Time Testing ==="
    
    local endpoints=(
        "$WEB_FRONTEND_URL Web-Frontend"
        "$WEB_FRONTEND_URL/health Web-Frontend-Health"
        "http://localhost:8001/health SSH-Service"
        "http://localhost:8002/health Kubectl-Service"
        "http://localhost:8003/health Redis-Service"
        "http://localhost:8004/health Logs-Service"
        "$NGINX_URL NGINX-LoadBalancer"
    )
    
    echo "Endpoint,Average_Response_Time,Min_Time,Max_Time,Status" > "$RESULTS_DIR/response_times_$TIMESTAMP.csv"
    
    for endpoint_info in "${endpoints[@]}"; do
        read -r url name <<< "$endpoint_info"
        
        log_info "Testing response times for $name..."
        
        local times=()
        local successful_requests=0
        local total_requests=10
        
        for ((i=1; i<=total_requests; i++)); do
            local response_time=$(curl -o /dev/null -s -w "%{time_total}" "$url" 2>/dev/null || echo "0")
            
            if [[ "$response_time" != "0" ]] && (( $(echo "$response_time > 0" | bc -l 2>/dev/null || echo "0") )); then
                times+=("$response_time")
                ((successful_requests++))
            fi
        done
        
        if [[ $successful_requests -gt 0 ]]; then
            # Calculate statistics
            local sum=0
            local min=${times[0]}
            local max=${times[0]}
            
            for time in "${times[@]}"; do
                sum=$(echo "$sum + $time" | bc -l)
                
                if (( $(echo "$time < $min" | bc -l) )); then
                    min=$time
                fi
                
                if (( $(echo "$time > $max" | bc -l) )); then
                    max=$time
                fi
            done
            
            local avg=$(echo "scale=3; $sum / $successful_requests" | bc -l)
            
            echo "$name,$avg,$min,$max,SUCCESS" >> "$RESULTS_DIR/response_times_$TIMESTAMP.csv"
            log_success "$name: Avg=${avg}s, Min=${min}s, Max=${max}s"
        else
            echo "$name,0,0,0,FAILED" >> "$RESULTS_DIR/response_times_$TIMESTAMP.csv"
            log_error "$name: All requests failed"
        fi
    done
}

# Apache Bench load test
test_apache_bench() {
    log_info "=== Apache Bench Load Testing ==="
    
    if ! command -v ab &> /dev/null; then
        log_error "Apache Bench (ab) not found. Installing..."
        
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y apache2-utils
        elif command -v yum &> /dev/null; then
            sudo yum install -y httpd-tools
        else
            log_error "Cannot install Apache Bench. Skipping this test."
            return 1
        fi
    fi
    
    local test_configs=(
        "50 10 Light-Load"
        "100 20 Medium-Load"
        "200 50 Heavy-Load"
    )
    
    for config in "${test_configs[@]}"; do
        read -r requests concurrency load_type <<< "$config"
        
        log_info "Running $load_type test: $requests requests, $concurrency concurrent"
        
        local ab_output="$RESULTS_DIR/ab_${load_type}_$TIMESTAMP.txt"
        
        if ab -n "$requests" -c "$concurrency" -g "$RESULTS_DIR/ab_${load_type}_$TIMESTAMP.tsv" "$WEB_FRONTEND_URL/" > "$ab_output" 2>&1; then
            log_success "$load_type test completed successfully"
            
            # Extract key metrics
            local rps=$(grep "Requests per second:" "$ab_output" | awk '{print $4}')
            local tpr=$(grep "Time per request:" "$ab_output" | head -1 | awk '{print $4}')
            local failed=$(grep "Failed requests:" "$ab_output" | awk '{print $3}')
            
            log_info "$load_type Results: RPS=$rps, Time/Request=${tpr}ms, Failed=$failed"
        else
            log_error "$load_type test failed"
        fi
    done
}

# Custom concurrent test
test_concurrent_requests() {
    log_info "=== Concurrent Request Testing ==="
    
    local concurrent_levels=(5 10 20 30)
    
    echo "Concurrent_Level,Successful_Requests,Failed_Requests,Average_Response_Time,Success_Rate" > "$RESULTS_DIR/concurrent_test_$TIMESTAMP.csv"
    
    for concurrent in "${concurrent_levels[@]}"; do
        log_info "Testing with $concurrent concurrent requests..."
        
        local pids=()
        local results_file="/tmp/concurrent_test_$$"
        rm -f "${results_file}_*"
        
        # Launch concurrent requests
        for ((i=1; i<=concurrent; i++)); do
            {
                local start_time=$(date +%s.%3N)
                if curl -f -s "$WEB_FRONTEND_URL" >/dev/null 2>&1; then
                    local end_time=$(date +%s.%3N)
                    local response_time=$(echo "$end_time - $start_time" | bc -l)
                    echo "SUCCESS $response_time" > "${results_file}_$i"
                else
                    echo "FAILED 0" > "${results_file}_$i"
                fi
            } &
            pids+=($!)
        done
        
        # Wait for all requests to complete
        for pid in "${pids[@]}"; do
            wait "$pid"
        done
        
        # Analyze results
        local successful=0
        local failed=0
        local total_time=0
        
        for ((i=1; i<=concurrent; i++)); do
            if [[ -f "${results_file}_$i" ]]; then
                read -r status response_time < "${results_file}_$i"
                if [[ "$status" == "SUCCESS" ]]; then
                    ((successful++))
                    total_time=$(echo "$total_time + $response_time" | bc -l)
                else
                    ((failed++))
                fi
            else
                ((failed++))
            fi
        done
        
        local avg_time=0
        if [[ $successful -gt 0 ]]; then
            avg_time=$(echo "scale=3; $total_time / $successful" | bc -l)
        fi
        
        local success_rate=$(echo "scale=1; $successful * 100 / $concurrent" | bc -l)
        
        echo "$concurrent,$successful,$failed,$avg_time,$success_rate" >> "$RESULTS_DIR/concurrent_test_$TIMESTAMP.csv"
        log_info "Concurrent $concurrent: $successful succeeded, $failed failed, ${success_rate}% success rate, ${avg_time}s avg time"
        
        # Cleanup
        rm -f "${results_file}_"*
        
        sleep 5  # Brief pause between tests
    done
}

# Resource monitoring
monitor_resources() {
    log_info "=== Resource Monitoring ==="
    
    local monitor_duration=60
    local interval=5
    local iterations=$((monitor_duration / interval))
    
    echo "Timestamp,Container,CPU_Percent,Memory_Usage,Memory_Limit,Memory_Percent,Network_IO,Block_IO" > "$RESULTS_DIR/resource_monitoring_$TIMESTAMP.csv"
    
    log_info "Monitoring resources for $monitor_duration seconds..."
    
    for ((i=1; i<=iterations; i++)); do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # Get Docker stats
        docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}}" | grep "vms-" | while IFS=',' read -r container cpu mem_usage mem_perc net_io block_io; do
            # Parse memory usage (e.g., "100MiB / 2GiB")
            local mem_used=$(echo "$mem_usage" | awk '{print $1}')
            local mem_limit=$(echo "$mem_usage" | awk '{print $3}')
            
            echo "$timestamp,$container,$cpu,$mem_used,$mem_limit,$mem_perc,$net_io,$block_io" >> "$RESULTS_DIR/resource_monitoring_$TIMESTAMP.csv"
        done
        
        sleep "$interval"
    done
    
    log_success "Resource monitoring completed"
}

# Stress test
test_stress() {
    log_info "=== Stress Testing ==="
    
    log_info "Running sustained load test for $TEST_DURATION seconds..."
    
    local stress_results="$RESULTS_DIR/stress_test_$TIMESTAMP.txt"
    local start_time=$(date +%s)
    local end_time=$((start_time + TEST_DURATION))
    local request_count=0
    local success_count=0
    local error_count=0
    
    # Start resource monitoring in background
    {
        echo "Timestamp,CPU_Usage,Memory_Usage,Load_Average" > "$RESULTS_DIR/system_resources_$TIMESTAMP.csv"
        while [[ $(date +%s) -lt $end_time ]]; do
            local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
            local memory_usage=$(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')
            local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
            
            echo "$timestamp,$cpu_usage,$memory_usage,$load_avg" >> "$RESULTS_DIR/system_resources_$TIMESTAMP.csv"
            sleep 10
        done
    } &
    local monitor_pid=$!
    
    # Generate sustained load
    while [[ $(date +%s) -lt $end_time ]]; do
        for ((i=1; i<=CONCURRENT_USERS; i++)); do
            {
                if curl -f -s "$WEB_FRONTEND_URL" >/dev/null 2>&1; then
                    echo "SUCCESS" >> "/tmp/stress_results_$$"
                else
                    echo "ERROR" >> "/tmp/stress_results_$$"
                fi
            } &
        done
        
        # Wait for this batch and count
        wait
        
        local batch_success=$(grep -c "SUCCESS" "/tmp/stress_results_$$" 2>/dev/null || echo 0)
        local batch_error=$(grep -c "ERROR" "/tmp/stress_results_$$" 2>/dev/null || echo 0)
        
        success_count=$((success_count + batch_success))
        error_count=$((error_count + batch_error))
        request_count=$((request_count + batch_success + batch_error))
        
        rm -f "/tmp/stress_results_$$"
        
        sleep 1
    done
    
    # Stop resource monitoring
    kill $monitor_pid 2>/dev/null || true
    
    local success_rate=0
    if [[ $request_count -gt 0 ]]; then
        success_rate=$(echo "scale=1; $success_count * 100 / $request_count" | bc -l)
    fi
    
    {
        echo "Stress Test Results"
        echo "=================="
        echo "Duration: $TEST_DURATION seconds"
        echo "Total Requests: $request_count"
        echo "Successful: $success_count"
        echo "Errors: $error_count"
        echo "Success Rate: ${success_rate}%"
        echo "Requests/Second: $(echo "scale=2; $request_count / $TEST_DURATION" | bc -l)"
    } | tee "$stress_results" >> "$PERF_LOG"
    
    log_success "Stress test completed: $success_count/$request_count requests successful (${success_rate}%)"
}

# Generate performance report
generate_performance_report() {
    log_info "=== Generating Performance Report ==="
    
    local report_file="$RESULTS_DIR/performance_summary_$TIMESTAMP.html"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>VMS-Versa-Docker Performance Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>VMS-Versa-Docker Performance Test Report</h1>
        <p><strong>Generated:</strong> $(date)</p>
        <p><strong>Test Duration:</strong> $TEST_DURATION seconds</p>
        <p><strong>Concurrent Users:</strong> $CONCURRENT_USERS</p>
    </div>

    <div class="section">
        <h2>Test Summary</h2>
        <p>Performance testing completed for VMS-Versa-Docker microservices architecture.</p>
        <p>All test results and detailed logs are available in the test results directory.</p>
    </div>

    <div class="section">
        <h2>Response Time Results</h2>
EOF
    
    if [[ -f "$RESULTS_DIR/response_times_$TIMESTAMP.csv" ]]; then
        echo "<table>" >> "$report_file"
        echo "<tr><th>Endpoint</th><th>Avg Response Time</th><th>Min Time</th><th>Max Time</th><th>Status</th></tr>" >> "$report_file"
        
        tail -n +2 "$RESULTS_DIR/response_times_$TIMESTAMP.csv" | while IFS=',' read -r endpoint avg min max status; do
            local css_class="success"
            if [[ "$status" == "FAILED" ]]; then
                css_class="error"
            elif (( $(echo "$avg > 1.0" | bc -l 2>/dev/null || echo "0") )); then
                css_class="warning"
            fi
            
            echo "<tr class=\"$css_class\"><td>$endpoint</td><td>${avg}s</td><td>${min}s</td><td>${max}s</td><td>$status</td></tr>" >> "$report_file"
        done
        
        echo "</table>" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF
    </div>

    <div class="section">
        <h2>Files Generated</h2>
        <ul>
            <li>Response Times: response_times_$TIMESTAMP.csv</li>
            <li>Concurrent Tests: concurrent_test_$TIMESTAMP.csv</li>
            <li>Resource Monitoring: resource_monitoring_$TIMESTAMP.csv</li>
            <li>System Resources: system_resources_$TIMESTAMP.csv</li>
            <li>Detailed Log: performance_test_$TIMESTAMP.log</li>
        </ul>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            <li>Monitor response times under different load conditions</li>
            <li>Implement caching strategies for frequently accessed data</li>
            <li>Consider horizontal scaling for high-traffic scenarios</li>
            <li>Regular performance regression testing</li>
        </ul>
    </div>
</body>
</html>
EOF
    
    log_success "Performance report generated: $report_file"
}

# Main execution
main() {
    echo "VMS-Versa-Docker Performance Test Suite"
    echo "======================================="
    
    init_performance_testing
    
    case "${1:-all}" in
        "response")
            check_prerequisites
            test_response_times
            ;;
        "load")
            check_prerequisites
            test_apache_bench
            ;;
        "concurrent")
            check_prerequisites
            test_concurrent_requests
            ;;
        "monitor")
            check_prerequisites
            monitor_resources
            ;;
        "stress")
            check_prerequisites
            test_stress
            ;;
        "all"|"")
            check_prerequisites
            test_response_times
            test_concurrent_requests
            monitor_resources &
            monitor_pid=$!
            test_apache_bench
            test_stress
            kill $monitor_pid 2>/dev/null || true
            generate_performance_report
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Options:"
            echo "  all         Run all performance tests (default)"
            echo "  response    Run response time tests only"
            echo "  load        Run Apache Bench load tests only"
            echo "  concurrent  Run concurrent request tests only"
            echo "  monitor     Run resource monitoring only"
            echo "  stress      Run stress tests only"
            echo "  help        Show this help message"
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use '$0 help' for usage information."
            exit 1
            ;;
    esac
    
    log_success "Performance testing completed. Results saved in: $RESULTS_DIR"
}

# Run main function
main "$@"
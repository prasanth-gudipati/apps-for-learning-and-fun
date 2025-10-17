#!/bin/bash

# VMS Debug Tool - Health Monitoring Script
# Comprehensive health checking and monitoring for all microservices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
HEALTH_CHECK_TIMEOUT=5
RETRY_COUNT=3
RETRY_DELAY=2

# Service definitions
declare -A SERVICES
SERVICES[web-frontend]="5000"
SERVICES[ssh-service]="8001"
SERVICES[kubectl-service]="8002"
SERVICES[redis-service]="8003"
SERVICES[logs-service]="8004"

# Function to print colored output
print_header() {
    echo -e "${CYAN}=================================================================${NC}"
    echo -e "${CYAN} VMS Debug Tool - Health Monitoring Dashboard${NC}"
    echo -e "${CYAN}=================================================================${NC}"
}

print_section() {
    echo -e "\n${BLUE}─── $1 ───${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check if a service is responding
check_service_health() {
    local service_name="$1"
    local port="$2"
    local url="http://localhost:$port/health"
    
    for i in $(seq 1 $RETRY_COUNT); do
        if curl -f -s --connect-timeout $HEALTH_CHECK_TIMEOUT "$url" >/dev/null 2>&1; then
            return 0
        fi
        if [ $i -lt $RETRY_COUNT ]; then
            sleep $RETRY_DELAY
        fi
    done
    return 1
}

# Function to get service response time
get_response_time() {
    local port="$1"
    local url="http://localhost:$port/health"
    
    local response_time=$(curl -o /dev/null -s -w "%{time_total}" --connect-timeout $HEALTH_CHECK_TIMEOUT "$url" 2>/dev/null || echo "timeout")
    echo "$response_time"
}

# Function to check Docker containers
check_docker_status() {
    print_section "Docker Container Status"
    
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        return 1
    fi
    
    print_success "Docker daemon is running"
    
    # Check if docker-compose project is running
    local project_name=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    local containers=$(docker ps -q -f "label=com.docker.compose.project=$project_name" 2>/dev/null | wc -l)
    
    if [ "$containers" -eq 0 ]; then
        print_warning "No VMS Debug Tool containers are running"
        print_info "Run './vms-docker.sh start' to start all services"
        return 1
    fi
    
    print_success "$containers containers are running"
    
    # Show container status
    echo ""
    printf "%-20s %-15s %-10s %-15s\n" "CONTAINER" "STATUS" "HEALTH" "PORTS"
    echo "────────────────────────────────────────────────────────────────"
    
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.State}}\t{{.Ports}}" \
        -f "label=com.docker.compose.project=$project_name" \
        --no-trunc | tail -n +2 | while read line; do
        echo "$line"
    done
}

# Function to check service health
check_services_health() {
    print_section "Service Health Checks"
    
    local all_healthy=true
    local total_services=${#SERVICES[@]}
    local healthy_count=0
    
    printf "%-18s %-8s %-12s %-10s\n" "SERVICE" "STATUS" "RESPONSE" "PORT"
    echo "──────────────────────────────────────────────────────────"
    
    for service in "${!SERVICES[@]}"; do
        local port="${SERVICES[$service]}"
        
        if check_service_health "$service" "$port"; then
            local response_time=$(get_response_time "$port")
            printf "%-18s ${GREEN}%-8s${NC} %-12s %-10s\n" "$service" "HEALTHY" "${response_time}s" "$port"
            ((healthy_count++))
        else
            printf "%-18s ${RED}%-8s${NC} %-12s %-10s\n" "$service" "FAILED" "timeout" "$port"
            all_healthy=false
        fi
    done
    
    echo ""
    if [ "$all_healthy" = true ]; then
        print_success "All $total_services services are healthy"
    else
        print_warning "$healthy_count/$total_services services are healthy"
    fi
    
    return $all_healthy
}

# Function to check Redis connectivity
check_redis() {
    print_section "Redis Health Check"
    
    if docker-compose ps session-redis | grep -q "Up"; then
        if docker-compose exec -T session-redis redis-cli ping >/dev/null 2>&1; then
            local redis_info=$(docker-compose exec -T session-redis redis-cli info server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
            print_success "Redis is healthy (version: $redis_info)"
            
            # Get Redis stats
            local connected_clients=$(docker-compose exec -T session-redis redis-cli info clients 2>/dev/null | grep "connected_clients" | cut -d: -f2 | tr -d '\r')
            local used_memory=$(docker-compose exec -T session-redis redis-cli info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
            
            echo "  Connected clients: $connected_clients"
            echo "  Memory usage: $used_memory"
        else
            print_error "Redis is not responding to commands"
            return 1
        fi
    else
        print_error "Redis container is not running"
        return 1
    fi
}

# Function to check NGINX
check_nginx() {
    print_section "NGINX Load Balancer Check"
    
    if docker-compose ps nginx | grep -q "Up"; then
        if curl -f -s --connect-timeout $HEALTH_CHECK_TIMEOUT "http://localhost:80" >/dev/null 2>&1; then
            print_success "NGINX is healthy and routing traffic"
        else
            print_warning "NGINX container is running but not responding"
            return 1
        fi
    else
        print_warning "NGINX container is not running"
        print_info "Load balancer is not available, services accessible directly"
    fi
}

# Function to check system resources
check_system_resources() {
    print_section "System Resource Usage"
    
    # Docker stats for VMS containers
    local project_name=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        echo "Container Resource Usage:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
            $(docker ps -q -f "label=com.docker.compose.project=$project_name" 2>/dev/null) 2>/dev/null || \
            print_warning "No containers running or unable to get stats"
    fi
    
    echo ""
    echo "Host System Resources:"
    
    # Memory usage
    if command -v free >/dev/null 2>&1; then
        local mem_info=$(free -h | grep "Mem:")
        local mem_used=$(echo $mem_info | awk '{print $3}')
        local mem_total=$(echo $mem_info | awk '{print $2}')
        echo "  Memory: $mem_used / $mem_total used"
    fi
    
    # Disk usage
    if command -v df >/dev/null 2>&1; then
        local disk_usage=$(df -h . | tail -1 | awk '{print $5 " used (" $3 "/" $2 ")"}')
        echo "  Disk: $disk_usage"
    fi
    
    # Load average
    if command -v uptime >/dev/null 2>&1; then
        local load_avg=$(uptime | sed 's/.*load average: //' | cut -d, -f1-3)
        echo "  Load average: $load_avg"
    fi
}

# Function to check network connectivity
check_network() {
    print_section "Network Connectivity"
    
    # Check if Docker network exists
    local network_name="vms-versa-docker_vms-network"
    if docker network ls | grep -q "$network_name"; then
        print_success "Docker network '$network_name' exists"
        
        # Check network connectivity between services
        if docker-compose ps web-frontend | grep -q "Up"; then
            local ping_results=""
            for service in "${!SERVICES[@]}"; do
                if [ "$service" != "web-frontend" ]; then
                    if docker-compose exec -T web-frontend ping -c 1 "$service" >/dev/null 2>&1; then
                        ping_results="${ping_results}✓ $service "
                    else
                        ping_results="${ping_results}✗ $service "
                    fi
                fi
            done
            echo "  Inter-service connectivity: $ping_results"
        fi
    else
        print_warning "Docker network not found"
    fi
    
    # Check external connectivity (if services need it)
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_success "External internet connectivity available"
    else
        print_warning "No external internet connectivity"
    fi
}

# Function to show application URLs
show_access_info() {
    print_section "Application Access Information"
    
    echo "Web Interfaces:"
    echo "  Main Application:     http://localhost:5000"
    echo "  Load Balanced:        http://localhost:80"
    echo ""
    echo "Service APIs:"
    echo "  SSH Service:          http://localhost:8001"
    echo "  Kubectl Service:      http://localhost:8002"
    echo "  Redis Service:        http://localhost:8003"
    echo "  Logs Service:         http://localhost:8004"
    echo ""
    echo "Direct Database Access:"
    echo "  Redis Session Store:  redis://localhost:6379"
}

# Function to run continuous monitoring
monitor_continuous() {
    print_info "Starting continuous monitoring (Ctrl+C to stop)"
    echo "Refresh interval: 10 seconds"
    echo ""
    
    while true; do
        clear
        print_header
        
        check_docker_status
        check_services_health
        check_redis
        check_nginx
        
        echo ""
        echo -e "${BLUE}Last updated: $(date)${NC}"
        echo -e "${BLUE}Press Ctrl+C to stop monitoring${NC}"
        
        sleep 10
    done
}

# Function to generate health report
generate_report() {
    local report_file="health-report-$(date +%Y%m%d-%H%M%S).txt"
    
    print_info "Generating health report: $report_file"
    
    {
        echo "VMS Debug Tool - Health Report"
        echo "Generated: $(date)"
        echo "=========================================="
        echo ""
        
        # Redirect all check functions to the report
        check_docker_status
        echo ""
        check_services_health
        echo ""
        check_redis
        echo ""
        check_nginx
        echo ""
        check_system_resources
        echo ""
        check_network
        
    } > "$report_file" 2>&1
    
    print_success "Health report saved to: $report_file"
}

# Function to show help
show_help() {
    echo "VMS Debug Tool - Health Monitoring Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  check          Run all health checks once (default)"
    echo "  monitor        Run continuous monitoring with auto-refresh"
    echo "  docker         Check Docker containers status only"
    echo "  services       Check service health only"
    echo "  redis          Check Redis status only"
    echo "  nginx          Check NGINX status only"
    echo "  resources      Check system resources only"
    echo "  network        Check network connectivity only"
    echo "  urls           Show application URLs and access info"
    echo "  report         Generate detailed health report file"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Run all health checks"
    echo "  $0 monitor             # Start continuous monitoring"
    echo "  $0 services            # Check only service health"
    echo "  $0 report              # Generate health report file"
}

# Main script logic
case "$1" in
    "check"|"")
        print_header
        check_docker_status
        check_services_health
        check_redis
        check_nginx
        check_system_resources
        check_network
        show_access_info
        ;;
    "monitor")
        monitor_continuous
        ;;
    "docker")
        print_header
        check_docker_status
        ;;
    "services")
        print_header
        check_services_health
        ;;
    "redis")
        print_header
        check_redis
        ;;
    "nginx")
        print_header
        check_nginx
        ;;
    "resources")
        print_header
        check_system_resources
        ;;
    "network")
        print_header
        check_network
        ;;
    "urls")
        print_header
        show_access_info
        ;;
    "report")
        generate_report
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
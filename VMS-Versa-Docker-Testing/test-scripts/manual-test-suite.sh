#!/bin/bash

# VMS-Versa-Docker Manual Test Script
# Version: 1.0
# Date: October 17, 2025
# Description: Simple manual testing script for VMS-Versa-Docker

set -e

# Configuration
PROJECT_DIR="/home/versa/pgudipati/SAMBA-70-188-169/apps-for-learning-and-fun/VMS-Versa-Docker"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_step() {
    echo -e "${YELLOW}Step $1:${NC} $2"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

wait_for_user() {
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read -r
}

check_url() {
    local url="$1"
    local name="$2"
    
    print_info "Checking $name at $url"
    
    if curl -f -s "$url" > /dev/null 2>&1; then
        print_success "$name is accessible"
        return 0
    else
        print_error "$name is not accessible"
        return 1
    fi
}

# Test functions
test_prerequisites() {
    print_header "Prerequisites Check"
    
    print_step "1" "Checking Docker installation"
    if command -v docker &> /dev/null; then
        print_success "Docker is installed: $(docker --version | head -1)"
    else
        print_error "Docker is not installed"
        exit 1
    fi
    
    print_step "2" "Checking docker-compose installation"
    if command -v docker-compose &> /dev/null; then
        print_success "docker-compose is installed: $(docker-compose --version)"
    else
        print_error "docker-compose is not installed"
        exit 1
    fi
    
    print_step "3" "Checking project directory"
    if [[ -d "$PROJECT_DIR" ]]; then
        print_success "Project directory exists: $PROJECT_DIR"
    else
        print_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    print_step "4" "Checking management script"
    if [[ -x "$PROJECT_DIR/vms-docker.sh" ]]; then
        print_success "Management script is executable"
    else
        print_error "Management script not found or not executable"
        exit 1
    fi
}

test_build() {
    print_header "Build Test"
    
    cd "$PROJECT_DIR"
    
    print_step "1" "Building all Docker images"
    print_info "This may take several minutes..."
    
    if ./vms-docker.sh build; then
        print_success "All Docker images built successfully"
    else
        print_error "Docker build failed"
        return 1
    fi
}

test_startup() {
    print_header "Service Startup Test"
    
    cd "$PROJECT_DIR"
    
    print_step "1" "Starting all services"
    print_info "Starting Docker containers..."
    
    if ./vms-docker.sh start; then
        print_success "All services started"
    else
        print_error "Service startup failed"
        return 1
    fi
    
    print_step "2" "Waiting for services to initialize"
    print_info "Waiting 30 seconds for services to be ready..."
    sleep 30
    
    print_step "3" "Checking service status"
    ./vms-docker.sh status
}

test_connectivity() {
    print_header "Service Connectivity Test"
    
    print_step "1" "Testing service endpoints"
    
    # Test main services
    check_url "http://localhost:5000" "Web Frontend"
    check_url "http://localhost:8001/health" "SSH Service"
    check_url "http://localhost:8002/health" "Kubectl Service"
    check_url "http://localhost:8003/health" "Redis Service"
    check_url "http://localhost:8004/health" "Logs Service"
    check_url "http://localhost:80" "NGINX Load Balancer"
    
    print_step "2" "Testing web interface"
    print_info "Opening web browser to test the interface..."
    print_info "Manual step: Open http://localhost:5000 in your browser"
    print_info "Verify that the web interface loads properly"
    wait_for_user
}

test_basic_functionality() {
    print_header "Basic Functionality Test"
    
    print_step "1" "Testing container status"
    echo "Current running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    print_step "2" "Testing service logs"
    print_info "Checking web-frontend logs (last 10 lines):"
    cd "$PROJECT_DIR"
    ./vms-docker.sh logs web-frontend | tail -10
    
    print_step "3" "Testing service scaling"
    print_info "Scaling web-frontend to 2 instances..."
    if ./vms-docker.sh scale web-frontend 2; then
        print_success "Scaling up successful"
        sleep 10
        
        print_info "Scaling back to 1 instance..."
        if ./vms-docker.sh scale web-frontend 1; then
            print_success "Scaling down successful"
        else
            print_error "Scaling down failed"
        fi
    else
        print_error "Scaling up failed"
    fi
}

test_manual_interaction() {
    print_header "Manual Interaction Test"
    
    print_info "This section requires manual testing in the web interface"
    print_info "Please open http://localhost:5000 in your browser and:"
    echo ""
    echo "1. Verify the main page loads correctly"
    echo "2. Check that all navigation elements are present"
    echo "3. Try connecting to a test SSH host (if available)"
    echo "4. Test any available functionality"
    echo "5. Check for JavaScript errors in browser console"
    echo ""
    
    wait_for_user
    
    echo "Was the manual testing successful? (y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_success "Manual testing completed successfully"
        return 0
    else
        print_error "Manual testing reported issues"
        return 1
    fi
}

test_performance() {
    print_header "Basic Performance Test"
    
    print_step "1" "Testing response times"
    
    for url in "http://localhost:5000" "http://localhost:8001/health" "http://localhost:8002/health"; do
        print_info "Testing response time for $url"
        
        response_time=$(curl -o /dev/null -s -w "%{time_total}" "$url" 2>/dev/null || echo "error")
        
        if [[ "$response_time" != "error" ]]; then
            print_info "Response time: ${response_time}s"
            
            # Check if response time is reasonable (< 2 seconds)
            if (( $(echo "$response_time < 2.0" | bc -l 2>/dev/null || echo "0") )); then
                print_success "Response time is good"
            else
                print_error "Response time is slow (> 2s)"
            fi
        else
            print_error "Failed to get response time for $url"
        fi
    done
    
    print_step "2" "Checking resource usage"
    print_info "Current Docker container resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

cleanup_test() {
    print_header "Cleanup"
    
    cd "$PROJECT_DIR"
    
    print_step "1" "Stopping all services"
    if ./vms-docker.sh stop; then
        print_success "All services stopped"
    else
        print_error "Some services may still be running"
    fi
    
    print_step "2" "Checking for running containers"
    remaining=$(docker ps -q --filter "name=vms-" | wc -l)
    if [[ "$remaining" -eq 0 ]]; then
        print_success "All VMS containers stopped"
    else
        print_error "$remaining VMS containers still running"
    fi
}

# Main menu
show_menu() {
    clear
    echo -e "${BLUE}"
    echo "VMS-Versa-Docker Manual Test Suite"
    echo "=================================="
    echo -e "${NC}"
    echo "Select a test to run:"
    echo ""
    echo "1) Run All Tests (Recommended)"
    echo "2) Prerequisites Check"
    echo "3) Build Test"
    echo "4) Startup Test"
    echo "5) Connectivity Test"
    echo "6) Basic Functionality Test"
    echo "7) Manual Interaction Test"
    echo "8) Performance Test"
    echo "9) Cleanup"
    echo "0) Exit"
    echo ""
    echo -n "Enter your choice [0-9]: "
}

# Main execution
main() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1)
                print_info "Running complete test suite..."
                test_prerequisites
                test_build
                test_startup
                test_connectivity
                test_basic_functionality
                test_manual_interaction
                test_performance
                print_success "All tests completed!"
                wait_for_user
                ;;
            2)
                test_prerequisites
                wait_for_user
                ;;
            3)
                test_build
                wait_for_user
                ;;
            4)
                test_startup
                wait_for_user
                ;;
            5)
                test_connectivity
                wait_for_user
                ;;
            6)
                test_basic_functionality
                wait_for_user
                ;;
            7)
                test_manual_interaction
                wait_for_user
                ;;
            8)
                test_performance
                wait_for_user
                ;;
            9)
                cleanup_test
                wait_for_user
                ;;
            0)
                echo "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please select 0-9."
                wait_for_user
                ;;
        esac
    done
}

# Check if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
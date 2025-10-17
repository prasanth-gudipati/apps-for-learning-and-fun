#!/bin/bash

# VMS Debug Tool - Docker Microservices
# Build and Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install docker-compose and try again."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Function to build all services
build_services() {
    print_status "Building all microservices..."
    docker-compose build
    print_success "All services built successfully"
}

# Function to start all services
start_services() {
    print_status "Starting all microservices..."
    docker-compose up -d
    print_success "All services started successfully"
    
    print_status "Services status:"
    docker-compose ps
    
    echo ""
    print_success "VMS Debug Tool is now running!"
    echo -e "${GREEN}Access the application at:${NC}"
    echo -e "  • Direct Access: ${BLUE}http://localhost:5000${NC}"
    echo -e "  • Load Balanced: ${BLUE}http://localhost:80${NC}"
    echo ""
    echo -e "${YELLOW}Service Endpoints:${NC}"
    echo -e "  • SSH Service: ${BLUE}http://localhost:8001${NC}"
    echo -e "  • Kubectl Service: ${BLUE}http://localhost:8002${NC}"
    echo -e "  • Redis Service: ${BLUE}http://localhost:8003${NC}"
    echo -e "  • Logs Service: ${BLUE}http://localhost:8004${NC}"
    echo -e "  • Session Redis: ${BLUE}redis://localhost:6379${NC}"
}

# Function to stop all services
stop_services() {
    print_status "Stopping all microservices..."
    docker-compose down
    print_success "All services stopped successfully"
}

# Function to restart all services
restart_services() {
    print_status "Restarting all microservices..."
    docker-compose down
    docker-compose up -d
    print_success "All services restarted successfully"
}

# Function to view logs
view_logs() {
    if [ -z "$1" ]; then
        print_status "Showing logs for all services..."
        docker-compose logs -f
    else
        print_status "Showing logs for service: $1"
        docker-compose logs -f "$1"
    fi
}

# Function to show service status
show_status() {
    print_status "Service status:"
    docker-compose ps
    
    echo ""
    print_status "Service health checks:"
    
    services=("web-frontend:5000" "ssh-service:8001" "kubectl-service:8002" "redis-service:8003" "logs-service:8004")
    
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        if curl -f -s "http://localhost:$port/health" >/dev/null 2>&1; then
            print_success "$name is healthy"
        else
            print_error "$name is not responding"
        fi
    done
    
    # Check Redis
    if docker-compose exec -T session-redis redis-cli ping >/dev/null 2>&1; then
        print_success "session-redis is healthy"
    else
        print_error "session-redis is not responding"
    fi
}

# Function to clean up everything
cleanup() {
    print_warning "This will remove all containers, networks, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up all resources..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to scale services
scale_service() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        print_error "Usage: $0 scale <service_name> <replicas>"
        echo "Available services: web-frontend, ssh-service, kubectl-service, redis-service, logs-service"
        exit 1
    fi
    
    print_status "Scaling $1 to $2 replicas..."
    docker-compose up -d --scale "$1"="$2"
    print_success "Service $1 scaled to $2 replicas"
}

# Function to show help
show_help() {
    echo "VMS Debug Tool - Docker Microservices Management"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build          Build all microservices"
    echo "  start          Start all microservices"
    echo "  stop           Stop all microservices"
    echo "  restart        Restart all microservices"
    echo "  status         Show service status and health"
    echo "  logs [service] Show logs for all services or specific service"
    echo "  scale <service> <replicas>  Scale a specific service"
    echo "  cleanup        Remove all containers, networks, and volumes"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build && $0 start     # Build and start all services"
    echo "  $0 logs web-frontend     # Show logs for web frontend only"
    echo "  $0 scale web-frontend 3  # Scale web frontend to 3 replicas"
    echo "  $0 status                # Check health of all services"
    echo ""
    echo "Services:"
    echo "  • web-frontend   - Main web interface (Port 5000)"
    echo "  • ssh-service    - SSH connection management (Port 8001)"
    echo "  • kubectl-service - Kubectl operations (Port 8002)"
    echo "  • redis-service  - Redis operations (Port 8003)"
    echo "  • logs-service   - Log file operations (Port 8004)"
    echo "  • session-redis  - Session storage (Port 6379)"
    echo "  • nginx          - Load balancer (Port 80)"
}

# Main script logic
case "$1" in
    "build")
        check_docker
        check_docker_compose
        build_services
        ;;
    "start")
        check_docker
        check_docker_compose
        start_services
        ;;
    "stop")
        check_docker
        check_docker_compose
        stop_services
        ;;
    "restart")
        check_docker
        check_docker_compose
        restart_services
        ;;
    "logs")
        check_docker
        check_docker_compose
        view_logs "$2"
        ;;
    "status")
        check_docker
        check_docker_compose
        show_status
        ;;
    "scale")
        check_docker
        check_docker_compose
        scale_service "$2" "$3"
        ;;
    "cleanup")
        check_docker
        check_docker_compose
        cleanup
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
# VMS-Versa-Docker Testing Suite

This directory contains comprehensive testing tools and documentation for the VMS-Versa-Docker microservices application.

## Directory Structure

```
VMS-Versa-Docker-Testing/
├── README.md                    # This file
├── test-plans/                  # Test planning documentation
│   └── VMS-Docker-Test-Plan.md  # Comprehensive test plan
├── test-scripts/                # Automated test scripts
│   ├── automated-test-suite.sh  # Full automated test suite
│   ├── manual-test-suite.sh     # Interactive manual testing
│   └── performance-test.sh      # Performance and load testing
├── test-data/                   # Test data and configurations
├── test-results/                # Test execution results and logs
└── logs/                        # Test execution logs
```

## Quick Start

### Prerequisites

Before running any tests, ensure you have:

- Docker 20.10+ installed
- docker-compose 1.29+ installed
- Basic networking tools (curl, ping)
- Apache Bench (optional, for advanced load testing)
- bc calculator (for numeric calculations)

### Running Tests

#### 1. Automated Test Suite (Recommended)

Run the complete automated test suite:

```bash
cd test-scripts
./automated-test-suite.sh
```

Run specific test phases:

```bash
./automated-test-suite.sh infrastructure    # Infrastructure tests only
./automated-test-suite.sh integration       # Integration tests only
./automated-test-suite.sh functional        # Functional tests only
./automated-test-suite.sh performance       # Performance tests only
./automated-test-suite.sh load              # Load tests only
./automated-test-suite.sh scaling           # Scaling tests only
```

#### 2. Manual Test Suite (Interactive)

For step-by-step interactive testing:

```bash
cd test-scripts
./manual-test-suite.sh
```

This will present a menu with options to run individual test categories.

#### 3. Performance Testing

Run comprehensive performance tests:

```bash
cd test-scripts
./performance-test.sh                # Run all performance tests
./performance-test.sh response       # Response time tests only
./performance-test.sh load           # Load tests only
./performance-test.sh concurrent     # Concurrent request tests only
./performance-test.sh stress         # Stress tests only
```

## Test Categories

### 1. Infrastructure Tests
- Docker container build verification
- Service startup validation
- Health check verification
- Network connectivity testing
- Volume mount validation

### 2. Integration Tests
- Service-to-service communication
- API endpoint accessibility
- WebSocket functionality
- Database connectivity
- Load balancer functionality

### 3. Functional Tests
- Web UI functionality
- SSH connection management
- Kubernetes operations
- Redis data operations
- Log file analysis
- User session management

### 4. Performance Tests
- Response time measurement
- Load testing with varying user counts
- Concurrent request handling
- Resource usage monitoring
- Stress testing under high load

### 5. Scalability Tests
- Horizontal service scaling
- Load distribution verification
- Service recovery testing
- Resource allocation testing

## Test Results

### Automated Test Results

After running automated tests, results are stored in:

- **Detailed Logs**: `logs/test_execution_YYYYMMDD_HHMMSS.log`
- **JSON Results**: `test-results/test_results_YYYYMMDD_HHMMSS.json`
- **Summary Report**: `test-results/test_summary_YYYYMMDD_HHMMSS.txt`

### Performance Test Results

Performance tests generate:

- **CSV Data Files**: Response times, concurrent tests, resource monitoring
- **HTML Report**: `test-results/performance_summary_YYYYMMDD_HHMMSS.html`
- **Apache Bench Results**: Detailed load testing metrics
- **Resource Monitoring**: System and container resource usage

## Understanding Test Results

### Success Criteria

Tests pass when:
- All containers start successfully (100% success rate)
- All health checks return positive status
- Web interface loads and functions correctly
- Service-to-service communication works
- Response times are under acceptable thresholds
- No unhandled errors or service crashes occur

### Performance Benchmarks

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Response Time | < 1s | 1-2s | > 2s |
| Success Rate | > 95% | 90-95% | < 90% |
| CPU Usage | < 50% | 50-80% | > 80% |
| Memory Usage | < 70% | 70-85% | > 85% |

## Troubleshooting

### Common Issues

1. **Services Not Starting**
   ```bash
   # Check if ports are already in use
   netstat -tulpn | grep -E "(5000|8001|8002|8003|8004|6379|80)"
   
   # Check Docker daemon
   docker info
   
   # Check available resources
   docker system df
   ```

2. **Health Check Failures**
   ```bash
   # Check service logs
   cd /path/to/VMS-Versa-Docker
   ./vms-docker.sh logs [service-name]
   
   # Check container status
   docker ps -a
   ```

3. **Performance Issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Check system load
   top
   htop
   ```

4. **Network Connectivity Issues**
   ```bash
   # Test service reachability
   curl -v http://localhost:5000/health
   
   # Check Docker networks
   docker network ls
   docker network inspect vms-network
   ```

### Log Analysis

Test logs contain detailed information about:
- Each test execution step
- Service response codes and times
- Error messages and stack traces
- Resource usage metrics
- Performance measurements

Look for patterns in the logs to identify recurring issues.

## Customizing Tests

### Adding New Test Cases

To add new test cases to the automated suite:

1. Edit `test-scripts/automated-test-suite.sh`
2. Add new test function following the existing pattern
3. Call `record_test_result "Test Name" "PASS/FAIL" "Details"`
4. Add the function call to the appropriate test phase

### Modifying Test Configuration

Key configuration variables in the scripts:

```bash
# Timeouts
HEALTH_CHECK_TIMEOUT=30
STARTUP_TIMEOUT=120

# Load testing
CONCURRENT_USERS=10
TEST_DURATION=60

# Service URLs
WEB_FRONTEND_URL="http://localhost:5000"
SSH_SERVICE_URL="http://localhost:8001"
# ... etc
```

### Custom Performance Metrics

To add custom performance metrics:

1. Edit `test-scripts/performance-test.sh`
2. Add new monitoring functions
3. Update the CSV output format
4. Modify the HTML report generation

## Integration with CI/CD

### Jenkins Integration

```bash
# In Jenkins build step
cd VMS-Versa-Docker-Testing/test-scripts
./automated-test-suite.sh

# Publish test results
publishHTML([
    allowMissing: false,
    alwaysLinkToLastBuild: true,
    keepAll: true,
    reportDir: 'test-results',
    reportFiles: 'performance_summary_*.html',
    reportName: 'Performance Report'
])
```

### GitLab CI Integration

```yaml
# In .gitlab-ci.yml
test_vms_docker:
  stage: test
  script:
    - cd VMS-Versa-Docker-Testing/test-scripts
    - ./automated-test-suite.sh
  artifacts:
    when: always
    reports:
      junit: test-results/*.xml
    paths:
      - test-results/
      - logs/
```

## Best Practices

### Before Testing

1. Ensure sufficient system resources (4GB+ RAM)
2. Close unnecessary applications
3. Verify network connectivity
4. Clean up previous Docker containers/images if needed

### During Testing

1. Monitor system resources during long-running tests
2. Don't interrupt tests in progress
3. Review logs in real-time for immediate issues
4. Take note of any manual intervention required

### After Testing

1. Review all generated reports
2. Archive test results for comparison
3. Clean up test artifacts if needed
4. Document any issues found

## Maintenance

### Regular Updates

- Update test scripts when new features are added
- Refresh performance baselines periodically  
- Update test data and configurations as needed
- Review and update test documentation

### Test Environment Maintenance

- Clean up old test results periodically
- Monitor disk space usage in test directories
- Update testing tools and dependencies
- Verify test environment configuration

## Support

For issues with the testing suite:

1. Check the troubleshooting section above
2. Review test logs for detailed error information
3. Verify that the VMS-Versa-Docker application is working correctly
4. Check system resources and prerequisites
5. Consult the main VMS-Versa-Docker documentation

## Contributing

When contributing new tests or improvements:

1. Follow the existing code style and patterns
2. Add appropriate logging and error handling
3. Update this documentation
4. Test your changes thoroughly
5. Consider backward compatibility

## License

This testing suite follows the same license as the VMS-Versa-Docker application.
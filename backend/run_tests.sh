#!/bin/bash

# Test runner script for Stock Code backend
set -e

echo "🧪 Stock Code Backend Test Runner"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from backend directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from the backend directory${NC}"
    exit 1
fi

# Function to check if Docker container is running
check_container() {
    if docker ps --format '{{.Names}}' | grep -q "$1"; then
        return 0
    else
        return 1
    fi
}

# Function to start minimal test services
start_test_services() {
    echo "Starting test services..."
    
    # Start only PostgreSQL and Redis
    docker-compose -f ../docker-compose.yml up -d postgres redis
    
    # Wait for services to be healthy
    echo "Waiting for services to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f ../docker-compose.yml ps | grep -q "healthy"; then
            echo -e "${GREEN}Services are ready!${NC}"
            break
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}Services failed to start${NC}"
        exit 1
    fi
}

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if containers are running
echo "Checking Docker containers..."
if check_container "stock_code_db" && check_container "stock_code_redis"; then
    echo -e "${GREEN}✓ Database and Redis containers are running${NC}"
else
    echo -e "${YELLOW}Starting required containers...${NC}"
    start_test_services
fi

# Get container connection info
DB_HOST="localhost"
DB_PORT="5432"
DB_USER="stockcode"
DB_PASSWORD="stockcode123"
DB_NAME="stockcode"
REDIS_HOST="localhost"
REDIS_PORT="6379"

# Create test database
echo "Setting up test database..."

# Check if test database exists (using Docker)
if docker exec stock_code_db psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw stock_code_test; then
    echo "Test database already exists"
else
    echo "Creating test database..."
    docker exec stock_code_db psql -U $DB_USER -d postgres -c "CREATE DATABASE stock_code_test;"
    echo -e "${GREEN}✓ Test database created${NC}"
fi

# Export test environment variables
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/stock_code_test"
export REDIS_URL="redis://$REDIS_HOST:$REDIS_PORT/1"
export ENVIRONMENT="test"
export SECRET_KEY="test_secret_key_for_testing_only"
export EDINET_API_KEY="test_api_key"
export CORS_ORIGINS="http://localhost:3000,http://localhost:8000"

# Install test dependencies if not installed
echo "Checking test dependencies..."
python -c "import pytest" 2>/dev/null || {
    echo "Installing test dependencies..."
    pip install pytest pytest-cov pytest-asyncio pytest-mock
}

# Run tests
echo ""
echo "Running tests..."
echo "================"

# Default to all tests, or run specific tests if provided
if [ $# -eq 0 ]; then
    # Run all tests with coverage
    pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=html
else
    # Run specific tests passed as arguments
    pytest "$@"
fi

# Check test result
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    # Show coverage report location
    if [ -f "htmlcov/index.html" ]; then
        echo ""
        echo "📊 Coverage report generated at: backend/htmlcov/index.html"
        echo "   Open with: open htmlcov/index.html"
    fi
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Please review the errors above."
fi

echo ""
echo "Tips:"
echo "  • Run specific test file: ./run_tests.sh tests/test_edinet_client.py"
echo "  • Run with markers: ./run_tests.sh -m unit"
echo "  • Run with verbose: ./run_tests.sh -vv"
echo "  • Stop containers: docker-compose -f ../docker-compose.yml down"

exit $TEST_RESULT
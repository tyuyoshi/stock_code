#!/bin/bash

# Simple test runner - assumes Docker containers are already running
set -e

echo "🧪 Running tests (simple mode)"
echo "=============================="

# Check if running from backend directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the backend directory"
    exit 1
fi

# Load test environment
if [ -f ".env.test" ]; then
    export $(cat .env.test | grep -v '^#' | xargs)
    echo "✓ Loaded .env.test"
else
    echo "Warning: .env.test not found, using defaults"
    export DATABASE_URL="postgresql://stockcode:stockcode123@localhost:5432/stock_code_test"
    export REDIS_URL="redis://localhost:6379/1"
    export ENVIRONMENT="test"
    export SECRET_KEY="test_secret_key"
fi

# Install test dependencies if needed
python -c "import pytest" 2>/dev/null || pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run tests
echo ""
echo "Running tests..."

if [ $# -eq 0 ]; then
    # Run all tests
    python -m pytest tests/ -v --tb=short
else
    # Run specific tests
    python -m pytest "$@"
fi
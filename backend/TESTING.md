# Testing Guide for Stock Code Backend

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL client tools (psql, createdb)

### Running Tests

#### Option 1: Full Test Suite with Docker (Recommended)
```bash
cd backend
./run_tests.sh
```

This script will:
- Check/start Docker containers (PostgreSQL, Redis)
- Create test database if needed
- Run all tests with coverage report
- Generate HTML coverage report in `htmlcov/`

#### Option 2: Simple Test Run (Containers must be running)
```bash
# First, ensure containers are running
docker-compose up -d postgres redis

# Then run tests
cd backend
./run_tests_simple.sh
```

#### Option 3: Manual Test Run
```bash
# Start containers
docker-compose up -d postgres redis

# Set environment variables
export DATABASE_URL="postgresql://stockcode:stockcode123@localhost:5432/stock_code_test"
export REDIS_URL="redis://localhost:6379/1"
export ENVIRONMENT="test"

# Run tests
cd backend
pytest tests/ -v
```

## 📝 Test Organization

```
backend/tests/
├── test_edinet_client.py       # EDINET API client tests
├── test_xbrl_parser.py         # XBRL parser tests
├── test_financial_indicators.py # Financial calculations
├── test_data_processor.py      # Data processing logic
├── test_security.py            # Security features
└── conftest.py                 # Shared fixtures
```

## 🎯 Running Specific Tests

### Run a specific test file
```bash
./run_tests.sh tests/test_edinet_client.py
```

### Run tests by marker
```bash
# Unit tests only
./run_tests.sh -m unit

# Integration tests only
./run_tests.sh -m integration

# Skip slow tests
./run_tests.sh -m "not slow"
```

### Run a specific test class or method
```bash
# Specific class
./run_tests.sh tests/test_edinet_client.py::TestEDINETClient

# Specific method
./run_tests.sh tests/test_edinet_client.py::TestEDINETClient::test_init
```

## 📊 Coverage Reports

### Terminal Coverage Report
```bash
pytest --cov=. --cov-report=term-missing
```

### HTML Coverage Report
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Coverage Threshold
The project targets **80% code coverage**. Tests will warn if coverage falls below this threshold.

## 🏷️ Test Markers

Tests are organized with markers for different test types:

- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (may require database/API)
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.requires_db` - Tests requiring database connection
- `@pytest.mark.requires_api` - Tests requiring external API access

## 🔧 Test Configuration

### Environment Variables
Test configuration is managed through `.env.test`:

```env
DATABASE_URL=postgresql://stockcode:stockcode123@localhost:5432/stock_code_test
REDIS_URL=redis://localhost:6379/1
ENVIRONMENT=test
SECRET_KEY=test_secret_key_for_testing_only
EDINET_API_KEY=test_api_key
```

### pytest.ini Configuration
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short --strict-markers --cov=. --cov-report=term-missing
```

## 🐛 Debugging Tests

### Run with verbose output
```bash
pytest -vv
```

### Show print statements
```bash
pytest -s
```

### Drop into debugger on failure
```bash
pytest --pdb
```

### Run with detailed traceback
```bash
pytest --tb=long
```

## 🔄 Continuous Integration

Tests are automatically run on:
- Push to main/develop branches
- Pull requests
- Manual workflow dispatch

See `.github/workflows/test.yml` for CI configuration.

## 📚 Writing Tests

### Test Structure Example
```python
import pytest
from services.edinet_client import EDINETClient

class TestEDINETClient:
    @pytest.fixture
    def client(self):
        return EDINETClient(api_key="test_key")
    
    @pytest.mark.unit
    def test_init(self, client):
        assert client.api_key == "test_key"
    
    @pytest.mark.integration
    @pytest.mark.requires_api
    def test_api_call(self, client):
        # Integration test requiring API
        pass
```

### Using Fixtures
Common fixtures are defined in `conftest.py`:
- `db_session` - Database session
- `client` - FastAPI test client
- `mock_edinet_api` - Mocked EDINET API
- `sample_company_data` - Sample test data

## 🚫 Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker logs stock_code_db

# Test connection
psql -h localhost -U stockcode -d stock_code_test
```

### Import Errors
```bash
# Ensure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Permission Errors
```bash
# Make test scripts executable
chmod +x run_tests.sh run_tests_simple.sh
```

## 📈 Current Test Coverage

As of the latest run:
- **Overall Coverage**: Target 80%
- **Critical Modules**: 
  - EDINET Client: Covered
  - XBRL Parser: Covered
  - Financial Indicators: Covered
  - Data Processor: Covered
  - Security: Covered

## 🎯 Testing Best Practices

1. **Isolate Tests**: Each test should be independent
2. **Use Fixtures**: Share common setup via fixtures
3. **Mock External Dependencies**: Don't make real API calls in unit tests
4. **Test Edge Cases**: Include tests for error conditions
5. **Keep Tests Fast**: Mark slow tests appropriately
6. **Clear Test Names**: Test names should describe what they test
7. **Arrange-Act-Assert**: Follow the AAA pattern in tests
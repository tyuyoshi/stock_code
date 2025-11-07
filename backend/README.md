# Backend - Stock Code API

FastAPI-based backend service for the Stock Code financial analysis platform.

## Overview

This backend provides RESTful APIs for financial data collection, processing, and analysis of Japanese listed companies. Built with FastAPI, SQLAlchemy 2.0, and PostgreSQL.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Data Processing**: Pandas, NumPy, SciPy
- **API Clients**: EDINET API, Yahoo Finance (yfinance)
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Cache**: Redis
- **Security**: JWT authentication, Rate limiting

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Virtual environment (venv)

### Installation

**IMPORTANT**: Always use virtual environment to keep local environment clean!

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your settings
```

### Environment Variables

Required in `.env`:

```env
# Database
DATABASE_URL=postgresql://stockcode:stockcode123@localhost:5432/stockcode

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# API Keys
EDINET_API_KEY=your-edinet-api-key

# Environment
ENVIRONMENT=development
```

## Database Migration (Alembic)

We use Alembic with SQLAlchemy 2.0 for managing database schema migrations.

### Configuration

- **alembic.ini**: Main configuration file (timestamps in filenames, black formatting)
- **alembic/env.py**: Environment configuration (DATABASE_URL from .env, SQLAlchemy 2.0 mode)
- **models/__init__.py**: Aggregates all models for autogenerate

### Common Commands

Always activate virtual environment first:

```bash
source venv/bin/activate
```

#### Check Current Migration Status

```bash
alembic current
# or use our helper script
python migrations/run_migrations.py current
```

#### Create a New Migration

Auto-generate from Model Changes (Recommended):

```bash
# After modifying models
alembic revision --autogenerate -m "Add new feature"
# or
python migrations/run_migrations.py generate "Add new feature"
```

Create Empty Migration:

```bash
alembic revision -m "Custom migration"
# or
python migrations/run_migrations.py generate "Custom migration" --empty
```

#### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head
# or
python migrations/run_migrations.py upgrade

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade
alembic downgrade -1  # One revision back
alembic downgrade <revision_id>  # To specific revision
```

#### View Migration History

```bash
alembic history --verbose
# or
python migrations/run_migrations.py history
```

### Production Deployment

Generate SQL for DBA Review (Offline Mode):

```bash
# Generate SQL without executing
alembic upgrade head --sql > migration.sql
# or
python migrations/run_migrations.py upgrade --sql > migration.sql

# Review the SQL, then apply manually or via script
```

### Docker Integration

When using Docker Compose, migrations run automatically on container startup:

```bash
docker compose up  # Migrations run before server starts
```

### Migration Best Practices

1. **Always Review Auto-generated Migrations**
   - Table/column renames are detected as drop + create
   - Custom SQL functions or triggers not detected
   - Some constraint changes may be missed

2. **Test Migrations**
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

3. **Naming Conventions**
   - ✅ "Add user preferences table"
   - ✅ "Add index on company ticker_symbol"
   - ❌ "Update database"
   - ❌ "Fix stuff"

4. **Handle Existing Databases**
   ```bash
   # Mark database as up-to-date with initial migration
   alembic stamp head
   # or
   python migrations/run_migrations.py stamp head
   ```

### Migration Troubleshooting

#### Connection Issues

1. Check DATABASE_URL in .env
2. Ensure PostgreSQL is running: `docker compose ps`
3. Test connection: `python migrations/run_migrations.py check`

#### Migration Conflicts

```bash
# Check current state
alembic current
alembic history

# Resolve by merging or creating a merge revision
alembic merge -m "Merge migrations" <rev1> <rev2>
```

#### Reset Database (Development Only!)

```bash
# Drop all tables and recreate
alembic downgrade base
alembic upgrade head
```

## Running the Application

### Development Server

```bash
# With virtual environment activated
uvicorn api.main:app --reload --port 8000
```

### With Docker

```bash
docker compose up backend
```

The API will be available at http://localhost:8000

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_edinet_client.py

# Run with Docker database
./run_tests.sh
```

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_security.py     # Security tests
├── test_financial_indicators.py  # Financial calculation tests
├── test_edinet_client.py  # EDINET API tests
└── test_xbrl_parser.py  # XBRL parsing tests
```

### Current Coverage

- Overall: 78% coverage
- 93 tests total
- Key areas tested:
  - Security middleware
  - Financial indicators (60+ indicators)
  - EDINET API integration
  - XBRL parsing

## Project Structure

```
backend/
├── alembic/             # Database migrations
│   ├── versions/        # Migration files (timestamped)
│   ├── env.py          # Environment configuration
│   └── README          # Alembic info
├── api/                # API endpoints
│   ├── main.py         # FastAPI app
│   └── routers/        # API routers
├── core/               # Core configuration
│   ├── config.py       # Settings management
│   ├── database.py     # Database connection
│   └── security.py     # Security utilities
├── models/             # SQLAlchemy models
│   ├── __init__.py     # Model aggregation
│   ├── company.py      # Company model
│   └── financial.py    # Financial models
├── services/           # Business logic
│   ├── edinet_client.py    # EDINET API client
│   ├── xbrl_parser.py      # XBRL parser
│   └── data_processor.py   # Financial calculations
├── migrations/         # Migration utilities
│   └── run_migrations.py   # Helper script
├── tests/              # Test files
├── alembic.ini         # Alembic configuration
├── requirements.txt    # Python dependencies
├── pytest.ini          # Pytest configuration
└── README.md          # This file
```

## Development Guidelines

### Code Style

```bash
# Format code
black .

# Lint
flake8

# Type checking
mypy .
```

### Git Workflow

1. Create feature branch from main
2. Make changes
3. Run tests
4. Format code
5. Create PR with tests passing

### Adding New Features

1. **Models**: Add to `models/`, update `models/__init__.py`
2. **Migrations**: Run `alembic revision --autogenerate -m "Description"`
3. **API Endpoints**: Add to `api/routers/`
4. **Business Logic**: Add to `services/`
5. **Tests**: Add to `tests/`

## Security Notes

1. Never commit `.env` files with production credentials
2. Use read-only database users for generating SQL in production
3. Always backup database before applying migrations in production
4. Test migrations in staging environment first
5. Keep dependencies updated for security patches

## CI/CD Integration

For GitHub Actions:

```yaml
- name: Run migrations
  run: |
    cd backend
    source venv/bin/activate
    alembic upgrade head

- name: Run tests
  run: |
    cd backend
    source venv/bin/activate
    pytest --cov
```

## Troubleshooting

### Common Issues

- **Import errors**: Ensure virtual environment is activated
- **Database connection failed**: Check DATABASE_URL and PostgreSQL status
- **Redis connection failed**: Check REDIS_URL and Redis status
- **Port already in use**: Kill process on port 8000 or use different port

### Useful Commands

```bash
# Check PostgreSQL connection
docker compose exec postgres psql -U stockcode -d stockcode

# View logs
docker compose logs backend

# Reset database (development)
alembic downgrade base && alembic upgrade head

# Generate requirements
pip freeze > requirements.txt
```

## Yahoo Finance Integration

### Overview

Yahoo Finance integration provides real-time and historical stock price data for Japanese listed companies. The integration includes automated data collection, API endpoints, and comprehensive testing.

### Features

- **Real-time Data**: Current stock prices via Yahoo Finance API
- **Historical Data**: Up to 5+ years of historical price data
- **Japanese Stock Support**: Automatic ticker formatting (.T suffix)
- **Rate Limiting**: Built-in delays to respect API limits
- **Caching**: Redis integration for improved performance
- **Error Handling**: Comprehensive error handling and logging

### Setup and Testing

#### 1. Sample Data Creation

```bash
# Create sample companies for testing
python -c "
from core.database import SessionLocal
from models.company import Company

db = SessionLocal()
companies = [
    Company(ticker_symbol='7203', company_name_jp='トヨタ自動車株式会社'),
    Company(ticker_symbol='9984', company_name_jp='ソフトバンクグループ株式会社'),
    Company(ticker_symbol='6758', company_name_jp='ソニーグループ株式会社')
]

for company in companies:
    existing = db.query(Company).filter(Company.ticker_symbol == company.ticker_symbol).first()
    if not existing:
        db.add(company)

db.commit()
db.close()
"
```

#### 2. Historical Data Backfill

```bash
# Backfill 1 month of data for testing
python scripts/backfill_stock_prices.py --tickers 7203 --period 1mo

# Backfill multiple tickers
python scripts/backfill_stock_prices.py --tickers 7203 9984 6758 --period 1mo

# Backfill with custom date range
python scripts/backfill_stock_prices.py --tickers 7203 --start-date 2024-01-01 --end-date 2024-12-31

# Dry run to see what would be processed
python scripts/backfill_stock_prices.py --dry-run
```

#### 3. API Testing

```bash
# Start API server
uvicorn api.main:app --reload

# Run automated API tests
python test_api_manual.py

# Manual endpoint testing
curl "http://localhost:8000/api/v1/stock-prices/7203/latest"
curl "http://localhost:8000/api/v1/stock-prices/7203/historical?days=30"
curl "http://localhost:8000/api/v1/stock-prices/7203/chart?period=1mo"
curl "http://localhost:8000/api/v1/stock-prices/?tickers=7203&tickers=9984"
```

### API Endpoints

#### Stock Prices
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stock-prices/{ticker}/latest` | GET | Latest price with change calculation |
| `/api/v1/stock-prices/{ticker}/historical` | GET | Historical data with date filtering |
| `/api/v1/stock-prices/{ticker}/chart` | GET | Chart data for various periods |
| `/api/v1/stock-prices/` | GET | Multiple tickers (use `?tickers=A&tickers=B`) |

#### Companies (New - Issue #35)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/companies/` | GET | Company list with search and pagination |
| `/api/v1/companies/{id}` | GET | Company details by ID |
| `/api/v1/companies/{id}/financials` | GET | Company financial statements |
| `/api/v1/companies/{id}/indicators` | GET | Company financial indicators |
| `/api/v1/companies/` | POST | Create new company |
| `/api/v1/companies/{id}` | PUT | Update company information |
| `/api/v1/companies/{id}` | DELETE | Delete company |

#### Screening (New - Issue #35)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/screening/` | POST | Execute custom screening filters |
| `/api/v1/screening/presets` | GET | Get predefined screening presets |
| `/api/v1/screening/presets/{preset_id}` | GET | Execute preset screening |
| `/api/v1/screening/fields` | GET | Get available screening fields |

#### Company Comparison (New - Issue #35)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/compare/` | POST | Compare multiple companies |
| `/api/v1/compare/templates` | GET | Get comparison templates |
| `/api/v1/compare/templates/{template_id}` | POST | Compare using template |
| `/api/v1/compare/metrics` | GET | Get available comparison metrics |

#### Data Export (New - Issue #35)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/export/companies` | POST | Export companies data (CSV/Excel) |
| `/api/v1/export/screening` | POST | Export screening results |
| `/api/v1/export/comparison` | POST | Export comparison results |
| `/api/v1/export/financial-data` | POST | Export financial data |
| `/api/v1/export/templates` | GET | Get export templates |
| `/api/v1/export/formats` | GET | Get supported export formats |

### Daily Batch Jobs

The daily batch job automatically updates stock prices:

```bash
# Manual execution for testing
python -c "
import asyncio
from batch.daily_update import DailyUpdateJob

async def test_daily_job():
    job = DailyUpdateJob()
    await job.run()

asyncio.run(test_daily_job())
"
```

### Troubleshooting

#### yfinance Issues

```bash
# Check yfinance version (should be 0.2.66+)
python -c "import yfinance as yf; print(f'yfinance: {yf.__version__}')"

# Update if needed
pip install --upgrade yfinance

# Test individual ticker
python -c "
import yfinance as yf
ticker = yf.Ticker('7203.T')
hist = ticker.history(period='1mo')
print(f'Records: {len(hist)}')
"
```

#### Live Data Errors

- **503 errors**: Usually indicate market closure or temporary API issues
- **Timezone errors**: Market may be closed or ticker delisted
- **Rate limiting**: Increase delays in batch processing

#### Database Issues

```bash
# Check stock price data
python -c "
from core.database import SessionLocal
from models.financial import StockPrice
db = SessionLocal()
count = db.query(StockPrice).count()
print(f'Stock price records: {count}')
db.close()
"
```

### Performance Notes

- **Backfill Speed**: ~23 records/company/second
- **API Response Time**: <200ms for cached data
- **Rate Limiting**: 0.5s delay between requests
- **Memory Usage**: ~50MB for 1000+ tickers

## Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don%27t_Do_This)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
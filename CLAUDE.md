# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Stock Code is an enterprise financial analysis SaaS platform for Japanese listed companies, similar to Buffett Code. The platform collects, analyzes, and visualizes financial data from EDINET API and other sources.

## Technology Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy, PostgreSQL
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Infrastructure**: GCP (Cloud Run, Cloud SQL, Cloud Storage)
- **Data Processing**: Pandas, NumPy, yfinance
- **Containerization**: Docker & Docker Compose

## Project Structure

```
stock_code/
├── backend/           # FastAPI backend
│   ├── api/          # API endpoints and routers
│   ├── core/         # Core configuration
│   ├── models/       # SQLAlchemy models
│   ├── services/     # Business logic (EDINET client, data processor)
│   └── batch/        # Batch jobs for data updates
├── frontend/         # Next.js frontend
│   └── src/
│       ├── app/      # App Router pages
│       ├── components/ # React components
│       └── lib/      # Utilities and API clients
└── infrastructure/   # Docker and Terraform configs
```

## Common Commands

### Setup
```bash
./setup.sh              # Run initial setup
cp .env.example .env    # Configure environment
```

### Development
```bash
# With Docker
docker-compose up       # Start all services
docker-compose logs -f  # View logs

# Backend (without Docker)
cd backend
source venv/bin/activate
# Alembic初期化（初回のみ）
alembic init alembic
# データベースマイグレーション
alembic upgrade head
uvicorn api.main:app --reload

# Frontend (without Docker)
cd frontend
npm run dev
```

### Testing & Quality
```bash
# Backend
cd backend
pytest                  # Run tests (78% coverage achieved)
./run_tests.sh          # Run tests with Docker database
black .                 # Format code
flake8                  # Lint code
mypy .                  # Type checking

# Frontend
cd frontend
npm run lint            # ESLint
npm run type-check      # TypeScript check
npm run build           # Production build
```

## Key Features Implemented

1. **Data Collection**: 
   - ✅ **EDINET API integration** - Japanese financial reports (Issue #6)
   - ✅ **XBRL Parser** - Financial data extraction from EDINET (Issue #6)
   - 🔄 Yahoo Finance data fetching (planned)
2. **Data Processing**: 
   - ✅ **Basic financial indicators** - ROE, equity ratio, operating margin (Issue #6)
   - ✅ **Advanced financial indicator calculations** - 60+ indicators across 6 categories (Issue #13)
3. **API Endpoints**: Company search, screening, comparison, data export (planned)
7. **Testing Infrastructure** (Completed - 2025/11/01):
   - ✅ **Comprehensive test suite** - 91 tests with 78% coverage (Issue #32)
   - ✅ **Optimized CI/CD pipeline** - 60-80% GitHub Actions credit savings (PR #58)
   - 🔄 **Test Coverage Monitoring** - Future improvements (Issues #59-61)
4. **Frontend**: Company details, screening interface, chart visualization (planned)
5. **Batch Jobs**: Daily and quarterly data updates (planned)
6. **User Features** (New - 2025/11/01):
   - 🔄 **Google OAuth Authentication** - Replacing JWT auth (Issue #34)
   - 🔄 **Watchlist Management** - Portfolio tracking (Issue #50)
   - 🔄 **Alert Notifications** - Price & event alerts (Issue #51)
   - 🔄 **User Analytics** - Behavior tracking & recommendations (Issue #52)
   - 🔄 **Analyst Coverage** - Rating & coverage info (Issue #49)
   - 🔄 **GA4 Integration** - Marketing analytics (Issue #53)

## Development Guidelines

### When Adding New Features

1. **API Endpoints**: Add to `backend/api/routers/`, follow REST conventions
2. **Database Models**: Define in `backend/models/`, run migrations with Alembic
3. **Frontend Pages**: Use Next.js App Router in `frontend/src/app/`
4. **Data Processing**: Add to `backend/services/data_processor.py`
5. **External APIs**: Implement clients in `backend/services/`

### Best Practices

1. **Environment Variables**: Never commit `.env`, use `.env.example` as template
2. **Type Safety**: Use TypeScript in frontend, type hints in Python
3. **Error Handling**: Implement proper error handling and logging
4. **Testing**: Write tests for critical business logic
5. **Documentation**: Update API.md for new endpoints

### Security Considerations

- API keys stored in environment variables
- JWT authentication implemented
- Rate limiting configured
- SQL injection prevention via SQLAlchemy ORM
- CORS properly configured

## GitHub Integration

- **Repository**: https://github.com/tyuyoshi/stock_code
- **Issues**: 41 total issues (36 active after duplicate removal)
- **Project Board**: https://github.com/users/tyuyoshi/projects/5

### Issue Management Guidelines

**IMPORTANT**: All new issues MUST be added to the GitHub Project board immediately after creation.

```bash
# When creating a new issue, always add it to the project
gh issue create --repo tyuyoshi/stock_code --title "..." --body "..."
gh project item-add 5 --owner tyuyoshi --url https://github.com/tyuyoshi/stock_code/issues/{NUMBER}
```

### Issue Status (as of 2025/11/01 - Updated)
- **Total Issues**: 48 (Including new test-related issues)
- **Closed**: 11 (#6, #13, #17, #27, #30, #32, #33, #63, #64, #65, #66)
- **Open**: 37
- **High Priority**: #31, #34, #35, #50, #51

## External APIs Used

1. **EDINET API**: Japanese financial reports (https://disclosure.edinet-fsa.go.jp/)
2. **Yahoo Finance**: Stock price data (via yfinance library)
3. **JPX API**: Japan Exchange Group market data (optional)

## Known Issues and TODOs

### Critical Security Items (Must fix before production)
- ✅ **python-jose vulnerability** fixed (Issue #63 - Completed 2025/11/01)
- ✅ **python-multipart DoS vulnerability** fixed (Issue #64 - Completed 2025/11/01)
- ✅ **aiohttp multiple vulnerabilities** fixed (Issue #65 - Completed 2025/11/01)
- ✅ **Other dependency vulnerabilities** fixed (Issue #66 - Completed 2025/11/01)
- **Google OAuth Authentication** implementation in progress (Issue #34)

### Missing Core Features
- **Database migrations** with Alembic - setup method documented, needs env.py configuration (Issue #31)
- **Core API endpoints** for business logic (Issue #35)

### Performance & Quality Improvements (New Issues)
- **Test coverage expansion** - unit tests, error cases, edge cases (Issue #46)
- **Performance optimization** - streaming, caching, memory usage (Issue #47)  
- **Error handling standardization** - retry logic, rate limiting (Issue #48)

### Development Status
- ✅ Initial setup phase completed
- ✅ Core infrastructure in place  
- ✅ **EDINET API & XBRL Parser implemented** (Issue #6)
- ✅ **Financial indicators calculation engine** - 60+ indicators (Issue #13)
- ✅ **Security hardening completed** (Issue #30) - CORS, Rate Limiting, Security Headers
- ✅ **Test suite implementation completed** (Issue #32) - 78% coverage, 56/91 tests passing (PR #58)
- ✅ **All security vulnerabilities fixed** (Issues #63-66) - 14 Dependabot alerts resolved (PR #67, #68, #70, #71)
  - python-jose updated to 3.5.0
  - python-multipart updated to 0.0.20
  - aiohttp updated to 3.12.14
  - requests updated to 2.32.4
  - black updated to 24.3.0
  - sentry-sdk updated to 1.45.1
- 🚀 User features in planning (Issues #34, #49-53)

### Next Session Priority
1. **Database migration system** (Issue #31) - Infrastructure foundation  
2. **Google OAuth Authentication** (Issue #34) - User management base
3. **Core API endpoints** (Issue #35) - Business logic APIs
4. **Watchlist & Alert Features** (Issues #50, #51) - Core user features
5. **Test Suite Improvements** (Issues #59-61) - Extend coverage, CI/CD monitoring

## Troubleshooting

### Common Issues

- **Database connection**: Check `DATABASE_URL` in `.env`
- **Port conflicts**: Use `lsof -i :PORT` to find conflicts
- **Docker issues**: Run `docker-compose down -v` and rebuild
- **API errors**: Check logs with `docker-compose logs backend`

### Database Migrations (Alembic) ✅ Completed

**Status**: Fully configured and operational (Issue #31 completed - 2025/11/02)

**Quick Commands** (Always in virtual environment):
```bash
cd backend
source venv/bin/activate
alembic current                    # Check current migration
alembic revision --autogenerate -m "Description"  # Generate migration
alembic upgrade head                # Apply migrations
python migrations/run_migrations.py upgrade  # Helper script
```

**Configuration**:
- ✅ Alembic initialized with SQLAlchemy 2.0 support
- ✅ env.py configured with DATABASE_URL from environment (production-ready)
- ✅ All models aggregated in models/__init__.py
- ✅ Initial migration created and applied (4 tables)
- ✅ Docker integration configured (auto-migration on startup)
- ✅ Migration helper script with comprehensive CLI
- ✅ Black formatter integration for generated migrations
- ✅ Security hardened (no hardcoded credentials)
- ✅ GitHub Actions CI/CD integrated

**Implemented Tables**:
- `companies` - Company master data
- `financial_statements` - Financial reports  
- `stock_prices` - Daily stock prices
- `financial_indicators` - Calculated metrics

See `backend/README.md` for detailed documentation.
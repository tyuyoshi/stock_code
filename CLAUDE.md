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
pytest                  # Run tests
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
   - 🔄 Advanced financial indicator calculations (Issue #13)
3. **API Endpoints**: Company search, screening, comparison, data export (planned)
4. **Frontend**: Company details, screening interface, chart visualization (planned)
5. **Batch Jobs**: Daily and quarterly data updates (planned)

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
- **Issues**: 26 issues created covering all development phases
- **Project Board**: https://github.com/users/tyuyoshi/projects/5

## External APIs Used

1. **EDINET API**: Japanese financial reports (https://disclosure.edinet-fsa.go.jp/)
2. **Yahoo Finance**: Stock price data (via yfinance library)
3. **JPX API**: Japan Exchange Group market data (optional)

## Known Issues and TODOs

### Critical Security Items (Must fix before production)
- **CORS configuration** needs environment-specific settings (Issue #30)
- **Secret keys** must be generated for production (Issue #30)
- **Authentication system** not yet implemented (Issue #34)

### Missing Core Features
- **Database migrations** with Alembic - setup method documented, needs env.py configuration (Issue #31)
- **Test suite** implementation - currently ZERO coverage (Issue #32)
- **Financial indicators calculation engine** - advanced metrics and ratios (Issue #13)
- **Core API endpoints** for business logic (Issue #35)

### Performance & Quality Improvements (New Issues)
- **Test coverage expansion** - unit tests, error cases, edge cases (Issue #46)
- **Performance optimization** - streaming, caching, memory usage (Issue #47)  
- **Error handling standardization** - retry logic, rate limiting (Issue #48)

### Development Status
- ✅ Initial setup phase completed
- ✅ Core infrastructure in place  
- ✅ **EDINET API & XBRL Parser implemented** (Issue #6)
- ✅ **Basic financial indicators** calculation working
- ⚠️ Advanced business logic implementation pending
- ⚠️ Security hardening required (Issue #30)
- ⚠️ Comprehensive test suite needed (Issue #32)

### Next Session Priority
1. **Financial indicators calculation engine** (Issue #13) - High impact, builds on Issue #6
2. **Database migration system** (Issue #31) - Infrastructure foundation
3. **Daily batch jobs** (Issue #9) - Data automation, unblocked by Issue #6
4. **Test suite implementation** (Issue #32) - Quality assurance

## Troubleshooting

### Common Issues

- **Database connection**: Check `DATABASE_URL` in `.env`
- **Port conflicts**: Use `lsof -i :PORT` to find conflicts
- **Docker issues**: Run `docker-compose down -v` and rebuild
- **API errors**: Check logs with `docker-compose logs backend`

### Alembic Setup Issues

**Error: "No config file 'alembic.ini' found"**
```bash
cd backend
alembic init alembic
```

**After initialization, configure `alembic/env.py`:**
1. Set database URL from environment:
```python
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
```

2. Import and set model metadata:
```python
from models import Base
target_metadata = Base.metadata
```
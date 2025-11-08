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

**IMPORTANT**: Always use virtual environment for Python development to keep the local environment clean.

```bash
# With Docker
docker compose up       # Start all services
docker compose logs -f  # View logs

# Backend (without Docker) - ALWAYS USE VIRTUAL ENVIRONMENT
cd backend
source venv/bin/activate  # Activate virtual environment first!
# All Python commands must be run inside venv:
(venv) $ alembic init alembic  # Alembic initialization (first time only)
(venv) $ alembic upgrade head   # Database migrations
(venv) $ uvicorn api.main:app --reload  # Run server
(venv) $ pip install <package>  # Install packages
(venv) $ pytest                 # Run tests

# Frontend (without Docker)
cd frontend
npm run dev
```

### Testing & Quality
```bash
# Backend - ALWAYS IN VIRTUAL ENVIRONMENT
cd backend
source venv/bin/activate
(venv) $ pytest                  # Run tests (78% coverage achieved)
(venv) $ ./run_tests.sh          # Run tests with Docker database
(venv) $ black .                 # Format code
(venv) $ flake8                  # Lint code
(venv) $ mypy .                  # Type checking

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
   - ✅ **Yahoo Finance integration** - Real-time & historical stock prices (Issue #8, PR #75)
2. **Data Processing**: 
   - ✅ **Basic financial indicators** - ROE, equity ratio, operating margin (Issue #6)
   - ✅ **Advanced financial indicator calculations** - 60+ indicators across 6 categories (Issue #13)
3. **API Endpoints**: 
   - ✅ **Stock Price APIs** - Latest, historical, chart data endpoints (PR #75)
   - 🔄 Company search, screening, comparison, data export (planned)
7. **Testing Infrastructure** (Completed - 2025/11/01):
   - ✅ **Comprehensive test suite** - 91 tests with 78% coverage (Issue #32)
   - ✅ **Optimized CI/CD pipeline** - 60-80% GitHub Actions credit savings (PR #58)
   - 🔄 **Test Coverage Monitoring** - Future improvements (Issues #59-61)
4. **Frontend**: Company details, screening interface, chart visualization (planned)
5. **Batch Jobs**: 
   - ✅ **Daily stock price updates** - Automated Yahoo Finance data collection (PR #75)
   - 🔄 Quarterly financial data updates (planned)
6. **User Features** (New - 2025/11/01):
   - 🔄 **Google OAuth Authentication** - Replacing JWT auth (Issue #34)
   - 🔄 **Watchlist Management** - Portfolio tracking (Issue #50)
   - 🔄 **Alert Notifications** - Price & event alerts (Issue #51)
   - 🔄 **User Analytics** - Behavior tracking & recommendations (Issue #52)
   - 🔄 **Analyst Coverage** - Rating & coverage info (Issue #49)
   - 🔄 **GA4 Integration** - Marketing analytics (Issue #53)

## Development Guidelines

### Documentation Policy (IMPORTANT)

**One Directory, One README.md Rule**: 
- Each directory should have only ONE README.md file
- Do NOT create multiple markdown files (e.g., MIGRATION.md, TESTING.md, API.md)
- All documentation for a directory should be consolidated in its README.md
- Example structure:
  - `/README.md` - Project overview
  - `/backend/README.md` - All backend docs (setup, migration, testing, API)
  - `/frontend/README.md` - All frontend docs
- Exception: CLAUDE.md (this file) for Claude Code guidance only

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

### Issue Status (as of 2025/11/08 - Updated)
- **Total Issues**: 87 (After comprehensive cleanup and new feature additions)
- **Closed**: 17 (#6, #13, #17, #27, #30, #32, #33, #35, #37, #63, #64, #65, #66, #74, #80-82, #85, #88)
- **Open**: 70 
- **High Priority**: #22, #34, #83, #90 (Core development priorities)

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

### Core Features Completed
- ✅ **Database migrations** with Alembic - Fully configured and operational (Issue #31 - Completed 2025/11/02)
- ✅ **Core API endpoints** for business logic - 22 endpoints implemented (Issue #35 - PR #76 - Completed 2025/11/08)

### Performance & Quality Improvements (Active Development)
- ✅ **Stock price auto-update** - Daily batch job completed (Issue #85 - PR #92)
- ✅ **Database index optimization** - 7 indexes for query performance (Issue #88 - Completed 2025/11/08)
- **Export API completion** - Complete remaining endpoints & security (Issue #83) 🔥 HIGH PRIORITY
- **Test coverage expansion** - Error cases and edge cases (Issue #90) 🔥 HIGH PRIORITY
- **Redis cache implementation** - Cache static data (Issue #89) ⚡ MEDIUM PRIORITY
- **Comprehensive logging** - Production monitoring & debugging (Issue #84) ⚡ MEDIUM PRIORITY
- **Data freshness check** - Auto-detect stale data (Issue #86)

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
- ✅ **Yahoo Finance integration completed** (Issue #8, PR #75) - 2025/11/02
  - Complete stock price data collection system
  - 5 REST API endpoints with comprehensive testing
  - Daily batch job automation ready
  - Security hardening and performance optimization applied
- ✅ **Core API Endpoints completed** (Issue #35, PR #76) - 2025/11/08
  - 企業情報API - 7 endpoints (CRUD, financials, indicators)
  - スクリーニングAPI - 5 endpoints (filters, presets, saved searches)
  - 比較API - 5 endpoints (comparison, templates, rankings)
  - エクスポートAPI - 5 endpoints (CSV/Excel export, templates)
  - Total: 22 new endpoints with 78% test coverage
- ✅ **Automatic Stock Price Update Batch Job completed** (Issue #85) - 2025/11/08
  - Daily cron job (16:00 JST weekdays) with Docker scheduler service
  - Japanese trading calendar with holiday detection
  - Slack/Email notification system for batch results
  - Error handling and retry mechanisms (3x with exponential backoff)
  - Production-ready Cloud Scheduler configuration (Terraform)
- 🚀 User features in planning (Issues #34, #49-53)

### Next Session Priority (Updated 2025/11/08 - Post Issue #88)
1. **Frontend development start** (Issue #22) - Next.js setup, UI components 🔥
2. **Google OAuth Authentication** (Issue #34) - Unblocks user features (#50, #51, #52) 🔥
3. **Export API completion** (Issue #83) - Finish remaining endpoints (Screening, Comparison, Financial) 🔥
4. **Test coverage enhancement** (Issue #90) - Error cases & integration tests ⚡
5. **Redis cache implementation** (Issue #89) - Cache static data ⚡

### GitHub Issue Cleanup Completed (2025/11/08)
- ✅ **5 duplicate issues** closed and consolidated (#37, #74, #80-82)
- ✅ **Dependency relationships** clarified with comments and blocking notices
- ✅ **Priority labels** standardized across all issues
- ✅ **Development roadmap** optimized for efficiency

## Docker Safe Operation Guidelines ⚠️

### CRITICAL: Data Protection 

**永続化されたデータ**: 以下のボリュームには重要なデータが保存されています
- `postgres_data` - 企業マスター、財務データ、株価履歴
- `redis_data` - APIキャッシュ、セッション情報
- `scheduler_logs` - バッチ実行履歴、エラーログ

### ❌ 絶対に実行してはいけないコマンド

```bash
# データ完全消失の危険
docker system prune -a --volumes  # 全データ削除
docker volume prune                # 未使用ボリューム削除  
docker compose down -v            # ボリューム含めて削除
docker volume rm postgres_data    # データベース削除
```

### ✅ 安全な開発コマンド

```bash
# 安全なコンテナ操作
docker compose restart            # サービス再起動
docker compose stop               # 停止 (データ保持)
docker compose build --no-cache   # イメージ再ビルド
docker compose logs --tail=100    # ログ確認

# 安全なクリーンアップ  
docker image prune                # 未使用イメージのみ削除
docker container prune            # 停止コンテナのみ削除

# Scheduler操作
docker compose --profile scheduler up -d    # バッチジョブ開始
docker compose --profile scheduler down     # バッチジョブ停止
```

### 🔄 スケジューラー運用

```bash
# バッチジョブ状態確認
docker exec stock_code_scheduler crontab -l
docker compose logs scheduler

# 手動バッチ実行 (テスト用)
cd backend && source venv/bin/activate
python -m batch.daily_update
```

### 🆘 データ復旧が必要な場合

1. **即座に作業停止**
2. **バックアップ確認** (将来実装予定)
3. **Issue作成**: データ復旧の記録

## Troubleshooting

### Common Issues

- **Database connection**: Check `DATABASE_URL` in `.env`
- **Port conflicts**: Use `lsof -i :PORT` to find conflicts
- **Docker issues**: Use safe commands above, avoid `-v` flag
- **API errors**: Check logs with `docker compose logs backend`
- **Cron not working**: Check `docker compose --profile scheduler logs`

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


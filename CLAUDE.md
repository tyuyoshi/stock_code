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

# 環境変数の設定（重要）
# ⚠️ よくある間違い: backend/.env.example は存在しません
# 正しい手順: ルートの .env.example を backend/.env にコピー
cd /Users/tsuyoshi-hasegawa/Documents/workspace/github/private/stock_code
cp .env.example backend/.env
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
4. **Frontend** (Next.js Setup Completed - 2025/11/09):
   - ✅ **Next.js 14 App Router Setup** - Project foundation with TypeScript & Tailwind (Issue #22, PR #110 - Merged 2025/11/09)
     - Complete App Router structure (app/, components/, lib/)
     - Google OAuth integration (AuthContext, protected routes)
     - API client with axios interceptors and error handling
     - Responsive landing page with features section
     - Toast notification system (Radix UI)
     - ESLint, Prettier, TypeScript strict mode configured
     - Docker development environment ready
     - Production-ready security (HTTPOnly cookies, SameSite, CSRF protection)
   - 🔄 **Company Details Page** - Financial data visualization (Issue #23) - Ready to start
   - 🔄 **Screening Interface** - Advanced filtering UI (Issue #24) - Ready to start
   - 🔄 **Chart Visualization** - Interactive stock price charts (Issue #25) - Ready to start
   - 🔄 **Frontend Test Coverage** - Jest, RTL, E2E tests (Issue #111)
   - 🔄 **Error Boundaries** - Graceful error handling (Issue #112)
   - 🔄 **Performance Monitoring** - Web Vitals, analytics (Issue #113)
   - 🔄 **Code Splitting** - Bundle optimization (Issue #114)
   - 🔄 **CSP Headers** - Content Security Policy (Issue #115)
   - 🔄 **Storybook** - Component documentation (Issue #116)
5. **Batch Jobs**: 
   - ✅ **Daily stock price updates** - Automated Yahoo Finance data collection (PR #75)
   - 🔄 Quarterly financial data updates (planned)
6. **User Features** (Google OAuth Completed - 2025/11/09):
   - ✅ **Google OAuth Authentication** - Complete OAuth 2.0 flow with Redis sessions (Issue #34, PR #105 - Merged 2025/11/09)
     - Complete authentication system with CSRF protection (OAuth state parameter)
     - 5 auth endpoints: login, callback, me, profile, logout
     - Redis session management with 7-day TTL, HTTPOnly cookies
     - Role-based access control (free/premium/enterprise)
     - 19 comprehensive tests (17 passing)
     - Race condition handling for concurrent user creation
     - Production-ready security (rate limiting, error sanitization, transaction safety)
   - 🔄 **Watchlist Management** - Portfolio tracking (Issue #50) - Unblocked by Issue #34
   - 🔄 **Alert Notifications** - Price & event alerts (Issue #51) - Unblocked by Issue #34
   - 🔄 **User Analytics** - Behavior tracking & recommendations (Issue #52) - Unblocked by Issue #34
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
- Google OAuth 2.0 authentication implemented (Issue #34)
- Redis-based session management with secure cookies
- Rate limiting configured
- SQL injection prevention via SQLAlchemy ORM
- CORS properly configured
- HTTPOnly cookies for XSS protection
- Role-based access control (free/premium/enterprise)

## GitHub Integration

- **Repository**: https://github.com/tyuyoshi/stock_code
- **Issues**: 41 total issues (36 active after duplicate removal)
- **Project Board**: https://github.com/users/tyuyoshi/projects/5

### Issue Management Guidelines

**CRITICAL RULE**: All new issues MUST be added to the GitHub Project board immediately after creation.

#### Required Steps When Creating an Issue

```bash
# Step 1: Create the issue
gh issue create --repo tyuyoshi/stock_code --title "..." --body "..."

# Step 2: Get the issue number (latest created issue)
ISSUE_NUM=$(gh issue list --repo tyuyoshi/stock_code --limit 1 --json number --jq '.[0].number')

# Step 3: Add to Project board #5 (REQUIRED!)
gh project item-add 5 --owner tyuyoshi --url https://github.com/tyuyoshi/stock_code/issues/$ISSUE_NUM

# Or manually with known issue number:
gh project item-add 5 --owner tyuyoshi --url https://github.com/tyuyoshi/stock_code/issues/{NUMBER}
```

#### GitHub CLI Setup (One-time)

If you encounter permission errors, refresh authentication with required scopes:

```bash
# For reading project data
gh auth refresh -s read:project

# For adding items to project board (REQUIRED for issue creation)
gh auth refresh -s project
```

#### Verification

Check that all open issues are in the project:

```bash
# List issues in project board
gh project item-list 5 --owner tyuyoshi --format json --limit 1000 | jq '[.items[].content.number] | sort'

# List all open issues
gh issue list --repo tyuyoshi/stock_code --limit 1000 --json number --state open --jq '[.[].number] | sort'
```

### Issue Status (as of 2025/11/09 - Frontend foundation completed)

- **Total Issues**: 116 total
- **Closed**: 31 (#2, #6, #8, #13, #16, #17, #18, #19, #20, #21, #22, #27, #30, #32, #33, #34, #35, #36, #37, #59, #63, #64, #65, #66, #74, #80-82, #83, #85, #88)
  - **Issue #22 completed**: Next.js 14 App Router setup (PR #110 - Merged 2025/11/09) - Frontend foundation established
  - **Issue #34 merged**: Google OAuth 2.0 implementation (PR #105 - Merged 2025/11/09)
  - **Issue cleanup**: 8 duplicate/completed issues closed - 2025/11/09
- **Open**: 85
- **High Priority**: #23-25 (Frontend UI pages), #50 (Watchlist), #90 (Test coverage), #100 (Audit logging)
- **New Issues** (2025/11/09 - PR #110 review follow-ups):
  - #111 (Frontend test coverage - Jest, RTL, E2E)
  - #112 (React Error Boundaries)
  - #113 (Code splitting & bundle optimization)
  - #114 (CSP headers)
  - #115 (Storybook component documentation)
  - #99 (Performance and load testing - Issue #83 follow-up)
  - #100 (Audit logging - Issue #83 follow-up)
  - #101 (Export history tracking - Issue #83 follow-up, optional)

## External APIs Used

1. **EDINET API**: Japanese financial reports (https://disclosure.edinet-fsa.go.jp/)
2. **Yahoo Finance**: Stock price data (via yfinance library)
3. **JPX API**: Japan Exchange Group market data (optional)
4. **Google OAuth 2.0**: User authentication (Google Identity Platform)

## Google OAuth 開発環境設定

**GCPプロジェクト**: `stock-code-dev`  
**作成日**: 2025-11-08  
**用途**: ローカル開発・動作確認

### OAuth Client設定
- **アプリケーションの種類**: ウェブアプリケーション
- **承認済みリダイレクトURI**: `http://localhost:8000/api/v1/auth/google/callback`
- **クライアントID**: `120481795465-1jn41flhq5t3m0f3of03huesokf2h380.apps.googleusercontent.com`
- **クライアントシークレット**: `backend/.env` に記載（Git管理外）

### 環境変数設定
```bash
# backend/.env に以下を設定
GOOGLE_CLIENT_ID=120481795465-1jn41flhq5t3m0f3of03huesokf2h380.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=（Google Consoleから取得したシークレット）
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

詳細な設定手順は `backend/README.md` の「Google OAuth 2.0 認証設定」セクションを参照

## Dependency Updates

### PR #108: authlib 1.6.5 Security Update
**Status**: ⏸️ **Blocked by CI/CD configuration** (Issue #109)

**Dependency**: authlib 1.3.0 → 1.6.5

**Security Fixes**:
- DoS vulnerability fixes (JWE/JWS size limits)
- CVE fixes for JOSE libraries
- Security improvements from 7 releases (1.3.0 → 1.6.5)

**Blocker**: GitHub Actions環境でOAuth認証情報未設定
- `GOOGLE_CLIENT_ID` と `GOOGLE_CLIENT_SECRET` がCI/CD環境で必要
- PR #105 (Google OAuth実装) で追加された起動時検証により、環境変数未設定でテスト失敗

**Next Action**: 
1. Issue #109 を解決 (GitHub Secrets設定 or テスト環境で検証スキップ)
2. CI/CD グリーン確認
3. PR #108 マージ

**関連**:
- Issue #109: Fix CI/CD environment for OAuth credentials
- Issue #34: Google OAuth 2.0 認証実装 (完了)
- PR #105: Google OAuth実装 (マージ済み - 2025/11/09)

## Known Issues and TODOs

### Critical Security Items (Must fix before production)
- ✅ **python-jose vulnerability** fixed (Issue #63 - Completed 2025/11/01)
- ✅ **python-multipart DoS vulnerability** fixed (Issue #64 - Completed 2025/11/01)
- ✅ **aiohttp multiple vulnerabilities** fixed (Issue #65 - Completed 2025/11/01)
- ✅ **Other dependency vulnerabilities** fixed (Issue #66 - Completed 2025/11/01)
- ⏸️ **authlib security update** blocked (Issue #109 - PR #108 waiting for CI/CD fix)

### Core Features Completed
- ✅ **Database migrations** with Alembic - Fully configured and operational (Issue #31 - Completed 2025/11/02)
- ✅ **Core API endpoints** for business logic - 22 endpoints implemented (Issue #35 - PR #76 - Completed 2025/11/08)

### Performance & Quality Improvements (Active Development)

- ✅ **Stock price auto-update** - Daily batch job completed (Issue #85 - PR #92)
- ✅ **Database index optimization** - 7 indexes for query performance (Issue #88 - Completed 2025/11/08)
- ✅ **Export API completion** - 3 export endpoints with security hardening (Issue #83 - PR #97 - Completed 2025/11/08)
- **Test coverage expansion** - Error cases and edge cases (Issue #90) 🔥 HIGH PRIORITY
- **Audit logging for exports** - Security and compliance (Issue #100) 🔥 HIGH PRIORITY
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
- ✅ **Automatic Stock Price Update Batch Job completed** (Issue #85, PR #92) - 2025/11/08
  - Daily cron job (16:00 JST weekdays) with Docker scheduler service
  - Japanese trading calendar with holiday detection
  - Slack/Email notification system for batch results
  - Error handling and retry mechanisms (3x with exponential backoff)
  - Production-ready Cloud Scheduler configuration (Terraform)
- ✅ **Database Index Optimization completed** (Issue #88, PR #93) - 2025/11/08
  - 7 strategic performance indexes for query optimization
  - Screening API target: 40ms → 20ms (50% improvement)
  - Comprehensive test suite with security hardening
  - SQLAlchemy parameterized queries (SQL injection prevention)
  - Follow-up issues created: #94 (test reliability), #95 (query validation), #96 (production monitoring)
- ✅ **Export API Implementation completed** (Issue #83, PR #97) - 2025/11/08
  - 3 export endpoints: Screening, Comparison, Financial Data
  - CSV/Excel format support with Japanese character encoding (UTF-8 BOM)
  - Security: Field injection protection, N+1 query fix, parameterized queries
  - 12 comprehensive test cases with 78% coverage maintained
  - Follow-up issues created: #98 (code quality), #99 (performance testing), #100 (audit logging), #101 (export history)
- ✅ **Google OAuth Authentication completed** (Issue #34, PR #105) - Merged 2025/11/09
  - Complete OAuth 2.0 flow with Google Identity Platform
  - User model with investment profile (experience, style, industries)
  - Redis-based session management (7-day TTL, secure cookies)
  - Authentication middleware with role-based access control (free/premium/enterprise)
  - 5 auth endpoints: login, callback, me, profile update, logout
  - 19 comprehensive tests (17 passing, 2 skipped)
  - Production-ready security features:
    - CSRF protection with OAuth state parameter (5-min TTL, one-time use)
    - Rate limiting (5 req/min on auth endpoints)
    - Error sanitization (generic client messages, detailed server logs)
    - Transaction safety with rollback
    - Race condition handling for concurrent user creation
    - HTTPOnly cookies with SameSite=lax
    - Email verification enforcement
  - Unblocked Issues: #50 (Watchlist), #51 (Alerts), #52 (Analytics), #100 (Audit logging)
- 🚀 User features ready for development (Issues #50-53)

### Next Session Priority (Updated 2025/11/09 - After issue cleanup)

**Phase 1: Frontend Foundation** (1-2 weeks) 🔥
1. **Issue #22**: Next.js setup - App Router, auth context, protected routes

**Phase 2: User Features** (2-3 weeks) 🔥  
2. **Issue #50**: Watchlist Management - Database models, CRUD API, UI (Unblocked by #34)
3. **Issue #100**: Audit logging - Export operations tracking, compliance (Unblocked by #34)

**Phase 3: Quality & Engagement** (1-2 weeks) ⚡
4. **Issue #90**: Test coverage enhancement - Integration tests, error cases (78% → 90%+)
5. **Issue #51**: Alert Notifications - Price alerts, email/app notifications (Unblocked by #34)

### GitHub Issue Cleanup History

**2025/11/09 Cleanup**:
- ✅ **8 duplicate/completed issues** closed (#2, #8, #16, #18-21, #36, #59)
- ✅ **Dependency relationships** clarified for user features (#50, #51, #52, #100)
- ✅ **Priority labels** updated for next development phase (#22, #50, #100 → HIGH)
- ✅ **Total reduction**: 101 issues → 72 open (29% reduction)

**2025/11/08 Cleanup**:
- ✅ **5 duplicate issues** closed and consolidated (#37, #74, #80-82)
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


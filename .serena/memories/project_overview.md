# Stock Code - Project Overview

## Purpose

Stock Code is an enterprise financial analysis SaaS platform for Japanese listed companies, similar to Buffett Code. The platform collects, analyzes, and visualizes financial data from EDINET API and other sources.

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Cache & Sessions**: Redis (with session management & rate limiting)
- **Data Processing**: Pandas, NumPy, yfinance
- **Authentication**: Google OAuth 2.0, authlib 1.6.5, Redis sessions
- **XBRL Processing**: python-xbrl, lxml
- **Testing**: pytest (91 tests, 78% coverage)
- **Monitoring**: Sentry SDK

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Data Fetching**: axios with interceptors
- **UI Components**: Radix UI (Toast notifications)
- **Real-time**: WebSocket client with auto-reconnection
- **Authentication**: Google OAuth integration, protected routes

### Infrastructure
- **Platform**: GCP (Cloud Run, Cloud SQL, Cloud Storage) - Planned
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions (optimized for 60-80% cost savings)
- **Batch Jobs**: Docker scheduler with cron

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

## Key Features Implemented (as of 2025/11/16)

### Data Collection & Processing ✅
- EDINET API integration with XBRL parser
- Yahoo Finance API integration with Token Bucket rate limiting
- 60+ financial indicators calculation engine
- Daily batch job for stock price updates

### Backend APIs ✅
- 22 core API endpoints (company, screening, comparison, export)
- Google OAuth 2.0 authentication with RBAC
- Watchlist management with plan-based limits
- WebSocket endpoint for real-time price streaming
- Redis-based rate limiting and session management

### Frontend ✅
- Next.js 14 App Router foundation
- Google OAuth integration with protected routes
- WebSocket client with auto-reconnection
- Real-time price updates UI
- Toast notification system

### Testing & Quality ✅
- 91 tests with 78% coverage
- Optimized CI/CD pipeline
- Database index optimization (50% query improvement)
- Security hardening (CORS, rate limiting, CSRF protection)

### Infrastructure ✅
- Docker & Docker Compose development environment
- Database migrations with Alembic
- Batch job scheduler with Docker
- Safe operation guidelines for data protection

## External APIs

1. **EDINET API**: Japanese financial reports (https://disclosure.edinet-fsa.go.jp/)
2. **Yahoo Finance**: Stock price data (via yfinance library)
3. **JPX API**: Japan Exchange Group market data (optional)
4. **Google OAuth 2.0**: User authentication (Google Identity Platform)

## Development Status

### Current Phase: Frontend Development & Quality Enhancement

**Active Development**:
- Company details page (Issue #23)
- Screening interface (Issue #24)
- Test coverage expansion to 90%+ (Issue #90)
- Audit logging for exports (Issue #100)

**Deployment Strategy**:
- Deploy after MVP features complete (Issues #23, #24, #90, #100)
- Target: GCP infrastructure ($23-34/month)
- Timeline: After core frontend pages implemented

## GitHub Repository

- **URL**: https://github.com/tyuyoshi/stock_code
- **Project Board**: https://github.com/users/tyuyoshi/projects/5
- **Issues**: 152 total (86 open, 66 closed)

## Documentation

- **CLAUDE.md**: Claude Code guidance (compressed from 954 → 395 lines)
- **backend/README.md**: Backend setup, API docs, testing
- **frontend/README.md**: Frontend development, WebSocket testing (520+ lines)
- **Serena Memories**: Archived sessions, issue cleanup history, development principles

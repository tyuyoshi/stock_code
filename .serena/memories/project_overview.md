# Stock Code - Project Overview

## Purpose
Stock Code is an enterprise financial analysis SaaS platform for Japanese listed companies, similar to Buffett Code. The platform collects, analyzes, and visualizes financial data from EDINET API and other sources.

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Data Processing**: Pandas, NumPy, SciPy
- **API Clients**: requests, aiohttp, yfinance
- **Authentication**: python-jose, passlib
- **XBRL Processing**: python-xbrl, lxml
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Task Queue**: Celery (optional)
- **Cache**: Redis
- **Monitoring**: Sentry SDK

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: @tanstack/react-query
- **Charts**: Chart.js, Recharts
- **Forms**: react-hook-form with Zod validation
- **UI Components**: Radix UI

### Infrastructure
- **Platform**: GCP (Cloud Run, Cloud SQL, Cloud Storage)
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

## External APIs
1. **EDINET API**: Japanese financial reports (https://disclosure.edinet-fsa.go.jp/)
2. **Yahoo Finance**: Stock price data (via yfinance library)
3. **JPX API**: Japan Exchange Group market data (optional)
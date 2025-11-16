# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Stock Code is an enterprise financial analysis SaaS platform for Japanese listed companies, similar to Buffett Code. The platform collects, analyzes, and visualizes financial data from EDINET API and other sources.

## Language Guidelines / 言語ガイドライン

### Development Language / 開発言語

**IMPORTANT**: Claude Code must follow these language rules for consistency and team collaboration.

- **Thinking/Design/Coding**: **English** (英語で思考・設計・コーディング)
  - Internal reasoning, architecture design, code implementation
  - All code (functions, classes, variables) in English
  - Code comments in English

- **Documentation/Reports**: **Japanese** (日本語でドキュメント・レポート作成)
  - Session reports and progress updates to the user
  - Documentation files (README.md sections for Japanese users)
  - User-facing explanations and summaries

- **GitHub Issues/PRs**: **Japanese** (日本語でIssue・PR作成)
  - Issue titles, descriptions, and comments
  - Pull request titles, descriptions, and comments
  - Commit messages

- **Code Comments**: **English** (コード内コメントは英語)
  - Inline comments, docstrings, type hints

### Examples / 例

✅ **Correct**:
```python
# Code in English
def calculate_financial_indicators(company_data: dict) -> dict:
    """Calculate ROE, ROA, and other financial indicators."""
    return indicators
```

```markdown
Issue Title: 機能: 財務指標計算機能の実装
PR Title: 修正: WebSocketメモリリークの解消 (#125)
Commit: feat: 企業詳細ページのUI実装
```

❌ **Incorrect**:
```python
# Mixing languages in code
def 財務指標計算(company_data):  # Wrong: Function name in Japanese
    """ROEとROAを計算する"""  # Wrong: Docstring in Japanese
```

```markdown
Issue Title: Implement Financial Indicators Calculation  # Wrong: English title
Commit: Implement company details page UI  # Wrong: English commit
```

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
cp .env.example backend/.env  # Copy environment variables (IMPORTANT!)
```

### Development

**IMPORTANT**: Always use virtual environment for Python development.

```bash
# Docker
docker compose up       # Start all services
docker compose logs -f  # View logs

# Backend - ALWAYS IN VIRTUAL ENVIRONMENT
cd backend && source venv/bin/activate
(venv) $ alembic upgrade head   # Database migrations
(venv) $ uvicorn api.main:app --reload  # Run server
(venv) $ pytest                 # Run tests (78% coverage)

# Frontend
cd frontend && npm run dev
```

### Testing & Quality
```bash
# Backend (in venv)
pytest                  # Run tests
./run_tests.sh          # Tests with Docker DB
black . && flake8       # Format & lint
mypy .                  # Type checking

# Frontend
npm run lint            # ESLint
npm run type-check      # TypeScript
npm run build           # Production build
```

## Key Features Status

### Completed ✅
1. **Data Collection**: EDINET API integration, XBRL Parser, Yahoo Finance integration (Issues #6, #8)
2. **Data Processing**: 60+ financial indicators calculation engine (Issue #13)
3. **API Endpoints**: 22 core APIs (company, screening, comparison, export) (Issue #35)
4. **Testing**: 91 tests, 78% coverage, optimized CI/CD (Issue #32)
5. **Frontend Foundation**: Next.js 14 App Router, Google OAuth, API client (Issue #22, PR #110)
6. **User Authentication**: Google OAuth 2.0 with Redis sessions, RBAC (Issue #34, PR #105)
7. **Watchlist Management**: Portfolio tracking with plan-based limits (Issue #50, PR #121)
8. **WebSocket Real-time**: Live stock price streaming with centralized broadcasting (Issues #117, #125)
9. **Rate Limiting**: Token Bucket algorithm for Yahoo Finance API (Issue #126, PR #133)
10. **Frontend WebSocket Client**: Real-time UI with auto-reconnection (Issue #123, PR #142)
11. **Batch Jobs**: Daily stock price auto-update with scheduler (Issue #85)
12. **Performance**: Database index optimization, 50% query improvement (Issue #88)
13. **Data Initialization Scripts**: 4 scripts for loading initial company data (Issue #149, PR #157)

### In Progress 🔄
- **Issue #23**: Company Details Page - Ready to start (frontend foundation complete)
- **Issue #24**: Screening Interface - Ready to start (backend APIs available)
- **Issue #90**: Test coverage expansion to 90%+ (HIGH PRIORITY)
- **Issue #100**: Audit logging for exports (HIGH PRIORITY)

### Planned 📋
- Chart visualization (Issue #25)
- Alert notifications (Issue #51)
- User analytics (Issue #52)
- Portfolio analysis API (Issue #118)
- Frontend testing suite (Issue #111)

## Development Guidelines

### Documentation Policy

**One Directory, One README.md Rule**:
- Each directory has only ONE README.md file
- Do NOT create multiple markdown files (MIGRATION.md, TESTING.md, etc.)
- Exception: CLAUDE.md (this file) for Claude Code guidance

### When Adding New Features

1. **API Endpoints**: Add to `backend/api/routers/`, follow REST conventions
2. **Database Models**: Define in `backend/models/`, run Alembic migrations
3. **Frontend Pages**: Use Next.js App Router in `frontend/src/app/`
4. **Data Processing**: Add to `backend/services/data_processor.py`
5. **External APIs**: Implement clients in `backend/services/`

### Best Practices

1. **Environment Variables**: Never commit `.env`, use `.env.example` as template
2. **Type Safety**: Use TypeScript in frontend, type hints in Python
3. **Error Handling**: Implement proper error handling and logging
4. **Testing**: Write tests for critical business logic

## GitHub Integration

- **Repository**: https://github.com/tyuyoshi/stock_code
- **Project Board**: https://github.com/users/tyuyoshi/projects/5
- **Total Issues**: 152 (85 open, 67 closed)
- **Milestones**: 3 active (MVP, Infrastructure, Monetization)

### Issue Management Guidelines

**CRITICAL RULE**: All new issues MUST be added to Project board #5 immediately after creation.

```bash
# Create issue and add to project
gh issue create --repo tyuyoshi/stock_code --title "..." --body "..."
ISSUE_NUM=$(gh issue list --limit 1 --json number --jq '.[0].number')
gh project item-add 5 --owner tyuyoshi --url https://github.com/tyuyoshi/stock_code/issues/$ISSUE_NUM
```

**GitHub CLI Setup** (one-time):
```bash
gh auth refresh -s read:project
gh auth refresh -s project
```

### GitHub Workflow Rules (Cost Optimization) ⚠️

**IMPORTANT**: Minimize GitHub Actions costs by following these rules:

1. **Always Create PRs as Draft**
   ```bash
   gh pr create --draft --title "..." --body "..."  # CORRECT
   ```

2. **User Confirms Before "Ready for Review"**
   - Keep PR as Draft until user explicitly approves
   - User tests locally first
   ```bash
   gh pr ready  # After user approval
   ```

3. **Keep Commits Local Until User Says "Push"**
   ```bash
   git add . && git commit -m "..."
   # WAIT for user to say "push して"
   git push origin <branch>  # After approval
   ```

4. **Rationale**:
   - Draft PRs don't trigger workflows → cost savings
   - Local testing catches issues before CI/CD
   - User controls when automation runs

**Common Mistakes to Avoid**:
- ❌ Push immediately after commit → ✅ Wait for user approval
- ❌ Create ready-for-review PRs → ✅ Always start with drafts
- ❌ Force-push repeatedly → ✅ Get commits right locally first

See `.serena/memories/github_workflow_rules.md` for detailed workflow examples.

## External APIs

1. **EDINET API**: Japanese financial reports (https://disclosure.edinet-fsa.go.jp/)
2. **Yahoo Finance**: Stock price data (via yfinance library)
3. **JPX API**: Japan Exchange Group market data (optional)
4. **Google OAuth 2.0**: User authentication (Google Identity Platform)

## Google OAuth 開発環境設定

**GCPプロジェクト**: `stock-code-dev`
**OAuth Client**:
- **クライアントID**: `120481795465-1jn41flhq5t3m0f3of03huesokf2h380.apps.googleusercontent.com`
- **リダイレクトURI**: `http://localhost:8000/api/v1/auth/google/callback`
- **シークレット**: `backend/.env` に記載（Git管理外）

詳細は `backend/README.md` の「Google OAuth 2.0 認証設定」を参照

## Recent Major Updates

### Completed PRs (2025/11 - See archived_sessions_2025_11.md for details)
- ✅ PR #116: authlib 1.6.5 security update (2025/11/09)
- ✅ PR #142: Frontend WebSocket client (2025/11/16)
- ✅ PR #157: Initial data loading scripts (2025/11/16)

### Active Development Focus
- **Performance & Quality**: Test coverage (Issue #90), Audit logging (Issue #100)
- **Core Frontend Pages**: Company details (#23), Screening UI (#24)
- **Real-time Features**: Portfolio analysis API (#118), WebSocket monitoring (#124)

### Deployment Status
- **Current**: Development environment only
- **Strategy**: Defer infrastructure deployment until MVP features complete
- **Target**: GCP (Cloud Run, Cloud SQL, Redis Memorystore) - $23-34/month
- **Timeline**: After Issues #23, #24, #90, #100 complete

See deployment section below for full infrastructure plan.

## Active Development Priorities

**Milestones Established (2025/11/16)**:

1. **MVP - Production Launch** (Due: 2025/12/31) - 7 issues
2. **Cloud Infrastructure - Phase 1** (Due: 2025/12/15) - 4 issues
3. **Monetization & Growth** (Due: 2026/03/31) - 4 issues

### Week 1-2: MVP Development (最優先)

- #149: 初期企業データ1000社投入 [high-priority, MVP milestone]
- #23: 企業詳細ページ実装 [high-priority, MVP milestone]
- #24: スクリーニング画面実装 [high-priority, MVP milestone]
- #150: 企業検索ページ実装 [medium-priority, MVP milestone]

### Week 3-4: Quality & Compliance

- #90: テストカバレッジ90%+ [high-priority, MVP milestone]
- #100: 監査ログ実装 [high-priority, MVP milestone]

### Week 5-6: Infrastructure & Deployment

- #136-138, #4: GCPインフラ構築 [high-priority, Infrastructure milestone]
- #139: CI/CDパイプライン構築 [high-priority, MVP milestone]

### Week 7-8: Production Launch

- Staging環境テスト
- Production環境公開

## Docker Safe Operation Guidelines ⚠️

### CRITICAL: Data Protection

**永続化されたデータ**:
- `postgres_data` - 企業マスター、財務データ、株価履歴
- `redis_data` - APIキャッシュ、セッション情報
- `scheduler_logs` - バッチ実行履歴、エラーログ

### ❌ 絶対に実行してはいけないコマンド

```bash
docker system prune -a --volumes  # 全データ削除 - DANGER!
docker volume prune               # 未使用ボリューム削除 - DANGER!
docker compose down -v            # ボリューム含めて削除 - DANGER!
```

### ✅ 安全な開発コマンド

```bash
# コンテナ操作
docker compose restart            # サービス再起動
docker compose stop               # 停止 (データ保持)
docker compose build --no-cache   # イメージ再ビルド
docker compose logs --tail=100    # ログ確認

# クリーンアップ (安全)
docker image prune                # 未使用イメージのみ削除
docker container prune            # 停止コンテナのみ削除

# Scheduler操作
docker compose --profile scheduler up -d    # バッチジョブ開始
docker compose --profile scheduler down     # バッチジョブ停止
```

## Troubleshooting

### Common Issues

- **Database connection**: Check `DATABASE_URL` in `backend/.env`
- **Port conflicts**: Use `lsof -i :PORT` to find conflicts
- **Docker issues**: Use safe commands above, avoid `-v` flag
- **API errors**: Check logs with `docker compose logs backend`

### Database Migrations (Alembic)

**Status**: Fully configured (Issue #31 completed)

```bash
cd backend && source venv/bin/activate
alembic current                    # Check current migration
alembic revision --autogenerate -m "Description"  # Generate
alembic upgrade head               # Apply migrations
```

See `backend/README.md` for detailed documentation.

## Deployment Roadmap (GCP Infrastructure)

### Strategy: Defer Until MVP Features Complete

**Decision** (2025/11/09): Deploy after high-priority features (#23, #24, #90, #100) complete.

### Deployment Issues Created

### Phase 1: Critical Infrastructure

(~$23-33/month)

- **#136**: Cloud SQL (PostgreSQL) - $7-9/month
- **#137**: Redis Memorystore - $6-12/month
- **#138**: Secret Manager - $0/month
- **#4**: Cloud Run (Backend API) - $8-10/month

### Phase 2: DevOps & Observability

- **#139**: CI/CD Pipeline (Cloud Build + GitHub Actions) - ~$0.50/month
- **#140**: Monitoring & Logging - $0-2/month

### Phase 3: Cost Optimization

(Future)

- **#141**: Budget alerts, resource optimization

**Total Estimated Cost**: $23-34/month

### Infrastructure Stack (Terraform-managed)

- **Compute**: Cloud Run, Cloud Scheduler, Cloud Build + GitHub Actions
- **Data**: Cloud SQL (PostgreSQL), Redis Memorystore, Cloud Storage
- **Security**: Secret Manager, Cloud Logging, Cloud Monitoring, Error Reporting
- **Networking**: VPC peering, Cloud CDN (future), Cloud Armor (future)

### Timeline & Rationale

- **Current**: Development environment only
- **Deploy**: After MVP features complete (Issues #23, #24, #90, #100)

**Rationale**:

- 🚀 Faster time-to-market: Features before infrastructure
- 📊 Data-driven decisions: User feedback before scaling
- 💰 Cost efficiency: Avoid premature infrastructure spend
- 🔄 Iterative approach: Deploy when MVP ready

### Risk Mitigation

- **Risks**: No staging, no DR, no HA initially (acceptable for MVP)
- **Mitigations**: 78% test coverage, monitoring & alerting, easy rollback (Cloud Run revisions, Terraform state)

---

**Historical Reference**: For completed session details, see `.serena/memories/archived_sessions_2025_11.md` and `.serena/memories/issue_cleanup_history.md`

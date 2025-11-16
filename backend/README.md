# Backend - Stock Code API

FastAPIベースのバックエンドサービス。日本の上場企業の財務データ収集・処理・分析APIを提供します。

## 技術スタック

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Cache**: Redis (sessions, rate limiting)
- **Authentication**: Google OAuth 2.0
- **Data Sources**: EDINET API, Yahoo Finance
- **Testing**: pytest, 78% coverage

## セットアップ

### 前提条件

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### インストール

**重要**: 必ず仮想環境を使用してください！

```bash
# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp ../env.example .env
# .env を編集して設定を行う
```

### 環境変数

`.env` ファイルに以下を設定:

```env
# Database
DATABASE_URL=postgresql://stockcode:stockcode123@localhost:5432/stockcode

# Redis
REDIS_URL=redis://localhost:6379/0

# Google OAuth 2.0
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Session
SESSION_SECRET_KEY=（python -c "import secrets; print(secrets.token_urlsafe(32))" で生成）
SESSION_EXPIRE_DAYS=7

# Yahoo Finance Rate Limiting
YAHOO_FINANCE_MAX_TOKENS=100
YAHOO_FINANCE_REFILL_RATE=0.5  # 30 requests/min
```

## Google OAuth 2.0 設定

### 1. Google Cloud Console

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを作成（例: `stock-code-dev`）
3. **APIs & Services** > **認証情報** > **+ 認証情報を作成** > **OAuth クライアント ID**
4. 同意画面の設定:
   - ユーザータイプ: **外部**
   - アプリ名: Stock Code
5. アプリケーションの種類: **ウェブアプリケーション**
6. 承認済みのリダイレクトURI:
   ```
   http://localhost:8000/api/v1/auth/google/callback
   ```
7. **作成** → クライアントIDとシークレットをコピー

### 2. 環境変数に設定

```bash
# .env に追加
GOOGLE_CLIENT_ID=あなたのクライアントID
GOOGLE_CLIENT_SECRET=あなたのクライアントシークレット

# セッション秘密鍵を生成
python -c "import secrets; print(f'SESSION_SECRET_KEY={secrets.token_urlsafe(32)}')"
```

### 3. 動作確認

```bash
# Services起動
docker compose up postgres redis -d

# Backend起動
source venv/bin/activate
alembic upgrade head
uvicorn api.main:app --reload

# ブラウザでテスト
# http://localhost:8000/api/v1/auth/google/login にアクセス
```

## データベースマイグレーション

```bash
source venv/bin/activate

# 現在のバージョン確認
alembic current

# マイグレーション作成
alembic revision --autogenerate -m "説明文"

# マイグレーション適用
alembic upgrade head

# ロールバック
alembic downgrade -1
```

## データ初期化

### スクリプト一覧

| スクリプト | 説明 |
|-----------|------|
| `init_companies.py` | 企業マスターデータ投入 |
| `fetch_financials.py` | 財務データ取得・投入 |
| `fetch_stock_prices.py` | 株価データ取得・投入 |
| `calculate_indicators.py` | 財務指標計算 |

### 使用方法

```bash
source venv/bin/activate

# 1. サンプルデータ生成（開発用）
python -m scripts.init_companies --generate-sample --sample-count 10
python -m scripts.init_companies --csv companies_sample.csv

python -m scripts.fetch_financials --generate-sample
python -m scripts.fetch_financials --csv financials_sample.csv

python -m scripts.fetch_stock_prices --generate-sample
python -m scripts.fetch_stock_prices --csv stock_prices_sample.csv

# 2. 財務指標計算
python -m scripts.calculate_indicators

# 3. Yahoo Financeから株価取得（本番用）
python -m scripts.fetch_stock_prices --yahoo \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --rate-limit-delay 0.5
```

### Dockerを使用

```bash
# プロジェクトルートで実行
docker compose run --rm init_data python -m scripts.init_companies --generate-sample
docker compose run --rm init_data python -m scripts.init_companies --csv companies_sample.csv
docker compose run --rm init_data python -m scripts.calculate_indicators
```

## テスト

```bash
source venv/bin/activate

# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=. --cov-report=html

# 特定のテストのみ
pytest tests/test_auth.py

# HTMLレポート確認
open htmlcov/index.html  # macOS
```

## 開発

### コード品質

```bash
# Formatting & Linting
black .
flake8
mypy .
```

### Yahoo Finance レート制限

Token Bucket アルゴリズムで Yahoo Finance API のレート制限を管理:

- **容量**: 100 tokens
- **補充率**: 0.5 tokens/秒（30 requests/分）
- **バックエンド**: Redis（複数インスタンス対応）

設定は `.env` の `YAHOO_FINANCE_*` 変数で調整可能。

### API ドキュメント

サーバー起動後:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## トラブルシューティング

### OAuth エラー: "redirect_uri_mismatch"
- Google Console と `.env` の `GOOGLE_REDIRECT_URI` が完全一致しているか確認

### "Session service unavailable"
```bash
# Redis起動確認
docker ps | grep redis
docker compose up redis -d
```

### "Not authenticated"
```bash
# Redisのセッション確認
docker exec stock_code_redis redis-cli GET session:あなたのトークン
```

### データベース接続エラー
```bash
# PostgreSQL起動確認
docker ps | grep postgres
docker compose up postgres -d
```

## プロジェクト構成

```
backend/
├── api/              # FastAPI application & routers
├── core/             # Configuration, database, auth, sessions
├── models/           # SQLAlchemy models
├── services/         # Business logic (EDINET, Yahoo Finance, etc)
├── schemas/          # Pydantic schemas
├── batch/            # Batch jobs
├── tests/            # Test code (78% coverage)
├── alembic/          # Database migrations
└── requirements.txt  # Dependencies
```

## セキュリティ

- ✅ `.env` は Git 管理外
- ✅ HTTPOnly Cookie で XSS 対策
- ✅ SameSite Cookie で CSRF 対策
- ✅ Parameterized queries で SQL injection 対策

## 関連ドキュメント

- **プロジェクト全体**: [`/CLAUDE.md`](../CLAUDE.md)
- **フロントエンド**: [`/frontend/README.md`](../frontend/README.md)
- **バッチジョブ**: [`/backend/batch/README.md`](./batch/README.md)

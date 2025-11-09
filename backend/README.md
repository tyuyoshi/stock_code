# Backend - Stock Code API

FastAPIベースのバックエンドサービス。日本の上場企業の財務データ収集・処理・分析APIを提供します。

## 概要

このバックエンドは、日本の上場企業に関する財務データの収集、処理、分析のためのRESTful APIを提供します。FastAPI、SQLAlchemy 2.0、PostgreSQLで構築されています。

## 技術スタック

- **フレームワーク**: FastAPI (Python 3.11+)
- **データベース**: PostgreSQL with SQLAlchemy ORM
- **マイグレーション**: Alembic
- **データ処理**: Pandas, NumPy, SciPy
- **APIクライアント**: EDINET API, Yahoo Finance (yfinance)
- **認証**: Google OAuth 2.0, Redis Session Management
- **テスト**: pytest, pytest-asyncio, pytest-cov
- **キャッシュ**: Redis
- **セキュリティ**: OAuth 2.0認証, Rate Limiting, CORS

## セットアップ

### 前提条件

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- 仮想環境 (venv)

### インストール

**重要**: ローカル環境をクリーンに保つため、必ず仮想環境を使用してください！

```bash
# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
# ⚠️ 注意: backend/.env.example は存在しません
# プロジェクトルートの .env.example を使用してください
cd /Users/tsuyoshi-hasegawa/Documents/workspace/github/private/stock_code
cp .env.example backend/.env

# backend/.env を編集して設定を行う
vi backend/.env  # または任意のエディタ
```

### 環境変数

`backend/.env` に以下を設定:

```env
# アプリケーション設定
APP_NAME="Stock Code"
ENVIRONMENT=development
DEBUG=true

# データベース
DATABASE_URL=postgresql://stockcode:stockcode123@localhost:5432/stockcode

# Redis
REDIS_URL=redis://localhost:6379/0

# Google OAuth 2.0（開発環境）
GOOGLE_CLIENT_ID=120481795465-1jn41flhq5t3m0f3of03huesokf2h380.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=（Google Consoleから取得）
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# セッション設定
SESSION_SECRET_KEY=（python -c "import secrets; print(secrets.token_urlsafe(32))" で生成）
SESSION_EXPIRE_DAYS=7
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SECURE=false  # 本番環境ではtrue

# API Keys
EDINET_API_KEY=your-edinet-api-key
```

## Google OAuth 2.0 認証設定

### 開発用OAuth認証情報の作成

#### ステップ1: Google Cloud Consoleにアクセス
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを選択または作成（推奨: `stock-code-dev`）

#### ステップ2: OAuth 2.0 認証情報の作成
1. **APIs & Services** > **認証情報** に移動
2. **+ 認証情報を作成** > **OAuth クライアント ID**
3. 同意画面の設定（初回のみ）:
   - ユーザータイプ: **外部**
   - アプリ名: Stock Code
   - サポートメール: あなたのメールアドレス
   - 開発者の連絡先: あなたのメールアドレス
4. アプリケーションの種類: **ウェブアプリケーション**
5. 名前: Stock Code Local Development
6. 承認済みのリダイレクトURIを追加:
   ```
   http://localhost:8000/api/v1/auth/google/callback
   ```
7. **作成** をクリック
8. **クライアントID** と **クライアントシークレット** をコピー

#### ステップ3: 環境変数に設定
```bash
# backend/.env に以下を追加
GOOGLE_CLIENT_ID=あなたのクライアントID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=あなたのクライアントシークレット
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# セッション秘密鍵を生成
python -c "import secrets; print(f'SESSION_SECRET_KEY={secrets.token_urlsafe(32)}')"
# 出力された値を SESSION_SECRET_KEY に設定
```

### ローカル環境でのテスト

#### サービスの起動
```bash
# PostgreSQL と Redis を起動
docker compose up postgres redis -d

# 起動確認
docker ps | grep -E "postgres|redis"

# Redis 動作確認
docker exec stock_code_redis redis-cli ping
# PONG と表示されればOK
```

#### バックエンドサーバーの起動
```bash
cd backend
source venv/bin/activate

# マイグレーション実行（初回のみ）
alembic upgrade head

# サーバー起動
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### 認証フローのテスト

**ブラウザでのテスト**:
1. ブラウザで `http://localhost:8000/api/v1/auth/google/login` にアクセス
2. Googleログイン画面にリダイレクトされる
3. アプリケーションを承認
4. コールバックURLにリダイレクトされ、JSONレスポンスが表示される
5. `session_token` をコピー

**APIテスト**:
```bash
# セッショントークンを環境変数に設定
export TOKEN="あなたのセッショントークン"

# ユーザー情報取得
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/auth/me

# プロフィール更新
curl -X PUT \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "investment_experience": "intermediate",
       "investment_style": "long_term",
       "interested_industries": ["technology", "finance"]
     }' \
     http://localhost:8000/api/v1/auth/profile

# ログアウト
curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/auth/logout
```

### 認証API エンドポイント

| メソッド | エンドポイント | 説明 | 認証 |
|---------|---------------|------|-----|
| GET | `/api/v1/auth/google/login` | Googleログイン開始 | 不要 |
| GET | `/api/v1/auth/google/callback?code=...` | OAuth認証コールバック | 不要 |
| GET | `/api/v1/auth/me` | 現在のユーザー情報取得 | 必要 |
| PUT | `/api/v1/auth/profile` | プロフィール更新 | 必要 |
| POST | `/api/v1/auth/logout` | ログアウト | 必要 |

### データベース・セッション確認

**PostgreSQLでユーザー確認**:
```bash
docker exec -it stock_code_postgres psql -U stockcode -d stockcode

# ユーザーテーブル確認
SELECT id, email, name, role, investment_experience FROM users;

\q  # 終了
```

**Redisでセッション確認**:
```bash
docker exec -it stock_code_redis redis-cli

# セッション一覧
KEYS session:*

# 特定セッションの内容
GET session:あなたのセッショントークン

# 有効期限確認（秒単位）
TTL session:あなたのセッショントークン

exit  # 終了
```

## データベースマイグレーション

### Alembicの使い方

**マイグレーション確認**:
```bash
source venv/bin/activate
alembic current  # 現在のマイグレーションバージョン確認
alembic history  # マイグレーション履歴表示
```

**新しいマイグレーション作成**:
```bash
# モデル変更後、自動生成
alembic revision --autogenerate -m "説明文"

# 生成されたファイルを確認・編集
# backend/alembic/versions/TIMESTAMP_説明文.py

# マイグレーション適用
alembic upgrade head
```

**マイグレーションのロールバック**:
```bash
# 1つ前に戻す
alembic downgrade -1

# 特定のバージョンに戻す
alembic downgrade <revision_id>
```

## テスト

### テスト実行

```bash
source venv/bin/activate

# 全テスト実行
pytest

# カバレッジ付き実行
pytest --cov=. --cov-report=html

# 特定のテストファイルのみ
pytest tests/test_auth.py

# 特定のテストケースのみ
pytest tests/test_auth.py::test_google_login_redirect
```

### テストカバレッジ確認
```bash
# HTMLレポート生成
pytest --cov=. --cov-report=html

# ブラウザで確認
open htmlcov/index.html  # macOS
```

## 開発

### コードフォーマット
```bash
# Black フォーマッター
black .

# Flake8 リント
flake8

# 型チェック
mypy .
```

### Yahoo Finance APIレート制限

Stock Codeは**Token Bucketレート制限アルゴリズム**を実装し、Yahoo Finance APIからのエラーやIPブロックを防止しています。

#### 設定方法

```bash
# backend/.env
YAHOO_FINANCE_MAX_TOKENS=100
YAHOO_FINANCE_REFILL_RATE=0.5  # tokens/second (30/min, 1800/hour)
YAHOO_FINANCE_RATE_LIMIT_KEY=rate_limit:yahoo_api
```

#### 仕組み

- **Token Bucket方式**: 100トークン容量、0.5トークン/秒で補充
- **保守的な制限**: 毎分30リクエスト（Yahoo Financeの制限~2000/時間を大きく下回る）
- **分散システム対応**: Redisバックエンドで複数インスタンス間で調整
- **グレースフルな待機**: トークン不足時は失敗せずに待機

#### レート制限の動作確認

Python環境でレート制限の状態を確認できます：

```python
from services.yahoo_finance_client import YahooFinanceClient
from core.dependencies import get_redis_client

redis = next(get_redis_client())
client = YahooFinanceClient(redis_client=redis)

# レート制限の統計情報を取得
stats = await client.rate_limiter.get_stats()
print(stats)
# {'current_tokens': 87.5, 'max_tokens': 100, 'refill_rate': 0.5,
#  'utilization_percent': 12.5, 'last_refill': 1699876543.21}
```

#### トラブルシューティング

**問題**: レート制限が厳しすぎる（待機時間が長い）
- `YAHOO_FINANCE_REFILL_RATE` を増やす（例: 1.0 = 60リクエスト/分）
- `YAHOO_FINANCE_MAX_TOKENS` を増やして大きなバーストに対応

**問題**: それでも429エラーが発生する
- `YAHOO_FINANCE_REFILL_RATE` を減らす（例: 0.3 = 18リクエスト/分）
- 同じIPを使用している他のサービスがないか確認

**問題**: Redis接続エラー
- レート制限機能は無効化され、レガシーの固定遅延（0.5秒）にフォールバック
- Redis接続を確認: `redis-cli ping`

#### 実装の詳細

- **統合箇所**: `YahooFinanceClient`の5つのAPIメソッド
  - `get_stock_price()` - 株価取得
  - `get_historical_data()` - 過去データ取得
  - `get_company_info()` - 企業情報取得
  - `get_dividends()` - 配当情報取得
  - `get_stock_splits()` - 株式分割情報取得
- **WebSocket対応**: リアルタイム価格更新も自動的にレート制限が適用
- **バッチジョブ対応**: 日次株価更新ジョブも自動的にレート制限が適用
- **並行処理制御**: Semaphore(5)で最大5並行リクエスト + Token Bucket制御

### API ドキュメント

サーバー起動後、以下のURLでインタラクティブなAPIドキュメントにアクセスできます:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## トラブルシューティング

### よくあるエラーと対処法

#### エラー: "redirect_uri_mismatch"
- Google Consoleの承認済みリダイレクトURIと `.env` の `GOOGLE_REDIRECT_URI` が完全一致しているか確認
- 末尾のスラッシュ有無、HTTP/HTTPSを確認

#### エラー: "Session service unavailable"
```bash
# Redisが起動しているか確認
docker ps | grep redis

# 起動していない場合
docker compose up redis -d
```

#### エラー: "Not authenticated"（有効なトークンのはず）
```bash
# Redisにセッションが存在するか確認
docker exec stock_code_redis redis-cli GET session:あなたのトークン

# 存在しない場合は再ログイン（セッション期限切れまたはRedis再起動）
```

#### データベース接続エラー
```bash
# PostgreSQLが起動しているか確認
docker ps | grep postgres

# DATABASE_URLが正しいか確認
echo $DATABASE_URL  # または .env ファイルを確認
```

## プロジェクト構成

```
backend/
├── api/              # APIエンドポイント
│   ├── main.py      # FastAPIアプリケーション
│   └── routers/     # ルーター（auth, companies, screening, etc）
├── core/            # コア機能
│   ├── config.py    # 設定管理
│   ├── database.py  # データベース接続
│   ├── auth.py      # 認証ミドルウェア
│   └── sessions.py  # セッション管理
├── models/          # SQLAlchemyモデル
│   ├── user.py      # ユーザーモデル
│   ├── company.py   # 企業モデル
│   └── financial.py # 財務データモデル
├── services/        # ビジネスロジック
│   ├── google_oauth.py      # Google OAuth クライアント
│   ├── edinet_client.py     # EDINET API クライアント
│   ├── yahoo_finance_client.py  # Yahoo Finance クライアント
│   └── data_processor.py    # データ処理
├── schemas/         # Pydanticスキーマ（リクエスト/レスポンス）
├── batch/           # バッチジョブ
│   └── daily_update.py  # 日次株価更新
├── tests/           # テストコード
├── alembic/         # データベースマイグレーション
└── requirements.txt # 依存パッケージ
```

## セキュリティに関する注意事項

- ✅ `backend/.env` は `.gitignore` に含まれています（Gitにコミットされません）
- ✅ クライアントシークレットは `.env` にのみ記載
- ✅ 本番環境では環境変数を Secret Manager で管理
- ✅ HTTPOnly Cookie でXSS攻撃を防止
- ✅ SameSite Cookie でCSRF攻撃を防止
- ✅ SQLAlchemyのパラメータ化クエリでSQLインジェクションを防止

## その他のドキュメント

- **プロジェクト全体の概要**: `/CLAUDE.md`
- **テスト詳細**: `/backend/TESTING.md`
- **開発ガイドライン**: `/CLAUDE.md` の Development Guidelines セクション

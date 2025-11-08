# 環境設定の重要な注意事項

## ⚠️ よくある間違い

### `.env.example` の場所

**間違い**: `backend/.env.example` をコピーしようとする  
**正解**: プロジェクトルートの `.env.example` を `backend/.env` にコピーする

```bash
# ❌ 間違った手順
cd backend
cp .env.example .env  # backend/.env.example は存在しない

# ✅ 正しい手順
cd /Users/tsuyoshi-hasegawa/Documents/workspace/github/private/stock_code
cp .env.example backend/.env
```

## Google OAuth 開発環境設定

### GCPプロジェクト
- **プロジェクト名**: `stock-code-dev`
- **作成日**: 2025-11-08
- **用途**: ローカル開発・動作確認

### OAuth Client設定
- **アプリケーションの種類**: ウェブアプリケーション
- **承認済みリダイレクトURI**: `http://localhost:8000/api/v1/auth/google/callback`
- **クライアントID**: `120481795465-1jn41flhq5t3m0f3of03huesokf2h380.apps.googleusercontent.com`
- **クライアントシークレット**: `backend/.env` に記載（Git管理外）

### セキュリティ上の注意
- クライアントシークレットは `.env` ファイルにのみ記載
- CLAUDE.md や serena メモリには**記録しない**
- `.env` ファイルは `.gitignore` で除外されている
- 万が一Gitにコミットした場合は、Google Consoleでシークレットを再生成

## 環境変数設定手順

### 1. .env ファイル作成
```bash
cd /Users/tsuyoshi-hasegawa/Documents/workspace/github/private/stock_code
cp .env.example backend/.env
```

### 2. Google OAuth設定を追加
```bash
# backend/.env に以下を追加
GOOGLE_CLIENT_ID=120481795465-1jn41flhq5t3m0f3of03huesokf2h380.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=（Google Consoleから取得したシークレット）
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### 3. セッション秘密鍵を生成
```bash
python -c "import secrets; print(f'SESSION_SECRET_KEY={secrets.token_urlsafe(32)}')"
# 出力された値を SESSION_SECRET_KEY に設定
```

## ローカル開発フロー

### サービス起動順序
```bash
# 1. PostgreSQL と Redis を起動
docker compose up postgres redis -d

# 2. 仮想環境を有効化
cd backend
source venv/bin/activate

# 3. マイグレーション実行（初回のみ）
alembic upgrade head

# 4. サーバー起動
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 動作確認
```bash
# ブラウザで Google OAuth ログインテスト
open http://localhost:8000/api/v1/auth/google/login

# API ドキュメント確認
open http://localhost:8000/api/docs
```

## トラブルシューティング

### .env ファイルが見つからない
```bash
# 正しいパスを確認
ls -la /Users/tsuyoshi-hasegawa/Documents/workspace/github/private/stock_code/.env.example
ls -la backend/.env

# .env が存在しない場合は作成
cd /Users/tsuyoshi-hasegawa/Documents/workspace/github/private/stock_code
cp .env.example backend/.env
```

### Google OAuth エラー
- `redirect_uri_mismatch`: リダイレクトURIが完全一致しているか確認
- `invalid_client`: クライアントIDとシークレットが正しいか確認
- `Email not verified`: Google側でメール認証が必要

### Redis接続エラー
```bash
# Redis起動確認
docker ps | grep redis

# Redis疎通確認
docker exec stock_code_redis redis-cli ping
```

## ドキュメント参照先

- **完全な設定手順**: `backend/README.md` の「Google OAuth 2.0 認証設定」セクション
- **プロジェクト全体概要**: `/CLAUDE.md`
- **開発ガイドライン**: `/CLAUDE.md` の Development Guidelines

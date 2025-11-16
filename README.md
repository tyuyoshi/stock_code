# Stock Code - 企業分析SaaSプラットフォーム

日本上場企業の財務データを収集・分析・可視化するプラットフォームです。EDINET APIやYahoo Financeからデータを取得し、投資判断に必要な各種指標を自動計算・提供します。

## 🎯 プロジェクトステータス

**現在**: MVP開発フェーズ（企業詳細ページ、WebSocket実装完了）
**次**: スクリーニング画面実装、テストカバレッジ90%達成

詳細なステータスと機能は [CLAUDE.md](./CLAUDE.md) を参照してください。

## 🚀 クイックスタート

### 前提条件

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15+
- Git

### セットアップ

```bash
# 1. リポジトリのクローン
git clone https://github.com/tyuyoshi/stock_code.git
cd stock_code

# 2. セットアップスクリプトの実行
./setup.sh

# 3. Docker Composeで起動
docker compose up -d

# 4. アクセス
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

## 📚 ドキュメント

- **[CLAUDE.md](./CLAUDE.md)** - プロジェクト全体の詳細情報、開発ガイドライン、技術スタック
- **[backend/README.md](./backend/README.md)** - バックエンドセットアップと API ドキュメント
- **[frontend/README.md](./frontend/README.md)** - フロントエンドセットアップと開発ガイド
- **[docs/SETUP.md](./docs/SETUP.md)** - 詳細なセットアップ手順
- **[docs/API.md](./docs/API.md)** - API仕様書

## 🛠 開発

### Backend開発

```bash
cd backend
source venv/bin/activate

# マイグレーション
alembic upgrade head

# サーバー起動
uvicorn api.main:app --reload

# テスト実行
pytest --cov
```

### Frontend開発

```bash
cd frontend

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# 型チェック
npm run type-check
```

## 📦 主な機能

- ✅ EDINET API連携と財務データ取得
- ✅ Yahoo Finance株価データ取得（レート制限対応）
- ✅ 60+財務指標の自動計算
- ✅ Google OAuth 2.0認証
- ✅ ウォッチリスト管理
- ✅ WebSocketリアルタイム株価更新
- ✅ 企業詳細ページ（日中チャート対応）
- 🔄 スクリーニング機能（実装中）

詳細は [CLAUDE.md - Key Features Status](./CLAUDE.md#key-features-status) を参照。

## 🧪 テスト

```bash
# Backend
cd backend && pytest --cov

# Frontend
cd frontend && npm run type-check && npm run lint
```

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/tyuyoshi/stock_code/issues)
- **Project Board**: [GitHub Project #5](https://github.com/users/tyuyoshi/projects/5)

## 📝 ライセンス

MIT

---

**詳細な開発情報、アーキテクチャ、デプロイ手順については [CLAUDE.md](./CLAUDE.md) を参照してください。**

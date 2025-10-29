# Stock Code - 企業分析SaaSプラットフォーム

> ⚠️ **開発ステータス**: 現在は開発環境向けの初期セットアップです。本番環境での使用前に、セキュリティ設定（Issue #30）とテストの実装（Issue #32）が必要です。

日本上場企業の財務データを収集・分析・可視化するプラットフォームです。
EDINET APIやYahoo Financeからデータを取得し、投資判断に必要な各種指標を自動計算・提供します。

## 🚀 主な機能

- 📊 **財務データ分析**: BS/PL/CFの詳細分析
- 📈 **株価チャート**: リアルタイム株価情報とテクニカル指標
- 🔍 **スクリーニング**: 複数条件での企業絞り込み
- 📊 **財務指標計算**: PER, PBR, ROE, ROA等の自動計算
- 🆚 **企業比較**: 複数企業の横断的分析
- 📄 **データエクスポート**: CSV/Excel形式でのデータ出力

## 🛠 技術スタック

### 技術選定の詳細

| カテゴリ | 技術 | バージョン | 選定理由 |
|---------|------|-----------|----------|
| **Backend Framework** | FastAPI | 0.109.0 | 高速な非同期処理、自動APIドキュメント生成、型ヒントサポート |
| **言語** | Python | 3.11+ | データ分析ライブラリの充実、金融計算に適した数値処理 |
| **Database** | PostgreSQL | 15 | ACID特性、複雑なクエリ対応、JSON対応、高い信頼性 |
| **ORM** | SQLAlchemy | 2.0 | 高機能なORM、型安全性、マイグレーション管理 |
| **Cache** | Redis | 7 | 高速インメモリDB、セッション管理、リアルタイムデータ |
| **Data Processing** | Pandas/NumPy | 2.1.4/1.26.3 | 財務データ分析の業界標準、高速な数値計算 |
| **Task Queue** | Celery | 5.3.4 | 非同期タスク処理、定期バッチ実行 |

### Frontend
| 技術 | バージョン | 選定理由 |
|------|-----------|----------|
| **Framework** | Next.js | 14.0.4 | SEO対応、App Router、ISR/SSG対応、最新のReact機能 |
| **Language** | TypeScript | 5.3.3 | 型安全性、開発効率向上、エラー削減 |
| **Styling** | Tailwind CSS | 3.4.0 | ユーティリティファースト、高速開発、カスタマイズ性 |
| **UI Library** | Shadcn/ui + Radix UI | latest | 高品質なコンポーネント、アクセシビリティ対応 |
| **State** | Zustand | 4.4.7 | シンプルで軽量、TypeScript完全対応 |
| **Data Fetching** | TanStack Query | 5.17.9 | キャッシュ管理、楽観的更新、無限スクロール |
| **Charts** | Chart.js/Recharts | 4.4.1/2.10.3 | 金融チャート対応、高いカスタマイズ性 |

### Infrastructure
| サービス | 用途 | 選定理由 |
|---------|------|----------|
| **Cloud Run** | アプリホスティング | サーバーレス、自動スケーリング、従量課金 |
| **Cloud SQL** | マネージドDB | 自動バックアップ、高可用性、メンテナンスフリー |
| **Cloud Storage** | ファイルストレージ | 安価、高耐久性、CDN統合 |
| **Cloud Scheduler** | バッチ実行 | Cronジョブ、高信頼性、Cloud Run統合 |
| **Docker** | コンテナ化 | 環境統一、本番環境との差異削減 |

## 💻 セットアップ

### 前提条件

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Git

### 1. リポジトリのクローン

```bash
git clone https://github.com/tyuyoshi/stock_code.git
cd stock_code
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集して必要な設定を追加
```

### 3. セットアップスクリプトの実行

```bash
./setup.sh
```

### 4. Docker Composeで起動

```bash
docker-compose up -d
```

### 5. アクセス

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## 📝 開発

### Backend開発

```bash
cd backend

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# データベースマイグレーション
alembic upgrade head

# 開発サーバー起動
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend開発

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# 型チェック
npm run type-check

# Lint
npm run lint
```

## 🧪 テスト

### Backendテスト

```bash
cd backend
pytest
pytest --cov=api --cov-report=html  # カバレッジレポート付き
```

### Frontendテスト

```bash
cd frontend
npm test
npm run test:coverage
```

## 📦 プロジェクト構造

```
stock_code/
├── backend/                # バックエンド (FastAPI)
│   ├── api/               # APIエンドポイント
│   ├── core/              # コア設定
│   ├── models/            # データベースモデル
│   ├── services/          # ビジネスロジック
│   └── batch/             # バッチ処理
├── frontend/               # フロントエンド (Next.js)
│   ├── src/
│   │   ├── app/           # App Router
│   │   ├── components/    # Reactコンポーネント
│   │   └── lib/           # ユーティリティ
│   └── public/            # 静的ファイル
├── infrastructure/         # インフラ設定
│   ├── terraform/         # Terraform構成
│   └── docker/            # Docker設定
└── docs/                   # ドキュメント
```

## 🛣️ ロードマップ

### Phase 1: MVP (2週間)
- [x] GitHubプロジェクト初期設定
- [ ] GCP環境構築
- [ ] 基本的なデータ収集機能
- [ ] データベーススキーマ設計

### Phase 2: コア機能 (2週間)
- [ ] 財務データ取得・保存
- [ ] 財務指標計算
- [ ] 基本的なAPIエンドポイント

### Phase 3: UI/UX (2週間)
- [ ] 企業詳細ページ
- [ ] スクリーニング機能
- [ ] チャート表示

## 🤝 コントリビュート

IssueやPull Requestは大歓迎です。

## 📝 ライセンス

MIT

## 📞 コンタクト

- GitHub: [tyuyoshi/stock_code](https://github.com/tyuyoshi/stock_code)
- Issues: [GitHub Issues](https://github.com/tyuyoshi/stock_code/issues)

## 💰 インフラストラクチャコスト見積もり

### 開発環境（最小構成）
| サービス | スペック | 月額費用 |
|----------|----------|----------|
| Cloud Run (Backend) | 0.5 vCPU, 1GB RAM | $20-30 |
| Cloud Run (Frontend) | 0.5 vCPU, 512MB RAM | $15-20 |
| Cloud SQL | db-f1-micro, 10GB | $17 |
| Cloud Storage | 10GB | $0.2 |
| Cloud Scheduler | 基本利用 | $0.1 |
| **合計** | | **$52-67 (約8,000-10,000円)** |

### 本番環境（推奨構成）
| サービス | スペック | 月額費用 |
|----------|----------|----------|
| Cloud Run (Backend) | 2 vCPU, 4GB RAM, 2-5インスタンス | $100-200 |
| Cloud Run (Frontend) | 1 vCPU, 2GB RAM, 2-3インスタンス | $50-80 |
| Cloud SQL | db-n1-standard-1, 100GB SSD | $75 |
| Cloud Storage | 100GB | $2 |
| Cloud Load Balancer | HTTPS LB | $20 |
| Cloud CDN | キャッシュ配信 | $10-20 |
| **合計** | | **$257-397 (約40,000-60,000円)** |

### エンタープライズ（大規模運用）
| サービス | スペック | 月額費用 |
|----------|----------|----------|
| Cloud Run | 高スペック・複数リージョン | $500-800 |
| Cloud SQL | HA構成、リードレプリカ | $300-500 |
| その他インフラ | CDN、監視、バックアップ強化 | $200-400 |
| **合計** | | **$1,000-1,700 (約150,000-250,000円)** |

### コスト最適化のポイント
1. **Cloud Run** - リクエストがない時は課金ゼロ（自動スケールダウン）
2. **開発環境** - 夜間/週末の自動停止で最大50%削減
3. **Committed Use Discounts** - 1-3年契約で最大57%割引
4. **Cloud CDN** - 静的コンテンツのキャッシュでデータ転送費削減
5. **適切なインスタンスサイジング** - 定期的な使用状況レビュー

---

⚠️ **注意**: このプロジェクトは開発中です。本番環境での使用には注意してください。

💡 **コスト試算について**: 上記は概算です。実際の費用は使用状況により変動します。[GCP料金計算ツール](https://cloud.google.com/products/calculator)で詳細な見積もりが可能です。
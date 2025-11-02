# ドキュメント作成の基本方針

## 重要原則（2025年11月2日確立）
**1ディレクトリ、1 README.md の原則**

### 基本ルール
- 各ディレクトリにはREADME.md を1つだけ配置
- 追加のマークダウンファイル（MIGRATION.md, TESTING.md, etc.）は作成しない
- 全ての情報は該当ディレクトリのREADME.md に集約する

### ディレクトリ構造例
```
stock_code/
├── README.md            # プロジェクト全体の説明
├── backend/
│   ├── README.md        # backend全体の説明（マイグレーション、テスト等含む）
│   ├── alembic/
│   │   └── README       # Alembic自動生成（例外）
│   └── tests/
│       └── README.md    # テスト関連の説明
├── frontend/
│   └── README.md        # frontend全体の説明
└── infrastructure/
    └── README.md        # インフラ関連の説明
```

### 良い例
- ✅ backend/README.md にマイグレーション、テスト、APIドキュメントをセクション分けして記載
- ✅ frontend/README.md に開発、ビルド、デプロイ手順を統合

### 悪い例
- ❌ backend/MIGRATION.md を別途作成
- ❌ backend/TESTING.md を別途作成
- ❌ backend/API.md を別途作成

### 例外
- CLAUDE.md: Claude Code用の特別なガイダンスファイル（プロジェクトルートのみ）
- .github/: GitHub特有のファイル（CONTRIBUTING.md等）
- Alembic等のツールが自動生成するREADME

### 理由
1. ドキュメントの検索性向上
2. 情報の重複や矛盾を防ぐ
3. メンテナンスの簡素化
4. ディレクトリ構造のクリーンさ維持

この方針により、開発者は各ディレクトリのREADME.mdを見れば必要な情報が全て得られる。
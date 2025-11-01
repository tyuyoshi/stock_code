# 次回セッションのタスク

## 優先順位

### 1. Issue #32: テストスイート基盤構築
**目的**: 現在0%のテストカバレッジを改善し、品質保証体制を確立

**実装内容**:
- pytest設定ファイルの作成
- テストデータベースの設定
- Fixture と Mock の準備
- CI/CD用のテスト設定
- カバレッジ目標: 80%以上

**関連ファイル**:
- `backend/tests/`
- `pytest.ini` or `setup.cfg`
- `.github/workflows/test.yml`（CI設定）

### 2. Issue #31: Alembicマイグレーション設定
**目的**: データベーススキーマのバージョン管理と自動マイグレーション

**実装内容**:
- Alembic初期設定（alembic init）
- `alembic/env.py`の設定
- 既存モデルの初期マイグレーション作成
- マイグレーション実行スクリプト
- Docker Compose統合

**関連ファイル**:
- `backend/alembic/`
- `backend/alembic.ini`
- `backend/models/`

## 完了済みタスク（参考）

### Issue #30: セキュリティ脆弱性修正 ✅
- CORS設定の環境別対応
- Secret Key管理とJWT実装
- セキュリティヘッダー追加
- Rate Limiting実装
- PR #54でマージ済み

### Issue #13: 財務指標計算エンジン ✅
- 60以上の財務指標実装
- 6カテゴリ（収益性、安全性、効率性、成長性、割安性、キャッシュフロー）
- PR #46でマージ済み

### Issue #6: EDINET API連携 ✅
- EDINET APIクライアント実装
- XBRLパーサー実装
- PR #45でマージ済み

## 開発環境の現状

### Docker Compose
- PostgreSQL、Redis、Backend、Frontend統合済み
- 環境変数による設定管理完備
- 開発用Dockerfileを別途用意

### セキュリティ
- 本番レベルのセキュリティ設定完了
- Rate Limiting有効（Redisストレージ）
- CSPヘッダー、CORS設定済み

## 推奨作業順序
1. まずIssue #32でテスト基盤を整備
2. テストがある程度整ったらIssue #31でマイグレーション設定
3. その後、Core APIエンドポイント（Issue #35）の実装へ

## 注意事項
- テスト実装時は既存の`test_security.py`、`test_financial_indicators.py`を参考に
- Alembic設定時はDockerコンテナ内での実行を考慮
- 環境変数の管理に注意（.envファイルの取り扱い）
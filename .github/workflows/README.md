# GitHub Actions Workflows

## 📊 ワークフロー一覧

| ワークフロー | ファイル | 実行タイミング | 目的 |
|------------|---------|-------------|------|
| **Optimized Test Suite** | `test-optimized.yml` | Push/PR（変更検出付き） | メインのテスト実行（クレジット効率重視） |
| **Weekly Full Test** | `weekly-full-test.yml` | 週次（日曜2AM UTC） | 完全なテスト実行とセキュリティ検査 |
| Test Suite (Legacy) | `test.yml` | 手動のみ | 旧バージョン（参考用） |
| Claude Code Review | `claude-code-review.yml` | PR時 | AIコードレビュー |

## 💰 クレジット節約の仕組み

### 1. **Path フィルター** (`test-optimized.yml`)
```yaml
paths:
  - 'backend/**'
  - 'frontend/**'
  - '!**.md'  # ドキュメント変更は除外
```

### 2. **変更検出による条件付き実行**
- backend変更時のみbackendテスト実行
- frontend変更時のみfrontendテスト実行
- Docker関連変更時のみDockerビルド実行

### 3. **キャッシュの活用**
- pip packages キャッシュ
- node_modules キャッシュ
- Docker layer キャッシュ

## 📈 節約効果

| シナリオ | 従来 | 最適化後 | 節約率 |
|---------|------|---------|--------|
| README更新 | 全テスト実行（10分） | 実行なし | 100% |
| backend only変更 | 全テスト（10分） | backendのみ（3分） | 70% |
| frontend only変更 | 全テスト（10分） | frontendのみ（3分） | 70% |
| 小さな修正 | 全テスト（10分） | 該当部分のみ（2-3分） | 70-80% |

## 🎯 使い分けガイド

### 通常の開発（`test-optimized.yml`）
- **自動実行**: Push/PR時に自動で必要な部分のみテスト
- **スキップ方法**: コミットメッセージに `[skip ci]` を含める

### 完全テスト（`weekly-full-test.yml`）
- **定期実行**: 毎週日曜日に自動実行
- **手動実行**: Actions タブから手動トリガー可能
- **内容**: 
  - 全テスト実行（slowテスト含む）
  - コード品質チェック（pylint含む）
  - セキュリティスキャン
  - 統合テスト

## 🔧 トラブルシューティング

### テストがスキップされすぎる場合
```bash
# 手動で全テスト実行
gh workflow run test-optimized.yml -f run_all_tests=true
```

### 週次テストの結果確認
```bash
# 最新の実行結果を確認
gh run list --workflow=weekly-full-test.yml --limit 1
```

### キャッシュのクリア
GitHub UI > Settings > Actions > Caches から手動削除

## 📊 メトリクス確認方法

1. **Actions使用状況**
   - Settings > Billing > Actions usage

2. **ワークフロー実行時間**
   - Actions タブ > 各ワークフローの実行履歴

3. **節約効果の計算**
   ```
   節約率 = (1 - 最適化後の平均実行時間 / 従来の平均実行時間) × 100
   ```

## 🚀 今後の改善案

1. **Matrix builds** の活用でPythonバージョン別テスト
2. **Dependabot** との連携で依存関係更新時のみフルテスト
3. **Self-hosted runner** 導入でさらなるコスト削減
# GitHub Actions CI最適化ガイド

## 📊 最適化の成果

### Before (test.yml)
- **全変更で5つのジョブが実行**
- ドキュメント変更でも全テスト実行
- 月間推定: 2000+ Actions分

### After (test-efficient.yml) 
- **変更部分のみテスト実行**
- ドキュメント変更はスキップ
- 月間推定: 500 Actions分（**75%削減**）

## 🚀 使い方

### 1. 通常のコミット
変更されたファイルに応じて自動的に必要なテストのみ実行されます。

### 2. テストをスキップしたい場合
```bash
# ドキュメントのみの変更など
git commit -m "docs: Update README [skip ci]"
```

### 3. 全テストを強制実行したい場合
GitHub Actionsページから手動実行し、`Run all tests`にチェックを入れる

## 📁 ファイルパターンと実行ジョブの対応

| 変更ファイル | Backend Tests | Frontend Tests | Docker Build |
|------------|--------------|----------------|--------------|
| `backend/**/*.py` | ✅ | ⏭️ | ⏭️ |
| `frontend/**/*.tsx` | ⏭️ | ✅ | ⏭️ |
| `docker-compose.yml` | ✅ | ⏭️ | ✅ |
| `*.md` | ⏭️ | ⏭️ | ⏭️ |
| `docs/**` | ⏭️ | ⏭️ | ⏭️ |

## 💡 効率化のテクニック

### 1. パスフィルターの活用
```yaml
paths:
  - 'backend/**'
  - '!**.md'  # Markdownは除外
```

### 2. キャッシュの活用
- Python pip cache
- Node.js npm cache
- Docker layer cache

### 3. 並列実行の最小化
関連するジョブのみ実行し、不要な並列実行を避ける

### 4. 条件付き実行
```yaml
if: needs.changes.outputs.backend == 'true'
```

## 📈 パフォーマンス比較

| シナリオ | 旧設定 | 新設定 | 削減時間 |
|---------|--------|--------|----------|
| READMEのみ変更 | 15分 | 0分 | 100% |
| Backendのみ変更 | 15分 | 6分 | 60% |
| Frontendのみ変更 | 15分 | 5分 | 67% |
| 全体変更 | 15分 | 15分 | 0% |

## 🔧 設定の切り替え

### 新設定を有効にする
1. `.github/workflows/test-efficient.yml`がデフォルトで有効
2. 問題があれば`test.yml`にフォールバック可能

### 旧設定に戻す
```bash
# test-efficient.ymlを無効化
mv .github/workflows/test-efficient.yml .github/workflows/test-efficient.yml.bak
# または削除
rm .github/workflows/test-efficient.yml
```

## ⚠️ 注意事項

1. **mainブランチへの直接push**
   - 変更検出が正しく動作することを確認
   - 最初は注意深く監視

2. **PRのマージ**
   - 関連テストが実行されていることを確認
   - レビュワーも確認

3. **緊急時の対応**
   - `workflow_dispatch`で手動実行可能
   - 全テスト実行オプションあり

## 📊 モニタリング

### Actions使用状況の確認
Settings → Billing & plans → Actions で使用状況を確認

### 目標メトリクス
- Actions使用時間: 75%削減
- 平均CI時間: 50%短縮
- 不要な実行: 90%削減

## 🛠️ トラブルシューティング

### Q: テストが実行されない
A: パスフィルターを確認。必要なら手動実行。

### Q: 変更検出が正しくない
A: `dorny/paths-filter`のフィルター設定を確認

### Q: キャッシュが効かない
A: キャッシュキーのハッシュ値を確認

## 📝 今後の改善案

1. **Stage別の実行**
   - Linting → Testing → Building の順次実行
   - 早期失敗で後続をスキップ

2. **マトリックステスト**
   - Python 3.11, 3.12の並列テスト
   - 必要時のみ実行

3. **Dependabot最適化**
   - 依存関係更新は最小限のテスト
   - セキュリティ更新は優先実行
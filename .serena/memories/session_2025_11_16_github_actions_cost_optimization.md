# Session 2025/11/16: GitHub Actions コスト最適化

## セッション概要

**日時**: 2025年11月16日（Issue #149の後続作業）
**目的**: GitHub Actions のコスト最適化機能をmainブランチに直接適用
**方法**: PR経由ではなく、mainブランチへの直接コミット

## 背景

### PR #157での失敗経験

Issue #149の実装中に、以下の改善を試みたがrevertした：
1. Draft PRスキップ機能
2. ready_for_reviewトリガー追加

**revert理由**: Claude Code ReviewのOIDC認証エラー

```
Error: Workflow validation failed. The workflow file must exist 
and have identical content to the version on the repository's default branch.
```

### OIDC認証の要件

Claude Code Reviewは、セキュリティのため：
- ワークフローファイルがmainブランチと一致している必要がある
- PR内でワークフローを変更 → OIDC トークン交換が失敗

## 実装内容

### 1. Draft PRスキップ機能

**目的**: Draft PR作成時にワークフローを実行しない（コスト削減）

#### claude-code-review.yml
```yaml
jobs:
  claude-review:
    if: ${{ !github.event.pull_request.draft }}  # 追加
    runs-on: ubuntu-latest
```

#### test-efficient.yml (3ジョブ修正)
```yaml
backend-tests:
  if: >
    (needs.changes.outputs.backend == 'true' || ...) &&
    (github.event_name != 'pull_request_target' ||
     !github.event.pull_request.draft)  # 追加

frontend-tests: # 同様
docker-build: # 同様
```

#### test-optimized.yml (3ジョブ修正)
```yaml
backend-tests:
  if: |
    (...) &&
    (github.event_name != 'pull_request' ||
     !github.event.pull_request.draft)  # 追加

frontend-tests: # 同様
docker-build: # 同様
```

### 2. ready_for_reviewトリガー追加

**目的**: Draft → Ready変更時に自動的にワークフロー実行

#### claude-code-review.yml
```yaml
on:
  pull_request:
    types: [opened, synchronize, ready_for_review]  # ready_for_review追加
```

#### test-efficient.yml
```yaml
on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review]  # 追加
```

#### test-optimized.yml
```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]  # 明示的に定義
```

## 技術的な詳細

### イベントトリガーの違い

- **test-efficient.yml**: `pull_request_target`使用
  - フォークからのPRも実行可能（シークレットアクセス可）
  - セキュリティリスク高いため、Draft判定必須

- **test-optimized.yml**: `pull_request`使用
  - フォークからのPRはシークレットなし
  - より安全だが、機能制限あり

### Draft判定条件の違い

```yaml
# pull_request_target の場合
(github.event_name != 'pull_request_target' || !github.event.pull_request.draft)

# pull_request の場合
(github.event_name != 'pull_request' || !github.event.pull_request.draft)
```

## 期待される効果

### コスト削減

**Draft PR作成時**:
- Claude Code Review: スキップ → 30秒節約
- Efficient Test Suite: スキップ → 8分節約
- Optimized Test Suite: スキップ → 8分節約
- **合計**: 約16分/Draft PR

**月間想定**:
- Draft PR: 10件/月
- 節約時間: 160分/月
- **GitHub Actionsクレジット削減**: 大幅なコスト削減

### 開発体験向上

**Before** (問題):
```bash
gh pr create --draft  # Draft PR作成
# → Actionsが実行される（無駄）
gh pr ready 157  # Ready化
# → Actionsが実行されない（空コミット必要）
```

**After** (改善):
```bash
gh pr create --draft  # Draft PR作成
# → Actionsはスキップ（コスト削減）
gh pr ready 157  # Ready化
# → Actionsが自動実行（空コミット不要）
```

## 実装手順

1. mainブランチで3つのワークフローファイルを修正
2. 直接コミット・プッシュ（PR経由なし）
3. CLAUDE.mdに記録
4. Serenaメモリに記録

**コミットハッシュ**: `1287113`

## 検証方法

### テストシナリオ

1. **Draft PR作成テスト**
   ```bash
   # 新しいブランチ作成
   git checkout -b test/draft-pr
   
   # 軽微な変更
   echo "test" > test.txt
   git add test.txt && git commit -m "test: Draft PR test"
   
   # Draft PR作成
   gh pr create --draft --title "test: Draft PR validation"
   
   # 期待結果: GitHub Actionsが実行されない
   ```

2. **Ready化テスト**
   ```bash
   # PRをReady化
   gh pr ready <pr-number>
   
   # 期待結果: 自動的にGitHub Actionsが実行される
   ```

3. **通常のPR作成テスト**
   ```bash
   # Ready状態でPR作成
   gh pr create --title "test: Normal PR validation"
   
   # 期待結果: GitHub Actionsが即座に実行される
   ```

## 学習ポイント

### OIDC認証とワークフローファイル

- Claude Code ReviewなどOIDC認証を使用するActionは、mainブランチとの一致が必須
- PR内でワークフローを変更する場合、まずワークフロー変更のみの別PRを先にマージ
- または、mainブランチに直接コミット

### GitHub Actionsのイベントトリガー

- `ready_for_review`: Draft → Ready変更時のみ発火
- デフォルトの`types`には含まれないため、明示的に指定必要
- `opened, synchronize, reopened`と組み合わせて使用

### コスト最適化のベストプラクティス

1. **Draft PRは積極的に活用**
   - 開発中はDraftで作業
   - レビュー準備完了時にReady化

2. **ワークフローは必要最小限に**
   - 変更検出（paths filter）活用
   - Draft判定で不要な実行をスキップ

3. **手動トリガーオプション保持**
   - `workflow_dispatch`で必要時のみ実行可能

## 関連ドキュメント

- CLAUDE.md: "GitHub Workflow Rules (Cost Optimization)"
- `.github/workflows/claude-code-review.yml`
- `.github/workflows/test-efficient.yml`
- `.github/workflows/test-optimized.yml`

## 今後の改善案

1. **ワークフロー実行統計の可視化**
   - Draft PRスキップによるコスト削減効果を測定

2. **さらなる最適化**
   - キャッシュ戦略の改善
   - 並列実行の最適化

3. **モニタリング**
   - Actions実行時間の追跡
   - コスト分析レポート自動生成

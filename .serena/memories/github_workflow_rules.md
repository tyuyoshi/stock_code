# GitHub Workflow Rules - Cost Optimization

## 概要
GitHub Actions の無駄な実行を抑え、CI/CD コストを最小化するためのワークフロールール。

## 4つの重要ルール

### 1. 基本的にPRを作る時は、Draftで作る

**理由**: Draft PR は多くのワークフローをトリガーしないため、コスト削減になる。

```bash
# 正しい方法
gh pr create --draft --title "機能: Issue #XXX実装" --body "..."

# 間違った方法（すぐにCI/CDが走る）
gh pr create --title "機能: Issue #XXX実装" --body "..."
```

### 2. こちらで動作確認が取れ次第、Ready For Review を押す

**理由**: ユーザーがローカルで動作確認してから CI/CD を実行することで、失敗による再実行を防ぐ。

```bash
# ユーザーの動作確認後
gh pr ready  # Draft → Ready for Review に変更
```

### 3. push して、というまではローカルのコミットまでにして

**理由**: ローカルコミットの段階でユーザーがレビューできる。問題があれば push 前に修正可能。

**正しいワークフロー**:
```bash
# 1. ローカルでコミット
git add .
git commit -m "機能: 実装完了"

# 2. ユーザーの確認を待つ
# User: "動作確認OK、push して"

# 3. ユーザーの指示があってから push
git push origin feature/issue-xxx
```

**間違ったワークフロー**:
```bash
git add .
git commit -m "機能: 実装完了"
git push origin feature/issue-xxx  # ❌ ユーザーの確認前に push しない！
```

### 4. 無駄なRunが走らないようにする

**理由**: GitHub Actions は実行回数/時間で課金される。無駄な実行を避けることでコスト削減。

**避けるべき行動**:
- ❌ 何度も force-push する（再実行がトリガーされる）
- ❌ Draft でない PR を作成する
- ❌ ユーザーの確認前に push する
- ❌ 小さな修正で何度も push する

**推奨する行動**:
- ✅ ローカルで十分にテストしてから push
- ✅ Draft PR を使う
- ✅ コミットをまとめてから push
- ✅ ユーザーの指示を待つ

## 完全なワークフロー例

```bash
# ステップ1: ブランチ作成
git checkout -b feature/issue-xxx

# ステップ2: 実装とローカルコミット
git add .
git commit -m "機能: Issue #XXX実装"
# ⚠️ まだ push しない！

# ステップ3: Draft PR 作成（push なしでも可能な場合）
# または、最初の push は Draft PR 作成時のみ
git push origin feature/issue-xxx
gh pr create --draft --title "機能: Issue #XXX実装" --body "..."

# ステップ4: ユーザーのローカル動作確認
# User: ローカルでテスト、動作確認

# ステップ5: 問題があれば修正
git add .
git commit -m "修正: XXX"
# ⚠️ まだ push しない、ユーザーの指示を待つ

# User: "動作確認OK、push して"

# ステップ6: ユーザーの指示後に push
git push origin feature/issue-xxx

# ステップ7: ユーザーが Ready for Review に変更
# User: "Ready for Review にして"
gh pr ready

# ステップ8: CI/CD 実行、コードレビュー
# GitHub Actions が実行される（ここで初めて本格的なテストが走る）
```

## コスト削減効果

### これまでの実績
- **PR #58**: テスト最適化により 60-80% の GitHub Actions コスト削減
- **Draft PR の活用**: 不要なワークフロー実行を防ぐ
- **ローカル確認**: CI/CD 失敗による再実行を削減

### 期待される効果
- **Draft PR 使用**: 1 PR あたり平均 2-3 回の不要な CI/CD 実行を削減
- **ローカルコミット**: 修正→push→失敗→修正のサイクルを防ぐ
- **ユーザー確認**: 品質向上により CI/CD 失敗率を低下

## 注意点

### 例外ケース
以下の場合は、すぐに push/Ready for Review にしても良い:
- ホットフィックス（緊急のバグ修正）
- ドキュメント修正のみ（CI/CD 負荷が低い）
- ユーザーが明示的に「すぐに push して」と指示した場合

### GitHub Actions の設定
Draft PR でもトリガーされるワークフローがある場合は、`.github/workflows/` で以下のように設定:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    # Draft では実行されないように設定

jobs:
  test:
    if: github.event.pull_request.draft == false
    # Draft でない場合のみ実行
```

## チェックリスト

PR 作成時の確認事項:
- [ ] Draft PR として作成したか？
- [ ] ローカルで動作確認したか？
- [ ] ユーザーの「push して」指示を待ったか？
- [ ] 不要な force-push をしていないか？
- [ ] コミットメッセージは適切か？

## 参照
- CLAUDE.md: "GitHub Workflow Rules (Cost Optimization)" セクション
- PR #58: テスト最適化とコスト削減の実績
- Issue #90: テストカバレッジ向上（品質向上によるCI/CD失敗率低下）

# Session 2025/11/16: Issue管理とマイルストーン設定

## セッション概要

**日時**: 2025年11月16日  
**目的**: GitHub Issueの整理、マイルストーン設定、優先順位の明確化  
**ユーザー要求**: Production公開とバッチジョブのクラウド運用を最優先

## 実施内容

### 1. マイルストーン作成（3件）

| マイルストーン | 期限 | Issues | 概要 |
|---|---|---|---|
| MVP - Production Launch | 2025/12/31 | 7件 | 404防止のフロントエンド完成、データ投入、品質保証 |
| Cloud Infrastructure - Phase 1 | 2025/12/15 | 4件 | GCPインフラ構築、バッチジョブのクラウド移行 |
| Monetization & Growth | 2026/03/31 | 4件 | 有料プラン、ユーザー価値向上機能 |

### 2. Issue整理

**削除**:
- #151（企業詳細ページ株価情報セクション）→ #23に統合してクローズ

**優先度変更**:
- #149（初期企業データ1000社投入）: medium → high-priority

**ラベル追加**:
- #143（EDINET四半期バッチ）: high-priority, backend, data-collection を追加

### 3. マイルストーン割り当て（15件）

#### MVP - Production Launch（7件）
- #23: 企業詳細ページ実装 [high-priority]
- #24: スクリーニング画面実装 [high-priority]
- #150: 企業検索ページ実装 [medium-priority]
- #149: 初期企業データ1000社投入 [high-priority]
- #100: 監査ログ実装 [high-priority]
- #90: テストカバレッジ90%+ [high-priority]
- #139: CI/CDパイプライン構築 [high-priority]

#### Cloud Infrastructure - Phase 1（4件）
- #136: Cloud SQL (PostgreSQL) セットアップ [high-priority]
- #137: Redis Memorystore セットアップ [high-priority]
- #138: Secret Manager セットアップ [high-priority]
- #4: Cloud Run環境構築 [high-priority]

#### Monetization & Growth（4件）
- #148: Stripe決済システム [high-priority]
- #118: ポートフォリオ分析API [high-priority]
- #51: アラート通知システム [medium-priority]
- #77: 財務指標計算完全実装 [medium-priority]

### 4. Project #5への追加

すべての16 Issuesを正常にProject #5に追加完了。

## 開発優先順位の確立

### Week 1-2: MVP開発（最優先）
1. #149: 初期企業データ1000社投入（Production公開の前提）
2. #23, #24: 企業詳細・スクリーニング画面実装（並行）
3. #150: 企業検索ページ実装

**ゴール**: Production公開時に404エラーなし

### Week 3-4: 品質保証
4. #90: テストカバレッジ78% → 90%+
5. #100: 監査ログ実装（コンプライアンス）

### Week 5-6: インフラ構築
6. #136-138, #4: GCPインフラ構築（並行）
7. #139: CI/CDパイプライン構築

**ゴール**: バッチジョブのクラウド運用開始

### Week 7-8: 本番公開
- Staging環境テスト
- Production環境公開

## 株価データ保存方法の結論

**現状のPostgreSQLで問題なし**:
- **データ量**: 10年で約900MB（9.1万レコード）→ SQL十分対応可能
- **書き込み頻度**: 日次バッチのみ（1日1回、数分で完了）
- **リアルタイム**: WebSocketはメモリキャッシュのみ、DB書き込みなし

**将来的な最適化**:
- #106: 株価データ重複除去処理（既存Issue）
- #47: 株価データキャッシュレイヤー（読み込み高速化）
- テーブルパーティション化（10年後、1億レコード超えたら検討）

## Issue管理の改善効果

**Before**:
- マイルストーン: 0件（タイムライン不明確）
- 優先順位: ラベルのみで曖昧
- 重複Issue: 存在（#151など）
- Total: 86 open issues

**After**:
- マイルストーン: 3件（明確なタイムライン設定）
- 優先順位: MVP/Infrastructure/Monetizationで明確化
- 重複Issue: 削除完了
- Project #5: すべての重要Issueを追跡
- Total: 85 open, 67 closed

## 実行コマンド記録

```bash
# マイルストーン作成
gh api --method POST repos/tyuyoshi/stock_code/milestones \
  -f title="MVP - Production Launch" \
  -f due_on="2025-12-31T23:59:59Z" \
  -f description="..."

gh api --method POST repos/tyuyoshi/stock_code/milestones \
  -f title="Cloud Infrastructure - Phase 1" \
  -f due_on="2025-12-15T23:59:59Z"

gh api --method POST repos/tyuyoshi/stock_code/milestones \
  -f title="Monetization & Growth" \
  -f due_on="2026-03-31T23:59:59Z"

# Issue更新
gh issue close 151 --comment "#23に統合しました..."
gh issue edit 149 --add-label "high-priority" --remove-label "medium-priority"
gh issue edit 143 --add-label "high-priority,backend,data-collection"

# マイルストーン割り当て（例）
gh issue edit 23 --milestone "MVP - Production Launch" --add-label "high-priority"
gh issue edit 24 --milestone "MVP - Production Launch" --add-label "high-priority"
# ... (他の15 issues同様)

# Project #5追加
gh project item-add 5 --owner tyuyoshi --url https://github.com/tyuyoshi/stock_code/issues/23
# ... (他の15 issues同様)
```

## 次のアクション

最優先で着手すべきIssue:
1. **#149**: 初期企業データ1000社のDB投入（Production公開の前提）
2. **#23**: 企業詳細ページの実装（最重要UI）
3. **#24**: スクリーニング画面の実装（最重要UI）

これらを完了すれば、Production環境を安全に公開できる。

## 更新されたファイル

- `CLAUDE.md`: GitHub Integration、Active Development Priorities セクション更新
  - Milestone情報追加
  - 開発優先順位を8週間のタイムラインに整理

## 補足情報

### 404エラー分析

**存在するページ**:
- `/` - トップページ（ウォッチリスト表示） ✅
- `/auth/*` - Google OAuth認証 ✅
- `/watchlist` - ウォッチリスト画面 ✅

**404になるページ（実装必要）**:
1. `/companies/[code]` - 企業詳細ページ（#23）
2. `/screening` - スクリーニング画面（#24）
3. `/search` - 企業検索ページ（#150）

Backend APIは完成済み（PR #79）なので、フロントエンド実装のみでOK。

### バッチジョブの現状

- **株価データ更新**: PR #92で完全実装済み（Docker cron、16:00 JST実行）
- **レート制限**: Token Bucket実装済み（PR #133）
- **EDINET四半期データ**: #143で実装予定（Infrastructure構築後）

## セッション成果

**処理Issue数**: 16件（削除1件、ラベル更新2件、マイルストーン割り当て15件）  
**マイルストーン作成**: 3件  
**Project #5追加確認**: 16件

Production公開とバッチジョブのクラウド運用に向けた明確なロードマップが確立された。
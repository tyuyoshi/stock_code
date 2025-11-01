# 2025/11/01 作業記録 - Issue管理とユーザー機能拡張

## 実施内容サマリー

### 1. GitHub Issue整理
- 全38個のIssueをGitHub Project #5に統合完了
- 重複Issue解消: #17をクローズ（#34と重複）、#34を再オープン
- 優先度ラベル設定（Critical/High/Medium）

### 2. Issue #34更新 - Google OAuth認証への変更
従来のJWT認証から**Google OAuth2.0**への大幅変更：
- Google Identity Platform / Firebase Auth使用
- 会員登録フロー追加（初回ログイン時）
- ユーザー属性収集（投資経験、スタイル、興味業種等）
- プロファイル管理機能

### 3. 新規Issue作成（5件）

#### Issue #49: アナリストカバレッジ属性管理
- 銘柄へのカバレッジ情報付与
- レーティング管理（Buy/Hold/Sell）
- コンセンサス予想の計算
- 目標株価の追跡

#### Issue #50: ウォッチリスト機能実装
- お気に入り銘柄管理
- ポートフォリオ分析
- リアルタイム価格更新
- 複数リスト作成、共有機能

#### Issue #51: アラート通知システム実装
- 価格変動アラート
- イベント通知（決算、配当等）
- Email/Push通知対応
- 通知頻度制御

#### Issue #52: ユーザー行動分析と銘柄タグ付けシステム
- 行動トラッキング実装
- 自動タグ生成（「個人投資家注目」等）
- レコメンデーションエンジン
- プライバシー保護対応

#### Issue #53: Google Analytics 4統合
- GA4導入とカスタムイベント設定
- コンバージョントラッキング
- ユーザープロパティ設定
- BigQuery連携

## 技術選定決定

### 認証・ユーザー管理
- **Google Identity Platform** or **Firebase Auth**
- OAuth2.0フロー実装

### 通知システム
- **SendGrid** or **Amazon SES**（Email）
- **Firebase Cloud Messaging**（Push通知）

### 分析基盤
- **Google Analytics 4**
- **BigQuery**（データウェアハウス）
- **scikit-learn**（レコメンデーション）

## Issue管理ルール（新規追加）

**重要**: 新規Issueは必ずGitHub Projectに追加すること

```bash
# Issue作成と同時にProjectへ追加
gh issue create --repo tyuyoshi/stock_code --title "..." --body "..."
gh project item-add 5 --owner tyuyoshi --url https://github.com/tyuyoshi/stock_code/issues/{NUMBER}
```

## 現在のプロジェクト状態

### 完了済み
- ✅ Issue #6: EDINET API連携・XBRL Parser
- ✅ Issue #13: 財務指標計算エンジン（60以上の指標）
- ✅ Issue #27: 初期セットアップ

### 最優先対応
1. Issue #30: セキュリティ脆弱性修正（CORS、Secret Keys）
2. Issue #32: テストカバレッジ実装（現在0%）

### 実装予定フェーズ
1. **Phase 1**: 認証基盤（#34）
2. **Phase 2**: ユーザー機能（#50, #51）
3. **Phase 3**: データ拡張（#49, #52）
4. **Phase 4**: 分析基盤（#53）

## Issue統計（2025/11/01時点）
- **Total**: 41 Issues作成
- **Active**: 36 Issues（重複除去後）
- **Closed**: 5 Issues
- **Open**: 36 Issues

## CLAUDE.md更新内容
1. 完了機能の更新（Issue #13完了を反映）
2. 新規ユーザー機能6件の追加
3. Issue管理ガイドラインの追加
4. GitHub Project必須利用の明記
5. 優先度別Issue状態の更新

## 次回セッション推奨タスク
1. Issue #30のセキュリティ修正（最優先）
2. Issue #32のテスト実装開始
3. Issue #31のAlembic設定完了
4. Issue #34のGoogle OAuth実装着手
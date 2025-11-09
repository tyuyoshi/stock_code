# Language Guidelines for Stock Code Project

## Date: 2025-11-09

## Overview

This document establishes the official language guidelines for the Stock Code project. All development work, documentation, and communication must follow these rules for consistency and effective team collaboration.

---

## Language Rules / 言語ルール

### 1. Thinking, Design, and Coding (思考・設計・コーディング)

**Language**: **English** (英語)

**Scope**:
- Internal reasoning and problem-solving
- Architecture design and technical design documents
- Code implementation (functions, classes, variables, constants)
- Code comments and docstrings
- Type hints and annotations
- API endpoint names and routes
- Database schema and model names

**Rationale**:
- Industry standard for code readability
- Enables international collaboration
- Consistent with libraries and frameworks (FastAPI, Next.js, etc.)
- Easier debugging and stack overflow searches

**Examples**:
```python
def calculate_roe(net_income: float, equity: float) -> float:
    """Calculate Return on Equity (ROE) ratio."""
    if equity == 0:
        return 0.0
    return (net_income / equity) * 100
```

```typescript
interface CompanyData {
  code: string;
  name: string;
  financialIndicators: FinancialIndicators;
}
```

---

### 2. Documentation and Reports (ドキュメント・レポート)

**Language**: **Japanese** (日本語)

**Scope**:
- Session reports and progress updates to users
- User-facing documentation (README sections for Japanese users)
- Feature explanations and summaries
- Development status reports
- Technical decisions explanations for stakeholders

**Rationale**:
- Project stakeholders are Japanese
- Better understanding for product owners
- Clearer communication of business value
- Aligns with user-facing content

**Examples**:
```markdown
## 開発進捗レポート - 2025/11/09

本日のセッションでは、WebSocketのメモリリーク問題を解決し、以下の成果を達成しました：

1. ✅ 集約型価格配信システムの設計完了
2. ✅ APIレート制限機構の実装準備完了
3. 🔄 フロントエンドWebSocketクライアントの開発開始
```

---

### 3. GitHub Issues and Pull Requests (Issue・PR)

**Language**: **Japanese** (日本語)

**Scope**:
- Issue titles and descriptions
- Issue comments and discussions
- Pull request titles and descriptions
- Pull request review comments
- Commit messages

**Rationale**:
- Team collaboration in Japanese
- Product backlog managed in Japanese
- Easier for non-technical stakeholders to understand
- Consistent with project management tools

**Format Convention**:
- Use conventional commits format in Japanese:
  - `機能:` (feat) - New features
  - `修正:` (fix) - Bug fixes
  - `パフォーマンス:` (perf) - Performance improvements
  - `リファクタリング:` (refactor) - Code refactoring
  - `ドキュメント:` (docs) - Documentation changes
  - `テスト:` (test) - Test additions/changes
  - `セキュリティ:` (security) - Security fixes
  - `インフラ:` (infra) - Infrastructure changes

**Examples**:

**Issue Title**:
```
機能: ウォッチリストのリアルタイム価格更新機能の実装
```

**Issue Description**:
```markdown
## 概要
ユーザーのウォッチリストに登録された銘柄の株価をWebSocketでリアルタイム更新する機能を実装する。

## 受け入れ条件
- [ ] WebSocketクライアントの実装
- [ ] 価格更新のUI反映
- [ ] エラーハンドリングと再接続機構

## 技術仕様
- WebSocket接続: `/ws/watchlist/{watchlist_id}`
- 更新間隔: 5秒
- 対象データ: 最新価格、前日比、騰落率
```

**Pull Request Title**:
```
修正: WebSocket接続時のメモリリーク問題を解消 (#125)
```

**Commit Message**:
```
feat: 企業詳細ページのレスポンシブUIを実装

- Tailwind CSSによるモバイル対応
- 財務指標の可視化コンポーネント追加
- ローディング状態の改善
```

---

### 4. Code Comments (コード内コメント)

**Language**: **English** (英語)

**Scope**:
- Inline comments
- Function/class docstrings
- Module documentation
- TODO comments
- Complex logic explanations

**Rationale**:
- Maintains code readability for international developers
- Consistent with open-source best practices
- Easier to use with AI coding assistants
- Documentation generation tools expect English

**Examples**:
```python
class FinancialDataProcessor:
    """Process and calculate financial indicators from XBRL data.
    
    This class handles data transformation from raw EDINET XBRL format
    to normalized financial indicators used in the application.
    """
    
    def normalize_data(self, raw_data: dict) -> dict:
        """Normalize XBRL data to standard format.
        
        Args:
            raw_data: Raw XBRL data from EDINET API
            
        Returns:
            Normalized financial data dictionary
            
        Raises:
            ValidationError: If required fields are missing
        """
        # TODO: Add support for consolidated statements
        # Handle non-standard XBRL taxonomies for older reports
        pass
```

---

## Implementation Checklist

When creating new content, verify language usage:

### Code Files (.py, .ts, .tsx)
- [ ] Function/class names in English
- [ ] Variable names in English
- [ ] Comments in English
- [ ] Docstrings in English

### GitHub Issues
- [ ] Title in Japanese with conventional prefix
- [ ] Description in Japanese
- [ ] Technical details can include English code snippets
- [ ] Comments in Japanese

### Pull Requests
- [ ] Title in Japanese with conventional prefix + issue reference
- [ ] Description in Japanese
- [ ] Review comments in Japanese
- [ ] Code diff comments can reference English code

### Commit Messages
- [ ] Subject line in Japanese
- [ ] Body in Japanese (if detailed explanation needed)
- [ ] Follow conventional commits format in Japanese

### Documentation
- [ ] User-facing docs in Japanese (README, guides)
- [ ] Developer comments in code: English
- [ ] Technical architecture docs: English or Japanese (context-dependent)

---

## Migration Plan

**Existing English Issues**: Translate to Japanese progressively
- Priority 1 (CRITICAL): Issues #125, #126, #123
- Priority 2 (HIGH): Issues #23, #24, #100, #118, #90
- Priority 3 (MEDIUM): Issues #111-115, #128-130
- Priority 4 (LOW): All remaining open issues

**Timeline**: Complete by 2025-11-09 (today)

---

## References

- CLAUDE.md: Language Guidelines section
- GitHub Conventional Commits: https://www.conventionalcommits.org/
- Project documentation standards: backend/README.md, frontend/README.md

---

## Last Updated

- Date: 2025-11-09
- Updated by: Claude Code (Session: Major Issue Cleanup)
- Change: Initial language guidelines establishment
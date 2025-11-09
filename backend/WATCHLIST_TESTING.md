# ウォッチリスト機能 - 動作確認手順書

## 前提条件

### 環境セットアップ
```bash
# Docker起動確認
cd /Users/tsuyoshi-hasegawa/Documents/workspace/github/private/stock_code
docker compose ps

# 期待される出力:
# stock_code_db      postgres:15-alpine   Up (healthy)
# stock_code_redis   redis:7-alpine       Up (healthy)
# stock_code_backend stock_code-backend   Up

# Migration確認
cd backend
source venv/bin/activate
alembic current

# 期待される出力:
# 463ee6f38c6b (head) - add watchlists and watchlist_items tables
```

### サーバー起動
```bash
# Option 1: Dockerで起動 (推奨)
docker compose up

# Option 2: ローカルで起動 (開発用)
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## テストデータ準備

### 1. データベース接続
```bash
docker exec -it stock_code_db psql -U stockcode -d stockcode
```

### 2. テストユーザー作成

```sql
-- Google OAuth経由を想定したユーザー作成 (重複回避)
INSERT INTO users (google_id, email, name, role, is_active, created_at) 
VALUES 
  ('test_free_user', 'free@example.com', 'Free User', 'free', true, NOW()),
  ('test_premium_user', 'premium@example.com', 'Premium User', 'premium', true, NOW())
ON CONFLICT (google_id) DO NOTHING;

-- ユーザーID確認
SELECT id, email, role FROM users WHERE google_id LIKE 'test_%';
```

### 3. テスト企業データ作成

```sql
-- 既存データ確認
SELECT id, ticker_symbol, company_name_jp FROM companies 
WHERE ticker_symbol IN ('7203', '6758', '9984', '4063', '8035');

-- 不足している企業のみ追加 (ON CONFLICT で重複回避)
INSERT INTO companies (ticker_symbol, edinet_code, company_name_jp, company_name_en, market_division, industry_code, industry_name)
VALUES 
  ('7203', 'E02144', 'トヨタ自動車', 'Toyota Motor Corporation', 'Prime', '3050', '自動車'),
  ('6758', 'E01777', 'ソニーグループ', 'Sony Group Corporation', 'Prime', '5250', '電気機器'),
  ('9984', 'E04425', 'ソフトバンクグループ', 'SoftBank Group Corp.', 'Prime', '9050', '情報・通信'),
  ('4063', 'E00990', '信越化学工業', 'Shin-Etsu Chemical Co., Ltd.', 'Prime', '4050', '化学'),
  ('8035', 'E03466', '東京エレクトロン', 'Tokyo Electron Limited', 'Prime', '5250', '電気機器')
ON CONFLICT (ticker_symbol) DO NOTHING;

-- 再確認 (5件揃っていることを確認)
SELECT id, ticker_symbol, company_name_jp FROM companies 
WHERE ticker_symbol IN ('7203', '6758', '9984', '4063', '8035')
ORDER BY ticker_symbol;
```

### 4. 株価データ作成 (Optional - 分析機能用)

```sql
-- 既存の株価データを確認
SELECT COUNT(*) FROM stock_prices sp
JOIN companies c ON sp.company_id = c.id
WHERE c.ticker_symbol IN ('7203', '6758', '9984', '4063', '8035');

-- 株価データがない場合のみ追加 (31日分 × 5銘柄 = 155件)
INSERT INTO stock_prices (company_id, date, open_price, high_price, low_price, close_price, volume, data_source)
SELECT 
  c.id,
  CURRENT_DATE - (i || ' days')::interval,
  2000 + (random() * 500)::numeric(10,2),
  2200 + (random() * 500)::numeric(10,2),
  1900 + (random() * 500)::numeric(10,2),
  2100 + (random() * 500)::numeric(10,2),
  (10000000 + random() * 5000000)::bigint,
  'yahoo_finance'
FROM companies c
CROSS JOIN generate_series(0, 30) AS i
WHERE c.ticker_symbol IN ('7203', '6758', '9984', '4063', '8035');

-- 作成確認
SELECT 
  c.ticker_symbol,
  c.company_name_jp,
  COUNT(sp.id) as price_count,
  MIN(sp.date) as oldest_date,
  MAX(sp.date) as latest_date
FROM companies c
LEFT JOIN stock_prices sp ON c.id = sp.company_id
WHERE c.ticker_symbol IN ('7203', '6758', '9984', '4063', '8035')
GROUP BY c.ticker_symbol, c.company_name_jp
ORDER BY c.ticker_symbol;
```

### (オプション) データクリーンアップ

テストデータを全削除してクリーンスタートする場合:

```sql
-- 警告: 全データが削除されます
TRUNCATE TABLE stock_prices CASCADE;
TRUNCATE TABLE watchlist_items CASCADE;
TRUNCATE TABLE watchlists CASCADE;
TRUNCATE TABLE financial_indicators CASCADE;
TRUNCATE TABLE financial_statements CASCADE;
TRUNCATE TABLE companies CASCADE;
TRUNCATE TABLE users CASCADE;

-- その後、ステップ2-4を再実行
```

---

## API動作確認

### 認証準備

#### Option A: Google OAuthでログイン (推奨)
```bash
# ブラウザで以下にアクセス
open http://localhost:8000/api/v1/auth/google/login

# コールバック後、DevToolsでCookieから session_token を確認
# または、レスポンスJSONから取得

export SESSION_TOKEN="取得したトークン"
```

#### Option B: Redisに直接セッション作成 (開発用)
```bash
# Redis CLI接続
docker exec -it stock_code_redis redis-cli

# セッション作成 (user_id=1 の場合)
SET "session:test_session_token_123" "{\"user_id\": 1}" EX 604800

# 確認
GET "session:test_session_token_123"

# Bash環境変数設定
export SESSION_TOKEN="test_session_token_123"
```

---

### テストケース実行

#### 1. ウォッチリスト作成
```bash
curl -X POST http://localhost:8000/api/v1/watchlists/ \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "日本株ポートフォリオ",
    "description": "優良大型株中心のウォッチリスト",
    "is_public": false,
    "display_order": 0
  }'

# 期待されるレスポンス (201 Created):
# {
#   "id": 1,
#   "user_id": 1,
#   "name": "日本株ポートフォリオ",
#   "description": "優良大型株中心のウォッチリスト",
#   "is_public": false,
#   "display_order": 0,
#   "created_at": "2025-11-09T12:00:00Z",
#   "updated_at": null
# }

# WATCHLIST_ID を記録
export WATCHLIST_ID=1
```

#### 2. ウォッチリスト一覧取得
```bash
curl -X GET http://localhost:8000/api/v1/watchlists/ \
  -H "Authorization: Bearer $SESSION_TOKEN"

# 期待されるレスポンス (200 OK):
# [
#   {
#     "id": 1,
#     "name": "日本株ポートフォリオ",
#     ...
#   }
# ]
```

#### 3. 銘柄追加 (トヨタ)
```bash
curl -X POST http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID/stocks \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "display_order": 0,
    "memo": "自動車セクターのリーディングカンパニー。EV戦略に注目。",
    "tags": ["自動車", "大型株", "配当"],
    "quantity": "100",
    "purchase_price": "2500.50"
  }'

# 期待されるレスポンス (201 Created):
# {
#   "id": 1,
#   "watchlist_id": 1,
#   "company_id": 1,
#   "display_order": 0,
#   "memo": "自動車セクターのリーディングカンパニー。EV戦略に注目。",
#   "tags": ["自動車", "大型株", "配当"],
#   "quantity": "100.00",
#   "purchase_price": "2500.50",
#   "added_at": "2025-11-09T12:05:00Z"
# }
```

#### 4. 複数銘柄追加
```bash
# ソニー追加
curl -X POST http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID/stocks \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 2,
    "display_order": 1,
    "memo": "エンタメ・半導体・金融と多角化",
    "tags": ["電気機器", "グロース"],
    "quantity": "50",
    "purchase_price": "15000.00"
  }'

# ソフトバンク追加
curl -X POST http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID/stocks \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 3,
    "display_order": 2,
    "memo": "AI・通信・投資事業",
    "tags": ["情報通信", "テクノロジー"]
  }'
```

#### 5. ウォッチリスト詳細取得 (items含む)
```bash
curl -X GET http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID \
  -H "Authorization: Bearer $SESSION_TOKEN" | jq .

# 期待されるレスポンス:
# {
#   "id": 1,
#   "name": "日本株ポートフォリオ",
#   "description": "...",
#   "items": [
#     {
#       "id": 1,
#       "company_id": 1,
#       "memo": "自動車セクター...",
#       "tags": ["自動車", "大型株", "配当"],
#       "quantity": "100.00",
#       "purchase_price": "2500.50",
#       ...
#     },
#     ... (3銘柄)
#   ]
# }
```

#### 6. ウォッチリスト更新
```bash
curl -X PUT http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "日本株コアポートフォリオ（更新）",
    "is_public": true
  }'

# 期待されるレスポンス (200 OK):
# {
#   "id": 1,
#   "name": "日本株コアポートフォリオ（更新）",
#   "is_public": true,
#   ...
# }
```

#### 7. プラン制限テスト (Free User)

**7-1. ウォッチリスト制限**
```bash
# 2つ目のウォッチリスト作成試行 → 403 Forbidden
curl -X POST http://localhost:8000/api/v1/watchlists/ \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2つ目のウォッチリスト",
    "is_public": false,
    "display_order": 1
  }'

# 期待されるエラー (403 Forbidden):
# {
#   "detail": "Plan limit reached: free plan allows maximum 1 watchlists"
# }
```

**7-2. 銘柄数制限**
```bash
# 20銘柄追加後、21個目を追加試行
# (信越化学工業、東京エレクトロン等を追加して20銘柄に)

# ... (15銘柄追加スクリプト省略) ...

# 21個目追加 → 403 Forbidden
curl -X POST http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID/stocks \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 5,
    "display_order": 20
  }'

# 期待されるエラー (403 Forbidden):
# {
#   "detail": "Plan limit reached: free plan allows maximum 20 items per watchlist"
# }
```

#### 8. 重複追加防止
```bash
# 既に追加済みの銘柄を再追加試行 → 409 Conflict
curl -X POST http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID/stocks \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "display_order": 10
  }'

# 期待されるエラー (409 Conflict):
# {
#   "detail": "Company already exists in this watchlist"
# }
```

#### 9. 銘柄削除
```bash
# トヨタ (company_id=1) を削除
curl -X DELETE http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID/stocks/1 \
  -H "Authorization: Bearer $SESSION_TOKEN"

# 期待されるレスポンス (204 No Content)
# (レスポンスボディなし)

# 削除確認
curl -X GET http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID \
  -H "Authorization: Bearer $SESSION_TOKEN" | jq '.items | length'

# 期待される出力: 2 (3銘柄から1銘柄削除)
```

#### 10. ウォッチリスト削除
```bash
curl -X DELETE http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID \
  -H "Authorization: Bearer $SESSION_TOKEN"

# 期待されるレスポンス (204 No Content)

# 削除確認
curl -X GET http://localhost:8000/api/v1/watchlists/ \
  -H "Authorization: Bearer $SESSION_TOKEN"

# 期待される出力: []
```

#### 11. 認証なしアクセス (エラーケース)
```bash
curl -X GET http://localhost:8000/api/v1/watchlists/

# 期待されるエラー (401 Unauthorized):
# {
#   "detail": "Not authenticated"
# }
```

#### 12. 他ユーザーのウォッチリストアクセス (エラーケース)
```bash
# ユーザー2のセッション作成
docker exec -it stock_code_redis redis-cli
SET "session:user2_token" "{\"user_id\": 2}" EX 604800

# ユーザー2でウォッチリスト作成
export SESSION_TOKEN_USER2="user2_token"
curl -X POST http://localhost:8000/api/v1/watchlists/ \
  -H "Authorization: Bearer $SESSION_TOKEN_USER2" \
  -H "Content-Type: application/json" \
  -d '{"name": "User2 Watchlist", "is_public": false, "display_order": 0}'

# ユーザー2のウォッチリストIDを取得 (例: id=2)
export WATCHLIST_ID_USER2=2

# ユーザー1でユーザー2のウォッチリストにアクセス試行 → 403 Forbidden
curl -X GET http://localhost:8000/api/v1/watchlists/$WATCHLIST_ID_USER2 \
  -H "Authorization: Bearer $SESSION_TOKEN"

# 期待されるエラー (403 Forbidden):
# {
#   "detail": "Not authorized to access this watchlist"
# }
```

---

## Swagger UIでの動作確認

### 1. Swagger UIアクセス
```bash
open http://localhost:8000/api/docs
```

### 2. 認証設定
1. 右上の「Authorize」ボタンをクリック
2. `Authorization (http, Bearer)` に `$SESSION_TOKEN` の値を入力
3. 「Authorize」→「Close」

### 3. Endpointテスト
`watchlists` セクションで各エンドポイントを順番にテスト

**推奨テスト順序:**
1. `POST /api/v1/watchlists/` - ウォッチリスト作成
2. `GET /api/v1/watchlists/` - 一覧取得
3. `POST /api/v1/watchlists/{watchlist_id}/stocks` - 銘柄追加
4. `GET /api/v1/watchlists/{watchlist_id}` - 詳細取得
5. `PUT /api/v1/watchlists/{watchlist_id}` - 更新
6. `DELETE /api/v1/watchlists/{watchlist_id}/stocks/{company_id}` - 銘柄削除
7. `DELETE /api/v1/watchlists/{watchlist_id}` - ウォッチリスト削除

---

## データベース確認

### ウォッチリストテーブル確認
```sql
-- PostgreSQL接続
docker exec -it stock_code_db psql -U stockcode -d stockcode

-- ウォッチリスト一覧
SELECT id, user_id, name, is_public, created_at FROM watchlists;

-- 銘柄アイテム一覧
SELECT 
  wi.id,
  wi.watchlist_id,
  c.ticker_symbol,
  c.company_name_jp,
  wi.quantity,
  wi.purchase_price,
  wi.tags,
  wi.memo
FROM watchlist_items wi
JOIN companies c ON wi.company_id = c.id
ORDER BY wi.watchlist_id, wi.display_order;

-- ユーザー別ウォッチリスト統計
SELECT 
  u.email,
  u.role,
  COUNT(DISTINCT w.id) AS watchlist_count,
  COUNT(wi.id) AS total_items
FROM users u
LEFT JOIN watchlists w ON u.id = w.user_id
LEFT JOIN watchlist_items wi ON w.id = wi.watchlist_id
GROUP BY u.id, u.email, u.role;
```

---

## トラブルシューティング

### Migration未適用エラー
```bash
# エラー: relation "watchlists" does not exist
# 解決策:
cd backend
source venv/bin/activate
alembic upgrade head
```

### 認証エラー (401 Unauthorized)
```bash
# エラー: Not authenticated
# 解決策:
# 1. session_tokenの有効性確認
docker exec -it stock_code_redis redis-cli
GET "session:$SESSION_TOKEN"

# 2. Redisが起動しているか確認
docker compose ps redis

# 3. 新しいセッション作成
SET "session:new_token" "{\"user_id\": 1}" EX 604800
export SESSION_TOKEN="new_token"
```

### Docker起動エラー
```bash
# エラー: port already allocated
# 解決策:
docker compose down
lsof -ti:8000 | xargs kill -9  # ポート8000を使用中のプロセスを終了
docker compose up
```

---

## 自動テストスイート実行

### 全テスト実行
```bash
cd backend
source venv/bin/activate
pytest tests/test_watchlist.py -v

# 期待される出力:
# 16 passed in 1.01s
```

### カバレッジ確認
```bash
pytest tests/test_watchlist.py --cov=api.routers.watchlist --cov-report=term-missing

# 期待されるカバレッジ: 97%
```

---

## 完了チェックリスト

- [ ] Migration適用完了 (463ee6f38c6b)
- [ ] テストユーザー作成完了
- [ ] テスト企業データ作成完了
- [ ] Google OAuthログイン成功
- [ ] ウォッチリスト作成成功
- [ ] 銘柄追加成功 (3銘柄以上)
- [ ] ウォッチリスト詳細取得成功 (items含む)
- [ ] プラン制限動作確認 (Free: 1リスト/20銘柄)
- [ ] 重複追加防止確認
- [ ] 銘柄削除成功
- [ ] ウォッチリスト削除成功
- [ ] 他ユーザーアクセス拒否確認
- [ ] 自動テスト16個全て合格

全てチェック完了で動作確認OK！ ✅

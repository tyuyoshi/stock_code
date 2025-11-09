# WebSocket接続テストガイド

このガイドでは、WebSocketリアルタイム価格配信機能のテスト方法を説明します。

## 前提条件

### 1. サーバーの起動

```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload
```

サーバーが `http://localhost:8000` で起動していることを確認してください。

### 2. テストデータのセットアップ

WebSocket接続をテストする前に、テストデータ（ユーザー、ウォッチリスト、セッショントークン）を作成します：

```bash
cd backend
source venv/bin/activate
python setup_websocket_test.py
```

このスクリプトは以下を作成します：
- テストユーザー（`websocket@test.com`）
- テスト企業データ（トヨタ、ソニー）
- ウォッチリスト「リアルタイムテスト」
- セッショントークン（7日間有効）

**重要**: スクリプトの出力から以下の情報を保存してください：
- **Watchlist ID**: ウォッチリストの識別子
- **Session Token**: 認証用トークン

出力例：
```
📋 WebSocket接続情報:
  User ID:       10
  Watchlist ID:  2
  Session Token: JEgDFesRKEQhDd9XFt22f3kWAola20f4NOzt0EnkVmA
```

---

## テスト方法

3つのテスト方法を提供しています：

### 方法1: Python CLIツール（推奨）

**特徴:**
- ✅ 追加インストール不要（websocketsライブラリは既にインストール済み）
- ✅ 見やすい整形された出力
- ✅ リアルタイム価格更新、P&L計算を表示
- ✅ エラー処理とデバッグ情報

**使用方法:**

```bash
cd backend
source venv/bin/activate

# セットアップスクリプトで取得したIDとトークンを使用
python scripts/websocket_test_cli.py \
  --watchlist-id 2 \
  --token JEgDFesRKEQhDd9XFt22f3kWAola20f4NOzt0EnkVmA
```

**または、ラッパースクリプトを使用:**

```bash
cd backend
./scripts/test_websocket_connection.sh 2 JEgDFesRKEQhDd9XFt22f3kWAola20f4NOzt0EnkVmA
```

**出力例:**

```
================================================================================
WebSocket接続テスト
================================================================================
接続先:        ws://localhost:8000/api/v1/ws/watchlist/2/prices?token=JEgDFe...
ウォッチリストID: 2
トークン:      JEgDFesRKEQhDd9XFt2...
================================================================================

接続中...

✅ WebSocket接続成功！

価格更新を受信中... (Ctrl+Cで終了)

────────────────────────────────────────────────────────────────────────────────
📊 価格更新 #1
⏰ 時刻: 2025-11-09T17:30:00.123456
────────────────────────────────────────────────────────────────────────────────

  📈 トヨタ自動車株式会社 (7203)
     現在値:   ¥2,550.00
     変動:     +¥50.00 (+2.00%)
     保有数:   100株
     購入価格: ¥2,500.00
     評価損益: 💰 +¥5,000.00

  📉 ソニーグループ株式会社 (6758)
     現在値:   ¥12,800.00
     変動:     ¥-200.00 (-1.54%)
     保有数:   50株
     購入価格: ¥13,000.00
     評価損益: 📊 ¥-10,000.00
```

**終了方法:**
- `Ctrl+C` を押して優雅に終了します

---

### 方法2: wscat（Node.jsツール）

**特徴:**
- 業界標準のWebSocketテストツール
- シンプルなコマンドラインインターフェース
- 手動テストやデバッグに適している

**インストール:**

```bash
# Node.jsとnpmがインストールされている必要があります
npm install -g wscat
```

**使用方法:**

```bash
# セットアップスクリプトで取得したIDとトークンを使用
wscat -c "ws://localhost:8000/api/v1/ws/watchlist/2/prices?token=JEgDFesRKEQhDd9XFt22f3kWAola20f4NOzt0EnkVmA"
```

**出力例:**

```
Connected (press CTRL+C to quit)
< {"type":"price_update","watchlist_id":2,"stocks":[{"company_id":9,"ticker_symbol":"7203","company_name":"トヨタ自動車株式会社","current_price":2550.0,"change":50.0,"change_percent":2.0,"quantity":100.0,"purchase_price":2500.0,"unrealized_pl":5000.0},{"company_id":10,"ticker_symbol":"6758","company_name":"ソニーグループ株式会社","current_price":12800.0,"change":-200.0,"change_percent":-1.54,"quantity":50.0,"purchase_price":13000.0,"unrealized_pl":-10000.0}],"timestamp":"2025-11-09T17:30:00.123456"}
```

**終了方法:**
- `Ctrl+C` を押して終了します

---

### 方法3: 自動テストスイート

**特徴:**
- 包括的な単体テストと統合テスト
- CI/CD統合に適している
- WebSocket機能の全側面を検証

**使用方法:**

```bash
cd backend
source venv/bin/activate

# WebSocketテストのみ実行
pytest tests/test_websocket.py -v

# すべてのテストを実行
pytest -v

# カバレッジ付きで実行
pytest tests/test_websocket.py -v --cov=api.routers.websocket --cov-report=term-missing
```

**テスト内容:**
- ✅ ConnectionManager - 接続管理機能
- ✅ WebSocket認証 - セッション認証とアクセス制御
- ✅ 価格取得ロジック - Yahoo Finance統合とP&L計算
- ✅ 統合テスト - エンドツーエンドのWebSocket通信

**出力例:**

```
tests/test_websocket.py::TestConnectionManager::test_connect_and_disconnect PASSED
tests/test_websocket.py::TestConnectionManager::test_multiple_connections PASSED
tests/test_websocket.py::TestConnectionManager::test_send_personal_message PASSED
tests/test_websocket.py::TestConnectionManager::test_broadcast_to_watchlist PASSED
tests/test_websocket.py::TestConnectionManager::test_broadcast_handles_disconnected_clients PASSED
tests/test_websocket.py::TestWebSocketAuthentication::test_verify_watchlist_access_owner PASSED
tests/test_websocket.py::TestWebSocketAuthentication::test_verify_watchlist_access_public PASSED
tests/test_websocket.py::TestWebSocketAuthentication::test_verify_watchlist_access_denied PASSED
tests/test_websocket.py::TestWebSocketAuthentication::test_verify_watchlist_not_found PASSED
tests/test_websocket.py::TestFetchWatchlistPrices::test_fetch_prices_empty_watchlist PASSED
tests/test_websocket.py::TestFetchWatchlistPrices::test_fetch_prices_with_data PASSED
tests/test_websocket.py::TestFetchWatchlistPrices::test_fetch_prices_partial_data PASSED
tests/test_websocket.py::test_websocket_connection_with_auth PASSED
tests/test_websocket.py::test_websocket_connection_without_auth PASSED
tests/test_websocket.py::test_websocket_connection_invalid_token PASSED
tests/test_websocket.py::test_websocket_access_denied PASSED

============================== 16 passed in 5.43s ===============================
```

---

## メッセージフォーマット

WebSocketで受信するJSONメッセージの構造：

```json
{
  "type": "price_update",
  "watchlist_id": 2,
  "stocks": [
    {
      "company_id": 9,
      "ticker_symbol": "7203",
      "company_name": "トヨタ自動車株式会社",
      "current_price": 2550.0,
      "change": 50.0,
      "change_percent": 2.0,
      "quantity": 100.0,
      "purchase_price": 2500.0,
      "unrealized_pl": 5000.0
    }
  ],
  "timestamp": "2025-11-09T17:30:00.123456"
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `type` | string | メッセージタイプ（常に`"price_update"`） |
| `watchlist_id` | integer | ウォッチリストID |
| `stocks` | array | 銘柄データの配列 |
| `timestamp` | string | 価格更新時刻（ISO 8601形式） |

**銘柄データフィールド:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `company_id` | integer | 企業ID |
| `ticker_symbol` | string | 銘柄コード（例: 7203） |
| `company_name` | string | 企業名 |
| `current_price` | float/null | 現在価格（円） |
| `change` | float/null | 価格変動（円） |
| `change_percent` | float/null | 変動率（%） |
| `quantity` | float/null | 保有株数 |
| `purchase_price` | float/null | 購入価格（円） |
| `unrealized_pl` | float/null | 評価損益（円） |

**注意:**
- Yahoo Finance APIからデータを取得できない場合、価格関連フィールドは`null`になります
- 更新間隔は5秒です

---

## トラブルシューティング

### 接続エラー: サーバーが起動していません

**問題:**
```
❌ 接続拒否: サーバーが起動していません
```

**解決策:**
1. サーバーが起動しているか確認:
   ```bash
   curl http://localhost:8000/health
   ```

2. サーバーを起動:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn api.main:app --reload
   ```

---

### 認証エラー: トークンが無効です

**問題:**
```
❌ 接続失敗: HTTPステータスコード 401
   認証エラー: トークンが無効です
```

**原因:**
- トークンの有効期限切れ（7日間）
- 誤ったトークン
- Redisセッションが削除された

**解決策:**
1. 新しいセッショントークンを生成:
   ```bash
   python setup_websocket_test.py
   ```

2. 出力された新しいトークンを使用してテスト

---

### アクセス拒否: ウォッチリストへのアクセス権限がありません

**問題:**
```
❌ 接続失敗: HTTPステータスコード 403
   アクセス拒否: ウォッチリストへのアクセス権限がありません
```

**原因:**
- 他のユーザーのプライベートウォッチリストにアクセスしようとしている
- ウォッチリストIDが誤っている

**解決策:**
1. 正しいウォッチリストIDを使用:
   ```bash
   python setup_websocket_test.py
   ```

2. 出力されたWatchlist IDを確認

---

### エラー: ウォッチリストが見つかりません

**問題:**
```
❌ 接続失敗: HTTPステータスコード 404
   エラー: ウォッチリストが見つかりません
```

**原因:**
- 存在しないウォッチリストID
- テストデータがクリーンアップされた

**解決策:**
1. テストデータを再作成:
   ```bash
   python setup_websocket_test.py
   ```

---

### タイムアウト: メッセージを受信していません

**問題:**
```
⏱️  タイムアウト: 30秒間メッセージを受信していません
```

**原因:**
- WebSocket接続は成功しているが、価格データの更新がない
- Yahoo Finance APIからデータを取得できない
- ウォッチリストに銘柄が登録されていない

**解決策:**
1. ウォッチリストにアイテムが存在するか確認
2. サーバーログを確認:
   ```bash
   # Uvicornのターミナルでエラーログを確認
   ```

3. Yahoo Finance APIの状態を確認

---

### websocketsパッケージが見つかりません

**問題:**
```
ModuleNotFoundError: No module named 'websockets'
```

**解決策:**
```bash
source venv/bin/activate
pip install websockets
```

---

## クリーンアップ

テスト終了後、テストデータをクリーンアップ：

```bash
cd backend
source venv/bin/activate

# 通常のクリーンアップ（企業データは保持）
python cleanup_websocket_test.py

# 完全なクリーンアップ（企業データも削除）
python cleanup_websocket_test.py --all
```

**クリーンアップ内容:**
- ✅ テストユーザー削除
- ✅ ウォッチリストとアイテム削除（カスケード）
- ✅ Redisセッション削除
- ⚠️  企業データは保持（他のテストで使用される可能性があるため）

---

## 参考情報

### WebSocketエンドポイント

```
ws://localhost:8000/api/v1/ws/watchlist/{watchlist_id}/prices?token={session_token}
```

**パラメータ:**
- `watchlist_id`: ウォッチリストID（パスパラメータ）
- `token`: セッショントークン（クエリパラメータ）

### 更新頻度

- **デフォルト**: 5秒間隔
- **初回接続時**: 即座に初期データを送信
- **以降**: 5秒ごとに最新価格を自動送信

### セッション有効期限

- **デフォルト**: 7日間
- **延長**: ログインし直すか、新しいセッションを作成

### 同時接続数

- **制限なし**: 同一ウォッチリストに複数のクライアントが同時接続可能
- **ブロードキャスト**: すべての接続クライアントに同じ価格更新を配信

---

## 関連ドキュメント

- [WebSocket API実装](../api/routers/websocket.py)
- [WebSocketテストスイート](../tests/test_websocket.py)
- [ウォッチリスト管理API](../api/routers/watchlist.py)
- [Yahoo Finance統合](../services/yahoo_finance_client.py)
- [セッション管理](../core/sessions.py)

---

## フィードバック

問題や改善提案がある場合は、GitHubでIssueを作成してください：
https://github.com/tyuyoshi/stock_code/issues

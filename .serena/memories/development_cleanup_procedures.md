# 開発作業のクリーンアップ手順

## 重要な原則

**すべての開発作業後は必ずクリーンアップを実行する**

## WebSocketテストデータのクリーンアップ

### 対象データ
- テストユーザー（websocket@test.com）
- テスト用ウォッチリスト
- テスト用セッショントークン（Redis）

### クリーンアップコマンド
```bash
cd backend
source venv/bin/activate
python cleanup_websocket_test.py
```

## 一般的なクリーンアップ手順

### 1. データベース
```sql
-- テストユーザーの削除（カスケードで関連データも削除）
DELETE FROM users WHERE email LIKE '%@test.com';

-- テストウォッチリストの削除
DELETE FROM watchlists WHERE name LIKE '%テスト%';

-- テスト企業データの削除（慎重に）
-- DELETE FROM companies WHERE ticker_symbol IN ('TEST1', 'TEST2');
```

### 2. Redis
```bash
# Redisの全データクリア（開発環境のみ）
docker exec stock_code_redis redis-cli FLUSHALL

# 特定パターンのキー削除
docker exec stock_code_redis redis-cli --scan --pattern "session:*" | xargs docker exec stock_code_redis redis-cli DEL
```

### 3. ログファイル
```bash
# バッチジョブログのクリーンアップ
rm -rf scheduler_logs/*.log

# アプリケーションログ
truncate -s 0 backend/logs/*.log
```

### 4. 一時ファイル
```bash
# Pythonキャッシュ
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# pytest キャッシュ
rm -rf .pytest_cache/
rm -rf backend/.pytest_cache/
```

## ブランチ作業後のクリーンアップ

```bash
# 作業ブランチの削除（マージ後）
git branch -d feature/issue-XXX-branch-name

# リモートブランチの削除
git push origin --delete feature/issue-XXX-branch-name

# 不要なリモート参照の削除
git remote prune origin
```

## Dockerクリーンアップ

```bash
# 停止中のコンテナ削除
docker container prune

# 未使用イメージ削除（タグなし）
docker image prune

# 未使用ネットワーク削除
docker network prune

# ⚠️ 注意：ボリュームは削除しない（データ消失の危険）
# docker volume prune  # 実行禁止
```

## テスト実行前のクリーンアップ

```bash
# テストデータベースのリセット
cd backend
source venv/bin/activate
alembic downgrade base
alembic upgrade head

# テストキャッシュクリア
pytest --cache-clear
```

## セッション異常時の対処

```python
# Pythonセッションでエラーが残る場合
db.rollback()  # トランザクションのロールバック
db.close()     # セッションクローズ
db = Session()  # 新しいセッション作成
```

## 開発終了時チェックリスト

- [ ] テストデータを削除したか
- [ ] 不要なログファイルを削除したか
- [ ] 作業ブランチをクリーンアップしたか
- [ ] Dockerコンテナを停止したか
- [ ] Redisセッションをクリアしたか
- [ ] .envファイルに本番情報が含まれていないか確認

## トラブルシューティング

### duplicate key エラーの対処
```python
# 既存データチェック＆作成パターン
existing = db.query(Model).filter_by(unique_field=value).first()
if not existing:
    new_obj = Model(unique_field=value)
    db.add(new_obj)
    db.commit()
```

### PendingRollbackError の対処
```python
try:
    # データベース操作
    db.commit()
except Exception as e:
    db.rollback()  # 必ずロールバック
    raise
```

## 重要な注意事項

1. **本番環境では絶対にクリーンアップスクリプトを実行しない**
2. **docker volume prune は絶対に実行しない（データ消失）**
3. **テストデータには必ず識別可能な命名規則を使用する**
   - メール: `*@test.com`
   - 名前: `*テスト*`
   - ID: `test_*`

最終更新: 2025-11-09
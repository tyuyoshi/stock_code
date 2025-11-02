# Docker Compose コマンドの更新

## 重要な変更点（2025年11月2日確認）
Docker Composeコマンドは`docker-compose`（ハイフン）から`docker compose`（スペース）に変更されました。

### 旧コマンド（非推奨）
```bash
docker-compose up
docker-compose down
docker-compose ps
docker-compose logs
```

### 新コマンド（使用すべき）
```bash
docker compose up
docker compose down
docker compose ps
docker compose logs
```

### 影響範囲
- スクリプト内のコマンド
- ドキュメント（README.md、CLAUDE.md等）
- CI/CD設定
- 開発者向けの手順書

この変更は Docker の公式な仕様変更であり、今後は全て`docker compose`（スペース）を使用する。
# 開発基本方針

## 仮想環境の使用（重要）
**基本原則**: ローカル環境を汚さないため、Pythonパッケージのインストールやコマンド実行は必ず仮想環境内で行う。

### 実行方法
```bash
# backend ディレクトリでの作業
cd backend

# 仮想環境の有効化（既存のvenv使用）
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# コマンド実行例
(venv) $ alembic init alembic
(venv) $ pip install <package>
(venv) $ pytest
```

### 対象コマンド
- pip install / pip freeze
- alembic コマンド全般
- pytest / black / flake8 / mypy
- python スクリプトの実行
- その他Pythonツール

### Docker環境との使い分け
- ローカル開発: 仮想環境を使用
- 統合テスト: docker-compose を使用
- 本番環境: Dockerコンテナ内で実行

### 注意事項
- requirements.txt の更新時は `pip freeze` ではなく手動管理
- 仮想環境のパスは .gitignore に含める
- CI/CDではDockerまたは専用の仮想環境を使用

この方針は 2025年11月2日に確立され、今後の全ての開発作業に適用される。
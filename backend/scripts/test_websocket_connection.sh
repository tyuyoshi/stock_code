#!/bin/bash
#
# WebSocket接続テスト用ラッパースクリプト
#
# 使用方法:
#   cd backend
#   ./scripts/test_websocket_connection.sh
#

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

echo "======================================================================"
echo "WebSocket接続テスト"
echo "======================================================================"
echo ""

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "❌ エラー: 仮想環境が見つかりません"
    echo "   以下のコマンドで仮想環境を作成してください:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 仮想環境をアクティベート
echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate

# websocketsパッケージの確認
if ! python -c "import websockets" 2>/dev/null; then
    echo "⚠️  websocketsパッケージがインストールされていません"
    echo "   インストール中..."
    pip install websockets
fi

echo ""

# セットアップスクリプトが実行されているか確認
echo "📋 テストデータのセットアップ状態を確認中..."
echo ""

# パラメータが提供されていない場合、セットアップを促す
if [ $# -lt 2 ]; then
    echo "⚠️  コマンドライン引数が不足しています"
    echo ""
    echo "使用方法:"
    echo "  $0 <WATCHLIST_ID> <SESSION_TOKEN>"
    echo ""
    echo "または、先にテストデータをセットアップしてください:"
    echo "  python setup_websocket_test.py"
    echo ""
    echo "セットアップスクリプトの出力から以下を取得してください:"
    echo "  - Watchlist ID"
    echo "  - Session Token"
    echo ""

    # セットアップスクリプトの実行を提案
    read -p "今すぐセットアップスクリプトを実行しますか? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python setup_websocket_test.py
        echo ""
        echo "======================================================================"
        echo "上記の出力から Watchlist ID と Session Token を使用して"
        echo "再度このスクリプトを実行してください:"
        echo "  $0 <WATCHLIST_ID> <SESSION_TOKEN>"
        echo "======================================================================"
    fi
    exit 1
fi

WATCHLIST_ID=$1
SESSION_TOKEN=$2
WS_URL="${3:-ws://localhost:8000}"

echo "======================================================================"
echo "接続パラメータ:"
echo "  Watchlist ID: $WATCHLIST_ID"
echo "  Token:        ${SESSION_TOKEN:0:20}..."
echo "  URL:          $WS_URL"
echo "======================================================================"
echo ""

# CLIツールを実行
python scripts/websocket_test_cli.py \
    --watchlist-id "$WATCHLIST_ID" \
    --token "$SESSION_TOKEN" \
    --url "$WS_URL"

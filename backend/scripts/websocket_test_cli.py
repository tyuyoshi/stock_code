#!/usr/bin/env python3
"""
WebSocket接続テスト用CLIツール

使用方法:
    # セットアップスクリプトで生成されたトークンを使用
    python scripts/websocket_test_cli.py

    # カスタムパラメータで実行
    python scripts/websocket_test_cli.py --watchlist-id 2 --token YOUR_TOKEN --url ws://localhost:8000
"""

import asyncio
import argparse
import json
import sys
import signal
from datetime import datetime
from typing import Optional
import websockets
from websockets.exceptions import WebSocketException


class WebSocketTestClient:
    """WebSocket接続テスト用クライアント"""

    def __init__(self, url: str, watchlist_id: int, token: str):
        self.url = url
        self.watchlist_id = watchlist_id
        self.token = token
        self.ws_url = f"{url}/api/v1/ws/watchlist/{watchlist_id}/prices?token={token}"
        self.message_count = 0
        self.running = True

    def print_header(self):
        """ヘッダー情報を表示"""
        print("=" * 80)
        print("WebSocket接続テスト")
        print("=" * 80)
        print(f"接続先:        {self.ws_url}")
        print(f"ウォッチリストID: {self.watchlist_id}")
        print(f"トークン:      {self.token[:20]}...")
        print("=" * 80)
        print("\n接続中...\n")

    def print_message(self, data: dict):
        """受信メッセージを整形して表示"""
        self.message_count += 1

        print(f"\n{'─' * 80}")
        print(f"📊 価格更新 #{self.message_count}")
        print(f"⏰ 時刻: {data.get('timestamp', 'N/A')}")
        print(f"{'─' * 80}")

        stocks = data.get('stocks', [])
        if not stocks:
            print("  ℹ️  銘柄データなし")
            return

        for stock in stocks:
            ticker = stock.get('ticker_symbol', 'N/A')
            name = stock.get('company_name', 'N/A')
            price = stock.get('current_price')
            change = stock.get('change')
            change_pct = stock.get('change_percent')
            quantity = stock.get('quantity')
            purchase_price = stock.get('purchase_price')
            unrealized_pl = stock.get('unrealized_pl')

            # 価格情報
            if price is not None:
                price_str = f"¥{price:,.2f}"
            else:
                price_str = "N/A"

            # 変動情報
            if change is not None and change_pct is not None:
                if change >= 0:
                    change_str = f"+¥{change:.2f} (+{change_pct:.2f}%)"
                    emoji = "📈"
                else:
                    change_str = f"¥{change:.2f} ({change_pct:.2f}%)"
                    emoji = "📉"
            else:
                change_str = "N/A"
                emoji = "➖"

            print(f"\n  {emoji} {name} ({ticker})")
            print(f"     現在値:   {price_str}")
            print(f"     変動:     {change_str}")

            # ポジション情報
            if quantity is not None and purchase_price is not None:
                print(f"     保有数:   {quantity:.0f}株")
                print(f"     購入価格: ¥{purchase_price:,.2f}")

                if unrealized_pl is not None:
                    if unrealized_pl >= 0:
                        pl_str = f"+¥{unrealized_pl:,.2f}"
                        pl_emoji = "💰"
                    else:
                        pl_str = f"¥{unrealized_pl:,.2f}"
                        pl_emoji = "📊"
                    print(f"     評価損益: {pl_emoji} {pl_str}")

    async def connect(self):
        """WebSocket接続を確立して価格更新を受信"""
        self.print_header()

        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("✅ WebSocket接続成功！")
                print("\n価格更新を受信中... (Ctrl+Cで終了)\n")

                while self.running:
                    try:
                        # メッセージ受信（タイムアウト付き）
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=30.0
                        )

                        # JSONパース
                        data = json.loads(message)

                        # メッセージタイプ確認
                        if data.get('type') == 'price_update':
                            self.print_message(data)
                        else:
                            print(f"⚠️  未知のメッセージタイプ: {data.get('type')}")

                    except asyncio.TimeoutError:
                        print("\n⏱️  タイムアウト: 30秒間メッセージを受信していません")
                        continue
                    except json.JSONDecodeError as e:
                        print(f"\n❌ JSONパースエラー: {e}")
                        continue
                    except WebSocketException as e:
                        print(f"\n❌ WebSocketエラー: {e}")
                        break

        except websockets.exceptions.InvalidStatusCode as e:
            print(f"\n❌ 接続失敗: HTTPステータスコード {e.status_code}")
            if e.status_code == 401:
                print("   認証エラー: トークンが無効です")
            elif e.status_code == 403:
                print("   アクセス拒否: ウォッチリストへのアクセス権限がありません")
            elif e.status_code == 404:
                print("   エラー: ウォッチリストが見つかりません")
            return False

        except websockets.exceptions.InvalidURI as e:
            print(f"\n❌ 無効なURL: {e}")
            print(f"   URL: {self.ws_url}")
            return False

        except ConnectionRefusedError:
            print(f"\n❌ 接続拒否: サーバーが起動していません")
            print(f"   URL: {self.ws_url}")
            print("\n   サーバーを起動してください:")
            print("   cd backend && source venv/bin/activate")
            print("   uvicorn api.main:app --reload")
            return False

        except Exception as e:
            print(f"\n❌ 予期しないエラー: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print(f"\n{'=' * 80}")
            print(f"接続終了")
            print(f"受信メッセージ数: {self.message_count}")
            print(f"{'=' * 80}")

        return True

    def stop(self):
        """接続を停止"""
        self.running = False


def load_test_config() -> Optional[tuple]:
    """
    セットアップスクリプトで生成されたテスト設定を読み込み

    Returns:
        (watchlist_id, token) or None
    """
    try:
        # Note: この関数は実際のセットアップスクリプトの出力を
        # パースする必要がある場合に実装します
        # 今回は環境変数やコマンドライン引数を優先します
        return None
    except Exception:
        return None


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="WebSocket接続テストツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デフォルト設定でテスト
  python scripts/websocket_test_cli.py --watchlist-id 1 --token YOUR_TOKEN

  # カスタムURLでテスト
  python scripts/websocket_test_cli.py --watchlist-id 1 --token YOUR_TOKEN --url ws://localhost:8000
        """
    )

    parser.add_argument(
        '--watchlist-id',
        type=int,
        help='ウォッチリストID（setup_websocket_test.pyの出力から取得）'
    )
    parser.add_argument(
        '--token',
        type=str,
        help='セッショントークン（setup_websocket_test.pyの出力から取得）'
    )
    parser.add_argument(
        '--url',
        type=str,
        default='ws://localhost:8000',
        help='WebSocketサーバーURL（デフォルト: ws://localhost:8000）'
    )

    args = parser.parse_args()

    # パラメータチェック
    if not args.watchlist_id or not args.token:
        print("❌ エラー: --watchlist-id と --token は必須です\n")
        print("セットアップスクリプトを実行してテストデータを作成してください:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  python setup_websocket_test.py")
        print("\n出力されたWatchlist IDとSession Tokenを使用してください:")
        print(f"  python {sys.argv[0]} --watchlist-id <ID> --token <TOKEN>")
        sys.exit(1)

    # クライアント作成
    client = WebSocketTestClient(
        url=args.url,
        watchlist_id=args.watchlist_id,
        token=args.token
    )

    # シグナルハンドラー設定（Ctrl+Cで優雅に終了）
    def signal_handler(sig, frame):
        print("\n\n⏹️  Ctrl+C検出: 接続を終了しています...")
        client.stop()

    signal.signal(signal.SIGINT, signal_handler)

    # 接続実行
    try:
        success = asyncio.run(client.connect())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  中断されました")
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
WebSocketテスト用データのセットアップスクリプト

使用方法:
    cd backend
    source venv/bin/activate
    python setup_websocket_test.py
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User
from models.company import Company
from models.watchlist import Watchlist, WatchlistItem
from core.config import settings
from core.sessions import create_session
import redis
import sys


def setup_test_data():
    """WebSocketテスト用データのセットアップ"""

    # データベース接続
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        print("=" * 60)
        print("WebSocketテストデータのセットアップを開始します")
        print("=" * 60)

        # 1. ユーザーの確認/作成
        print("\n[1/5] テストユーザーの確認...")
        user = db.query(User).filter_by(email="websocket@test.com").first()
        if not user:
            user = User(
                google_id="test_websocket_user",
                email="websocket@test.com",
                name="WebSocket Test User",
                role="premium",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"  ✅ ユーザー作成: {user.email} (ID: {user.id})")
        else:
            print(f"  ℹ️  ユーザー既存: {user.email} (ID: {user.id})")

        # 2. 企業データの確認/作成（トヨタ）
        print("\n[2/5] テスト企業データの確認...")
        toyota = db.query(Company).filter_by(ticker_symbol="7203").first()
        if not toyota:
            toyota = Company(
                ticker_symbol="7203",
                edinet_code="E02144",
                company_name_jp="トヨタ自動車株式会社",
                company_name_en="Toyota Motor Corporation"
            )
            db.add(toyota)
            db.commit()
            db.refresh(toyota)
            print(f"  ✅ 企業作成: トヨタ自動車 (ID: {toyota.id})")
        else:
            print(f"  ℹ️  企業既存: トヨタ自動車 (ID: {toyota.id})")

        # 3. 企業データの確認/作成（ソニー）
        sony = db.query(Company).filter_by(ticker_symbol="6758").first()
        if not sony:
            sony = Company(
                ticker_symbol="6758",
                edinet_code="E01777",
                company_name_jp="ソニーグループ株式会社",
                company_name_en="Sony Group Corporation"
            )
            db.add(sony)
            db.commit()
            db.refresh(sony)
            print(f"  ✅ 企業作成: ソニーグループ (ID: {sony.id})")
        else:
            print(f"  ℹ️  企業既存: ソニーグループ (ID: {sony.id})")

        # 4. ウォッチリストの確認/作成
        print("\n[3/5] ウォッチリストの確認...")
        watchlist = db.query(Watchlist).filter_by(
            user_id=user.id,
            name="リアルタイムテスト"
        ).first()

        if not watchlist:
            watchlist = Watchlist(
                user_id=user.id,
                name="リアルタイムテスト",
                description="WebSocket動作確認用"
            )
            db.add(watchlist)
            db.commit()
            db.refresh(watchlist)
            print(f"  ✅ ウォッチリスト作成: {watchlist.name} (ID: {watchlist.id})")
        else:
            print(f"  ℹ️  ウォッチリスト既存: {watchlist.name} (ID: {watchlist.id})")

        # 5. ウォッチリストアイテムの確認/作成
        print("\n[4/5] ウォッチリストアイテムの確認...")

        # トヨタのアイテム
        item1_exists = db.query(WatchlistItem).filter_by(
            watchlist_id=watchlist.id,
            company_id=toyota.id
        ).first()

        if not item1_exists:
            item1 = WatchlistItem(
                watchlist_id=watchlist.id,
                company_id=toyota.id,
                quantity=100,
                purchase_price=2500.00,
                memo="WebSocketテスト用",
                tags=["test", "automotive"]
            )
            db.add(item1)
            db.commit()
            print(f"  ✅ アイテム追加: トヨタ自動車 (数量: 100株, 購入価格: ¥2,500)")
        else:
            print(f"  ℹ️  アイテム既存: トヨタ自動車")

        # ソニーのアイテム
        item2_exists = db.query(WatchlistItem).filter_by(
            watchlist_id=watchlist.id,
            company_id=sony.id
        ).first()

        if not item2_exists:
            item2 = WatchlistItem(
                watchlist_id=watchlist.id,
                company_id=sony.id,
                quantity=50,
                purchase_price=13000.00,
                memo="WebSocketテスト用",
                tags=["test", "technology"]
            )
            db.add(item2)
            db.commit()
            print(f"  ✅ アイテム追加: ソニーグループ (数量: 50株, 購入価格: ¥13,000)")
        else:
            print(f"  ℹ️  アイテム既存: ソニーグループ")

        # 6. セッショントークン生成
        print("\n[5/5] セッショントークンの生成...")
        redis_client = redis.Redis.from_url(settings.redis_url)
        session_token = create_session(user.id, redis_client)
        print(f"  ✅ セッショントークン生成完了")

        # 結果表示
        print("\n" + "=" * 60)
        print("✅ セットアップ完了！")
        print("=" * 60)

        print("\n📋 WebSocket接続情報:")
        print(f"  User ID:       {user.id}")
        print(f"  Watchlist ID:  {watchlist.id}")
        print(f"  Session Token: {session_token}")

        # WebSocket URL生成
        ws_url = f"ws://localhost:8000/api/v1/ws/watchlist/{watchlist.id}/prices?token={session_token}"

        print(f"\n🔗 WebSocket接続URL:")
        print(f"  {ws_url}")

        print(f"\n💡 使用例:")
        print(f"  # wscatを使用する場合:")
        print(f"  wscat -c \"{ws_url}\"")
        print(f"\n  # Pythonを使用する場合:")
        print(f"  python -c \"import asyncio, websockets, json")
        print(f"  async def test():")
        print(f"      async with websockets.connect('{ws_url}') as ws:")
        print(f"          msg = await ws.recv()")
        print(f"          print(json.loads(msg))")
        print(f"  asyncio.run(test())\"")

        print(f"\n⚠️  作業終了後は必ずクリーンアップを実行してください:")
        print(f"  python cleanup_websocket_test.py")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        print(f"   トランザクションをロールバックします...")
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = setup_test_data()
    sys.exit(0 if success else 1)

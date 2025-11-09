#!/usr/bin/env python3
"""
WebSocketテスト用データのクリーンアップスクリプト

使用方法:
    cd backend
    source venv/bin/activate
    python cleanup_websocket_test.py
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User
from models.company import Company
from models.watchlist import Watchlist, WatchlistItem
from core.config import settings
import redis
import sys


def cleanup_test_data():
    """WebSocketテスト用データのクリーンアップ"""

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        print("=" * 60)
        print("WebSocketテストデータのクリーンアップを開始します")
        print("=" * 60)

        # 1. テストユーザーの確認
        print("\n[1/3] テストユーザーの確認...")
        test_user = db.query(User).filter_by(email="websocket@test.com").first()

        if not test_user:
            print("  ℹ️  テストユーザーが見つかりません（既に削除済みの可能性）")
        else:
            user_id = test_user.id
            user_email = test_user.email

            # 2. ウォッチリストの削除（カスケードでアイテムも削除）
            print("\n[2/3] ウォッチリストとアイテムの削除...")
            watchlists = db.query(Watchlist).filter_by(user_id=user_id).all()

            if watchlists:
                for wl in watchlists:
                    # アイテム数を確認
                    items_count = db.query(WatchlistItem).filter_by(
                        watchlist_id=wl.id
                    ).count()

                    print(f"  🗑️  ウォッチリスト削除: {wl.name} (アイテム数: {items_count})")
                    db.delete(wl)

                db.commit()
            else:
                print("  ℹ️  削除対象のウォッチリストはありません")

            # 3. ユーザーの削除
            print("\n[3/3] ユーザーの削除...")
            print(f"  🗑️  ユーザー削除: {user_email} (ID: {user_id})")
            db.delete(test_user)
            db.commit()

        # 4. Redisセッションのクリーンアップ
        print("\n[4/4] Redisセッションのクリーンアップ...")
        try:
            redis_client = redis.Redis.from_url(settings.redis_url)

            # セッションキーを検索
            session_keys = []
            for key in redis_client.scan_iter("session:*"):
                session_keys.append(key)

            if session_keys:
                # セッションを削除
                deleted_count = 0
                for key in session_keys:
                    try:
                        # セッションデータを確認（オプション）
                        session_data = redis_client.get(key)
                        if session_data:
                            redis_client.delete(key)
                            deleted_count += 1
                    except Exception as e:
                        print(f"    ⚠️  セッション削除エラー ({key.decode()}): {e}")

                print(f"  🗑️  Redisセッション削除: {deleted_count}件")
            else:
                print("  ℹ️  削除対象のRedisセッションはありません")

        except Exception as e:
            print(f"  ⚠️  Redis接続エラー: {e}")
            print(f"     Redisが起動していない可能性があります")

        # 完了メッセージ
        print("\n" + "=" * 60)
        print("✅ クリーンアップ完了")
        print("=" * 60)

        # テスト企業データに関する注意
        print("\n📝 注意:")
        print("  - テスト用企業データ（トヨタ、ソニー）は削除していません")
        print("  - 他のテストやデモで使用されている可能性があるためです")
        print("  - 必要に応じて手動で削除してください:")
        print("    DELETE FROM companies WHERE ticker_symbol IN ('7203', '6758');")

        print("\n💡 次回のテスト実行:")
        print("  python setup_websocket_test.py")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ クリーンアップエラー: {e}")
        print(f"   トランザクションをロールバックします...")
        db.rollback()
        return False

    finally:
        db.close()


def cleanup_all_test_data():
    """すべてのテストデータを削除（企業データ含む）"""

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        print("\n⚠️  警告: すべてのテストデータ（企業データ含む）を削除します")
        response = input("続行しますか？ (yes/no): ")

        if response.lower() != 'yes':
            print("  ℹ️  キャンセルしました")
            return False

        # 通常のクリーンアップを実行
        cleanup_test_data()

        # 企業データの削除
        print("\n企業データの削除...")
        toyota = db.query(Company).filter_by(ticker_symbol="7203").first()
        if toyota:
            print(f"  🗑️  企業削除: トヨタ自動車")
            db.delete(toyota)

        sony = db.query(Company).filter_by(ticker_symbol="6758").first()
        if sony:
            print(f"  🗑️  企業削除: ソニーグループ")
            db.delete(sony)

        db.commit()
        print("✅ すべてのテストデータを削除しました")

        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    import sys

    # コマンドライン引数で全削除モードを指定可能
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        success = cleanup_all_test_data()
    else:
        success = cleanup_test_data()

    sys.exit(0 if success else 1)

/**
 * Watchlist Page
 *
 * Displays a watchlist with real-time stock price updates via WebSocket.
 * Automatically creates a default watchlist for new users.
 */

"use client";

import React, { useState, useEffect } from "react";
import { WatchlistTable } from "@/components/watchlist";
import { useAuth } from "@/lib/auth/AuthContext";
import { useWatchlists } from "@/lib/hooks/useWatchlists";
import { Loader2 } from "lucide-react";

export default function WatchlistPage() {
  const { user, isLoading: authLoading } = useAuth();
  const {
    watchlists,
    isLoading: watchlistsLoading,
    error: watchlistsError,
    createDefaultWatchlist,
  } = useWatchlists(!!user); // Auto-fetch watchlists when user is logged in
  const [watchlistId, setWatchlistId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [creationError, setCreationError] = useState<string | null>(null);

  /**
   * Select the first watchlist when user logs in and watchlists are loaded
   */
  useEffect(() => {
    if (!user || watchlistsLoading) {
      return;
    }

    // If we already have a watchlist ID, do nothing
    if (watchlistId !== null) {
      return;
    }

    // If user has watchlists, use the first one
    if (watchlists.length > 0) {
      setWatchlistId(watchlists[0].id);
    }
    // If user has no watchlists, we'll show a "create" button
    // Don't auto-create to avoid 403 errors due to plan limits
  }, [user, watchlists, watchlistsLoading, watchlistId]);

  /**
   * Handle watchlist creation
   */
  const handleCreateWatchlist = async () => {
    setIsCreating(true);
    setCreationError(null);

    try {
      const newWatchlist = await createDefaultWatchlist();
      setWatchlistId(newWatchlist.id);
    } catch (error: any) {
      console.error("[WatchlistPage] Failed to create watchlist:", error);

      if (error.response?.status === 429) {
        setCreationError("リクエストが多すぎます。しばらくしてからもう一度お試しください。");
      } else if (error.response?.status === 403) {
        setCreationError("プランの上限に達しました。既存のウォッチリストをご利用ください。");
      } else {
        setCreationError("ウォッチリストの作成に失敗しました。もう一度お試しください。");
      }
    } finally {
      setIsCreating(false);
    }
  };

  // Show loading state while checking authentication
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">
            ログインが必要です
          </h1>
          <p className="mt-2 text-gray-600">
            ウォッチリストを表示するにはログインしてください
          </p>
          <button
            onClick={() =>
              (window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google/login`)
            }
            className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            ログイン
          </button>
        </div>
      </div>
    );
  }

  // Show loading state while fetching watchlists
  if (watchlistsLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto" />
          <p className="mt-4 text-gray-600">ウォッチリストを読み込み中...</p>
        </div>
      </div>
    );
  }

  // Show "Create Watchlist" UI if user has no watchlists
  if (!watchlistsLoading && watchlists.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center max-w-md">
          {creationError ? (
            <>
              <h1 className="text-2xl font-bold text-red-600">エラー</h1>
              <p className="mt-2 text-gray-600">{creationError}</p>
              <button
                onClick={() => setCreationError(null)}
                className="mt-4 rounded-md bg-gray-600 px-4 py-2 text-white hover:bg-gray-700 transition-colors"
              >
                戻る
              </button>
            </>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                ウォッチリストがありません
              </h1>
              <p className="text-gray-600 mb-6">
                最初のウォッチリストを作成して、銘柄の株価をモニタリングしましょう
              </p>
              <button
                onClick={handleCreateWatchlist}
                disabled={isCreating}
                className="rounded-md bg-blue-600 px-6 py-3 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isCreating ? (
                  <span className="flex items-center">
                    <Loader2 className="h-5 w-5 animate-spin mr-2" />
                    作成中...
                  </span>
                ) : (
                  "ウォッチリストを作成"
                )}
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  // Show loading state while watchlistId is being set
  if (watchlistId === null) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto" />
          <p className="mt-4 text-gray-600">初期化中...</p>
        </div>
      </div>
    );
  }

  // Show error state if watchlist fetch failed
  if (watchlistsError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">エラー</h1>
          <p className="mt-2 text-gray-600">
            ウォッチリストの読み込みに失敗しました
          </p>
          <p className="mt-1 text-sm text-gray-500">
            {watchlistsError.message}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            再読み込み
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            ウォッチリスト
          </h1>
          <p className="mt-2 text-gray-600">
            リアルタイムで株価とポートフォリオの状況を確認できます
          </p>
        </div>

        {/* Watchlist selector (if user has multiple watchlists) */}
        {watchlists.length > 1 && (
          <div className="mb-6">
            <label
              htmlFor="watchlist-selector"
              className="block text-sm font-medium text-gray-700"
            >
              ウォッチリスト
            </label>
            <select
              id="watchlist-selector"
              value={watchlistId || ""}
              onChange={(e) => setWatchlistId(parseInt(e.target.value, 10))}
              className="mt-1 block w-full max-w-md rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {watchlists.map((wl) => (
                <option key={wl.id} value={wl.id}>
                  {wl.name}
                  {wl.description && ` - ${wl.description}`}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Watchlist table with manual refresh */}
        <WatchlistTable watchlistId={watchlistId} autoConnect={false} />

        {/* Info section */}
        <div className="mt-8 rounded-lg bg-blue-50 p-4">
          <h3 className="font-semibold text-blue-900">
            💡 ウォッチリストの使い方
          </h3>
          <ul className="mt-2 space-y-1 text-sm text-blue-800">
            <li>• 右上の「更新」ボタンで最新の株価を取得できます</li>
            <li>• 銘柄をクリックすると詳細画面に移動します</li>
            <li>• 詳細画面では、選択した銘柄の株価がリアルタイムで更新されます</li>
            <li>• 評価損益は最新の株価に基づいて自動計算されます</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

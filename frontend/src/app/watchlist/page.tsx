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
  } = useWatchlists(!user); // Only auto-fetch if user is logged in
  const [watchlistId, setWatchlistId] = useState<number | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);

  /**
   * Initialize watchlist for the user
   * - If user has watchlists, use the first one
   * - If user has no watchlists, create a default one
   */
  useEffect(() => {
    if (!user || watchlistsLoading || isInitializing) {
      return;
    }

    // If we already have a watchlist ID, do nothing
    if (watchlistId !== null) {
      return;
    }

    // If user has watchlists, use the first one
    if (watchlists.length > 0) {
      setWatchlistId(watchlists[0].id);
      return;
    }

    // If user has no watchlists, create a default one
    setIsInitializing(true);
    createDefaultWatchlist()
      .then((newWatchlist) => {
        setWatchlistId(newWatchlist.id);
      })
      .catch((error) => {
        console.error("[WatchlistPage] Failed to create default watchlist:", error);
      })
      .finally(() => {
        setIsInitializing(false);
      });
  }, [
    user,
    watchlists,
    watchlistsLoading,
    watchlistId,
    isInitializing,
    createDefaultWatchlist,
  ]);

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

  // Show loading state while initializing watchlist
  if (watchlistsLoading || isInitializing || watchlistId === null) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto" />
          <p className="mt-4 text-gray-600">
            {isInitializing
              ? "ウォッチリストを作成中..."
              : "ウォッチリストを読み込み中..."}
          </p>
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

        {/* Watchlist table with real-time updates */}
        <WatchlistTable watchlistId={watchlistId} autoConnect={true} />

        {/* Info section */}
        <div className="mt-8 rounded-lg bg-blue-50 p-4">
          <h3 className="font-semibold text-blue-900">
            💡 リアルタイム更新について
          </h3>
          <ul className="mt-2 space-y-1 text-sm text-blue-800">
            <li>• 株価は5秒ごとに自動更新されます</li>
            <li>• 接続が切れた場合は自動的に再接続を試みます</li>
            <li>• 価格の変動は色分けして表示されます（緑: 上昇、赤: 下落）</li>
            <li>• 評価損益はリアルタイムで計算・表示されます</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

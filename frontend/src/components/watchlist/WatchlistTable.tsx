/**
 * Watchlist Table with Real-time Price Updates
 *
 * Displays a watchlist with real-time stock prices via WebSocket.
 * Features include live price updates, P&L calculations, and connection status.
 */

"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useRealtimePrices } from "@/lib/hooks/useRealtimePrices";
import { ConnectionState } from "@/lib/websocket";
import { ConnectionStatus } from "./ConnectionStatus";
import { PriceCell, PLCell } from "./PriceCell";
import { WatchlistCard } from "./WatchlistCard";
import { AlertCircle, Loader2, RefreshCw } from "lucide-react";
import { useToast } from "@/lib/hooks/use-toast";
import { useRouter } from "next/navigation";

export interface WatchlistTableProps {
  /** Watchlist ID to display */
  watchlistId: number;
  /** Auto-connect on mount (default: true) */
  autoConnect?: boolean;
  /** Show connection status (default: true) */
  showConnectionStatus?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Watchlist Table Component
 *
 * Displays real-time stock prices for a watchlist
 */
export const WatchlistTable = React.memo<WatchlistTableProps>(
  ({
    watchlistId,
    autoConnect = true,
    showConnectionStatus = true,
    className = "",
  }) => {
    const {
      stocks,
      connectionState,
      error,
      lastUpdate,
      isLoading,
      connect,
      disconnect,
      refresh,
      isConnected,
    } = useRealtimePrices(watchlistId, autoConnect);

    const { toast } = useToast();
    const router = useRouter();
    const [isRefreshing, setIsRefreshing] = useState(false);

    // Show toast notification for errors
    useEffect(() => {
      if (error) {
        toast({
          title: "接続エラー",
          description: error.message,
          variant: "destructive",
        });
      }
    }, [error, toast]);

    // Cleanup on unmount
    useEffect(() => {
      return () => {
        disconnect();
      };
    }, [disconnect]);

    // Calculate total portfolio value (handle null prices)
    const portfolioSummary = useMemo(() => {
      const totalValue = stocks.reduce((sum, stock) => {
        // Skip stocks with null price data
        if (stock.current_price === null || stock.current_price === undefined) {
          return sum;
        }
        const value = stock.current_price * (stock.quantity || 0);
        return sum + value;
      }, 0);

      const totalPL = stocks.reduce((sum, stock) => {
        // Skip stocks with null unrealized P/L
        if (stock.unrealized_pl === null || stock.unrealized_pl === undefined) {
          return sum;
        }
        return sum + stock.unrealized_pl;
      }, 0);

      const totalInvestment = totalValue - totalPL;
      const plPercent = totalInvestment > 0 ? (totalPL / totalInvestment) * 100 : 0;

      return {
        totalValue,
        totalPL,
        plPercent,
      };
    }, [stocks]);

    // Format number with commas
    const formatNumber = (num: number) => {
      return new Intl.NumberFormat("ja-JP", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(num);
    };

    // Format date/time
    const formatTimestamp = (timestamp: string | null) => {
      if (!timestamp) return "";
      const date = new Date(timestamp);
      return date.toLocaleTimeString("ja-JP", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    };

    const formatDate = (dateStr: string) => {
      const date = new Date(dateStr);
      return date.toLocaleDateString("ja-JP", {
        month: "numeric",
        day: "numeric",
        weekday: "short",
      });
    };

    // Handle manual refresh
    const handleRefresh = async () => {
      setIsRefreshing(true);
      try {
        await refresh();
        toast({
          title: "更新完了",
          description: "最新のデータを取得しました",
        });
      } catch (err) {
        toast({
          title: "更新失敗",
          description: "データの取得に失敗しました",
          variant: "destructive",
        });
      } finally {
        setIsRefreshing(false);
      }
    };

    // Handle stock row click
    const handleStockClick = (tickerSymbol: string) => {
      router.push(`/stocks/${tickerSymbol}`);
    };

    return (
      <div className={`space-y-4 ${className}`}>
        {/* Header with connection status and refresh button */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold">ウォッチリスト</h2>
            {showConnectionStatus && (
              <ConnectionStatus state={connectionState} error={error} />
            )}
          </div>

          <div className="flex items-center gap-3">
            {lastUpdate && (
              <div className="text-sm text-gray-500">
                最終更新: {formatTimestamp(lastUpdate)}
              </div>
            )}

            {/* WebSocket Connection Toggle Button */}
            <button
              onClick={() => (isConnected ? disconnect() : connect())}
              disabled={connectionState === ConnectionState.CONNECTING}
              className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                isConnected
                  ? "bg-green-600 text-white hover:bg-green-700"
                  : connectionState === ConnectionState.CONNECTING
                    ? "bg-yellow-600 text-white cursor-not-allowed"
                    : "bg-gray-600 text-white hover:bg-gray-700"
              } disabled:opacity-50`}
            >
              {connectionState === ConnectionState.CONNECTING && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              {connectionState === ConnectionState.CONNECTED && (
                <span className="h-2 w-2 rounded-full bg-white" />
              )}
              {connectionState === ConnectionState.DISCONNECTED && (
                <span className="h-2 w-2 rounded-full bg-gray-400" />
              )}
              {connectionState === ConnectionState.CONNECTING
                ? "接続中..."
                : isConnected
                  ? "切断"
                  : "リアルタイム接続"}
            </button>

            <button
              onClick={handleRefresh}
              disabled={isRefreshing || isLoading}
              className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw
                className={`h-4 w-4 ${isRefreshing || isLoading ? "animate-spin" : ""}`}
              />
              {isRefreshing || isLoading ? "更新中..." : "更新"}
            </button>
          </div>
        </div>

        {/* Market status banner */}
        {stocks.length > 0 && stocks[0]?.market_status && !stocks[0].market_status.is_open && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-amber-600" />
              <div className="flex-1">
                <div className="font-semibold text-amber-900">
                  {stocks[0].market_status.reason === "weekend_or_holiday"
                    ? "市場休場中（週末・祝日）"
                    : "市場終了"}
                </div>
                <div className="text-sm text-amber-800">
                  {stocks[0].market_status.last_trading_day && (
                    <span>
                      最終取引日: {formatDate(stocks[0].market_status.last_trading_day)}
                    </span>
                  )}
                  {stocks[0].market_status.next_trading_day && (
                    <span className="ml-4">
                      次回開場: {formatDate(stocks[0].market_status.next_trading_day)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="flex items-center gap-2 rounded-md bg-red-50 px-4 py-3 text-red-800">
            <AlertCircle className="h-5 w-5" />
            <div>
              <div className="font-semibold">接続エラー</div>
              <div className="text-sm">{error.message}</div>
            </div>
          </div>
        )}

        {/* Loading state */}
        {isLoading && stocks.length === 0 && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-600">読み込み中...</span>
          </div>
        )}

        {/* Empty watchlist - no stocks after loading */}
        {!isLoading && stocks.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="rounded-lg bg-blue-50 p-6 text-center max-w-md">
              <AlertCircle className="h-12 w-12 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                ウォッチリストに銘柄がありません
              </h3>
              <p className="text-gray-600 mb-4">
                銘柄を追加して、株価をモニタリングしましょう
              </p>
              <button
                onClick={() => (window.location.href = "/stocks")}
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition-colors"
              >
                銘柄を追加
              </button>
            </div>
          </div>
        )}

        {/* Stock display */}
        {stocks.length > 0 && (
          <>
            {/* Mobile: Card Layout */}
            <div className="md:hidden space-y-4">
              {stocks.map((stock) => (
                <WatchlistCard
                  key={stock.company_id}
                  stock={stock}
                  onClick={() => handleStockClick(stock.ticker_symbol)}
                />
              ))}
            </div>

            {/* Tablet & Desktop: Table Layout */}
            <div className="hidden md:block overflow-x-auto rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="whitespace-nowrap px-4 py-3 text-left text-sm font-medium text-gray-700">
                      銘柄
                    </th>
                    <th className="whitespace-nowrap px-4 py-3 text-left text-sm font-medium text-gray-700">
                      コード
                    </th>
                    <th className="whitespace-nowrap px-4 py-3 text-left text-sm font-medium text-gray-700">
                      現在値 / 変動
                    </th>
                    <th className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-gray-700">
                      保有数
                    </th>
                    <th className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-gray-700">
                      取得単価
                    </th>
                    <th className="hidden lg:table-cell whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-gray-700">
                      評価額
                    </th>
                    <th className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-gray-700">
                      評価損益
                    </th>
                    <th className="hidden md:table-cell whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-gray-700">
                      損益率
                    </th>
                    <th className="hidden xl:table-cell whitespace-nowrap px-4 py-3 text-left text-sm font-medium text-gray-700">
                      タグ
                    </th>
                    <th className="hidden xl:table-cell whitespace-nowrap px-4 py-3 text-left text-sm font-medium text-gray-700">
                      メモ
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {stocks.map((stock) => (
                    <tr
                      key={stock.company_id}
                      onClick={() => handleStockClick(stock.ticker_symbol)}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="whitespace-nowrap px-4 py-3">
                        <div className="text-sm font-medium text-gray-900">
                          {stock.company_name}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <div className="text-sm text-gray-600">
                          {stock.ticker_symbol}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <PriceCell
                          price={stock.current_price}
                          change={stock.change}
                          changePercent={stock.change_percent}
                          animate={isConnected}
                          marketStatus={stock.market_status}
                          date={stock.date}
                        />
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-600">
                        {stock.quantity ? formatNumber(stock.quantity) : "-"}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-600">
                        {stock.purchase_price
                          ? `¥${formatNumber(stock.purchase_price)}`
                          : "-"}
                      </td>
                      {/* 評価額 (Market Value) */}
                      <td className="hidden lg:table-cell whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
                        {stock.quantity && stock.current_price
                          ? `¥${formatNumber(stock.quantity * stock.current_price)}`
                          : "-"}
                      </td>
                      {/* 評価損益 (Unrealized P&L) */}
                      <td className="whitespace-nowrap px-4 py-3 text-right">
                        {stock.unrealized_pl !== undefined ? (
                          <PLCell unrealizedPL={stock.unrealized_pl} />
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      {/* 損益率 (P&L %) */}
                      <td className="hidden md:table-cell whitespace-nowrap px-4 py-3 text-right text-sm">
                        {stock.unrealized_pl !== undefined &&
                        stock.quantity &&
                        stock.purchase_price ? (
                          <span
                            className={`font-medium ${
                              stock.unrealized_pl > 0
                                ? "text-green-600"
                                : stock.unrealized_pl < 0
                                  ? "text-red-600"
                                  : "text-gray-600"
                            }`}
                          >
                            {((stock.unrealized_pl / (stock.purchase_price * stock.quantity)) * 100).toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      {/* タグ (Tags) */}
                      <td className="hidden xl:table-cell px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {stock.tags && stock.tags.length > 0 ? (
                            stock.tags.map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
                              >
                                {tag}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </div>
                      </td>
                      {/* メモ (Memo) */}
                      <td className="hidden xl:table-cell px-4 py-3 text-sm text-gray-600">
                        {stock.memo ? (
                          <span
                            title={stock.memo}
                            className="cursor-pointer hover:text-blue-600 hover:underline"
                          >
                            {stock.memo.length > 30
                              ? `${stock.memo.slice(0, 30)}...`
                              : stock.memo}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Portfolio summary */}
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-600">合計評価額</div>
                  <div className="text-2xl font-bold text-gray-900">
                    ¥{formatNumber(portfolioSummary.totalValue)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">評価損益</div>
                  <div
                    className={`text-2xl font-bold ${
                      portfolioSummary.totalPL > 0
                        ? "text-green-600"
                        : portfolioSummary.totalPL < 0
                          ? "text-red-600"
                          : "text-gray-600"
                    }`}
                  >
                    {portfolioSummary.totalPL > 0 ? "+" : ""}
                    ¥{formatNumber(portfolioSummary.totalPL)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">損益率</div>
                  <div
                    className={`text-2xl font-bold ${
                      portfolioSummary.plPercent > 0
                        ? "text-green-600"
                        : portfolioSummary.plPercent < 0
                          ? "text-red-600"
                          : "text-gray-600"
                    }`}
                  >
                    {portfolioSummary.plPercent > 0 ? "+" : ""}
                    {portfolioSummary.plPercent.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    );
  }
);

WatchlistTable.displayName = "WatchlistTable";

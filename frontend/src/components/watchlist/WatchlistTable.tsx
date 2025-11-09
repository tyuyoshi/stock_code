/**
 * Watchlist Table with Real-time Price Updates
 *
 * Displays a watchlist with real-time stock prices via WebSocket.
 * Features include live price updates, P&L calculations, and connection status.
 */

"use client";

import React, { useEffect, useMemo } from "react";
import { useRealtimePrices } from "@/lib/hooks/useRealtimePrices";
import { ConnectionStatus } from "./ConnectionStatus";
import { PriceCell, PLCell } from "./PriceCell";
import { AlertCircle, Loader2 } from "lucide-react";
import { useToast } from "@/lib/hooks/use-toast";

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
      disconnect,
      isConnected,
    } = useRealtimePrices(watchlistId, autoConnect);

    const { toast } = useToast();

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

    // Calculate total portfolio value
    const portfolioSummary = useMemo(() => {
      const totalValue = stocks.reduce((sum, stock) => {
        const value = stock.current_price * (stock.quantity || 0);
        return sum + value;
      }, 0);

      const totalPL = stocks.reduce((sum, stock) => {
        return sum + (stock.unrealized_pl || 0);
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

    return (
      <div className={`space-y-4 ${className}`}>
        {/* Header with connection status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold">ウォッチリスト</h2>
            {showConnectionStatus && (
              <ConnectionStatus state={connectionState} error={error} />
            )}
          </div>

          {lastUpdate && isConnected && (
            <div className="text-sm text-gray-500">
              最終更新: {formatTimestamp(lastUpdate)}
            </div>
          )}
        </div>

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
        {stocks.length === 0 && !error && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-600">データを読み込み中...</span>
          </div>
        )}

        {/* Stock table */}
        {stocks.length > 0 && (
          <>
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      銘柄
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      コード
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      現在値 / 変動
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      保有数
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      取得単価
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      評価損益
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {stocks.map((stock) => (
                    <tr key={stock.company_id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {stock.company_name}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="text-sm text-gray-600">
                          {stock.ticker_symbol}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <PriceCell
                          price={stock.current_price}
                          change={stock.change}
                          changePercent={stock.change_percent}
                          animate={isConnected}
                        />
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-600">
                        {stock.quantity ? formatNumber(stock.quantity) : "-"}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-600">
                        {stock.purchase_price
                          ? `¥${formatNumber(stock.purchase_price)}`
                          : "-"}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right">
                        {stock.unrealized_pl !== undefined ? (
                          <PLCell unrealizedPL={stock.unrealized_pl} />
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Portfolio summary */}
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="grid grid-cols-3 gap-4">
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

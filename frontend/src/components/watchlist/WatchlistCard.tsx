/**
 * Watchlist Card Component (Mobile Layout)
 *
 * Displays individual stock information in a card format for mobile devices.
 * Shows essential information: company name, ticker, price, change, and P&L.
 */

import React from "react";
import { StockPrice } from "@/lib/websocket";
import { PriceCell, PLCell } from "./PriceCell";

export interface WatchlistCardProps {
  stock: StockPrice;
  onClick?: () => void;
}

/**
 * Mobile-optimized card layout for watchlist items
 */
export const WatchlistCard = React.memo<WatchlistCardProps>(
  ({ stock, onClick }) => {
    const formatNumber = (num: number | null | undefined) => {
      if (num === null || num === undefined) return "-";
      return new Intl.NumberFormat("ja-JP", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(num);
    };

    return (
      <div
        onClick={onClick}
        className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      >
        {/* Header: Company Name & Ticker */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-base font-semibold text-gray-900">
              {stock.company_name}
            </h3>
            <p className="text-sm text-gray-500 mt-1">{stock.ticker_symbol}</p>
          </div>
        </div>

        {/* Price Section */}
        <div className="mb-3">
          <PriceCell
            price={stock.current_price}
            change={stock.change}
            changePercent={stock.change_percent}
            animate={false}
            compact={false}
            marketStatus={stock.market_status}
            date={stock.date}
          />
        </div>

        {/* Holdings & P&L Section */}
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100">
          {/* Quantity & Purchase Price */}
          <div>
            <p className="text-xs text-gray-500 mb-1">保有数</p>
            <p className="text-sm font-medium text-gray-900">
              {stock.quantity ? `${formatNumber(stock.quantity)}株` : "-"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">取得単価</p>
            <p className="text-sm font-medium text-gray-900">
              {stock.purchase_price ? `¥${formatNumber(stock.purchase_price)}` : "-"}
            </p>
          </div>

          {/* Market Value & P&L */}
          {stock.quantity && stock.current_price && (
            <>
              <div>
                <p className="text-xs text-gray-500 mb-1">評価額</p>
                <p className="text-sm font-medium text-gray-900">
                  ¥{formatNumber(stock.quantity * stock.current_price)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">評価損益</p>
                {stock.unrealized_pl !== undefined ? (
                  <PLCell unrealizedPL={stock.unrealized_pl} compact />
                ) : (
                  <span className="text-sm text-gray-400">-</span>
                )}
              </div>
            </>
          )}
        </div>

        {/* Tags & Memo Section (if available) */}
        {(stock.tags && stock.tags.length > 0) || stock.memo ? (
          <div className="mt-3 pt-3 border-t border-gray-100 space-y-2">
            {/* Tags */}
            {stock.tags && stock.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {stock.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Memo */}
            {stock.memo && (
              <p className="text-xs text-gray-600 line-clamp-2">
                {stock.memo}
              </p>
            )}
          </div>
        ) : null}
      </div>
    );
  }
);

WatchlistCard.displayName = "WatchlistCard";

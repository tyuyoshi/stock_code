/**
 * Price Cell Component with Animations
 *
 * Displays stock price with color-coded change indicators and
 * animations for real-time updates.
 */

import React, { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { MarketStatus } from "@/lib/websocket";

export interface PriceCellProps {
  /** Current price (null if data unavailable) */
  price: number | null;
  /** Price change amount (null if data unavailable) */
  change: number | null;
  /** Price change percentage (null if data unavailable) */
  changePercent: number | null;
  /** Show animation on price update (default: true) */
  animate?: boolean;
  /** Compact mode (smaller size, default: false) */
  compact?: boolean;
  /** Market status information */
  marketStatus?: MarketStatus;
  /** Date of the price data (YYYY-MM-DD) */
  date?: string;
}

/**
 * Price Cell Component
 *
 * Displays price with change indicator and optional animation
 */
export const PriceCell = React.memo<PriceCellProps>(
  ({ price, change, changePercent, animate = true, compact = false, marketStatus, date }) => {
    // All hooks must be called before any conditional returns
    const [showFlash, setShowFlash] = useState(false);
    const [prevPrice, setPrevPrice] = useState(price);

    // Trigger flash animation on price change
    useEffect(() => {
      if (animate && price !== null && price !== prevPrice) {
        setShowFlash(true);
        setPrevPrice(price);

        const timer = setTimeout(() => {
          setShowFlash(false);
        }, 500);

        return () => clearTimeout(timer);
      }
    }, [price, prevPrice, animate]);

    // Handle null values gracefully (after all hooks)
    if (price === null || price === undefined) {
      return (
        <span className="text-sm text-gray-400">価格データなし</span>
      );
    }

    // Determine if market is closed
    const isMarketClosed = marketStatus && !marketStatus.is_open;
    const priceLabel = isMarketClosed ? "終値" : "現在値";

    // Format date for display (MM/DD)
    const formatDate = (dateStr?: string) => {
      if (!dateStr) return "";
      const [, month, day] = dateStr.split("-");
      return `${month}/${day}`;
    };

    // Determine trend direction (handle null change values)
    const isPositive = change !== null && change > 0;
    const isNegative = change !== null && change < 0;

    // Color classes
    const trendColor = isPositive
      ? "text-green-600"
      : isNegative
        ? "text-red-600"
        : "text-gray-600";

    const bgColor = isPositive
      ? "bg-green-50"
      : isNegative
        ? "bg-red-50"
        : "bg-gray-50";

    const flashColor = isPositive ? "bg-green-200" : isNegative ? "bg-red-200" : "";

    // Format number with commas (handle null)
    const formatNumber = (num: number | null) => {
      if (num === null || num === undefined) return "--";
      return new Intl.NumberFormat("ja-JP", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(num);
    };

    // Format percentage (handle null)
    const formatPercent = (num: number | null) => {
      if (num === null || num === undefined) return "N/A";
      const sign = num > 0 ? "+" : "";
      return `${sign}${num.toFixed(2)}%`;
    };

    // Select appropriate icon
    const Icon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;

    return (
      <div className="flex flex-col gap-1">
        <div
          className={`inline-flex items-center gap-2 rounded-md px-2 py-1 transition-colors duration-300 ${
            showFlash ? flashColor : bgColor
          } ${compact ? "text-xs" : "text-sm"}`}
        >
          {/* Price with label */}
          <div className="flex flex-col">
            <span className={`font-semibold ${trendColor}`}>
              ¥{formatNumber(price)}
            </span>
            {isMarketClosed && date && (
              <span className="text-xs text-gray-500">
                {priceLabel} ({formatDate(date)})
              </span>
            )}
          </div>

          {/* Change indicator */}
          <div className={`flex items-center gap-1 ${trendColor}`}>
            <Icon className={compact ? "h-3 w-3" : "h-4 w-4"} />
            <span className="font-medium">
              {formatNumber(change !== null ? Math.abs(change) : null)} ({formatPercent(changePercent)})
            </span>
          </div>
        </div>
      </div>
    );
  }
);

PriceCell.displayName = "PriceCell";

/**
 * P&L (Profit/Loss) Cell Component
 *
 * Displays unrealized profit/loss with color coding
 */
export interface PLCellProps {
  /** Unrealized profit/loss amount (null if price data unavailable) */
  unrealizedPL: number | null;
  /** Show compact version (default: false) */
  compact?: boolean;
}

export const PLCell = React.memo<PLCellProps>(
  ({ unrealizedPL, compact = false }) => {
    // Handle null values
    if (unrealizedPL === null || unrealizedPL === undefined) {
      return (
        <span className="text-sm text-gray-400">--</span>
      );
    }

    const isProfit = unrealizedPL > 0;
    const isLoss = unrealizedPL < 0;

    const trendColor = isProfit
      ? "text-green-600"
      : isLoss
        ? "text-red-600"
        : "text-gray-600";

    const bgColor = isProfit
      ? "bg-green-50"
      : isLoss
        ? "bg-red-50"
        : "bg-gray-50";

    const formatNumber = (num: number) => {
      const sign = num > 0 ? "+" : "";
      return `${sign}${new Intl.NumberFormat("ja-JP", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(num)}`;
    };

    return (
      <div
        className={`inline-flex items-center rounded-md px-2 py-1 ${bgColor} ${compact ? "text-xs" : "text-sm"}`}
      >
        <span className={`font-semibold ${trendColor}`}>
          ¥{formatNumber(unrealizedPL)}
        </span>
      </div>
    );
  }
);

PLCell.displayName = "PLCell";

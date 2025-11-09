/**
 * Price Cell Component with Animations
 *
 * Displays stock price with color-coded change indicators and
 * animations for real-time updates.
 */

import React, { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export interface PriceCellProps {
  /** Current price */
  price: number;
  /** Price change amount */
  change: number;
  /** Price change percentage */
  changePercent: number;
  /** Show animation on price update (default: true) */
  animate?: boolean;
  /** Compact mode (smaller size, default: false) */
  compact?: boolean;
}

/**
 * Price Cell Component
 *
 * Displays price with change indicator and optional animation
 */
export const PriceCell = React.memo<PriceCellProps>(
  ({ price, change, changePercent, animate = true, compact = false }) => {
    const [showFlash, setShowFlash] = useState(false);
    const [prevPrice, setPrevPrice] = useState(price);

    // Determine trend direction
    const isPositive = change > 0;
    const isNegative = change < 0;

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

    // Trigger flash animation on price change
    useEffect(() => {
      if (animate && price !== prevPrice) {
        setShowFlash(true);
        setPrevPrice(price);

        const timer = setTimeout(() => {
          setShowFlash(false);
        }, 500);

        return () => clearTimeout(timer);
      }
    }, [price, prevPrice, animate]);

    // Format number with commas
    const formatNumber = (num: number) => {
      return new Intl.NumberFormat("ja-JP", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(num);
    };

    // Format percentage
    const formatPercent = (num: number) => {
      const sign = num > 0 ? "+" : "";
      return `${sign}${num.toFixed(2)}%`;
    };

    // Select appropriate icon
    const Icon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;

    return (
      <div
        className={`inline-flex items-center gap-2 rounded-md px-2 py-1 transition-colors duration-300 ${
          showFlash ? flashColor : bgColor
        } ${compact ? "text-xs" : "text-sm"}`}
      >
        {/* Price */}
        <span className={`font-semibold ${trendColor}`}>
          ¥{formatNumber(price)}
        </span>

        {/* Change indicator */}
        <div className={`flex items-center gap-1 ${trendColor}`}>
          <Icon className={compact ? "h-3 w-3" : "h-4 w-4"} />
          <span className="font-medium">
            {formatNumber(Math.abs(change))} ({formatPercent(changePercent)})
          </span>
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
  /** Unrealized profit/loss amount */
  unrealizedPL: number;
  /** Show compact version (default: false) */
  compact?: boolean;
}

export const PLCell = React.memo<PLCellProps>(
  ({ unrealizedPL, compact = false }) => {
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

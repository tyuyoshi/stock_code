/**
 * Stock Price Chart Component
 *
 * Displays historical stock price data using Recharts
 */

"use client";

import React, { useState } from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { StockPrice } from "@/types/company";

type ChartPeriod = "1d" | "5d" | "1mo" | "3mo" | "6mo" | "1y" | "2y" | "5y";
type ChartInterval = "5m" | "15m" | "1h" | "1d";

interface StockPriceChartProps {
  data: StockPrice[];
  ticker: string;
  onPeriodChange?: (period: ChartPeriod) => void;
  currentPeriod?: ChartPeriod;
  onIntervalChange?: (interval: ChartInterval | undefined) => void;
  currentInterval?: ChartInterval;
}

export function StockPriceChart({
  data,
  ticker,
  onPeriodChange,
  currentPeriod = "1mo",
  onIntervalChange,
  currentInterval,
}: StockPriceChartProps) {
  const [chartType, setChartType] = useState<"line" | "area">("area");

  const periods: { value: ChartPeriod; label: string }[] = [
    { value: "1d", label: "1日" },
    { value: "5d", label: "5日" },
    { value: "1mo", label: "1ヶ月" },
    { value: "3mo", label: "3ヶ月" },
    { value: "6mo", label: "6ヶ月" },
    { value: "1y", label: "1年" },
    { value: "2y", label: "2年" },
    { value: "5y", label: "5年" },
  ];

  const intervals: { value: ChartInterval; label: string }[] = [
    { value: "5m", label: "5分" },
    { value: "15m", label: "15分" },
    { value: "1h", label: "1時間" },
    { value: "1d", label: "日足" },
  ];

  // Determine if data contains timestamps (intraday) or dates (daily)
  const isIntradayData = data.length > 0 && !!data[0].timestamp;

  // Format data for Recharts
  const chartData = data.map((price) => {
    const dateTime = price.timestamp || price.date;
    let formattedDate: string;

    if (isIntradayData && price.timestamp) {
      // Intraday data: show time
      const dt = new Date(price.timestamp);
      formattedDate = dt.toLocaleTimeString("ja-JP", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (price.date) {
      // Daily data: show date
      const dt = new Date(price.date);
      formattedDate = dt.toLocaleDateString("ja-JP", {
        month: "short",
        day: "numeric",
      });
    } else {
      formattedDate = "";
    }

    return {
      date: formattedDate,
      rawDate: dateTime,
      price: price.close,
      high: price.high,
      low: price.low,
      volume: price.volume,
    };
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
          <p className="text-sm font-medium text-gray-900">{data.date}</p>
          <p className="mt-1 text-sm text-gray-600">
            終値: ¥{data.price?.toLocaleString("ja-JP") || "-"}
          </p>
          {data.high && (
            <p className="text-xs text-gray-500">
              高値: ¥{data.high.toLocaleString("ja-JP")}
            </p>
          )}
          {data.low && (
            <p className="text-xs text-gray-500">
              安値: ¥{data.low.toLocaleString("ja-JP")}
            </p>
          )}
          {data.volume && (
            <p className="text-xs text-gray-500">
              出来高: {data.volume.toLocaleString("ja-JP")}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  // Show interval selector only for short periods (1d, 5d)
  const showIntervalSelector = currentPeriod === "1d" || currentPeriod === "5d";

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          {/* Period selector */}
          <div className="flex gap-2">
            {periods.map((period) => (
              <button
                key={period.value}
                onClick={() => {
                  onPeriodChange?.(period.value);
                  // Reset interval when changing to longer periods
                  if (period.value !== "1d" && period.value !== "5d") {
                    onIntervalChange?.(undefined);
                  }
                }}
                className={`rounded px-3 py-1 text-sm transition-colors ${
                  currentPeriod === period.value
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {period.label}
              </button>
            ))}
          </div>

          {/* Chart type selector */}
          <div className="flex gap-2">
            <button
              onClick={() => setChartType("line")}
              className={`rounded px-3 py-1 text-sm transition-colors ${
                chartType === "line"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              折れ線
            </button>
            <button
              onClick={() => setChartType("area")}
              className={`rounded px-3 py-1 text-sm transition-colors ${
                chartType === "area"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              エリア
            </button>
          </div>
        </div>

        {/* Interval selector - only shown for 1d and 5d periods */}
        {showIntervalSelector && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">時間間隔:</span>
            <div className="flex gap-2">
              {intervals.map((interval) => (
                <button
                  key={interval.value}
                  onClick={() => onIntervalChange?.(interval.value)}
                  className={`rounded px-3 py-1 text-sm transition-colors ${
                    currentInterval === interval.value
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {interval.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="h-96 w-full">
          <ResponsiveContainer width="100%" height="100%">
            {chartType === "area" ? (
              <AreaChart
                data={chartData}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  stroke="#6b7280"
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fontSize: 12 }}
                  domain={["auto", "auto"]}
                  tickFormatter={(value) => `¥${value.toLocaleString()}`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorPrice)"
                  strokeWidth={2}
                />
              </AreaChart>
            ) : (
              <LineChart
                data={chartData}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  stroke="#6b7280"
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fontSize: 12 }}
                  domain={["auto", "auto"]}
                  tickFormatter={(value) => `¥${value.toLocaleString()}`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      )}

      {/* Stats */}
      {chartData.length > 0 && (
        <div className="grid grid-cols-4 gap-4 rounded-lg bg-gray-50 p-4">
          <div>
            <p className="text-xs text-gray-500">最高値</p>
            <p className="mt-1 text-sm font-semibold text-gray-900">
              ¥
              {Math.max(...chartData.map((d) => d.price || 0)).toLocaleString(
                "ja-JP"
              )}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">最安値</p>
            <p className="mt-1 text-sm font-semibold text-gray-900">
              ¥
              {Math.min(
                ...chartData.map((d) => d.price || Infinity)
              ).toLocaleString("ja-JP")}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">平均</p>
            <p className="mt-1 text-sm font-semibold text-gray-900">
              ¥
              {(
                chartData.reduce((sum, d) => sum + (d.price || 0), 0) /
                chartData.length
              ).toLocaleString("ja-JP")}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">変化率</p>
            <p
              className={`mt-1 text-sm font-semibold ${
                chartData[chartData.length - 1].price! >
                chartData[0].price!
                  ? "text-green-600"
                  : "text-red-600"
              }`}
            >
              {(
                ((chartData[chartData.length - 1].price! -
                  chartData[0].price!) /
                  chartData[0].price!) *
                100
              ).toFixed(2)}
              %
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Financial Trend Chart Component
 *
 * Displays financial data trends (revenue, profit, etc.) over time
 */

"use client";

import React from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { FinancialStatement } from "@/types/company";

interface FinancialTrendChartProps {
  data: FinancialStatement[];
  metrics?: string[];
}

export function FinancialTrendChart({
  data,
  metrics = ["revenue", "operating_income", "net_income"],
}: FinancialTrendChartProps) {
  // Format data for Recharts
  const chartData = data
    .map((stmt) => ({
      period: stmt.period,
      revenue: stmt.revenue ? stmt.revenue / 100_000_000 : null, // Convert to 億円
      operating_income: stmt.operating_income
        ? stmt.operating_income / 100_000_000
        : null,
      net_income: stmt.net_income ? stmt.net_income / 100_000_000 : null,
    }))
    .reverse(); // Oldest to newest for time series

  // Metric labels
  const metricLabels: Record<string, { label: string; color: string }> = {
    revenue: { label: "売上高", color: "#3b82f6" },
    operating_income: { label: "営業利益", color: "#10b981" },
    net_income: { label: "当期純利益", color: "#f59e0b" },
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
          <p className="text-sm font-medium text-gray-900">{data.period}</p>
          {payload.map((entry: any, index: number) => (
            <p
              key={index}
              className="mt-1 text-sm"
              style={{ color: entry.color }}
            >
              {entry.name}: {entry.value?.toFixed(2)}億円
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      <div className="h-96 w-full">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="period"
                stroke="#6b7280"
                tick={{ fontSize: 12 }}
              />
              <YAxis
                stroke="#6b7280"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${value}億円`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: "14px" }}
                formatter={(value) =>
                  metricLabels[value]?.label || value
                }
              />
              {metrics.includes("revenue") && (
                <Line
                  type="monotone"
                  dataKey="revenue"
                  name="revenue"
                  stroke={metricLabels.revenue.color}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
              {metrics.includes("operating_income") && (
                <Line
                  type="monotone"
                  dataKey="operating_income"
                  name="operating_income"
                  stroke={metricLabels.operating_income.color}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
              {metrics.includes("net_income") && (
                <Line
                  type="monotone"
                  dataKey="net_income"
                  name="net_income"
                  stroke={metricLabels.net_income.color}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center">
            <p className="text-gray-500">財務トレンドデータがありません</p>
          </div>
        )}
      </div>

      {/* Growth indicators */}
      {chartData.length >= 2 && (
        <div className="grid grid-cols-3 gap-4 rounded-lg bg-gray-50 p-4">
          {metrics.includes("revenue") && chartData[0].revenue && (
            <div>
              <p className="text-xs text-gray-500">売上高成長率</p>
              <p
                className={`mt-1 text-sm font-semibold ${
                  ((chartData[chartData.length - 1].revenue! -
                    chartData[0].revenue!) /
                    chartData[0].revenue!) *
                    100 >
                  0
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {(
                  ((chartData[chartData.length - 1].revenue! -
                    chartData[0].revenue!) /
                    chartData[0].revenue!) *
                  100
                ).toFixed(2)}
                %
              </p>
            </div>
          )}
          {metrics.includes("operating_income") &&
            chartData[0].operating_income && (
              <div>
                <p className="text-xs text-gray-500">営業利益成長率</p>
                <p
                  className={`mt-1 text-sm font-semibold ${
                    ((chartData[chartData.length - 1].operating_income! -
                      chartData[0].operating_income!) /
                      chartData[0].operating_income!) *
                      100 >
                    0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {(
                    ((chartData[chartData.length - 1].operating_income! -
                      chartData[0].operating_income!) /
                      chartData[0].operating_income!) *
                    100
                  ).toFixed(2)}
                  %
                </p>
              </div>
            )}
          {metrics.includes("net_income") && chartData[0].net_income && (
            <div>
              <p className="text-xs text-gray-500">純利益成長率</p>
              <p
                className={`mt-1 text-sm font-semibold ${
                  ((chartData[chartData.length - 1].net_income! -
                    chartData[0].net_income!) /
                    chartData[0].net_income!) *
                    100 >
                  0
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {(
                  ((chartData[chartData.length - 1].net_income! -
                    chartData[0].net_income!) /
                    chartData[0].net_income!) *
                  100
                ).toFixed(2)}
                %
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

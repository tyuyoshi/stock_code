/**
 * Company Details Page
 *
 * Displays comprehensive company information including:
 * - Basic company info
 * - Financial statements (BS, PL, CF)
 * - Financial indicators
 * - Stock price chart
 */

"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { companyApi } from "@/lib/api/companies";
import { Loader2, TrendingUp, TrendingDown } from "lucide-react";
import { StockPriceChart, FinancialTrendChart } from "@/components/companies";
import { Header } from "@/components/layout";
import { useHash } from "@/lib/hooks/useHash";

type Props = {
  params: { id: string };
};

type TabType = "overview" | "financials" | "chart" | "indicators";
type ChartPeriod = "1d" | "5d" | "1mo" | "3mo" | "6mo" | "1y" | "2y" | "5y";
type ChartInterval = "5m" | "15m" | "1h" | "1d";

export default function CompanyDetailPage({ params }: Props) {
  const { id } = params;
  const companyId = parseInt(id, 10);
  const hash = useHash();
  const [chartPeriod, setChartPeriod] = useState<ChartPeriod>("1mo");
  const [chartInterval, setChartInterval] = useState<ChartInterval | undefined>(undefined);

  // Define tabs
  const tabs = [
    { id: "overview" as TabType, label: "概要" },
    { id: "financials" as TabType, label: "財務諸表" },
    { id: "chart" as TabType, label: "チャート" },
    { id: "indicators" as TabType, label: "財務指標" },
  ];

  // Derive active tab from URL hash, default to 'overview'
  const activeTab = useMemo(() => {
    if (!hash) return "overview";
    const isValidTab = tabs.some((t) => t.id === hash);
    return (isValidTab ? hash : "overview") as TabType;
  }, [hash]);

  // Fetch company data
  const {
    data: company,
    isLoading: companyLoading,
    error: companyError,
  } = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => companyApi.getCompany(companyId),
    enabled: !isNaN(companyId),
  });

  // Fetch latest stock price
  const {
    data: latestPrice,
    isLoading: priceLoading,
    error: priceError,
  } = useQuery({
    queryKey: ["latestPrice", company?.ticker_symbol],
    queryFn: () => companyApi.getLatestPrice(company!.ticker_symbol),
    enabled: !!company?.ticker_symbol,
  });

  // Fetch financial data
  const {
    data: financials,
    isLoading: financialsLoading,
    error: financialsError,
  } = useQuery({
    queryKey: ["financials", companyId],
    queryFn: () => companyApi.getFinancials(companyId),
    enabled: !isNaN(companyId) && activeTab === "financials",
  });

  // Fetch financial indicators
  const {
    data: indicators,
    isLoading: indicatorsLoading,
    error: indicatorsError,
  } = useQuery({
    queryKey: ["indicators", companyId],
    queryFn: () => companyApi.getIndicators(companyId),
    enabled: !isNaN(companyId) && activeTab === "indicators",
  });

  // Fetch chart data
  const {
    data: chartData,
    isLoading: chartLoading,
    error: chartError,
  } = useQuery({
    queryKey: ["chartData", company?.ticker_symbol, chartPeriod, chartInterval],
    queryFn: () => companyApi.getChartData(company!.ticker_symbol, chartPeriod, chartInterval),
    enabled: !!company?.ticker_symbol && activeTab === "chart",
  });

  // Update page title when company data loads
  useEffect(() => {
    if (company) {
      document.title = `${company.company_name_jp} (${company.ticker_symbol}) - Stock Code`;
    }
  }, [company]);

  // Track tab views for analytics (GA4)
  useEffect(() => {
    if (company && hash) {
      // Track tab view as custom event
      if (typeof window !== "undefined" && (window as any).gtag) {
        (window as any).gtag("event", "tab_view", {
          company_id: company.id,
          company_name: company.company_name_jp,
          ticker_symbol: company.ticker_symbol,
          tab_name: hash,
          page_location: window.location.href,
          page_title: document.title,
        });
      }
    }
  }, [company, hash]);

  // Show loading state while fetching company
  if (companyLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto" />
          <p className="mt-4 text-gray-600">企業情報を読み込み中...</p>
        </div>
      </div>
    );
  }

  // Show error state if company fetch failed
  if (companyError || !company) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">エラー</h1>
          <p className="mt-2 text-gray-600">
            企業情報の読み込みに失敗しました
          </p>
          {companyError && (
            <p className="mt-1 text-sm text-gray-500">
              {(companyError as any).message}
            </p>
          )}
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

  const formatNumber = (value: number | undefined, decimals: number = 0) => {
    if (value === undefined || value === null) return "-";
    return value.toLocaleString("ja-JP", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatCurrency = (value: number | undefined) => {
    if (value === undefined || value === null) return "-";
    if (value >= 1_000_000_000_000) {
      return `${(value / 1_000_000_000_000).toFixed(2)}兆円`;
    } else if (value >= 100_000_000) {
      return `${(value / 100_000_000).toFixed(2)}億円`;
    } else if (value >= 10_000) {
      return `${(value / 10_000).toFixed(2)}万円`;
    }
    return `${value.toLocaleString("ja-JP")}円`;
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-gray-50 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Company Header */}
        <div className="mb-6 rounded-lg bg-white p-6 shadow">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-gray-900">
                  {company.company_name_jp}
                </h1>
                <span className="rounded bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
                  {company.ticker_symbol}
                </span>
              </div>
              {company.company_name_en && (
                <p className="mt-1 text-lg text-gray-600">
                  {company.company_name_en}
                </p>
              )}
              <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-600">
                {company.market_division && (
                  <span>市場: {company.market_division}</span>
                )}
                {company.industry_name && (
                  <span>業種: {company.industry_name}</span>
                )}
                {company.employee_count && (
                  <span>従業員数: {formatNumber(company.employee_count)}名</span>
                )}
              </div>
            </div>

            {/* Stock Price Info */}
            {latestPrice && (
              <div className="text-right">
                <div className="text-3xl font-bold text-gray-900">
                  ¥{formatNumber(latestPrice.current_price, 2)}
                </div>
                {latestPrice.change !== undefined &&
                  latestPrice.change_percent !== undefined && (
                    <div
                      className={`mt-1 flex items-center justify-end gap-1 text-sm ${
                        latestPrice.change >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {latestPrice.change >= 0 ? (
                        <TrendingUp className="h-4 w-4" />
                      ) : (
                        <TrendingDown className="h-4 w-4" />
                      )}
                      <span>
                        {latestPrice.change >= 0 ? "+" : ""}
                        {formatNumber(latestPrice.change, 2)} (
                        {latestPrice.change_percent >= 0 ? "+" : ""}
                        {latestPrice.change_percent.toFixed(2)}%)
                      </span>
                    </div>
                  )}
                <div className="mt-1 text-xs text-gray-500">
                  {new Date(latestPrice.last_updated).toLocaleString("ja-JP")}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    window.location.hash = tab.id;
                  }}
                  className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  }`}
                  aria-current={activeTab === tab.id ? "page" : undefined}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="rounded-lg bg-white p-6 shadow">
          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div>
              <h2 className="mb-4 text-xl font-bold text-gray-900">
                企業概要
              </h2>
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {company.listing_date && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      上場日
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {new Date(company.listing_date).toLocaleDateString(
                        "ja-JP"
                      )}
                    </dd>
                  </div>
                )}
                {company.fiscal_year_end && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      決算期
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {company.fiscal_year_end}
                    </dd>
                  </div>
                )}
                {company.market_cap && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      時価総額
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {formatCurrency(company.market_cap)}
                    </dd>
                  </div>
                )}
                {company.shares_outstanding && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      発行済株式数
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {formatNumber(company.shares_outstanding)}株
                    </dd>
                  </div>
                )}
                {company.website_url && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      ウェブサイト
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      <a
                        href={company.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                      >
                        {company.website_url}
                      </a>
                    </dd>
                  </div>
                )}
                {company.headquarters_address && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      本社所在地
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {company.headquarters_address}
                    </dd>
                  </div>
                )}
              </dl>
              {company.description && (
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-gray-500">
                    事業内容
                  </h3>
                  <p className="mt-2 text-sm text-gray-900">
                    {company.description}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Financials Tab */}
          {activeTab === "financials" && (
            <div>
              <h2 className="mb-4 text-xl font-bold text-gray-900">
                財務諸表
              </h2>
              {financialsLoading ? (
                <div className="py-12 text-center">
                  <Loader2 className="mx-auto h-8 w-8 animate-spin text-gray-400" />
                  <p className="mt-4 text-gray-600">財務データを読み込み中...</p>
                </div>
              ) : financialsError || !financials || financials.financial_statements.length === 0 ? (
                <div className="rounded-lg bg-gray-50 p-8 text-center">
                  <p className="text-gray-600">財務データがまだありません</p>
                  <p className="mt-2 text-sm text-gray-500">
                    データ投入後に財務諸表が表示されます
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          項目
                        </th>
                        {financials.financial_statements.map((stmt, idx) => (
                          <th
                            key={idx}
                            className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500"
                          >
                            {stmt.period}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {/* Revenue */}
                      <tr>
                        <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                          売上高
                        </td>
                        {financials.financial_statements.map((stmt, idx) => (
                          <td
                            key={idx}
                            className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900"
                          >
                            {formatCurrency(stmt.revenue)}
                          </td>
                        ))}
                      </tr>
                      {/* Operating Income */}
                      <tr>
                        <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                          営業利益
                        </td>
                        {financials.financial_statements.map((stmt, idx) => (
                          <td
                            key={idx}
                            className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900"
                          >
                            {formatCurrency(stmt.operating_income)}
                          </td>
                        ))}
                      </tr>
                      {/* Net Income */}
                      <tr>
                        <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                          当期純利益
                        </td>
                        {financials.financial_statements.map((stmt, idx) => (
                          <td
                            key={idx}
                            className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900"
                          >
                            {formatCurrency(stmt.net_income)}
                          </td>
                        ))}
                      </tr>
                      {/* Total Assets */}
                      <tr className="bg-gray-50">
                        <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                          総資産
                        </td>
                        {financials.financial_statements.map((stmt, idx) => (
                          <td
                            key={idx}
                            className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900"
                          >
                            {formatCurrency(stmt.total_assets)}
                          </td>
                        ))}
                      </tr>
                      {/* Total Equity */}
                      <tr className="bg-gray-50">
                        <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                          純資産
                        </td>
                        {financials.financial_statements.map((stmt, idx) => (
                          <td
                            key={idx}
                            className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900"
                          >
                            {formatCurrency(stmt.total_equity)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>

                  {/* Financial Trend Chart */}
                  <div className="mt-8">
                    <h3 className="mb-4 text-lg font-semibold text-gray-900">
                      財務推移
                    </h3>
                    <FinancialTrendChart
                      data={financials.financial_statements}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Chart Tab */}
          {activeTab === "chart" && (
            <div>
              <h2 className="mb-4 text-xl font-bold text-gray-900">
                株価チャート
              </h2>

              {/* Always show StockPriceChart to preserve period/interval controls */}
              <StockPriceChart
                data={chartData?.data || []}
                ticker={company!.ticker_symbol}
                currentPeriod={chartPeriod}
                onPeriodChange={setChartPeriod}
                currentInterval={chartInterval}
                onIntervalChange={setChartInterval}
              />

              {/* Show loading state below chart controls */}
              {chartLoading && (
                <div className="mt-4 py-12 text-center">
                  <Loader2 className="mx-auto h-8 w-8 animate-spin text-gray-400" />
                  <p className="mt-4 text-gray-600">
                    チャートデータを読み込み中...
                  </p>
                </div>
              )}

              {/* Show error/no-data message below chart controls */}
              {!chartLoading && chartError && (
                (chartError as any)?.response?.status === 404 ? (
                  <div className="mt-4 rounded-lg bg-gray-50 p-8 text-center">
                    <p className="text-gray-600">株価データがまだありません</p>
                    <p className="mt-2 text-sm text-gray-500">
                      データ投入後に株価チャートが表示されます
                    </p>
                  </div>
                ) : (
                  <div className="mt-4 rounded-lg bg-red-50 p-8 text-center">
                    <p className="text-red-600">
                      チャートデータの読み込みに失敗しました
                    </p>
                    <p className="mt-2 text-sm text-gray-600">
                      {(chartError as any)?.message || "エラーが発生しました"}
                    </p>
                  </div>
                )
              )}
            </div>
          )}

          {/* Indicators Tab */}
          {activeTab === "indicators" && (
            <div>
              <h2 className="mb-4 text-xl font-bold text-gray-900">
                財務指標
              </h2>
              {indicatorsLoading ? (
                <div className="py-12 text-center">
                  <Loader2 className="mx-auto h-8 w-8 animate-spin text-gray-400" />
                  <p className="mt-4 text-gray-600">財務指標を読み込み中...</p>
                </div>
              ) : indicatorsError || !indicators || !indicators.indicators || Object.keys(indicators.indicators).length === 0 ? (
                <div className="rounded-lg bg-gray-50 p-8 text-center">
                  <p className="text-gray-600">財務指標がまだありません</p>
                  <p className="mt-2 text-sm text-gray-500">
                    データ投入後に財務指標が表示されます
                  </p>
                </div>
              ) : (
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {/* Profitability */}
                  {indicators.indicators.profitability && (
                    <div className="rounded-lg border border-gray-200 p-4">
                      <h3 className="mb-3 text-sm font-semibold text-gray-700">
                        収益性
                      </h3>
                      <dl className="space-y-2">
                        {indicators.indicators.profitability.roe !==
                          undefined && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-600">ROE</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {indicators.indicators.profitability.roe.toFixed(
                                2
                              )}
                              %
                            </dd>
                          </div>
                        )}
                        {indicators.indicators.profitability.roa !==
                          undefined && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-600">ROA</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {indicators.indicators.profitability.roa.toFixed(
                                2
                              )}
                              %
                            </dd>
                          </div>
                        )}
                        {indicators.indicators.profitability
                          .operating_margin !== undefined && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-600">
                              営業利益率
                            </dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {indicators.indicators.profitability.operating_margin.toFixed(
                                2
                              )}
                              %
                            </dd>
                          </div>
                        )}
                      </dl>
                    </div>
                  )}

                  {/* Safety */}
                  {indicators.indicators.safety && (
                    <div className="rounded-lg border border-gray-200 p-4">
                      <h3 className="mb-3 text-sm font-semibold text-gray-700">
                        安全性
                      </h3>
                      <dl className="space-y-2">
                        {indicators.indicators.safety.equity_ratio !==
                          undefined && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-600">
                              自己資本比率
                            </dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {indicators.indicators.safety.equity_ratio.toFixed(
                                2
                              )}
                              %
                            </dd>
                          </div>
                        )}
                        {indicators.indicators.safety.current_ratio !==
                          undefined && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-600">
                              流動比率
                            </dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {indicators.indicators.safety.current_ratio.toFixed(
                                2
                              )}
                              %
                            </dd>
                          </div>
                        )}
                      </dl>
                    </div>
                  )}

                  {/* Valuation */}
                  {indicators.indicators.valuation && (
                    <div className="rounded-lg border border-gray-200 p-4">
                      <h3 className="mb-3 text-sm font-semibold text-gray-700">
                        株価指標
                      </h3>
                      <dl className="space-y-2">
                        {indicators.indicators.valuation.per !== undefined && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-600">PER</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {indicators.indicators.valuation.per.toFixed(2)}倍
                            </dd>
                          </div>
                        )}
                        {indicators.indicators.valuation.pbr !== undefined && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-600">PBR</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {indicators.indicators.valuation.pbr.toFixed(2)}倍
                            </dd>
                          </div>
                        )}
                      </dl>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
        </div>
      </main>
    </div>
  );
}

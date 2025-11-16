/**
 * Company-related types for API responses
 */

/**
 * Base company information
 */
export interface Company {
  id: number;
  ticker_symbol: string;
  company_name_jp: string;
  company_name_en?: string;
  market_division?: string;
  industry_code?: string;
  industry_name?: string;
  edinet_code?: string;
  founding_date?: string;
  listing_date?: string;
  fiscal_year_end?: string;
  employee_count?: number;
  market_cap?: number;
  shares_outstanding?: number;
  description?: string;
  website_url?: string;
  headquarters_address?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Financial statement data
 */
export interface FinancialStatement {
  period: string;
  period_type?: string;
  // Balance Sheet
  total_assets?: number;
  total_liabilities?: number;
  total_equity?: number;
  current_assets?: number;
  current_liabilities?: number;
  // Income Statement
  revenue?: number;
  operating_income?: number;
  ordinary_income?: number;
  net_income?: number;
  // Cash Flow
  operating_cash_flow?: number;
  investing_cash_flow?: number;
  financing_cash_flow?: number;
  free_cash_flow?: number;
  [key: string]: any;
}

/**
 * Company financial data response
 */
export interface FinancialDataResponse {
  company_id: number;
  financial_statements: FinancialStatement[];
  latest_period?: string;
  currency: string;
}

/**
 * Financial indicators organized by category
 */
export interface FinancialIndicators {
  profitability?: {
    roe?: number;
    roa?: number;
    operating_margin?: number;
    net_margin?: number;
    gross_margin?: number;
    [key: string]: number | undefined;
  };
  safety?: {
    equity_ratio?: number;
    debt_to_equity?: number;
    current_ratio?: number;
    quick_ratio?: number;
    [key: string]: number | undefined;
  };
  efficiency?: {
    asset_turnover?: number;
    inventory_turnover?: number;
    receivables_turnover?: number;
    [key: string]: number | undefined;
  };
  growth?: {
    revenue_growth?: number;
    income_growth?: number;
    asset_growth?: number;
    [key: string]: number | undefined;
  };
  valuation?: {
    per?: number;
    pbr?: number;
    pcfr?: number;
    dividend_yield?: number;
    ev_ebitda?: number;
    [key: string]: number | undefined;
  };
  cash_flow?: {
    operating_cf_margin?: number;
    free_cash_flow_margin?: number;
    cf_to_revenue?: number;
    [key: string]: number | undefined;
  };
  [key: string]: any;
}

/**
 * Company financial indicators response
 */
export interface FinancialIndicatorsResponse {
  company_id: number;
  indicators: FinancialIndicators;
  date?: string;
  period?: string;
}

/**
 * Stock price data point
 */
export interface StockPrice {
  date?: string; // For daily data
  timestamp?: string; // For intraday data
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
}

/**
 * Latest stock price response
 */
export interface LatestPriceResponse {
  ticker_symbol: string;
  current_price?: number;
  open_price?: number;
  high_price?: number;
  low_price?: number;
  volume?: number;
  previous_close?: number;
  change?: number;
  change_percent?: number;
  market_cap?: number;
  currency: string;
  last_updated: string;
}

/**
 * Chart data response
 */
export interface ChartDataResponse {
  ticker_symbol: string;
  period: string;
  interval?: string;
  data: StockPrice[];
  data_source?: string;
}

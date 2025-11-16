/**
 * Companies API Client
 *
 * Provides functions to interact with company-related API endpoints.
 */

import apiClient from "./client";
import type {
  Company,
  FinancialDataResponse,
  FinancialIndicatorsResponse,
  LatestPriceResponse,
  ChartDataResponse,
} from "@/types/company";

/**
 * Company API functions
 */
export const companyApi = {
  /**
   * Get company details by ID
   */
  getCompany: async (id: number): Promise<Company> => {
    const response = await apiClient.get<Company>(`/api/v1/companies/${id}`);
    return response.data;
  },

  /**
   * Get company's financial statements
   */
  getFinancials: async (
    id: number,
    limit: number = 5
  ): Promise<FinancialDataResponse> => {
    const response = await apiClient.get<FinancialDataResponse>(
      `/api/v1/companies/${id}/financials`,
      {
        params: { limit },
      }
    );
    return response.data;
  },

  /**
   * Get company's financial indicators
   */
  getIndicators: async (id: number): Promise<FinancialIndicatorsResponse> => {
    const response = await apiClient.get<FinancialIndicatorsResponse>(
      `/api/v1/companies/${id}/indicators`
    );
    return response.data;
  },

  /**
   * Get latest stock price for a ticker
   */
  getLatestPrice: async (
    ticker: string,
    live: boolean = false
  ): Promise<LatestPriceResponse> => {
    const response = await apiClient.get<LatestPriceResponse>(
      `/api/v1/stock-prices/${ticker}/latest`,
      {
        params: { live },
      }
    );
    return response.data;
  },

  /**
   * Get chart data for a ticker
   */
  getChartData: async (
    ticker: string,
    period: string = "1mo",
    interval?: string
  ): Promise<ChartDataResponse> => {
    const response = await apiClient.get<ChartDataResponse>(
      `/api/v1/stock-prices/${ticker}/chart`,
      {
        params: { period, ...(interval && { interval }) },
      }
    );
    return response.data;
  },
};

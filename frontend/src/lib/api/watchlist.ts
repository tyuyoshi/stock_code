/**
 * Watchlist API Client
 *
 * Provides functions to interact with watchlist-related API endpoints.
 */

import apiClient from "./client";
import type {
  Watchlist,
  WatchlistDetail,
  CreateWatchlistRequest,
  AddStockRequest,
  UpdateWatchlistRequest,
} from "@/types/watchlist";

/**
 * Watchlist API functions
 */
export const watchlistApi = {
  /**
   * Get all watchlists for the current user
   */
  getWatchlists: async (): Promise<Watchlist[]> => {
    const response = await apiClient.get<Watchlist[]>("/api/v1/watchlists/");
    return response.data;
  },

  /**
   * Get a specific watchlist with all its items
   */
  getWatchlistDetail: async (id: number): Promise<WatchlistDetail> => {
    const response = await apiClient.get<WatchlistDetail>(
      `/api/v1/watchlists/${id}`
    );
    return response.data;
  },

  /**
   * Create a new watchlist
   */
  createWatchlist: async (
    data: CreateWatchlistRequest
  ): Promise<Watchlist> => {
    const response = await apiClient.post<Watchlist>(
      "/api/v1/watchlists/",
      data
    );
    return response.data;
  },

  /**
   * Create a default watchlist for new users
   * This is a convenience method that creates a watchlist with default settings
   */
  createDefaultWatchlist: async (): Promise<Watchlist> => {
    return watchlistApi.createWatchlist({
      name: "マイウォッチリスト",
      description: "デフォルトのウォッチリストです",
      is_public: false,
      display_order: 0,
    });
  },

  /**
   * Update watchlist details
   */
  updateWatchlist: async (
    id: number,
    data: UpdateWatchlistRequest
  ): Promise<Watchlist> => {
    const response = await apiClient.put<Watchlist>(
      `/api/v1/watchlists/${id}`,
      data
    );
    return response.data;
  },

  /**
   * Delete a watchlist
   */
  deleteWatchlist: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/watchlists/${id}`);
  },

  /**
   * Add a stock to a watchlist
   */
  addStock: async (
    watchlistId: number,
    data: AddStockRequest
  ): Promise<void> => {
    await apiClient.post(`/api/v1/watchlists/${watchlistId}/stocks`, data);
  },

  /**
   * Remove a stock from a watchlist
   */
  removeStock: async (
    watchlistId: number,
    companyId: number
  ): Promise<void> => {
    await apiClient.delete(
      `/api/v1/watchlists/${watchlistId}/stocks/${companyId}`
    );
  },

  /**
   * Update stock details in a watchlist (quantity, price, memo, etc.)
   */
  updateStock: async (
    watchlistId: number,
    companyId: number,
    data: Partial<AddStockRequest>
  ): Promise<void> => {
    await apiClient.put(
      `/api/v1/watchlists/${watchlistId}/stocks/${companyId}`,
      data
    );
  },
};

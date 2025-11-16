/**
 * Watchlist Type Definitions
 *
 * Type definitions for watchlist entities used across the application.
 */

/**
 * Watchlist entity
 */
export interface Watchlist {
  id: number;
  name: string;
  description?: string;
  is_public: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

/**
 * Watchlist item (stock in a watchlist)
 */
export interface WatchlistItem {
  id: number;
  watchlist_id: number;
  company_id: number;
  ticker_symbol: string;
  company_name: string;
  display_order: number;
  quantity?: number;
  purchase_price?: number;
  memo?: string;
  tags?: string[];
}

/**
 * Watchlist with items (detailed view)
 */
export interface WatchlistDetail extends Watchlist {
  items: WatchlistItem[];
}

/**
 * Request payload for creating a new watchlist
 */
export interface CreateWatchlistRequest {
  name: string;
  description?: string;
  is_public?: boolean;
  display_order?: number;
}

/**
 * Request payload for adding a stock to a watchlist
 */
export interface AddStockRequest {
  company_id: number;
  display_order?: number;
  quantity?: number;
  purchase_price?: number;
  memo?: string;
  tags?: string[];
}

/**
 * Request payload for updating watchlist details
 */
export interface UpdateWatchlistRequest {
  name?: string;
  description?: string;
  is_public?: boolean;
  display_order?: number;
}

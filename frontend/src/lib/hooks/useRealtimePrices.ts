/**
 * React Hook for Real-time Stock Price Updates
 *
 * Manages WebSocket connection and provides real-time price data
 * with connection state management and automatic cleanup.
 *
 * Usage:
 * ```tsx
 * const { stocks, connectionState, error, connect, disconnect } = useRealtimePrices(watchlistId);
 *
 * useEffect(() => {
 *   connect();
 *   return () => disconnect();
 * }, [watchlistId]);
 * ```
 */

import { useState, useEffect, useCallback, useRef } from "react";
import {
  WebSocketClient,
  ConnectionState,
  StockPrice,
  PriceUpdateMessage,
} from "../websocket";
import { watchlistApi } from "../api/watchlist";

export interface UseRealtimePricesResult {
  /** Current stock prices */
  stocks: StockPrice[];
  /** WebSocket connection state */
  connectionState: ConnectionState;
  /** Latest error, if any */
  error: Error | null;
  /** Last update timestamp */
  lastUpdate: string | null;
  /** Loading state for initial data fetch */
  isLoading: boolean;
  /** Connect to WebSocket */
  connect: () => void;
  /** Disconnect from WebSocket */
  disconnect: () => void;
  /** Refresh data via REST API */
  refresh: () => Promise<void>;
  /** Check if currently connected */
  isConnected: boolean;
}

/**
 * Hook for managing real-time stock price updates via WebSocket
 *
 * @param watchlistId - ID of the watchlist to monitor
 * @param autoConnect - Whether to automatically connect on mount (default: false)
 * @returns Real-time price data and connection management functions
 */
export function useRealtimePrices(
  watchlistId: number | null,
  autoConnect: boolean = false
): UseRealtimePricesResult {
  const [stocks, setStocks] = useState<StockPrice[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    ConnectionState.DISCONNECTED
  );
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const clientRef = useRef<WebSocketClient | null>(null);
  const watchlistIdRef = useRef<number | null>(watchlistId);

  // Update ref when watchlistId changes
  useEffect(() => {
    watchlistIdRef.current = watchlistId;
  }, [watchlistId]);

  /**
   * Handle incoming price update messages
   */
  const handleMessage = useCallback((message: PriceUpdateMessage) => {
    console.log('[useRealtimePrices] Price update received:', {
      stocks: message.stocks.length,
      timestamp: message.timestamp,
      watchlistId: message.watchlist_id
    });

    setStocks(message.stocks);
    setLastUpdate(message.timestamp);
    setError(null);
  }, []);

  /**
   * Handle connection state changes
   */
  const handleStateChange = useCallback((state: ConnectionState) => {
    setConnectionState(state);

    // Clear error when successfully connected
    if (state === ConnectionState.CONNECTED) {
      setError(null);
    }
  }, []);

  /**
   * Handle WebSocket errors
   */
  const handleError = useCallback((err: Error) => {
    setError(err);
    console.error("[useRealtimePrices] Error:", err);
  }, []);

  /**
   * Fetch initial watchlist data via REST API (includes price data)
   */
  const fetchInitialData = useCallback(async () => {
    if (!watchlistIdRef.current) {
      console.warn("[useRealtimePrices] Cannot fetch: watchlistId is null");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Fetch watchlist structure
      const watchlistDetail = await watchlistApi.getWatchlistDetail(
        watchlistIdRef.current
      );

      // Fetch current prices for all stocks (same as refresh function)
      const prices = await watchlistApi.getWatchlistPrices(
        watchlistIdRef.current
      );

      // Merge watchlist items with price data
      const initialStocks: StockPrice[] = watchlistDetail.items.map((item) => {
        const priceData = prices[item.ticker_symbol];

        return {
          company_id: item.company_id,
          ticker_symbol: item.ticker_symbol,
          company_name: item.company_name,
          current_price: priceData?.close_price ?? null,
          change:
            priceData?.close_price && priceData?.previous_close
              ? priceData.close_price - priceData.previous_close
              : null,
          change_percent:
            priceData?.close_price && priceData?.previous_close
              ? ((priceData.close_price - priceData.previous_close) /
                  priceData.previous_close) *
                100
              : null,
          quantity: item.quantity,
          purchase_price: item.purchase_price,
          unrealized_pl:
            priceData?.close_price &&
            item.quantity &&
            item.purchase_price
              ? (priceData.close_price - item.purchase_price) * item.quantity
              : undefined,
          market_status: priceData?.market_status,
          date: priceData?.date,
          tags: item.tags,
          memo: item.memo,
        };
      });

      setStocks(initialStocks);
      setLastUpdate(new Date().toISOString());
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      console.error("[useRealtimePrices] Failed to fetch initial data:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Refresh data via REST API (manual refresh)
   */
  const refresh = useCallback(async () => {
    if (!watchlistIdRef.current) {
      console.warn("[useRealtimePrices] Cannot refresh: watchlistId is null");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Fetch fresh watchlist structure (for new items)
      const watchlistDetail = await watchlistApi.getWatchlistDetail(
        watchlistIdRef.current
      );

      // Fetch current prices for all stocks
      const prices = await watchlistApi.getWatchlistPrices(
        watchlistIdRef.current
      );

      // Merge watchlist items with price data
      const updatedStocks: StockPrice[] = watchlistDetail.items.map((item) => {
        const priceData = prices[item.ticker_symbol];

        return {
          company_id: item.company_id,
          ticker_symbol: item.ticker_symbol,
          company_name: item.company_name,
          current_price: priceData?.close_price ?? null,
          change:
            priceData?.close_price && priceData?.previous_close
              ? priceData.close_price - priceData.previous_close
              : null,
          change_percent:
            priceData?.close_price && priceData?.previous_close
              ? ((priceData.close_price - priceData.previous_close) /
                  priceData.previous_close) *
                100
              : null,
          quantity: item.quantity,
          purchase_price: item.purchase_price,
          unrealized_pl:
            priceData?.close_price &&
            item.quantity &&
            item.purchase_price
              ? (priceData.close_price - item.purchase_price) * item.quantity
              : undefined,
          market_status: priceData?.market_status,
          date: priceData?.date,
          tags: item.tags,
          memo: item.memo,
        };
      });

      setStocks(updatedStocks);
      setLastUpdate(new Date().toISOString());
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      console.error("[useRealtimePrices] Failed to refresh data:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!watchlistIdRef.current) {
      console.warn("[useRealtimePrices] Cannot connect: watchlistId is null");
      return;
    }

    // Disconnect existing client if any
    if (clientRef.current) {
      clientRef.current.disconnect();
    }

    try {
      clientRef.current = new WebSocketClient({
        watchlistId: watchlistIdRef.current,
        onMessage: handleMessage,
        onStateChange: handleStateChange,
        onError: handleError,
        maxReconnectAttempts: 5,
        reconnectInterval: 3000,
      });

      // Connect is now async - handle promise
      clientRef.current.connect().catch((err) => {
        const error = err instanceof Error ? err : new Error(String(err));
        handleError(error);
      });
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      handleError(error);
    }
  }, [handleMessage, handleStateChange, handleError]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }

    // Keep stocks data (fetched via REST API)
    // Only update connection state
    setConnectionState(ConnectionState.DISCONNECTED);
    setError(null);
  }, []);

  /**
   * Fetch initial data on mount or when watchlistId changes
   */
  useEffect(() => {
    if (watchlistId) {
      fetchInitialData();
    }
  }, [watchlistId, fetchInitialData]);

  /**
   * Auto-connect on mount if enabled
   */
  useEffect(() => {
    if (autoConnect && watchlistId) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect, watchlistId, connect, disconnect]);

  /**
   * Reconnect when watchlistId changes (if already connected)
   */
  useEffect(() => {
    if (clientRef.current?.isConnected() && watchlistId) {
      disconnect();
      connect();
    }
  }, [watchlistId, connect, disconnect]);

  return {
    stocks,
    connectionState,
    error,
    lastUpdate,
    isLoading,
    connect,
    disconnect,
    refresh,
    isConnected: connectionState === ConnectionState.CONNECTED,
  };
}

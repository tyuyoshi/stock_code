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

export interface UseRealtimePricesResult {
  /** Current stock prices */
  stocks: StockPrice[];
  /** WebSocket connection state */
  connectionState: ConnectionState;
  /** Latest error, if any */
  error: Error | null;
  /** Last update timestamp */
  lastUpdate: string | null;
  /** Connect to WebSocket */
  connect: () => void;
  /** Disconnect from WebSocket */
  disconnect: () => void;
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

      clientRef.current.connect();
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

    setStocks([]);
    setConnectionState(ConnectionState.DISCONNECTED);
    setError(null);
    setLastUpdate(null);
  }, []);

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
    connect,
    disconnect,
    isConnected: connectionState === ConnectionState.CONNECTED,
  };
}

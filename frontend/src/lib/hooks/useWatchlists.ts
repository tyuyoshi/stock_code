/**
 * Watchlist Management Hook
 *
 * React Hook for managing watchlist state and operations.
 * Provides functions to fetch, create, update, and delete watchlists.
 */

import { useState, useEffect, useCallback } from "react";
import { watchlistApi } from "../api/watchlist";
import type { Watchlist, CreateWatchlistRequest } from "@/types/watchlist";

export interface UseWatchlistsResult {
  /** List of user's watchlists */
  watchlists: Watchlist[];
  /** Loading state */
  isLoading: boolean;
  /** Error object if request failed */
  error: Error | null;
  /** Refetch watchlists from server */
  refetch: () => Promise<void>;
  /** Create a new watchlist */
  createWatchlist: (data: CreateWatchlistRequest) => Promise<Watchlist>;
  /** Create default watchlist for new users */
  createDefaultWatchlist: () => Promise<Watchlist>;
}

/**
 * Hook for managing user's watchlists
 *
 * Fetches watchlists on mount and provides functions for CRUD operations.
 *
 * @param autoFetch - Whether to automatically fetch on mount (default: true)
 * @returns Watchlist data and management functions
 *
 * @example
 * ```tsx
 * const { watchlists, isLoading, createDefaultWatchlist } = useWatchlists();
 *
 * useEffect(() => {
 *   if (!isLoading && watchlists.length === 0) {
 *     createDefaultWatchlist();
 *   }
 * }, [isLoading, watchlists]);
 * ```
 */
export function useWatchlists(
  autoFetch: boolean = true
): UseWatchlistsResult {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Fetch watchlists from server
   */
  const fetchWatchlists = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await watchlistApi.getWatchlists();
      setWatchlists(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      console.error("[useWatchlists] Failed to fetch watchlists:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Create a new watchlist
   */
  const createWatchlist = useCallback(
    async (data: CreateWatchlistRequest): Promise<Watchlist> => {
      try {
        const newWatchlist = await watchlistApi.createWatchlist(data);
        setWatchlists((prev) => [...prev, newWatchlist]);
        return newWatchlist;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        console.error("[useWatchlists] Failed to create watchlist:", error);
        throw error;
      }
    },
    []
  );

  /**
   * Create default watchlist for new users
   */
  const createDefaultWatchlist = useCallback(async (): Promise<Watchlist> => {
    try {
      const newWatchlist = await watchlistApi.createDefaultWatchlist();
      setWatchlists((prev) => [...prev, newWatchlist]);
      return newWatchlist;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      console.error(
        "[useWatchlists] Failed to create default watchlist:",
        error
      );
      throw error;
    }
  }, []);

  /**
   * Auto-fetch on mount if enabled
   */
  useEffect(() => {
    if (autoFetch) {
      fetchWatchlists();
    }
  }, [autoFetch, fetchWatchlists]);

  return {
    watchlists,
    isLoading,
    error,
    refetch: fetchWatchlists,
    createWatchlist,
    createDefaultWatchlist,
  };
}

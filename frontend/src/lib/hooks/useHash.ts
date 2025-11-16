/**
 * Custom hook to track URL hash changes in Next.js 14+
 *
 * Handles both native hashchange events and History API changes
 * to provide seamless hash-based navigation in client components.
 */

"use client";

import { useEffect, useState } from "react";

/**
 * useHash hook
 *
 * Returns the current URL hash (without the # prefix)
 * and updates whenever the hash changes via:
 * - Direct hash manipulation
 * - Browser back/forward navigation
 * - Next.js Link clicks
 * - History API calls
 *
 * @returns Current hash string (empty string if no hash)
 */
export const useHash = (): string => {
  const [hash, setHash] = useState<string>("");

  useEffect(() => {
    // Initialize hash from current URL (client-side only)
    const currentHash = window.location.hash.replace("#", "");
    setHash(currentHash);

    // Handler for hash changes
    const onHashChanged = () => {
      const newHash = window.location.hash.replace("#", "");
      setHash(newHash);
    };

    // Patch History API to catch Next.js Link hash changes
    // This is necessary because Next.js uses pushState/replaceState
    // which don't trigger hashchange events
    const { pushState, replaceState } = window.history;

    window.history.pushState = function (...args) {
      pushState.apply(window.history, args);
      // Use setTimeout to ensure the hash is updated after pushState
      setTimeout(() => {
        const newHash = window.location.hash.replace("#", "");
        setHash(newHash);
      }, 0);
    };

    window.history.replaceState = function (...args) {
      replaceState.apply(window.history, args);
      setTimeout(() => {
        const newHash = window.location.hash.replace("#", "");
        setHash(newHash);
      }, 0);
    };

    // Listen to native hashchange events (browser back/forward, manual changes)
    window.addEventListener("hashchange", onHashChanged);

    // Cleanup
    return () => {
      window.removeEventListener("hashchange", onHashChanged);
      // Restore original History API methods
      window.history.pushState = pushState;
      window.history.replaceState = replaceState;
    };
  }, []);

  return hash;
};

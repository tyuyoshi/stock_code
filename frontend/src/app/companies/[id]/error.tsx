/**
 * Error state for company details page
 */

"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to error reporting service
    console.error("Company details page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-red-600">エラー</h1>
        <p className="mt-2 text-gray-600">
          企業情報の読み込みに失敗しました
        </p>
        <p className="mt-1 text-sm text-gray-500">{error.message}</p>
        <button
          onClick={reset}
          className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          再読み込み
        </button>
      </div>
    </div>
  );
}

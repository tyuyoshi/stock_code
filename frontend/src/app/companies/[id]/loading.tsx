/**
 * Loading state for company details page
 */

import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto" />
        <p className="mt-4 text-gray-600">企業情報を読み込み中...</p>
      </div>
    </div>
  );
}

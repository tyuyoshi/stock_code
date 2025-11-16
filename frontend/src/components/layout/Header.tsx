/**
 * Header Component
 *
 * Common header with navigation and authentication
 */

"use client";

import { useAuth } from "@/lib/auth/AuthContext";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="border-b bg-white">
      <div className="container flex h-16 items-center px-4">
        <div className="mr-8 flex items-center space-x-2">
          <Link href="/">
            <span className="text-xl font-bold cursor-pointer hover:text-primary">
              Stock Code
            </span>
          </Link>
        </div>
        <nav className="flex items-center space-x-6 text-sm font-medium flex-1">
          {user && (
            <>
              <Link href="/companies" className="hover:text-primary">
                企業検索
              </Link>
              <Link href="/screening" className="hover:text-primary">
                スクリーニング
              </Link>
              <Link href="/watchlist" className="hover:text-primary">
                ウォッチリスト
              </Link>
            </>
          )}
        </nav>
        <div className="flex items-center space-x-4">
          {user ? (
            <>
              <span className="text-sm text-muted-foreground">
                {user.email}
              </span>
              <Button variant="outline" onClick={logout}>
                ログアウト
              </Button>
            </>
          ) : (
            <Button asChild>
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google/login`}
              >
                Googleでログイン
              </a>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

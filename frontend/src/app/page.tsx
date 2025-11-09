"use client";

import { useAuth } from "@/lib/auth/AuthContext";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function HomePage() {
  const { user, isLoading, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="container flex h-16 items-center px-4">
          <div className="mr-8 flex items-center space-x-2">
            <span className="text-xl font-bold">Stock Code</span>
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
                <a href={`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google/login`}>
                  Googleでログイン
                </a>
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="container px-4 py-24 md:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl mb-6">
              日本上場企業の
              <br />
              財務データ分析プラットフォーム
            </h1>
            <p className="text-lg text-muted-foreground mb-8">
              EDINET APIを活用した包括的な企業分析ツール。
              財務指標の可視化、スクリーニング、比較分析を簡単に。
            </p>
            {!user && (
              <Button size="lg" asChild>
                <a href={`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google/login`}>
                  今すぐ始める
                </a>
              </Button>
            )}
          </div>
        </section>

        <section className="border-t bg-muted/50">
          <div className="container px-4 py-16">
            <h2 className="text-3xl font-bold text-center mb-12">主な機能</h2>
            <div className="grid gap-8 md:grid-cols-3">
              <div className="flex flex-col items-center text-center">
                <div className="rounded-full bg-primary/10 p-4 mb-4">
                  <svg
                    className="h-6 w-6 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">財務データ分析</h3>
                <p className="text-muted-foreground">
                  60以上の財務指標を自動計算。ROE、PER、営業利益率など。
                </p>
              </div>

              <div className="flex flex-col items-center text-center">
                <div className="rounded-full bg-primary/10 p-4 mb-4">
                  <svg
                    className="h-6 w-6 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">スクリーニング</h3>
                <p className="text-muted-foreground">
                  柔軟な条件で企業を検索。カスタムフィルターで理想の銘柄を発見。
                </p>
              </div>

              <div className="flex flex-col items-center text-center">
                <div className="rounded-full bg-primary/10 p-4 mb-4">
                  <svg
                    className="h-6 w-6 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">チャート可視化</h3>
                <p className="text-muted-foreground">
                  リアルタイム株価とヒストリカルデータをわかりやすく表示。
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-6 md:py-0">
        <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row px-4">
          <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
            © 2025 Stock Code. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

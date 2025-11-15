"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";

export interface User {
  id: number;
  email: string;
  name: string;
  profile_picture_url?: string;
  role: "free" | "premium" | "enterprise";
  investment_experience?: string;
  investment_style?: string;
  interested_industries?: string[];
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Memoize fetchUser to prevent infinite loops
  const fetchUser = useCallback(async () => {
    console.log("[AuthContext] Fetching user...");
    try {
      const response = await apiClient.get<User>("/api/v1/auth/me");
      console.log("[AuthContext] User authenticated:", response.data.email);
      setUser(response.data);
    } catch (error) {
      console.log("[AuthContext] User not authenticated (expected on first load)");
      setUser(null);
    } finally {
      setIsLoading(false);
      console.log("[AuthContext] Loading complete");
    }
  }, []); // No dependencies - stable function reference

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = () => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google/login`;
  };

  const logout = async () => {
    try {
      await apiClient.post("/api/v1/auth/logout");
      setUser(null);
      window.location.href = "/";
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  // Memoize refreshUser to prevent infinite loops in callback page
  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

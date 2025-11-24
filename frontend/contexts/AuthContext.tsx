"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";

interface User {
  id: number;
  email: string;
  full_name: string | null;
  status: "pending" | "active" | "suspended";
  is_super_admin: boolean;
  can_use_advanced: boolean;
  organization_id: number | null;
  current_workspace_id: number | null;
  created_at: string;
  last_login_at: string | null;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string, userInfo: User) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isSuperAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Load token and user from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token");
    if (storedToken) {
      setToken(storedToken);
      loadUser(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async (authToken: string) => {
    try {
      // Set token in API client
      apiClient.setToken(authToken);
      
      // Get user info
      const userInfo = await apiClient.getMe();
      setUser(userInfo);
    } catch (error) {
      console.error("Failed to load user:", error);
      // Token might be invalid, clear it
      localStorage.removeItem("auth_token");
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (authToken: string, userInfo: User) => {
    setToken(authToken);
    setUser(userInfo);
    localStorage.setItem("auth_token", authToken);
    apiClient.setToken(authToken);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("auth_token");
    apiClient.setToken(null);
    router.push("/login");
  };

  const refreshUser = async () => {
    if (token) {
      await loadUser(token);
    }
  };

  const isSuperAdmin = user?.is_super_admin || false;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        refreshUser,
        isSuperAdmin,
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


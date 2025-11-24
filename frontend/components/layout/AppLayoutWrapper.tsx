"use client";

import { AppLayout } from "./AppLayout";
import { ProtectedRoute } from "./ProtectedRoute";
import { usePathname } from "next/navigation";

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  // Don't protect login page
  if (pathname === "/login") {
    return <>{children}</>;
  }
  
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}


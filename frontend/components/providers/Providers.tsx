"use client";

import { ReactNode } from "react";
import { ToastProvider } from "@/components/ui/Toast";
import { OrganizationProvider } from "@/contexts/OrganizationContext";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
import { AuthProvider } from "@/contexts/AuthContext";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <OrganizationProvider>
          <ToastProvider>{children}</ToastProvider>
        </OrganizationProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}


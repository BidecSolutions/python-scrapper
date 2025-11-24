"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { apiClient } from "@/lib/api";

interface Organization {
  id: number;
  name: string;
  slug: string;
  plan_tier: string;
  logo_url?: string | null;
  brand_name?: string | null;
  tagline?: string | null;
  created_at: string;
}

interface OrganizationContextType {
  organization: Organization | null;
  loading: boolean;
  refreshOrganization: () => Promise<void>;
  updateOrganization: (name: string, brandName?: string | null, tagline?: string | null) => Promise<void>;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);

  const loadOrganization = async () => {
    try {
      setLoading(true);
      const org = await apiClient.getOrganization();
      setOrganization(org);
    } catch (error) {
      console.error("Failed to load organization:", error);
    } finally {
      setLoading(false);
    }
  };

  const refreshOrganization = async () => {
    await loadOrganization();
  };

  const updateOrganization = async (name: string, brandName?: string | null, tagline?: string | null) => {
    try {
      const updated = await apiClient.updateOrganization(name, brandName, tagline);
      setOrganization(updated);
    } catch (error) {
      console.error("Failed to update organization:", error);
      throw error;
    }
  };

  useEffect(() => {
    loadOrganization();
  }, []);

  return (
    <OrganizationContext.Provider
      value={{
        organization,
        loading,
        refreshOrganization,
        updateOrganization,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (context === undefined) {
    throw new Error("useOrganization must be used within an OrganizationProvider");
  }
  return context;
}


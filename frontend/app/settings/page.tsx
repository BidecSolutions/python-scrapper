"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { useOrganization } from "@/contexts/OrganizationContext";
import { Copy, Trash2, Plus, X, Check, Upload, Image as ImageIcon } from "lucide-react";
import { CopyButton } from "@/components/ui/CopyButton";

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

interface ApiKey {
  id: number;
  name: string | null;
  key_prefix: string;
  status: string;
  last_used_at: string | null;
  created_at: string;
}

interface UsageStats {
  plan_tier: string;
  leads_used_this_month: number;
  leads_limit_per_month: number;
  total_leads: number;
  total_jobs: number;
}

export default function SettingsPage() {
  const { showToast } = useToast();
  const { organization: orgFromContext, refreshOrganization, updateOrganization: updateOrgContext } = useOrganization();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [orgName, setOrgName] = useState("");
  const [brandName, setBrandName] = useState("");
  const [tagline, setTagline] = useState("");
  const [savingOrg, setSavingOrg] = useState(false);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loadingKeys, setLoadingKeys] = useState(true);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [loadingUsage, setLoadingUsage] = useState(true);
  const [showCreateKey, setShowCreateKey] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [creatingKey, setCreatingKey] = useState(false);
  const [newKeyValue, setNewKeyValue] = useState<string | null>(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);

  useEffect(() => {
    loadOrganization();
    loadApiKeys();
    loadUsageStats();
  }, []);

  useEffect(() => {
    if (organization?.logo_url) {
      // Use full URL if it's already a URL, otherwise prepend API URL
      const logoUrl = organization.logo_url.startsWith("http") 
        ? organization.logo_url 
        : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002"}${organization.logo_url}`;
      setLogoPreview(logoUrl);
    } else {
      setLogoPreview(null);
    }
  }, [organization?.logo_url]);

  const loadOrganization = async () => {
    try {
      // Use context if available, otherwise fetch
      if (orgFromContext) {
        setOrganization(orgFromContext);
        setOrgName(orgFromContext.name);
        setBrandName(orgFromContext.brand_name || "");
        setTagline(orgFromContext.tagline || "");
      } else {
        const org = await apiClient.getOrganization();
        setOrganization(org);
        setOrgName(org.name);
        setBrandName(org.brand_name || "");
        setTagline(org.tagline || "");
      }
    } catch (error) {
      console.error("Failed to load organization:", error);
      showToast({
        type: "error",
        title: "Failed to load organization",
        message: "Please try again later",
      });
    }
  };

  useEffect(() => {
    if (orgFromContext) {
      setOrganization(orgFromContext);
      setOrgName(orgFromContext.name);
      setBrandName(orgFromContext.brand_name || "");
      setTagline(orgFromContext.tagline || "");
    }
  }, [orgFromContext]);

  const saveOrganization = async () => {
    if (!orgName.trim()) {
      showToast({
        type: "error",
        title: "Invalid name",
        message: "Organization name cannot be empty",
      });
      return;
    }

    setSavingOrg(true);
    try {
      // Update organization with all fields
      const updated = await apiClient.updateOrganization(
        orgName.trim(),
        brandName.trim() || null,
        tagline.trim() || null
      );
      setOrganization(updated);
      setBrandName(updated.brand_name || "");
      setTagline(updated.tagline || "");
      await refreshOrganization();
      showToast({
        type: "success",
        title: "Organization updated",
        message: "Your organization settings have been saved",
      });
    } catch (error: any) {
      console.error("Failed to update organization:", error);
      showToast({
        type: "error",
        title: "Failed to update",
        message: error?.response?.data?.detail || "Please try again later",
      });
    } finally {
      setSavingOrg(false);
    }
  };

  const loadApiKeys = async () => {
    setLoadingKeys(true);
    try {
      const keys = await apiClient.getApiKeys();
      setApiKeys(keys);
    } catch (error) {
      console.error("Failed to load API keys:", error);
      showToast({
        type: "error",
        title: "Failed to load API keys",
        message: "Please try again later",
      });
    } finally {
      setLoadingKeys(false);
    }
  };

  const createApiKey = async () => {
    setCreatingKey(true);
    try {
      const newKey = await apiClient.createApiKey(newKeyName.trim() || undefined);
      setNewKeyValue(newKey.key);
      setNewKeyName("");
      await loadApiKeys();
      showToast({
        type: "success",
        title: "API key created",
        message: "Make sure to copy it now - you won't be able to see it again!",
      });
    } catch (error: any) {
      console.error("Failed to create API key:", error);
      showToast({
        type: "error",
        title: "Failed to create API key",
        message: error?.response?.data?.detail || "Please try again later",
      });
    } finally {
      setCreatingKey(false);
    }
  };

  const revokeApiKey = async (keyId: number) => {
    if (!confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) {
      return;
    }

    try {
      await apiClient.revokeApiKey(keyId);
      await loadApiKeys();
      showToast({
        type: "success",
        title: "API key revoked",
        message: "The API key has been successfully revoked",
      });
    } catch (error: any) {
      console.error("Failed to revoke API key:", error);
      showToast({
        type: "error",
        title: "Failed to revoke",
        message: error?.response?.data?.detail || "Please try again later",
      });
    }
  };

  const loadUsageStats = async () => {
    setLoadingUsage(true);
    try {
      const stats = await apiClient.getUsageStats();
      setUsageStats(stats);
    } catch (error) {
      console.error("Failed to load usage stats:", error);
      showToast({
        type: "error",
        title: "Failed to load usage",
        message: "Please try again later",
      });
    } finally {
      setLoadingUsage(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ["image/png", "image/jpeg", "image/jpg", "image/gif", "image/svg+xml", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      showToast({
        type: "error",
        title: "Invalid file type",
        message: "Please upload a PNG, JPEG, GIF, SVG, or WebP image",
      });
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      showToast({
        type: "error",
        title: "File too large",
        message: "Maximum file size is 5MB",
      });
      return;
    }

    setUploadingLogo(true);
    try {
      const updated = await apiClient.uploadLogo(file);
      setOrganization(updated);
      await refreshOrganization();
      showToast({
        type: "success",
        title: "Logo uploaded",
        message: "Your organization logo has been updated",
      });
    } catch (error: any) {
      console.error("Failed to upload logo:", error);
      showToast({
        type: "error",
        title: "Upload failed",
        message: error?.response?.data?.detail || "Failed to upload logo. Please try again.",
      });
    } finally {
      setUploadingLogo(false);
      // Reset input
      e.target.value = "";
    }
  };

  const handleDeleteLogo = async () => {
    if (!confirm("Are you sure you want to remove the logo? This action cannot be undone.")) {
      return;
    }

    try {
      const updated = await apiClient.deleteLogo();
      setOrganization(updated);
      await refreshOrganization();
      showToast({
        type: "success",
        title: "Logo removed",
        message: "Your organization logo has been removed",
      });
    } catch (error: any) {
      console.error("Failed to delete logo:", error);
      showToast({
        type: "error",
        title: "Delete failed",
        message: error?.response?.data?.detail || "Failed to remove logo. Please try again.",
      });
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-white/90 dark:bg-slate-950/90 backdrop-blur border-b border-slate-200 dark:border-slate-800">
          <div className="px-6 py-4">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-50">Settings</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Manage your organization settings, API keys, and usage.
            </p>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto px-6 pt-6 pb-10 space-y-6 max-w-5xl mx-auto w-full">
          {/* Organization card */}
          <section className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
            <h2 className="text-sm font-semibold text-slate-100">Organization</h2>
            <div className="space-y-4">
              {/* Logo Upload */}
              <div className="space-y-2">
                <label className="text-xs text-slate-400">Organization Logo</label>
                <div className="flex items-center gap-4">
                  {/* Logo Preview */}
                  <div className="relative">
                    {logoPreview ? (
                      <div className="relative group">
                        <img
                          src={logoPreview}
                          alt="Organization logo"
                          className="h-16 w-16 rounded-lg object-cover border border-slate-800"
                        />
                        <button
                          onClick={handleDeleteLogo}
                          className="absolute -top-2 -right-2 p-1 rounded-full bg-rose-500 hover:bg-rose-600 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Remove logo"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ) : (
                      <div className="h-16 w-16 rounded-lg border-2 border-dashed border-slate-700 flex items-center justify-center bg-slate-900">
                        <ImageIcon className="w-6 h-6 text-slate-500" />
                      </div>
                    )}
                  </div>
                  
                  {/* Upload Button */}
                  <div className="flex-1">
                    <input
                      id="logo-upload-input"
                      type="file"
                      accept="image/png,image/jpeg,image/jpg,image/gif,image/svg+xml,image/webp"
                      onChange={handleLogoUpload}
                      disabled={uploadingLogo}
                      className="hidden"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={uploadingLogo}
                      className="w-full sm:w-auto"
                      onClick={() => document.getElementById('logo-upload-input')?.click()}
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      {uploadingLogo ? "Uploading..." : logoPreview ? "Change Logo" : "Upload Logo"}
                    </Button>
                    <p className="text-xs text-slate-500 mt-1">
                      PNG, JPEG, GIF, SVG, or WebP. Max 5MB
                    </p>
                  </div>
                </div>
              </div>

              {/* Organization Name */}
              <div className="space-y-2">
                <label className="text-xs text-slate-400">Organization Name</label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  placeholder="Enter organization name"
                />
              </div>

              {/* Brand Name */}
              <div className="space-y-2">
                <label className="text-xs text-slate-400">Brand Name</label>
                <p className="text-xs text-slate-500 mb-1">Display name shown in sidebar (e.g., "LeadFlux AI")</p>
                <input
                  type="text"
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  placeholder="LeadFlux AI"
                />
              </div>

              {/* Tagline */}
              <div className="space-y-2">
                <label className="text-xs text-slate-400">Tagline</label>
                <p className="text-xs text-slate-500 mb-1">Short description shown below brand name (e.g., "Scrape • Enrich • Score")</p>
                <input
                  type="text"
                  value={tagline}
                  onChange={(e) => setTagline(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  placeholder="Scrape • Enrich • Score"
                />
              </div>

              {/* Save Button */}
              <div className="pt-2">
                <Button
                  onClick={saveOrganization}
                  disabled={savingOrg || !organization || (orgName === organization.name && brandName === (organization.brand_name || "") && tagline === (organization.tagline || ""))}
                  className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
                >
                  {savingOrg ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </div>
          </section>

          {/* API Keys + Plan */}
          <section className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 space-y-6">
            <div>
              <h2 className="text-sm font-semibold mb-1 text-slate-100">API Keys</h2>
              <p className="text-[11px] text-slate-400 mb-3">
                Create keys for programmatic access to scraping and enrichment APIs.
              </p>
              <div className="flex items-center justify-between mb-4">
                <div></div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreateKey(true)}
                className="flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Create Key
              </Button>
            </div>

            {/* Create API Key Modal */}
            <AnimatePresence>
              {showCreateKey && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-4 p-4 rounded-lg border border-slate-800 bg-slate-950 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold">Create New API Key</h3>
                    <button
                      onClick={() => {
                        setShowCreateKey(false);
                        setNewKeyName("");
                        setNewKeyValue(null);
                      }}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  {newKeyValue ? (
                    <div className="space-y-3">
                      <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                        <p className="text-xs text-emerald-300 mb-2">
                          ⚠️ Make sure to copy this key now. You won't be able to see it again!
                        </p>
                        <div className="flex items-center gap-2">
                          <code className="flex-1 px-3 py-2 rounded bg-slate-900 text-emerald-400 text-sm font-mono break-all">
                            {newKeyValue}
                          </code>
                          <CopyButton textToCopy={newKeyValue} />
                        </div>
                      </div>
                      <Button
                        onClick={() => {
                          setShowCreateKey(false);
                          setNewKeyValue(null);
                          setNewKeyName("");
                        }}
                        className="w-full"
                      >
                        Done
                      </Button>
                    </div>
                  ) : (
                    <>
                      <input
                        type="text"
                        value={newKeyName}
                        onChange={(e) => setNewKeyName(e.target.value)}
                        placeholder="Key name (optional)"
                        className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-900 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      />
                      <Button
                        onClick={createApiKey}
                        disabled={creatingKey}
                        className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
                      >
                        {creatingKey ? "Creating..." : "Create API Key"}
                      </Button>
                    </>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* API Keys List */}
            {loadingKeys ? (
              <div className="text-sm text-slate-400 py-4">Loading API keys...</div>
            ) : apiKeys.length === 0 ? (
              <div className="text-sm text-slate-400 py-4">
                No API keys yet. Create one to get started.
              </div>
            ) : (
              <div className="space-y-2">
                {apiKeys.map((key) => (
                  <div
                    key={key.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-200">
                          {key.name || "Unnamed Key"}
                        </span>
                        {key.status === "active" ? (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/30">
                            Revoked
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="text-xs text-slate-400 font-mono">
                          {key.key_prefix}...
                        </code>
                        {key.last_used_at && (
                          <span className="text-xs text-slate-500">
                            • Last used: {new Date(key.last_used_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    {key.status === "active" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => revokeApiKey(key.id)}
                        className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
            </div>

            <div className="border-t border-slate-800 pt-4">
              <h2 className="text-sm font-semibold mb-1 text-slate-100">Plan & Usage</h2>
              {loadingUsage ? (
                <div className="text-sm text-slate-400 py-4">Loading usage stats...</div>
              ) : usageStats ? (
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Current Plan</span>
                    <span className="text-slate-200 font-semibold uppercase">
                      {usageStats.plan_tier}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Leads Used (This Month)</span>
                    <span className="text-slate-200">
                      {formatNumber(usageStats.leads_used_this_month)} / {formatNumber(usageStats.leads_limit_per_month)}
                    </span>
                  </div>
                  <div className="mt-2">
                    <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400"
                        initial={{ width: 0 }}
                        animate={{
                          width: `${Math.min(100, (usageStats.leads_used_this_month / usageStats.leads_limit_per_month) * 100)}%`,
                        }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  </div>
                  <div className="flex justify-between items-center text-xs pt-2 border-t border-slate-800">
                    <span className="text-slate-400">Total Leads</span>
                    <span className="text-slate-200">{formatNumber(usageStats.total_leads)}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Total Jobs</span>
                    <span className="text-slate-200">{formatNumber(usageStats.total_jobs)}</span>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-slate-400 py-4">Failed to load usage stats</div>
              )}
            </div>
          </section>
        </main>
      </div>
  );
}

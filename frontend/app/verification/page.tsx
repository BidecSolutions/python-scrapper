"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { apiClient, type SavedView } from "@/lib/api";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Plus,
  Upload,
  Download,
  RefreshCw,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MetricCard } from "@/components/ui/metrics";
import { SavedViewsBar } from "@/components/saved-views/SavedViewsBar";
import type { SavedView } from "@/lib/api";

interface VerificationJob {
  id: number;
  source_type: string;
  source_description: string;
  status: string;
  total_emails: number;
  processed_count: number;
  valid_count: number;
  invalid_count: number;
  risky_count: number;
  unknown_count: number;
  created_at: string;
  completed_at: string | null;
}

export default function VerificationPage() {
  const { showToast } = useToast();
  const [jobs, setJobs] = useState<VerificationJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewJobModal, setShowNewJobModal] = useState(false);
  const [activeTab, setActiveTab] = useState<"leads" | "csv">("leads");
  const [csvEmails, setCsvEmails] = useState("");
  const [selectedLeadIds, setSelectedLeadIds] = useState<number[]>([]);
  const [creatingJob, setCreatingJob] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  useEffect(() => {
    loadJobs();
  }, []);

  // Poll for running jobs separately
  useEffect(() => {
    const hasRunningJobs = jobs.some(
      (j) => j.status === "running" || j.status === "pending"
    );
    
    if (!hasRunningJobs) {
      return; // No need to poll if no running jobs
    }

    const interval = setInterval(() => {
      loadJobs();
    }, 3000);

    return () => clearInterval(interval);
  }, [jobs]);

  const loadJobs = async () => {
    try {
      // Only set loading on initial load
      if (jobs.length === 0) {
        setLoading(true);
      }
      const data = await apiClient.getVerificationJobs({ limit: 50 });
      setJobs(data);
    } catch (error: any) {
      console.error("Failed to load verification jobs:", error);
      showToast({
        type: "error",
        title: "Failed to load jobs",
        message: error?.response?.data?.detail || "Please try again",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyView = (view: SavedView) => {
    // Apply the saved view's filters
    if (view.filters.status) {
      setStatusFilter(view.filters.status);
    } else {
      setStatusFilter(null);
    }
    // Reload jobs with the view's filters
    // Note: The API might need to support status filtering in getVerificationJobs
    loadJobs();
  };

  const handleCreateJobFromLeads = async () => {
    if (selectedLeadIds.length === 0) {
      showToast({
        type: "error",
        title: "No leads selected",
        message: "Please select leads from the Leads page first",
      });
      return;
    }

    setCreatingJob(true);
    try {
      const result = await apiClient.createBulkVerifyFromLeads(selectedLeadIds);
      showToast({
        type: "success",
        title: "Verification job created",
        message: `Processing ${result.total_emails} emails`,
      });
      setShowNewJobModal(false);
      setSelectedLeadIds([]);
      loadJobs();
    } catch (error: any) {
      console.error("Failed to create job:", error);
      showToast({
        type: "error",
        title: "Failed to create job",
        message: error?.response?.data?.detail || "Please try again",
      });
    } finally {
      setCreatingJob(false);
    }
  };

  const handleCreateJobFromCSV = async () => {
    const emails = csvEmails
      .split("\n")
      .map((e) => e.trim())
      .filter((e) => e && e.includes("@"));

    if (emails.length === 0) {
      showToast({
        type: "error",
        title: "No emails provided",
        message: "Please enter email addresses (one per line)",
      });
      return;
    }

    if (emails.length > 10000) {
      showToast({
        type: "error",
        title: "Too many emails",
        message: "Maximum 10,000 emails per job",
      });
      return;
    }

    setCreatingJob(true);
    try {
      const result = await apiClient.createBulkVerifyFromCSV(emails);
      showToast({
        type: "success",
        title: "Verification job created",
        message: `Processing ${result.total_emails} emails`,
      });
      setShowNewJobModal(false);
      setCsvEmails("");
      loadJobs();
    } catch (error: any) {
      console.error("Failed to create job:", error);
      showToast({
        type: "error",
        title: "Failed to create job",
        message: error?.response?.data?.detail || "Please try again",
      });
    } finally {
      setCreatingJob(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
            <CheckCircle2 className="w-3 h-3" />
            Completed
          </span>
        );
      case "running":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Loader2 className="w-3 h-3 animate-spin" />
            Running
          </span>
        );
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
            Pending
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
            <XCircle className="w-3 h-3" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
            {status}
          </span>
        );
    }
  };

  const getProgressPercent = (job: VerificationJob) => {
    if (job.total_emails === 0) return 0;
    return Math.round((job.processed_count / job.total_emails) * 100);
  };

  // Calculate metrics
  const totalVerified = jobs.reduce((sum, j) => sum + j.valid_count + j.invalid_count + j.risky_count + j.unknown_count, 0);
  const totalValid = jobs.reduce((sum, j) => sum + j.valid_count, 0);
  const totalInvalid = jobs.reduce((sum, j) => sum + j.invalid_count, 0);
  const validPct = totalVerified > 0 ? `${Math.round((totalValid / totalVerified) * 100)}%` : "0%";
  const invalidPct = totalVerified > 0 ? `${Math.round((totalInvalid / totalVerified) * 100)}%` : "0%";

  return (
    <>
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-slate-950/90 backdrop-blur border-b border-slate-800">
          <div className="px-6 py-4 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
                Email Verification
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Bulk verify email addresses from leads or CSV uploads.
              </p>
            </div>
            <button
              onClick={() => setShowNewJobModal(true)}
              className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 text-xs font-medium px-4 py-2 shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              New Verification Job
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto px-6 pt-6 pb-10 space-y-5">
          {/* Saved Views Bar */}
          <SavedViewsBar
            pageType="verification"
            currentFilters={{
              status: statusFilter || undefined,
            }}
            onApplyView={handleApplyView}
          />

          {/* Metrics */}
          <section className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <MetricCard label="Verification jobs" value={jobs.length} />
            <MetricCard label="Total verified" value={totalVerified} tone="info" />
            <MetricCard label="Valid %" value={validPct} tone="success" />
            <MetricCard label="Invalid %" value={invalidPct} tone="danger" />
          </section>

          {/* Jobs Table or Empty State */}
          {loading && jobs.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
              Loading jobs...
            </div>
          ) : jobs.length === 0 ? (
            <section className="rounded-2xl bg-slate-900/80 border border-slate-800 px-6 py-10 text-center">
              <p className="mb-2 text-sm text-slate-100">No verification jobs yet</p>
              <p className="mb-5 text-xs text-slate-400">
                Start by uploading a CSV or selecting leads to verify. We'll track each
                job here with status, progress, and results.
              </p>
              <button
                onClick={() => setShowNewJobModal(true)}
                className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 text-xs font-medium px-4 py-2 shadow-sm transition-colors"
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Create First Verification Job
              </button>
            </section>
          ) : (
            <section className="rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-slate-900">
                    <tr className="text-slate-400">
                      <th className="px-4 py-2 text-left font-medium">Source</th>
                      <th className="px-4 py-2 text-left font-medium">Status</th>
                      <th className="px-4 py-2 text-left font-medium">Progress</th>
                      <th className="px-4 py-2 text-left font-medium">Results</th>
                      <th className="px-4 py-2 text-left font-medium">Created</th>
                      <th className="px-4 py-2 text-right font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <motion.tr
                        key={job.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="border-t border-slate-800 hover:bg-slate-900/70 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <div>
                            <div className="text-slate-100 font-medium text-xs">
                              {job.source_type === "leads" ? "Leads" : "CSV"}
                            </div>
                            <div className="text-[11px] text-slate-500">
                              {job.source_description}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">{getStatusBadge(job.status)}</td>
                        <td className="px-4 py-3">
                          <div className="space-y-1">
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-400">
                                {job.processed_count} / {job.total_emails}
                              </span>
                              <span className="text-slate-300">
                                {getProgressPercent(job)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-1.5">
                              <div
                                className="bg-cyan-500 h-1.5 rounded-full transition-all"
                                style={{ width: `${getProgressPercent(job)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3 text-[11px]">
                            <span className="text-emerald-400">
                              ✓ {job.valid_count}
                            </span>
                            <span className="text-rose-400">✗ {job.invalid_count}</span>
                            <span className="text-amber-400">
                              ⚠ {job.risky_count}
                            </span>
                            <span className="text-slate-400">? {job.unknown_count}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-slate-400 text-[11px]">
                          {new Date(job.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => {
                              showToast({
                                type: "info",
                                title: "Job details",
                                message: "Job detail page coming soon",
                              });
                            }}
                            className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
                          >
                            View
                          </button>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </main>
      </div>

      {/* New Job Modal */}
      <AnimatePresence>
        {showNewJobModal && (
          <div key="modal" className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-slate-900 rounded-xl border border-slate-800 p-6 max-w-md w-full"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">
                  New Verification Job
                </h2>
                <button
                  onClick={() => setShowNewJobModal(false)}
                  className="text-slate-400 hover:text-slate-200"
                >
                  ✕
                </button>
              </div>

              {/* Tabs */}
              <div className="flex gap-2 mb-4 border-b border-slate-800">
                <button
                  onClick={() => setActiveTab("leads")}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === "leads"
                      ? "text-cyan-400 border-b-2 border-cyan-400"
                      : "text-slate-400 hover:text-slate-300"
                  }`}
                >
                  From Leads
                </button>
                <button
                  onClick={() => setActiveTab("csv")}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === "csv"
                      ? "text-cyan-400 border-b-2 border-cyan-400"
                      : "text-slate-400 hover:text-slate-300"
                  }`}
                >
                  From CSV
                </button>
              </div>

              {/* Leads Tab */}
              {activeTab === "leads" && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-400">
                    Select leads from the Leads page, then use the bulk action
                    "Verify emails" to create a verification job.
                  </p>
                  <p className="text-xs text-slate-500">
                    Or enter lead IDs manually (comma-separated):
                  </p>
                  <input
                    type="text"
                    placeholder="1, 2, 3, 4, 5"
                    className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    onChange={(e) => {
                      const ids = e.target.value
                        .split(",")
                        .map((id) => parseInt(id.trim()))
                        .filter((id) => !isNaN(id));
                      setSelectedLeadIds(ids);
                    }}
                  />
                  <Button
                    onClick={handleCreateJobFromLeads}
                    disabled={creatingJob || selectedLeadIds.length === 0}
                    className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
                  >
                    {creatingJob ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Create Job ({selectedLeadIds.length} leads)
                      </>
                    )}
                  </Button>
                </div>
              )}

              {/* CSV Tab */}
              {activeTab === "csv" && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-slate-400 mb-2 block">
                      Email addresses (one per line, max 10,000)
                    </label>
                    <textarea
                      value={csvEmails}
                      onChange={(e) => setCsvEmails(e.target.value)}
                      rows={10}
                      className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono text-sm"
                      placeholder="john@example.com&#10;jane@example.com&#10;..."
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      {csvEmails.split("\n").filter((e) => e.trim()).length} emails
                    </p>
                  </div>
                  <Button
                    onClick={handleCreateJobFromCSV}
                    disabled={creatingJob || csvEmails.trim().length === 0}
                    className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
                  >
                    {creatingJob ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4 mr-2" />
                        Create Job
                      </>
                    )}
                  </Button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}


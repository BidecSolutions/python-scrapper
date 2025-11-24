"use client";

import { useEffect, useState, useMemo } from "react";
import { apiClient } from "@/lib/api";
import type { WorkspaceHealthSummary } from "@/types/health";
import { MetricCard } from "@/components/ui/metrics";
import { motion } from "framer-motion";

export default function AdminHealthPage() {
  const [workspaces, setWorkspaces] = useState<WorkspaceHealthSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const summaryMetrics = useMemo(() => {
    if (workspaces.length === 0) {
      return { avgHealth: 0, totalWorkspaces: 0, healthyCount: 0, warningCount: 0, criticalCount: 0 };
    }
    
    const avgHealth = Math.round(
      workspaces.reduce((sum, ws) => sum + ws.health_score, 0) / workspaces.length
    );
    const healthyCount = workspaces.filter((ws) => ws.health_score >= 80).length;
    const warningCount = workspaces.filter((ws) => ws.health_score >= 60 && ws.health_score < 80).length;
    const criticalCount = workspaces.filter((ws) => ws.health_score < 60).length;
    
    return {
      avgHealth,
      totalWorkspaces: workspaces.length,
      healthyCount,
      warningCount,
      criticalCount,
    };
  }, [workspaces]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getAllWorkspacesHealth();
      setWorkspaces(data);
    } catch (err: any) {
      console.error("Error loading workspace health:", err);
      setError(err.response?.data?.detail || err.message || "Failed to load workspace health");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function getHealthScoreColor(score: number): { bg: string; text: string; border: string } {
    if (score >= 80) {
      return {
        bg: "bg-emerald-50 dark:bg-emerald-950/20",
        text: "text-emerald-600 dark:text-emerald-400",
        border: "border-emerald-200 dark:border-emerald-900/50",
      };
    }
    if (score >= 60) {
      return {
        bg: "bg-amber-50 dark:bg-amber-950/20",
        text: "text-amber-600 dark:text-amber-400",
        border: "border-amber-200 dark:border-amber-900/50",
      };
    }
    return {
      bg: "bg-rose-50 dark:bg-rose-950/20",
      text: "text-rose-600 dark:text-rose-400",
      border: "border-rose-200 dark:border-rose-900/50",
    };
  }

  function getHealthScoreLabel(score: number): string {
    if (score >= 80) return "Healthy";
    if (score >= 60) return "Warning";
    return "Critical";
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-slate-500 dark:text-slate-400 mb-2">Loading workspace health...</div>
          <div className="text-xs text-slate-400 dark:text-slate-500">Please wait</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
              Global Health (Super Admin)
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Monitor system health metrics across all workspaces and organizations.
            </p>
          </div>
          <button
            onClick={load}
            className="inline-flex items-center rounded-lg bg-indigo-500 hover:bg-indigo-400 text-xs font-medium px-4 py-2 shadow-sm text-white transition-colors"
          >
            ↻ Refresh
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 pt-6 pb-10 space-y-6">
        {error && (
          <div className="rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-400 px-4 py-3">
            <strong className="font-semibold">Error:</strong> {error}
          </div>
        )}

        {/* Summary Metrics */}
        <section className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          <MetricCard
            label="Avg Health Score"
            value={summaryMetrics.avgHealth}
            tone={summaryMetrics.avgHealth >= 80 ? "success" : summaryMetrics.avgHealth >= 60 ? "info" : "danger"}
          />
          <MetricCard label="Total Workspaces" value={summaryMetrics.totalWorkspaces} />
          <MetricCard label="Healthy" value={summaryMetrics.healthyCount} tone="success" />
          <MetricCard label="Warning" value={summaryMetrics.warningCount} tone="info" />
          <MetricCard label="Critical" value={summaryMetrics.criticalCount} tone="danger" />
        </section>

        {/* Workspaces Health Table */}
        <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Showing {workspaces.length} workspace{workspaces.length !== 1 ? "s" : ""}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead className="bg-slate-50 dark:bg-slate-900">
                <tr className="text-slate-500 dark:text-slate-400">
                  <th className="px-4 py-3 text-left font-medium">Workspace</th>
                  <th className="px-4 py-3 text-left font-medium">Health Score</th>
                  <th className="px-4 py-3 text-left font-medium">Bounce Rate</th>
                  <th className="px-4 py-3 text-left font-medium">Jobs Failed (7d)</th>
                  <th className="px-4 py-3 text-left font-medium">LinkedIn Failure Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {workspaces.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                      <div className="flex flex-col items-center gap-2">
                        <span className="text-2xl">🏥</span>
                        <span>No workspace health data available.</span>
                      </div>
                    </td>
                  </tr>
                )}
                {workspaces.map((ws) => {
                  const colors = getHealthScoreColor(ws.health_score);
                  return (
                    <motion.tr
                      key={ws.workspace_id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-slate-50 dark:hover:bg-slate-900/70 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900 dark:text-slate-50">
                          {ws.name || `Workspace #${ws.workspace_id}`}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                          ID: {ws.workspace_id}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${colors.bg} ${colors.text} ${colors.border} border`}
                          >
                            {ws.health_score}
                          </span>
                          <span className="text-[11px] text-slate-500 dark:text-slate-400">
                            {getHealthScoreLabel(ws.health_score)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-slate-900 dark:text-slate-50">
                          {(ws.bounce_rate * 100).toFixed(2)}%
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400">
                          {ws.bounce_rate < 0.05 ? "Good" : ws.bounce_rate < 0.1 ? "Fair" : "High"}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-slate-900 dark:text-slate-50">
                          {ws.jobs_failed_recent}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400">
                          {ws.jobs_failed_recent === 0 ? "No failures" : "Failed jobs"}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-slate-900 dark:text-slate-50">
                          {(ws.linkedin_failure_rate * 100).toFixed(1)}%
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400">
                          {ws.linkedin_failure_rate < 0.1 ? "Good" : ws.linkedin_failure_rate < 0.2 ? "Fair" : "High"}
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

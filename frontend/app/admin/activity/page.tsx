"use client";

import { useEffect, useState, useMemo } from "react";
import { apiClient } from "@/lib/api";
import type { AdminActivityItem, ActivityType } from "@/types/adminActivity";
import { MetricCard } from "@/components/ui/metrics";
import { motion } from "framer-motion";

type ActivityTypeFilter = ActivityType | "all";

export default function AdminActivityPage() {
  const [items, setItems] = useState<AdminActivityItem[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [workspaceId, setWorkspaceId] = useState<string>("");
  const [actorUserId, setActorUserId] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<ActivityTypeFilter>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const metrics = useMemo(() => {
    const leadEvents = items.filter((a) => a.type.startsWith("lead_")).length;
    const emailEvents = items.filter((a) => a.type.startsWith("email_")).length;
    const campaignEvents = items.filter((a) => a.type.startsWith("campaign_")).length;
    const jobEvents = items.filter((a) => a.type.startsWith("job_")).length;
    return { total: items.length, leadEvents, emailEvents, campaignEvents, jobEvents };
  }, [items]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getAdminActivity({
        page,
        page_size: pageSize,
        workspace_id: workspaceId ? Number(workspaceId) : undefined,
        actor_user_id: actorUserId ? Number(actorUserId) : undefined,
        type: typeFilter !== "all" ? typeFilter : undefined,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err: any) {
      console.error("Error loading activity:", err);
      setError(err.response?.data?.detail || err.message || "Failed to load activity");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, typeFilter]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    load();
  };

  const typeOptions: ActivityTypeFilter[] = [
    "all",
    "lead_created",
    "lead_updated",
    "email_found",
    "email_verified",
    "lead_added_to_list",
    "lead_removed_from_list",
    "campaign_sent",
    "campaign_event",
    "task_created",
    "task_completed",
    "note_added",
    "playbook_run",
    "playbook_completed",
    "list_created",
    "list_marked_campaign_ready",
    "job_created",
    "job_completed",
    "job_failed",
  ];

  function getActivityTypeColor(type: ActivityType): string {
    if (type.startsWith("lead_")) return "bg-blue-500/15 text-blue-300 border border-blue-400/60";
    if (type.startsWith("email_")) return "bg-cyan-500/15 text-cyan-300 border border-cyan-400/60";
    if (type.startsWith("campaign_")) return "bg-purple-500/15 text-purple-300 border border-purple-400/60";
    if (type.startsWith("job_")) return "bg-amber-500/15 text-amber-300 border border-amber-400/60";
    if (type.startsWith("task_")) return "bg-indigo-500/15 text-indigo-300 border border-indigo-400/60";
    if (type.startsWith("playbook_")) return "bg-emerald-500/15 text-emerald-300 border border-emerald-400/60";
    return "bg-slate-500/15 text-slate-300 border border-slate-400/60";
  }

  function formatActivityType(type: ActivityType): string {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  }

  function renderMeta(meta: any) {
    if (!meta || typeof meta !== "object") return "—";
    try {
      const keys = Object.keys(meta);
      if (keys.length === 0) return "—";
      const snippets = keys.slice(0, 2).map((k) => `${k}: ${String(meta[k])}`);
      return snippets.join(" · ");
    } catch {
      return "—";
    }
  }

  function formatRelativeTime(date: string): string {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now.getTime() - then.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return then.toLocaleDateString();
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
              Global Activity (Super Admin)
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Monitor all activity events across workspaces, users, and system actions.
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 pt-6 pb-10 space-y-6">
        {error && (
          <div className="rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-400 px-4 py-3">
            <strong className="font-semibold">Error:</strong> {error}
          </div>
        )}

        {/* Metrics */}
        <section className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          <MetricCard label="Total Events" value={metrics.total} />
          <MetricCard label="Lead Events" value={metrics.leadEvents} tone="info" />
          <MetricCard label="Email Events" value={metrics.emailEvents} tone="info" />
          <MetricCard label="Campaign Events" value={metrics.campaignEvents} tone="default" />
          <MetricCard label="Job Events" value={metrics.jobEvents} tone="info" />
        </section>

        {/* Filters */}
        <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap gap-3 items-stretch sm:items-center">
            <input
              type="number"
              min={1}
              placeholder="Workspace ID"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs w-40 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <input
              type="number"
              min={1}
              placeholder="User ID"
              value={actorUserId}
              onChange={(e) => setActorUserId(e.target.value)}
              className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs w-40 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value as ActivityTypeFilter);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 flex-1"
            >
              {typeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt === "all" ? "All types" : formatActivityType(opt as ActivityType)}
                </option>
              ))}
            </select>
            <button
              type="submit"
              className="inline-flex items-center rounded-xl bg-indigo-500 hover:bg-indigo-400 text-xs font-medium px-4 py-2 shadow-sm text-white transition-colors"
            >
              Apply filters
            </button>
          </form>
        </section>

        {/* Activity Table */}
        <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead className="bg-slate-50 dark:bg-slate-900">
                <tr className="text-slate-500 dark:text-slate-400">
                  <th className="px-4 py-3 text-left font-medium">Time</th>
                  <th className="px-4 py-3 text-left font-medium">Workspace</th>
                  <th className="px-4 py-3 text-left font-medium">User</th>
                  <th className="px-4 py-3 text-left font-medium">Type</th>
                  <th className="px-4 py-3 text-left font-medium">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {loading && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                      Loading activity…
                    </td>
                  </tr>
                )}
                {!loading && items.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                      <div className="flex flex-col items-center gap-2">
                        <span className="text-2xl">📊</span>
                        <span>No activity found for this filter.</span>
                      </div>
                    </td>
                  </tr>
                )}
                {!loading &&
                  items.map((act) => (
                    <motion.tr
                      key={act.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-slate-50 dark:hover:bg-slate-900/70 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="text-slate-900 dark:text-slate-50 font-medium">
                          {formatRelativeTime(act.created_at)}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                          {new Date(act.created_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {act.workspace_id ? (
                          <span className="text-slate-900 dark:text-slate-50">#{act.workspace_id}</span>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {act.actor_user_id ? (
                          <span className="text-slate-900 dark:text-slate-50">User #{act.actor_user_id}</span>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-500">System</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${getActivityTypeColor(act.type)}`}>
                          {formatActivityType(act.type)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                        {renderMeta(act.meta)}
                      </td>
                    </motion.tr>
                  ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-between items-center text-xs text-slate-600 dark:text-slate-400">
            <span>
              Page {page} of {totalPages} • {total} events
            </span>
            <div className="space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 disabled:opacity-50 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
              >
                Prev
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 disabled:opacity-50 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

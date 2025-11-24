"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { Template, TemplateStatus } from "@/types/templates";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Plus, Lock, FileText, CheckCircle2, XCircle, Clock, Loader2 } from "lucide-react";
import { MetricCard } from "@/components/ui/metrics";

type TabKey = "all" | "draft" | "pending" | "approved";

const STATUS_LABELS: Record<TemplateStatus, string> = {
  draft: "Draft",
  pending_approval: "Pending",
  approved: "Approved",
  deprecated: "Deprecated",
  rejected: "Rejected",
};

function StatusBadge({ status }: { status: TemplateStatus }) {
  const map: Record<TemplateStatus, string> = {
    draft: "bg-slate-500/15 text-slate-300 border border-slate-400/60",
    pending_approval: "bg-amber-500/15 text-amber-300 border border-amber-400/60",
    approved: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/60",
    deprecated: "bg-slate-600/50 text-slate-400 border border-slate-600",
    rejected: "bg-rose-500/15 text-rose-300 border border-rose-400/60",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${map[status] || map.draft}`}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}

function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-900 to-slate-950 border border-slate-800 px-6 py-10 flex flex-col items-center text-center"
    >
      <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/15 border border-indigo-500/40 mb-4">
        <FileText className="w-6 h-6 text-indigo-400" />
      </div>

      <h2 className="text-lg font-semibold mb-1 text-slate-100">No templates yet</h2>
      <p className="text-xs text-slate-400 max-w-md mb-6">
        Create your first template to keep messaging consistent across your
        team. Save proven cold emails, follow-ups, and nurture sequences in one
        shared library.
      </p>

      {/* 3 small benefit cards */}
      <div className="grid gap-4 sm:grid-cols-3 text-left w-full max-w-3xl mb-8">
        <div className="rounded-xl bg-slate-900/70 border border-slate-800 p-3">
          <p className="text-[11px] font-semibold text-slate-200 mb-1">
            1. Save best-performing copy
          </p>
          <p className="text-[11px] text-slate-400">
            Turn winning emails into reusable templates instead of rewriting
            from scratch.
          </p>
        </div>
        <div className="rounded-xl bg-slate-900/70 border border-slate-800 p-3">
          <p className="text-[11px] font-semibold text-slate-200 mb-1">
            2. Control approvals
          </p>
          <p className="text-[11px] text-slate-400">
            Mark templates as draft, pending, or approved to keep content
            on-brand.
          </p>
        </div>
        <div className="rounded-xl bg-slate-900/70 border border-slate-800 p-3">
          <p className="text-[11px] font-semibold text-slate-200 mb-1">
            3. Power AI suggestions
          </p>
          <p className="text-[11px] text-slate-400">
            Let AI learn from your library to suggest the right template for
            each segment.
          </p>
        </div>
      </div>

      <button
        onClick={onCreateClick}
        className="inline-flex items-center rounded-lg bg-indigo-500 hover:bg-indigo-400 text-xs font-medium px-5 py-2.5 shadow-sm transition-colors"
      >
        <Plus className="w-4 h-4 mr-1.5" />
        Create First Template
      </button>
    </motion.section>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function TemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("all");

  const metrics = {
    total: templates.length,
    draft: templates.filter((t) => t.status === "draft").length,
    pending: templates.filter((t) => t.status === "pending_approval").length,
    approved: templates.filter((t) => t.status === "approved").length,
  };

  async function load() {
    setLoading(true);
    try {
      const params: any = {};
      if (activeTab !== "all") {
        if (activeTab === "pending") {
          params.status = "pending_approval";
        } else {
          params.status = activeTab;
        }
      }
      const res = await apiClient.getTemplates(params);
      setTemplates(res.items);
    } catch (err) {
      console.error("Error loading templates:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [activeTab]);

  const handleTabChange = (tab: TabKey) => {
    setActiveTab(tab);
  };

  async function handleApprove(templateId: number, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await apiClient.approveTemplate(templateId);
      load();
    } catch (err) {
      console.error("Error approving template:", err);
      alert("Failed to approve template");
    }
  }

  async function handleReject(templateId: number, e: React.MouseEvent) {
    e.stopPropagation();
    const reason = prompt("Rejection reason (optional):");
    try {
      await apiClient.rejectTemplate(templateId, reason || undefined);
      load();
    } catch (err) {
      console.error("Error rejecting template:", err);
      alert("Failed to reject template");
    }
  }

  const hasTemplates = templates.length > 0;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
              Template Library
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Manage email templates, approvals, and content governance
            </p>
          </div>

          <button
            onClick={() => router.push("/templates/new")}
            className="inline-flex items-center rounded-lg bg-indigo-500 hover:bg-indigo-400 text-xs font-medium px-4 py-2 shadow-sm text-white transition-colors"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Template
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 pt-6 pb-10 space-y-6">
        {/* Metrics */}
        <section className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <MetricCard label="Total Templates" value={metrics.total} />
          <MetricCard label="Draft" value={metrics.draft} tone="default" />
          <MetricCard label="Pending" value={metrics.pending} tone="info" />
          <MetricCard label="Approved" value={metrics.approved} tone="success" />
        </section>

        {/* Tabs */}
        <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-4">
          <nav className="flex items-center gap-6 border-b border-slate-200 dark:border-slate-800 pb-2">
            {[
              { key: "all" as TabKey, label: "All", icon: FileText },
              { key: "draft" as TabKey, label: "Draft", icon: FileText },
              { key: "pending" as TabKey, label: "Pending", icon: Clock },
              { key: "approved" as TabKey, label: "Approved", icon: CheckCircle2 },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => handleTabChange(tab.key)}
                  className={`inline-flex items-center gap-2 py-2 text-xs font-medium border-b-2 -mb-px transition-colors ${
                    activeTab === tab.key
                      ? "border-indigo-400 text-slate-900 dark:text-slate-50"
                      : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </section>

        {loading ? (
          <div className="flex items-center justify-center py-12 text-slate-500 dark:text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            Loading templates...
          </div>
        ) : hasTemplates ? (
          // Templates table
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 overflow-hidden"
          >
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead className="bg-slate-50 dark:bg-slate-900">
                  <tr className="text-slate-500 dark:text-slate-400">
                    <th className="px-4 py-3 text-left font-medium">Name</th>
                    <th className="px-4 py-3 text-left font-medium">Kind</th>
                    <th className="px-4 py-3 text-left font-medium">Status</th>
                    <th className="px-4 py-3 text-left font-medium">Tags</th>
                    <th className="px-4 py-3 text-left font-medium">Updated</th>
                    <th className="px-4 py-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {templates.map((template) => (
                    <motion.tr
                      key={template.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-slate-50 dark:hover:bg-slate-900/70 transition-colors cursor-pointer"
                      onClick={() => router.push(`/templates/${template.id}`)}
                    >
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900 dark:text-slate-50 flex items-center gap-2">
                          {template.name}
                          {template.locked && (
                            <Lock className="w-3 h-3 text-slate-500 dark:text-slate-400" />
                          )}
                        </div>
                        {template.description && (
                          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                            {template.description}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-slate-700 dark:text-slate-300 capitalize">{template.kind}</span>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={template.status as TemplateStatus} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {template.tags && template.tags.length > 0 ? (
                            template.tags.map((tag, tagIdx) => (
                              <span
                                key={tagIdx}
                                className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded text-[10px]"
                              >
                                {tag}
                              </span>
                            ))
                          ) : (
                            <span className="text-slate-400 dark:text-slate-500 text-[10px]">—</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                        {formatDate(template.updated_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => router.push(`/templates/${template.id}`)}
                            className="text-[11px] text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
                          >
                            View
                          </button>
                          {template.status === "pending_approval" && (
                            <>
                              <button
                                onClick={(e) => handleApprove(template.id, e)}
                                className="text-[11px] text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 font-medium"
                              >
                                Approve
                              </button>
                              <button
                                onClick={(e) => handleReject(template.id, e)}
                                className="text-[11px] text-rose-600 dark:text-rose-400 hover:text-rose-700 dark:hover:text-rose-300 font-medium"
                              >
                                Reject
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.section>
        ) : (
          <EmptyState onCreateClick={() => router.push("/templates/new")} />
        )}
      </main>
    </div>
  );
}

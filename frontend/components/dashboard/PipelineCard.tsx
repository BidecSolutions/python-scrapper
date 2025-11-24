"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";

export function PipelineCard() {
  const router = useRouter();
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await apiClient.getPipelineSummary();
      setSummary(data);
    } catch (err) {
      console.error("Error loading pipeline summary:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading || !summary) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-6">
        <div className="flex items-center justify-center py-8">
          <div className="text-sm text-slate-500 dark:text-slate-400">Loading pipeline...</div>
        </div>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-6 shadow-sm"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50">Pipeline</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Deal progress and performance</p>
        </div>
        <button
          onClick={() => router.push("/deals")}
          className="text-xs font-medium text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 transition-colors"
        >
          View all →
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="rounded-lg bg-slate-50 dark:bg-slate-950/50 p-4 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wide font-medium">In Progress Value</div>
          <div className="text-2xl font-bold text-slate-900 dark:text-slate-50 mb-1">
            {formatCurrency(summary.in_progress_value)}
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-400">
            {summary.in_progress_count} {summary.in_progress_count === 1 ? 'deal' : 'deals'}
          </div>
        </div>
        <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/20 p-4 border border-emerald-200 dark:border-emerald-900/50">
          <div className="text-xs text-emerald-700 dark:text-emerald-400 mb-1.5 uppercase tracking-wide font-medium">Won (Last 30d)</div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mb-1">
            {formatCurrency(summary.won_recent_value)}
          </div>
          <div className="text-xs text-emerald-600 dark:text-emerald-400">
            {summary.won_recent_count} {summary.won_recent_count === 1 ? 'deal' : 'deals'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 pt-5 border-t border-slate-200 dark:border-slate-800">
        <div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wide font-medium">Win Rate (90d)</div>
          <div className="text-xl font-bold text-slate-900 dark:text-slate-50">{summary.win_rate}%</div>
        </div>
        <div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wide font-medium">Avg Days to Close</div>
          <div className="text-xl font-bold text-slate-900 dark:text-slate-50">
            {summary.avg_days_to_close ? `${Math.round(summary.avg_days_to_close)}d` : "—"}
          </div>
        </div>
      </div>
    </motion.div>
  );
}


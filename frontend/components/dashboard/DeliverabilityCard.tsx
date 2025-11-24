"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  HelpCircle,
  Mail,
  TrendingUp,
  Loader2,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import Link from "next/link";

export function DeliverabilityCard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getDeliverabilityStats();
      setStats(data);
    } catch (error) {
      console.error("Failed to load deliverability stats:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const { breakdown, verification_rate, total_verified, email_records } = stats;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-6 shadow-sm"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50 flex items-center gap-2">
            <Mail className="w-5 h-5 text-cyan-500 dark:text-cyan-400" />
            Email Deliverability
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Verification status across all emails
          </p>
        </div>
        <Link
          href="/verification"
          className="text-xs font-medium text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 transition-colors"
        >
          View all →
        </Link>
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="rounded-lg bg-slate-50 dark:bg-slate-950/50 p-4 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wide font-medium">Total Verified</div>
          <div className="text-2xl font-bold text-slate-900 dark:text-slate-50">{total_verified}</div>
        </div>
        <div className="rounded-lg bg-cyan-50 dark:bg-cyan-950/20 p-4 border border-cyan-200 dark:border-cyan-900/50">
          <div className="text-xs text-cyan-700 dark:text-cyan-400 mb-1.5 uppercase tracking-wide font-medium">Verification Rate</div>
          <div className="text-2xl font-bold text-cyan-600 dark:text-cyan-400">
            {verification_rate.toFixed(1)}%
          </div>
        </div>
        <div className="rounded-lg bg-slate-50 dark:bg-slate-950/50 p-4 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wide font-medium">Email Records</div>
          <div className="text-2xl font-bold text-slate-900 dark:text-slate-50">
            {email_records.total}
          </div>
        </div>
      </div>

      {/* Breakdown */}
      <div className="space-y-3">
        <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
          Status Breakdown
        </div>

        {/* Valid */}
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Valid</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-32 bg-slate-200 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
              <motion.div
                className="bg-emerald-500 dark:bg-emerald-400 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${breakdown.valid.percent}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 w-20 text-right">
              {breakdown.valid.count} ({breakdown.valid.percent}%)
            </span>
          </div>
        </div>

        {/* Risky */}
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-500 dark:text-amber-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Risky</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-32 bg-slate-200 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
              <motion.div
                className="bg-amber-500 dark:bg-amber-400 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${breakdown.risky.percent}%` }}
                transition={{ duration: 0.5, delay: 0.1 }}
              />
            </div>
            <span className="text-sm font-semibold text-amber-600 dark:text-amber-400 w-20 text-right">
              {breakdown.risky.count} ({breakdown.risky.percent}%)
            </span>
          </div>
        </div>

        {/* Unknown */}
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2.5">
            <HelpCircle className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Unknown</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-32 bg-slate-200 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
              <motion.div
                className="bg-slate-400 dark:bg-slate-500 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${breakdown.unknown.percent}%` }}
                transition={{ duration: 0.5, delay: 0.2 }}
              />
            </div>
            <span className="text-sm font-semibold text-slate-600 dark:text-slate-400 w-20 text-right">
              {breakdown.unknown.count} ({breakdown.unknown.percent}%)
            </span>
          </div>
        </div>

        {/* Invalid */}
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2.5">
            <XCircle className="w-4 h-4 text-rose-500 dark:text-rose-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Invalid</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-32 bg-slate-200 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
              <motion.div
                className="bg-rose-500 dark:bg-rose-400 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${breakdown.invalid.percent}%` }}
                transition={{ duration: 0.5, delay: 0.3 }}
              />
            </div>
            <span className="text-sm font-semibold text-rose-600 dark:text-rose-400 w-20 text-right">
              {breakdown.invalid.count} ({breakdown.invalid.percent}%)
            </span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 pt-5 border-t border-slate-200 dark:border-slate-800">
        <Link
          href="/verification"
          className="inline-flex items-center gap-2 text-xs font-medium text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 transition-colors"
        >
          <TrendingUp className="w-3.5 h-3.5" />
          Create verification job
        </Link>
      </div>
    </motion.div>
  );
}


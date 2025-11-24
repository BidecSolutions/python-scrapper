"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { apiClient } from "@/lib/api";
import { BarChart3 } from "lucide-react";

interface LinkedInActivity {
  leads_this_week: number;
  total_leads: number;
  verification_stats: {
    valid: number;
    risky: number;
    invalid: number;
    unknown: number;
    total: number;
  };
  verification_rate: number;
}

export function LinkedInActivityCard() {
  const [activity, setActivity] = useState<LinkedInActivity | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActivity();
  }, []);

  const loadActivity = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getLinkedInActivity();
      setActivity(data);
    } catch (error) {
      console.error("Failed to load LinkedIn activity:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 px-5 py-5 h-56 animate-pulse" />
    );
  }

  if (!activity) {
    return null;
  }

  const stats = activity.verification_stats;
  const maxCount = Math.max(stats.valid, stats.risky, stats.invalid, stats.unknown, 1);

  return (
    <motion.div
      className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 px-5 py-5 shadow-sm"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center gap-2.5 mb-5">
        <BarChart3 className="w-5 h-5 text-blue-500 dark:text-blue-400" />
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-50">LinkedIn Capture Overview</h3>
      </div>

      <div className="space-y-5">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-slate-50 dark:bg-slate-950/50 p-3 border border-slate-200 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wide font-medium">Leads this week</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-50">{activity.leads_this_week}</p>
          </div>
          <div className="rounded-lg bg-slate-50 dark:bg-slate-950/50 p-3 border border-slate-200 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wide font-medium">Total LinkedIn leads</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-50">{activity.total_leads}</p>
          </div>
        </div>

        {/* Verification Rate */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide font-medium">Verification rate</p>
            <p className="text-xs font-bold text-cyan-600 dark:text-cyan-400">
              {activity.verification_rate.toFixed(1)}%
            </p>
          </div>
          <div className="h-2.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400"
              initial={{ width: 0 }}
              animate={{ width: `${activity.verification_rate}%` }}
              transition={{ duration: 0.5, delay: 0.2 }}
            />
          </div>
        </div>

        {/* Breakdown Chart */}
        {stats.total > 0 && (
          <div className="space-y-2.5">
            <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide font-medium">Email status breakdown</p>
            <div className="space-y-1.5">
              {stats.valid > 0 && (
                <div className="flex items-center gap-2">
                  <div className="w-12 text-xs text-slate-400">Valid</div>
                  <div className="flex-1 h-3 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-emerald-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${(stats.valid / maxCount) * 100}%` }}
                      transition={{ duration: 0.5, delay: 0.3 }}
                    />
                  </div>
                  <div className="w-8 text-xs text-slate-300 text-right">{stats.valid}</div>
                </div>
              )}
              {stats.risky > 0 && (
                <div className="flex items-center gap-2">
                  <div className="w-12 text-xs text-slate-400">Risky</div>
                  <div className="flex-1 h-3 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-amber-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${(stats.risky / maxCount) * 100}%` }}
                      transition={{ duration: 0.5, delay: 0.4 }}
                    />
                  </div>
                  <div className="w-8 text-xs text-slate-300 text-right">{stats.risky}</div>
                </div>
              )}
              {stats.invalid > 0 && (
                <div className="flex items-center gap-2">
                  <div className="w-12 text-xs text-slate-400">Invalid</div>
                  <div className="flex-1 h-3 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-rose-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${(stats.invalid / maxCount) * 100}%` }}
                      transition={{ duration: 0.5, delay: 0.5 }}
                    />
                  </div>
                  <div className="w-8 text-xs text-slate-300 text-right">{stats.invalid}</div>
                </div>
              )}
              {stats.unknown > 0 && (
                <div className="flex items-center gap-2">
                  <div className="w-12 text-xs text-slate-400">Unknown</div>
                  <div className="flex-1 h-3 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-slate-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${(stats.unknown / maxCount) * 100}%` }}
                      transition={{ duration: 0.5, delay: 0.6 }}
                    />
                  </div>
                  <div className="w-8 text-xs text-slate-300 text-right">{stats.unknown}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer note */}
        <p className="text-[10px] text-slate-500 dark:text-slate-400 pt-3 border-t border-slate-200 dark:border-slate-800 leading-relaxed">
          These numbers include leads captured by the Chrome extension. All emails are processed
          by the same Email Finder + Verifier engine.
        </p>
      </div>
    </motion.div>
  );
}


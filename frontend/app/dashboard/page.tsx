"use client";

import { useState, useEffect } from "react";
import { DeliverabilityCard } from "@/components/dashboard/DeliverabilityCard";
import { LinkedInActivityCard } from "@/components/dashboard/LinkedInActivityCard";
import { OnboardingChecklist } from "@/components/dashboard/OnboardingChecklist";
import { PipelineCard } from "@/components/dashboard/PipelineCard";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { formatRelativeTime } from "@/lib/time";
import { StatusChip } from "@/components/jobs/StatusChip";
import { MetricCard } from "@/components/ui/metrics";

interface DashboardStats {
  total_leads: number;
  leads_this_month: number;
  month_change: number;
  avg_lead_score: number;
  ai_enriched_pct: number;
  recent_jobs: Array<{
    id: number;
    niche: string;
    location: string | null;
    status: string;
    result_count: number;
    created_at: string;
  }>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [healthStats, setHealthStats] = useState<any>(null);

  useEffect(() => {
    loadStats();
    loadHealthStats();
  }, []);

  const loadHealthStats = async () => {
    try {
      const data = await apiClient.getHealthScoreStats();
      setHealthStats(data);
    } catch (error) {
      console.error("Failed to load health stats:", error);
    }
  };

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getDashboardStats();
      setStats(data);
    } catch (error) {
      console.error("Failed to load dashboard stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatChange = (change: number) => {
    if (change === 0) return null;
    const sign = change > 0 ? "+" : "";
    return `${sign}${change.toFixed(0)}%`;
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="px-6 py-4 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
                Dashboard
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Overview of your lead generation, enrichment, and verification
              </p>
            </div>
            <Link href="/jobs/new">
              <button className="inline-flex items-center rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-xs font-semibold px-4 py-2.5 shadow-lg shadow-cyan-500/20 dark:shadow-cyan-500/30 transition-all hover:shadow-xl hover:shadow-cyan-500/30 text-white">
                <Plus className="w-4 h-4 mr-1.5" />
                New Scrape Job
              </button>
            </Link>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto px-6 pt-6 pb-10 space-y-6 bg-slate-50 dark:bg-slate-950">
          {/* KPIs */}
          {loading ? (
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[0, 1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 px-5 py-4 h-24 animate-pulse"
                />
              ))}
            </section>
          ) : stats ? (
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <MetricCard label="Total leads" value={formatNumber(stats.total_leads)} />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <MetricCard label="This month" value={formatNumber(stats.leads_this_month)} tone="info" />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <MetricCard label="Avg lead score" value={stats.avg_lead_score.toString()} />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <MetricCard label="AI enriched" value={`${stats.ai_enriched_pct}%`} tone="info" />
              </motion.div>
            </section>
          ) : (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 px-6 py-8 text-center text-slate-500 dark:text-slate-400">
              Failed to load dashboard stats
            </div>
          )}

          {/* Health Score Summary */}
          {healthStats && (
            <section className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-50">Data Health Overview</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Average health score across all leads
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-slate-900 dark:text-slate-50">
                    {healthStats.average_score.toFixed(1)}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">out of 100</div>
                </div>
              </div>
              <div className="grid grid-cols-5 gap-2">
                {Object.entries(healthStats.grade_distribution).map(([grade, count]) => {
                  const gradeColors: Record<string, string> = {
                    A: "bg-emerald-500 dark:bg-emerald-400",
                    B: "bg-blue-500 dark:bg-blue-400",
                    C: "bg-amber-500 dark:bg-amber-400",
                    D: "bg-orange-500 dark:bg-orange-400",
                    F: "bg-rose-500 dark:bg-rose-400",
                  };
                  return (
                    <div key={grade} className="text-center">
                      <div className={`h-2 rounded-full ${gradeColors[grade] || "bg-slate-400"}`} 
                        style={{ width: `${((count as number) / healthStats.total_leads) * 100}%` }}
                      />
                      <div className="mt-1 text-xs font-semibold text-slate-900 dark:text-slate-50">{grade}</div>
                      <div className="text-[10px] text-slate-500 dark:text-slate-400">{count as number}</div>
                    </div>
                  );
                })}
              </div>
              {healthStats.top_recommendations && healthStats.top_recommendations.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800">
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">Top Recommendations:</p>
                  <ul className="space-y-1">
                    {healthStats.top_recommendations.slice(0, 3).map((rec: any, idx: number) => (
                      <li key={idx} className="text-xs text-slate-600 dark:text-slate-400">
                        • {rec.action} ({rec.count} leads)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          )}

          {/* Pipeline + Deliverability */}
          <section className="grid gap-5 md:grid-cols-[2fr,1.4fr]">
            <PipelineCard />
            <DeliverabilityCard />
          </section>

          {/* LinkedIn capture & Getting started */}
          <section className="grid gap-5 md:grid-cols-2">
            <LinkedInActivityCard />
            <OnboardingChecklist />
          </section>

          {/* Recent Jobs */}
          <section className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 overflow-hidden shadow-sm">
          <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-50">Recent Jobs</h2>
              <Link href="/jobs" className="text-xs text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 font-medium">
                View all →
              </Link>
            </div>
          </div>
          {loading ? (
            <div className="p-4">
              <div className="space-y-2">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-12 rounded bg-slate-800/60 animate-pulse"
                  />
                ))}
              </div>
            </div>
          ) : stats && stats.recent_jobs.length > 0 ? (
            <div className="divide-y divide-slate-200 dark:divide-slate-800">
              {stats.recent_jobs.map((job, index) => (
                <motion.div
                  key={job.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Link
                    href={`/jobs/${job.id}`}
                    className="block px-5 py-4 hover:bg-slate-50 dark:hover:bg-slate-900/70 transition-colors group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className="font-semibold text-slate-900 dark:text-slate-50 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors truncate">
                            {job.niche}
                          </span>
                          {job.location && (
                            <span className="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0">
                              • {job.location}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                          <span>{formatRelativeTime(job.created_at)}</span>
                          <span>•</span>
                          <span className="font-medium">{job.result_count} leads</span>
                        </div>
                      </div>
                      <div className="ml-4 flex-shrink-0">
                        <StatusChip status={job.status as any} />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 mb-3">
                <Plus className="w-6 h-6 text-slate-400 dark:text-slate-500" />
              </div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                No recent jobs
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Create your first scraping job to get started
              </p>
              <Link href="/jobs/new">
                <button className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 text-xs font-semibold px-4 py-2 text-white transition-colors">
                  <Plus className="w-3.5 h-3.5 mr-1.5" />
                  Create Job
                </button>
              </Link>
            </div>
          )}
          </section>
        </main>
      </div>
  );
}

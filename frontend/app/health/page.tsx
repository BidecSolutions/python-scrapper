"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { HealthResponse } from "@/types/health";
import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

type Status = "ok" | "warning" | "bad";

function StatusPill({ status }: { status: Status }) {
  const map: Record<Status, string> = {
    ok: "bg-emerald-100/80 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300",
    warning: "bg-amber-100/80 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300",
    bad: "bg-rose-100/80 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300",
  };
  const label: Record<Status, string> = {
    ok: "Healthy",
    warning: "Watch",
    bad: "Attention",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${map[status]}`}>
      {label[status]}
    </span>
  );
}

export default function HealthPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  async function load() {
    setLoading(true);
    try {
      const data = await apiClient.getHealth(days);
      setHealth(data);
    } catch (err) {
      console.error("Error loading health data:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [days]);

  function getHealthScoreColor(score: number): string {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-amber-400";
    return "text-rose-400";
  }

  function getHealthScoreStrokeColor(score: number): string {
    if (score >= 80) return "stroke-emerald-400";
    if (score >= 60) return "stroke-amber-400";
    return "stroke-rose-400";
  }

  const periodLabel = days === 7 ? "Last 7 days" : days === 30 ? "Last 30 days" : "Last 90 days";

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-slate-950/90 backdrop-blur border-b border-slate-800">
          <div className="px-6 py-4 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
                Health & Quality Dashboard
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                System health metrics and quality indicators across your workspace.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative">
                <select
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className="appearance-none bg-slate-900 border border-slate-700 text-xs text-slate-200 px-4 py-2 pr-8 rounded-lg hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent cursor-pointer"
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto px-6 pt-6 pb-10 space-y-6">
          {loading || !health ? (
            <div className="text-center py-12 text-slate-400">
              Loading health data...
            </div>
          ) : (
            <>
              {/* Overall score card */}
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-1 md:grid-cols-[2fr,1fr] gap-6 bg-slate-900/80 border border-slate-800 rounded-2xl p-5"
              >
                <div className="flex flex-col justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      Overall Health Score
                    </p>
                    <div className="mt-1 flex items-baseline gap-2">
                      <span className={`text-5xl font-semibold ${getHealthScoreColor(health.health_score)}`}>
                        {health.health_score}
                      </span>
                      <span className="text-sm text-slate-400">out of 100</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="rounded-xl bg-slate-900 border border-slate-800 p-3">
                      <p className="text-[11px] text-slate-400">Deliverability</p>
                      <p className="text-sm font-semibold mt-1 text-slate-200">
                        {(health.cards.deliverability.details.bounce_rate * 100).toFixed(2)}% bounce
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Spam complaints {(health.cards.deliverability.details.spam_complaint_rate * 100).toFixed(3)}%
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-900 border border-slate-800 p-3">
                      <p className="text-[11px] text-slate-400">Verification</p>
                      <p className="text-sm font-semibold mt-1 text-slate-200">
                        {(health.cards.verification.details.valid_pct * 100).toFixed(1)}% valid
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Invalid {(health.cards.verification.details.invalid_pct * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-900 border border-slate-800 p-3">
                      <p className="text-[11px] text-slate-400">Campaigns</p>
                      <p className="text-sm font-semibold mt-1 text-slate-200">
                        {(health.cards.campaigns.details.avg_open_rate * 100).toFixed(1)}% open
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        {(health.cards.campaigns.details.avg_reply_rate * 100).toFixed(1)}% reply
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-900 border border-slate-800 p-3">
                      <p className="text-[11px] text-slate-400">Jobs & Playbooks</p>
                      <p className="text-sm font-semibold mt-1 text-slate-200">
                        {health.cards.jobs.details.jobs_failed || 0} failures
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        of {health.cards.jobs.details.jobs_started || 0} jobs started
                      </p>
                    </div>
                  </div>
                </div>

                {/* Circular gauge */}
                <div className="flex items-center justify-center">
                  <div className="relative h-40 w-40">
                    <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
                      <circle
                        cx="50"
                        cy="50"
                        r="42"
                        className="stroke-slate-800"
                        strokeWidth="8"
                        fill="none"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="42"
                        className={`${getHealthScoreStrokeColor(health.health_score)} transition-all`}
                        strokeWidth="8"
                        strokeDasharray="264"
                        strokeDashoffset={264 - (264 * health.health_score) / 100}
                        strokeLinecap="round"
                        fill="none"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className={`text-2xl font-semibold ${getHealthScoreColor(health.health_score)}`}>
                        {health.health_score}
                      </span>
                      <span className="text-[11px] text-slate-400">Health</span>
                    </div>
                  </div>
                </div>
              </motion.section>

              {/* Metric sections grid */}
              <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Deliverability */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.1 }}
                  className="rounded-2xl bg-slate-900/80 border border-slate-800 p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h2 className="text-sm font-semibold text-slate-100">Deliverability</h2>
                    <StatusPill status={health.cards.deliverability.status as Status} />
                  </div>
                  <dl className="space-y-1 text-xs text-slate-300">
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Emails sent</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.deliverability.details.emails_sent || 0).toLocaleString()}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Bounce rate</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.deliverability.details.bounce_rate * 100).toFixed(2)}%
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Spam complaints</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.deliverability.details.spam_complaint_rate * 100).toFixed(3)}%
                      </dd>
                    </div>
                  </dl>
                </motion.div>

                {/* Verification */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.2 }}
                  className="rounded-2xl bg-slate-900/80 border border-slate-800 p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h2 className="text-sm font-semibold text-slate-100">Verification</h2>
                    <StatusPill status={health.cards.verification.status as Status} />
                  </div>
                  <dl className="space-y-1 text-xs text-slate-300">
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Emails verified</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.verification.details.emails_verified || 0).toLocaleString()}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Valid %</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.verification.details.valid_pct * 100).toFixed(1)}%
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Invalid %</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.verification.details.invalid_pct * 100).toFixed(1)}%
                      </dd>
                    </div>
                  </dl>
                </motion.div>

                {/* Campaigns */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.3 }}
                  className="rounded-2xl bg-slate-900/80 border border-slate-800 p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h2 className="text-sm font-semibold text-slate-100">Campaigns</h2>
                    <StatusPill status={health.cards.campaigns.status as Status} />
                  </div>
                  <dl className="space-y-1 text-xs text-slate-300">
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Avg open rate</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.campaigns.details.avg_open_rate * 100).toFixed(1)}%
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Avg reply rate</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.campaigns.details.avg_reply_rate * 100).toFixed(1)}%
                      </dd>
                    </div>
                  </dl>
                </motion.div>

                {/* Jobs & Playbooks */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.4 }}
                  className="rounded-2xl bg-slate-900/80 border border-slate-800 p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h2 className="text-sm font-semibold text-slate-100">Jobs & Playbooks</h2>
                    <StatusPill status={health.cards.jobs.status as Status} />
                  </div>
                  <dl className="space-y-1 text-xs text-slate-300">
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Jobs started</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.jobs.details.jobs_started || 0).toLocaleString()}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-400">Jobs failed</dt>
                      <dd className="font-medium text-slate-200">
                        {(health.cards.jobs.details.jobs_failed || 0).toLocaleString()}
                      </dd>
                    </div>
                  </dl>
                </motion.div>
              </section>

              {/* Trends placeholder */}
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.5 }}
                className="rounded-2xl bg-slate-900/80 border border-slate-800 p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-semibold text-slate-100">Trends</h2>
                  <p className="text-[11px] text-slate-500">
                    Bounce, verification, and reply rate over time
                  </p>
                </div>
                <div className="h-40 flex items-center justify-center text-[11px] text-slate-500 border border-dashed border-slate-800 rounded-xl">
                  Chart area – plug in Recharts / Chart.js here.
                </div>
              </motion.section>
            </>
          )}
        </main>
      </div>
  );
}

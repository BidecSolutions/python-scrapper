"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient, API_URL, type Job, type Lead } from "@/lib/api";
import { LeadRow } from "@/components/leads/LeadRow";
import { LeadDetailPanel } from "@/components/leads/LeadDetailPanel";
import { AnimatePresence } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Download, RefreshCw } from "lucide-react";
import { StatusChip } from "@/components/jobs/StatusChip";
import { JobTimeline } from "@/components/jobs/JobTimeline";
import { ProgressRing } from "@/components/jobs/ProgressRing";
import { JobTabs } from "@/components/jobs/JobTabs";
import { LayoutDashboard, Users, Layers, Lightbulb, Activity } from "lucide-react";
import { ClickableStat } from "@/components/ui/ClickableStat";
import { CoverageBar } from "@/components/jobs/CoverageBar";
import { AICopilot } from "@/components/ai/AICopilot";
import { SegmentCard } from "@/components/jobs/SegmentCard";

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = parseInt(params.id as string);
  
  const [job, setJob] = useState<Job | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  useEffect(() => {
    if (jobId) {
      loadJob();
      loadLeads();
    }
  }, [jobId]);

  // Poll for job updates if job is running
  useEffect(() => {
    if (!job || (job.status !== "running" && job.status !== "ai_pending")) {
      return;
    }

    const interval = setInterval(() => {
      loadJob();
      loadLeads();
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [job, jobId]);

  const loadJob = async () => {
    try {
      const data = await apiClient.getJob(jobId);
      setJob(data);
    } catch (error) {
      console.error("Failed to load job:", error);
    }
  };

  const loadLeads = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getLeads(jobId);
      setLeads(data);
    } catch (error) {
      console.error("Failed to load leads:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLeadClick = (lead: Lead) => {
    setSelectedLead(lead);
    setIsPanelOpen(true);
  };

  const stats = {
    high: leads.filter((l) => l.quality_label === "high").length,
    medium: leads.filter((l) => l.quality_label === "medium").length,
    low: leads.filter((l) => l.quality_label === "low").length,
    total: leads.length,
  };

  if (!job) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-slate-400">Loading job...</p>
      </div>
    );
  }

  return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/jobs">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold">{job.niche}</h1>
                <StatusChip status={job.status} />
              </div>
              {job.location && (
                <p className="text-sm text-slate-400 mt-1">{job.location}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Rerun
            </Button>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <JobTabs
          defaultTab="overview"
          tabs={[
            {
              id: "overview",
              label: "Overview",
              icon: LayoutDashboard,
              content: <OverviewTab job={job} stats={stats} leads={leads} />,
            },
            {
              id: "leads",
              label: "Leads",
              icon: Users,
              content: (
                <LeadsTab
                  leads={leads}
                  loading={loading}
                  job={job}
                  onLeadClick={handleLeadClick}
                />
              ),
            },
            {
              id: "segments",
              label: "Segments",
              icon: Layers,
              content: <SegmentsTab jobId={jobId} />,
            },
            {
              id: "insights",
              label: "Insights",
              icon: Lightbulb,
              content: <InsightsTab jobId={jobId} />,
            },
            {
              id: "activity",
              label: "Activity",
              icon: Activity,
              content: <ActivityTab jobId={jobId} />,
            },
          ]}
        />

        {/* Lead Detail Panel */}
        <LeadDetailPanel
          open={isPanelOpen}
          onClose={() => setIsPanelOpen(false)}
          lead={selectedLead}
        />
      </div>
  );
}

// Tab Components
function OverviewTab({ job, stats, leads }: { job: Job; stats: any; leads: Lead[] }) {
  return (
    <div className="space-y-6">
      {/* Progress & Timeline */}
      {(job.status === "running" || job.status === "ai_pending") && job.total_targets && job.total_targets > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">Progress</h3>
            <ProgressRing
              value={job.processed_targets || 0}
              max={job.total_targets}
              showCountdown={true}
              startedAt={job.started_at}
            />
          </div>
          <JobTimeline status={job.status} />
        </div>
      )}

      {/* Stats Grid with Clickable Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <ClickableStat
          label="Leads Found"
          value={job.result_count?.toString() || "0"}
          onClick={() => {
            // Switch to leads tab (would need tab state management)
            window.location.hash = "#leads";
          }}
        />
        <ClickableStat
          label="High Quality"
          value={stats.high}
          description={`${stats.total > 0 ? Math.round((stats.high / stats.total) * 100) : 0}% of total`}
          onClick={() => {
            // Filter to high quality leads
            window.location.hash = "#leads?quality=high";
          }}
        />
        <ClickableStat
          label="With Email"
          value={leads.filter((l) => l.emails && l.emails.length > 0).length}
          description={`${stats.total > 0 ? Math.round((leads.filter((l) => l.emails && l.emails.length > 0).length / stats.total) * 100) : 0}% coverage`}
          onClick={() => {
            // Filter to leads with email
            window.location.hash = "#leads?hasEmail=true";
          }}
        />
        <InfoCard
          label="Duration"
          value={
            job.duration_seconds
              ? `${Math.round(job.duration_seconds / 60)}m`
              : job.started_at && !job.completed_at
              ? (() => {
                  const elapsed = Math.round((Date.now() - new Date(job.started_at).getTime()) / 1000);
                  return elapsed < 60 ? `${elapsed}s` : `${Math.round(elapsed / 60)}m`;
                })()
              : "—"
          }
        />
      </div>

      {/* Coverage Bar */}
      {stats.total > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <CoverageBar
            high={stats.high}
            medium={stats.medium}
            low={stats.low}
            total={stats.total}
            withEmail={leads.filter((l) => l.emails && l.emails.length > 0).length}
            withPhone={leads.filter((l) => l.phones && l.phones.length > 0).length}
          />
        </div>
      )}

      {/* Quality Stats */}
      {stats.total > 0 && (
        <div className="flex flex-wrap gap-2">
          <StatChip label="High Quality" value={stats.high} color="emerald" />
          <StatChip label="Medium" value={stats.medium} color="amber" />
          <StatChip label="Low" value={stats.low} color="rose" />
        </div>
      )}

      {/* Job Configuration */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h3 className="text-sm font-semibold mb-3">Job Configuration</h3>
        <div className="grid gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Max Results:</span>
            <span className="text-slate-50">{job.max_results}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Max Pages per Site:</span>
            <span className="text-slate-50">{job.max_pages_per_site}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function LeadsTab({
  leads,
  loading,
  job,
  onLeadClick,
}: {
  leads: Lead[];
  loading: boolean;
  job: Job;
  onLeadClick: (lead: Lead) => void;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span>Leads ({leads.length})</span>
      </div>
      {loading ? (
        <div className="p-8 text-center text-slate-400">Loading leads...</div>
      ) : leads.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-slate-400 mb-2">No leads found for this job yet.</p>
          {job.error_message && (
            <div className="mt-4 p-4 rounded-lg border border-amber-500/30 bg-amber-500/10 max-w-2xl mx-auto">
              <p className="text-sm text-amber-300 font-medium mb-1">⚠️ Issue:</p>
              <p className="text-xs text-amber-200/80">{job.error_message}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/80 border-b border-slate-800">
                     <tr className="text-xs text-slate-400 text-left">
                       <th className="px-3 py-2">Name</th>
                       <th className="px-3 py-2">Email</th>
                       <th className="px-3 py-2">Phone</th>
                       <th className="px-3 py-2">Score</th>
                       <th className="px-3 py-2">QA</th>
                       <th className="px-3 py-2">Tags</th>
                     </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {leads.map((lead) => (
                  <LeadRow key={lead.id} lead={lead} onOpenDetail={onLeadClick} />
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SegmentsTab({ jobId }: { jobId: number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-center">
      <p className="text-slate-400">Segments will appear here after AI clustering completes.</p>
    </div>
  );
}

function InsightsTab({ jobId }: { jobId: number }) {
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInsights();
  }, [jobId]);

  const loadInsights = async () => {
    try {
      const response = await fetch(`${API_URL}/api/jobs/${jobId}/insights`);
      if (response.ok) {
        const data = await response.json();
        setInsights(data);
      }
    } catch (error) {
      console.error("Failed to load insights:", error);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "Which 10 leads should I prioritize?",
    "Why is this job's quality lower than my last hospital job?",
    "What are the main patterns in these leads?",
  ];

  const handleAISend = async (query: string): Promise<string> => {
    try {
      const response = await fetch(`${API_URL}/api/jobs/${jobId}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query }),
      });
      const data = await response.json();
      return data.answer || "I couldn't process that question.";
    } catch (error) {
      return "Failed to get AI response. Please try again.";
    }
  };

  return (
    <div className="space-y-6">
      {loading ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-center">
          <p className="text-slate-400">Loading insights...</p>
        </div>
      ) : insights ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-50">AI Insights</h3>
            <span className="text-[10px] uppercase tracking-wide text-cyan-300 flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" /> Powered by AI
            </span>
          </div>
          <div className="prose prose-invert max-w-none text-sm text-slate-200 whitespace-pre-wrap">
            {insights.text}
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-center">
          <p className="text-slate-400">AI insights will appear here after job completion.</p>
        </div>
      )}

      {/* AI Copilot */}
      <AICopilot
        context={`Job ${jobId} insights`}
        suggestions={suggestions}
        onSend={handleAISend}
        placeholder="Ask AI about this job..."
      />
    </div>
  );
}

function ActivityTab({ jobId }: { jobId: number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-center">
      <p className="text-slate-400">Activity timeline will appear here.</p>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <motion.div
      className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-xl font-semibold mt-1">{value}</p>
    </motion.div>
  );
}

function StatChip({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: "emerald" | "amber" | "rose";
}) {
  const colorClasses = {
    emerald: "border-emerald-400/50 bg-emerald-500/10 text-emerald-300",
    amber: "border-amber-400/50 bg-amber-500/10 text-amber-300",
    rose: "border-rose-400/50 bg-rose-500/10 text-rose-300",
  };

  return (
    <motion.div
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${colorClasses[color]}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <span>{label}:</span>
      <span className="font-semibold">{value}</span>
    </motion.div>
  );
}


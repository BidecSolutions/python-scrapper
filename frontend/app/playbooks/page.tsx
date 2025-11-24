"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { motion, AnimatePresence } from "framer-motion";
import { Play, CheckCircle2, Loader2, Clock, AlertCircle, ExternalLink } from "lucide-react";
import { useRouter } from "next/navigation";
import { formatRelativeTime } from "@/lib/time";

export default function PlaybooksPage() {
  const { showToast } = useToast();
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [jobId, setJobId] = useState<number | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [jobHistory, setJobHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  
  const [config, setConfig] = useState({
    days: 7,
    include_risky: false,
    min_score: 0,
    list_name: "",
  });

  useEffect(() => {
    loadJobHistory();
  }, []);

  // Poll for job status if job is running
  useEffect(() => {
    if (jobId && jobStatus && (jobStatus.status === "queued" || jobStatus.status === "running")) {
      const interval = setInterval(async () => {
        try {
          const updated = await apiClient.getPlaybookJob(jobId);
          setJobStatus(updated);
          
          if (updated.status === "completed" || updated.status === "failed") {
            clearInterval(interval);
            loadJobHistory(); // Refresh history
            if (updated.status === "completed") {
              showToast({
                type: "success",
                title: "Playbook completed",
                message: `Created list "${updated.output_list_name || updated.meta?.output_list_name}" with ${updated.meta?.leads_added_to_list || 0} leads`,
              });
            }
          }
        } catch (error) {
          console.error("Failed to poll job status:", error);
        }
      }, 3000); // Poll every 3 seconds
      
      return () => clearInterval(interval);
    }
  }, [jobId, jobStatus]);

  const loadJobHistory = async () => {
    try {
      setLoadingHistory(true);
      const jobs = await apiClient.getPlaybookJobs(10);
      setJobHistory(jobs);
    } catch (error) {
      console.error("Failed to load job history:", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const runLinkedInCampaignPlaybook = async () => {
    try {
      setRunning(true);
      setJobStatus(null);
      setJobId(null);
      
      const response = await apiClient.runLinkedInCampaignPlaybook({
        days: config.days,
        include_risky: config.include_risky,
        min_score: config.min_score,
        list_name: config.list_name || undefined,
      });
      
      setJobId(response.id);
      setJobStatus(response);
      
      // Start polling for status
      if (response.status === "queued" || response.status === "running") {
        // Polling will be handled by useEffect
      }
      
      if (response.estimated_credits) {
        showToast({
          type: "info",
          title: "Playbook started",
          message: `Estimated credits: ${response.estimated_credits}. Processing in background...`,
        });
      }
    } catch (error: any) {
      console.error("Failed to run playbook:", error);
      showToast({
        type: "error",
        title: "Playbook failed",
        message: error?.response?.data?.detail || "Failed to start playbook",
      });
      setRunning(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case "running":
        return <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />;
      case "queued":
        return <Clock className="w-4 h-4 text-amber-400" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-rose-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
      case "running":
        return "border-cyan-500/30 bg-cyan-500/10 text-cyan-300";
      case "queued":
        return "border-amber-500/30 bg-amber-500/10 text-amber-300";
      case "failed":
        return "border-rose-500/30 bg-rose-500/10 text-rose-300";
      default:
        return "border-slate-500/30 bg-slate-500/10 text-slate-300";
    }
  };

  return (
    <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Playbooks</h1>
          <p className="text-sm text-slate-400 mt-1">
            Automated workflows to transform your leads into campaign-ready lists
          </p>
        </div>

        {/* LinkedIn → Campaign Playbook */}
        <motion.div
          className="rounded-xl border border-slate-800 bg-slate-900/60 p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold mb-1">LinkedIn → Campaign</h2>
              <p className="text-sm text-slate-400">
                Transform LinkedIn leads into a campaign-ready list with verified emails
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                Extension
              </span>
            </div>
          </div>

          <div className="space-y-4 mt-6">
            {/* Configuration */}
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Time Range</label>
                <select
                  value={config.days}
                  onChange={(e) => setConfig({ ...config, days: parseInt(e.target.value) || 7 })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                </select>
              </div>
              
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Minimum Score</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={config.min_score}
                  onChange={(e) => setConfig({ ...config, min_score: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.include_risky}
                    onChange={(e) => setConfig({ ...config, include_risky: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span className="text-sm text-slate-300">Include risky emails</span>
                </label>
              </div>
              
              <div>
                <label className="text-xs text-slate-400 mb-1 block">List Name (optional)</label>
                <input
                  type="text"
                  placeholder="Auto-generated if empty"
                  value={config.list_name}
                  onChange={(e) => setConfig({ ...config, list_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
            </div>

            {/* What it does */}
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
              <p className="text-xs font-semibold text-slate-300 mb-2">What this playbook does:</p>
              <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
                <li>Finds all LinkedIn leads from the last {config.days} days</li>
                <li>Runs Email Finder on leads without emails</li>
                <li>Verifies all emails</li>
                <li>Filters to Valid{config.include_risky ? " and Risky" : ""} emails with score ≥ {config.min_score}</li>
                <li>Creates a campaign-ready list</li>
              </ul>
            </div>

            {/* Run button */}
            <Button
              onClick={runLinkedInCampaignPlaybook}
              disabled={running || (jobStatus && (jobStatus.status === "queued" || jobStatus.status === "running"))}
              className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
            >
              {running || (jobStatus && (jobStatus.status === "queued" || jobStatus.status === "running")) ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {jobStatus?.status === "running" ? "Processing..." : "Starting..."}
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Run Playbook
                </>
              )}
            </Button>

            {/* Current Job Status */}
            {jobStatus && (
              <motion.div
                className={`rounded-lg border p-4 ${getStatusColor(jobStatus.status)}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="flex items-start gap-3">
                  {getStatusIcon(jobStatus.status)}
                  <div className="flex-1">
                    <p className="text-sm font-semibold mb-2">
                      {jobStatus.status === "completed" ? "Playbook completed!" :
                       jobStatus.status === "running" ? "Processing playbook..." :
                       jobStatus.status === "queued" ? "Playbook queued..." :
                       "Playbook failed"}
                    </p>
                    
                    {jobStatus.meta && Object.keys(jobStatus.meta).length > 0 && (
                      <div className="space-y-1 text-xs">
                        {jobStatus.meta.total_leads !== undefined && (
                          <p>
                            <span className="opacity-70">Total leads:</span> {jobStatus.meta.total_leads}
                          </p>
                        )}
                        {jobStatus.meta.processed_leads !== undefined && (
                          <p>
                            <span className="opacity-70">Processed:</span> {jobStatus.meta.processed_leads} / {jobStatus.meta.total_leads || 0}
                          </p>
                        )}
                        {jobStatus.meta.valid_count !== undefined && (
                          <p>
                            <span className="opacity-70">Valid emails:</span> {jobStatus.meta.valid_count}
                          </p>
                        )}
                        {jobStatus.meta.risky_count !== undefined && jobStatus.meta.risky_count > 0 && (
                          <p>
                            <span className="opacity-70">Risky emails:</span> {jobStatus.meta.risky_count}
                          </p>
                        )}
                        {jobStatus.meta.leads_added_to_list !== undefined && (
                          <p>
                            <span className="opacity-70">Leads added to list:</span> {jobStatus.meta.leads_added_to_list}
                          </p>
                        )}
                      </div>
                    )}
                    
                    {jobStatus.status === "completed" && jobStatus.output_list_id && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-3"
                        onClick={() => router.push(`/lists/${jobStatus.output_list_id}`)}
                      >
                        <ExternalLink className="w-3 h-3 mr-2" />
                        View List
                      </Button>
                    )}
                    
                    {jobStatus.estimated_credits && (
                      <p className="text-xs opacity-70 mt-2">
                        Estimated credits: {jobStatus.estimated_credits} | Used: {jobStatus.credits_used || 0}
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>

        {/* Job History */}
        <motion.div
          className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="px-4 py-3 border-b border-slate-800">
            <h2 className="text-sm font-semibold">Recent Playbook Jobs</h2>
          </div>
          
          {loadingHistory ? (
            <div className="p-4 text-center text-slate-400">Loading history...</div>
          ) : jobHistory.length === 0 ? (
            <div className="p-4 text-center text-slate-400">
              No playbook jobs yet. Run your first playbook above!
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              <AnimatePresence>
                {jobHistory.map((job) => (
                  <motion.div
                    key={job.id}
                    className="px-4 py-3 hover:bg-slate-800/40 transition-colors"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {getStatusIcon(job.status)}
                          <span className="text-sm font-medium">
                            LinkedIn → Campaign
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded border ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                        
                        <div className="text-xs text-slate-400 space-y-1 mt-2">
                          <p>
                            {job.meta?.total_leads ? (
                              <>Processed {job.meta.total_leads} LinkedIn leads → {job.meta.valid_count || 0} Valid, {job.meta.risky_count || 0} Risky, {job.meta.invalid_count || 0} Invalid, {job.meta.unknown_count || 0} Unknown.</>
                            ) : (
                              <>Job {job.status}</>
                            )}
                          </p>
                          {job.output_list_name && (
                            <p>
                              Created list: <span className="text-slate-300 font-medium">{job.output_list_name}</span>
                            </p>
                          )}
                          <p className="text-slate-500">
                            {formatRelativeTime(job.created_at)}
                            {job.finished_at && ` • Finished ${formatRelativeTime(job.finished_at)}`}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {job.output_list_id && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => router.push(`/lists/${job.output_list_id}`)}
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            View List
                          </Button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </motion.div>
      </div>
  );
}

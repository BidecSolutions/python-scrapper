"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  RefreshCw, 
  Merge, 
  X, 
  CheckCircle2, 
  AlertCircle,
  Mail,
  Globe,
  MapPin,
  Calendar,
  TrendingUp,
  Loader2,
} from "lucide-react";
import { apiClient, type DuplicateGroup } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { MetricCard } from "@/components/ui/metrics";

export default function DuplicatesPage() {
  const { showToast } = useToast();
  const [groups, setGroups] = useState<DuplicateGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [selectedGroup, setSelectedGroup] = useState<DuplicateGroup | null>(null);
  const [showMergeModal, setShowMergeModal] = useState(false);

  useEffect(() => {
    loadGroups();
    loadStats();
  }, []);

  const loadGroups = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getDuplicateGroups("pending");
      setGroups(data);
    } catch (error: any) {
      console.error("Failed to load duplicate groups:", error);
      showToast({
        type: "error",
        title: "Failed to load duplicates",
        message: error?.response?.data?.detail || "Please try again",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await apiClient.getDuplicateStats();
      setStats(data);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  const handleDetect = async () => {
    try {
      setDetecting(true);
      const result = await apiClient.detectDuplicates(0.7);
      showToast({
        type: "success",
        title: "Detection complete",
        message: result.message,
      });
      await loadGroups();
      await loadStats();
    } catch (error: any) {
      showToast({
        type: "error",
        title: "Detection failed",
        message: error?.response?.data?.detail || "Please try again",
      });
    } finally {
      setDetecting(false);
    }
  };

  const handleMerge = async (groupId: number, canonicalLeadId: number) => {
    try {
      const result = await apiClient.mergeDuplicates(groupId, canonicalLeadId);
      showToast({
        type: "success",
        title: "Merge successful",
        message: result.message,
      });
      setShowMergeModal(false);
      setSelectedGroup(null);
      await loadGroups();
      await loadStats();
    } catch (error: any) {
      showToast({
        type: "error",
        title: "Merge failed",
        message: error?.response?.data?.detail || "Please try again",
      });
    }
  };

  const handleIgnore = async (groupId: number) => {
    if (!confirm("Are you sure you want to ignore this duplicate group? You can always detect duplicates again later.")) {
      return;
    }

    try {
      await apiClient.ignoreDuplicateGroup(groupId);
      showToast({
        type: "success",
        title: "Group ignored",
        message: "This duplicate group has been marked as ignored",
      });
      await loadGroups();
      await loadStats();
    } catch (error: any) {
      showToast({
        type: "error",
        title: "Failed to ignore",
        message: error?.response?.data?.detail || "Please try again",
      });
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="px-6 py-4 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              Duplicate Detection
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Find and merge duplicate leads automatically
            </p>
          </div>
          <button
            onClick={handleDetect}
            disabled={detecting}
            className="inline-flex items-center rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-xs font-semibold px-4 py-2.5 shadow-lg shadow-cyan-500/20 dark:shadow-cyan-500/30 transition-all hover:shadow-xl hover:shadow-cyan-500/30 text-white disabled:opacity-50"
          >
            {detecting ? (
              <>
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                Detecting...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-1.5" />
                Detect Duplicates
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto px-6 pt-6 pb-10 space-y-6 bg-slate-50 dark:bg-slate-950">
        {/* Stats */}
        {stats && (
          <section className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <MetricCard label="Pending groups" value={stats.pending_groups} tone="info" />
            <MetricCard label="Total groups" value={stats.total_groups} />
            <MetricCard label="Merged groups" value={stats.merged_groups} tone="success" />
            <MetricCard label="Duplicate leads" value={stats.total_duplicate_leads} tone="danger" />
          </section>
        )}

        {/* Duplicate Groups */}
        {loading ? (
          <div className="text-center py-12 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading duplicate groups...
          </div>
        ) : groups.length === 0 ? (
          <section className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 px-6 py-10 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 mb-3">
              <CheckCircle2 className="w-6 h-6 text-slate-400 dark:text-slate-500" />
            </div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              No duplicate groups found
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Click "Detect Duplicates" to scan your leads for potential duplicates
            </p>
            <button
              onClick={handleDetect}
              disabled={detecting}
              className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 text-xs font-semibold px-4 py-2 text-white transition-colors disabled:opacity-50"
            >
              {detecting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                  Detecting...
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                  Detect Duplicates
                </>
              )}
            </button>
          </section>
        ) : (
          <section className="space-y-4">
            {groups.map((group) => (
              <DuplicateGroupCard
                key={group.id}
                group={group}
                onMerge={() => {
                  setSelectedGroup(group);
                  setShowMergeModal(true);
                }}
                onIgnore={() => handleIgnore(group.id)}
              />
            ))}
          </section>
        )}
      </main>

      {/* Merge Modal */}
      <AnimatePresence>
        {showMergeModal && selectedGroup && (
          <MergeModal
            group={selectedGroup}
            onClose={() => {
              setShowMergeModal(false);
              setSelectedGroup(null);
            }}
            onMerge={handleMerge}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function DuplicateGroupCard({
  group,
  onMerge,
  onIgnore,
}: {
  group: DuplicateGroup;
  onMerge: () => void;
  onIgnore: () => void;
}) {
  const confidenceColor =
    group.confidence_score >= 0.8
      ? "text-emerald-600 dark:text-emerald-400"
      : group.confidence_score >= 0.6
      ? "text-amber-600 dark:text-amber-400"
      : "text-rose-600 dark:text-rose-400";

  const matchReasonLabels: Record<string, string> = {
    same_email: "Same Email",
    same_domain_name: "Same Domain + Name",
    same_domain: "Same Domain",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-50">
              Group #{group.id}
            </h3>
            <span className={`text-xs font-semibold ${confidenceColor}`}>
              {(group.confidence_score * 100).toFixed(0)}% confidence
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {matchReasonLabels[group.match_reason] || group.match_reason}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {group.leads.length} potential duplicate{group.leads.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onMerge}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-xs font-semibold text-white transition-colors"
          >
            <Merge className="w-3.5 h-3.5" />
            Merge
          </button>
          <button
            onClick={onIgnore}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            Ignore
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {group.leads.map((lead, idx) => (
          <div
            key={lead.id}
            className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800"
          >
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-100 dark:bg-cyan-950/30 flex items-center justify-center text-xs font-semibold text-cyan-600 dark:text-cyan-400">
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-sm text-slate-900 dark:text-slate-50">
                  {lead.name || "Unnamed Lead"}
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400">
                  #{lead.id}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600 dark:text-slate-400">
                {lead.website && (
                  <div className="flex items-center gap-1">
                    <Globe className="w-3 h-3" />
                    <span className="truncate max-w-[200px]">{lead.website}</span>
                  </div>
                )}
                {lead.emails && lead.emails.length > 0 && (
                  <div className="flex items-center gap-1">
                    <Mail className="w-3 h-3" />
                    <span>{lead.emails[0]}</span>
                    {lead.emails.length > 1 && (
                      <span className="text-[10px]">+{lead.emails.length - 1}</span>
                    )}
                  </div>
                )}
                {lead.city && (
                  <div className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    <span>{lead.city}</span>
                  </div>
                )}
              </div>
              {lead.matched_fields && lead.matched_fields.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {lead.matched_fields.map((field) => (
                    <span
                      key={field}
                      className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-100 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400"
                    >
                      {field}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function MergeModal({
  group,
  onClose,
  onMerge,
}: {
  group: DuplicateGroup;
  onClose: () => void;
  onMerge: (groupId: number, canonicalLeadId: number) => void;
}) {
  const [selectedCanonical, setSelectedCanonical] = useState<number | null>(
    group.leads[0]?.id || null
  );

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 max-w-2xl w-full shadow-xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
            Merge Duplicates
          </h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
          Select which lead to keep (canonical). All other leads will be merged into it, and their
          data (emails, phones, sources) will be combined.
        </p>

        <div className="space-y-2 mb-6">
          {group.leads.map((lead) => (
            <label
              key={lead.id}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedCanonical === lead.id
                  ? "border-cyan-500 dark:border-cyan-400 bg-cyan-50 dark:bg-cyan-950/30"
                  : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              <input
                type="radio"
                name="canonical"
                value={lead.id}
                checked={selectedCanonical === lead.id}
                onChange={(e) => setSelectedCanonical(Number(e.target.value))}
                className="mt-1 w-4 h-4 text-cyan-600 focus:ring-cyan-500"
              />
              <div className="flex-1">
                <div className="font-semibold text-sm text-slate-900 dark:text-slate-50 mb-1">
                  {lead.name || "Unnamed Lead"} #{lead.id}
                </div>
                <div className="text-xs text-slate-600 dark:text-slate-400 space-y-0.5">
                  {lead.website && <div>🌐 {lead.website}</div>}
                  {lead.emails && lead.emails.length > 0 && (
                    <div>📧 {lead.emails.join(", ")}</div>
                  )}
                  {lead.phones && lead.phones.length > 0 && (
                    <div>📞 {lead.phones.join(", ")}</div>
                  )}
                </div>
              </div>
            </label>
          ))}
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => {
              if (selectedCanonical) {
                onMerge(group.id, selectedCanonical);
              }
            }}
            disabled={!selectedCanonical}
            className="flex-1 inline-flex items-center justify-center rounded-lg bg-cyan-600 hover:bg-cyan-700 text-xs font-semibold px-4 py-2.5 text-white transition-colors disabled:opacity-50"
          >
            <Merge className="w-3.5 h-3.5 mr-1.5" />
            Merge {group.leads.length - 1} duplicate{group.leads.length - 1 !== 1 ? "s" : ""}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
        </div>
      </motion.div>
    </div>
  );
}


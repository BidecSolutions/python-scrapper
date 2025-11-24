"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient, type Lead } from "@/lib/api";
import { LeadDetailPanel } from "@/components/leads/LeadDetailPanel";
import { LeadRow as LeadRowComponent, ScorePill } from "@/components/leads/LeadRow";
import { Download, Search, ExternalLink } from "lucide-react";
import { BulkActionsToolbar } from "@/components/leads/BulkActionsToolbar";
import { ScoreHeatBadge } from "@/components/leads/ScoreHeatBadge";
import { useToast } from "@/components/ui/Toast";
import { SavedViewsBar } from "@/components/saved-views/SavedViewsBar";
import type { SavedView } from "@/lib/api";

export default function LeadsPage() {
  const { showToast } = useToast();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [exporting, setExporting] = useState(false);
  const [selectedLeads, setSelectedLeads] = useState<Set<number>>(new Set());
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [qualityFilter, setQualityFilter] = useState<"all" | "high" | "medium" | "low">("all");
  const [minScore, setMinScore] = useState<number | null>(null);
  const [maxScore, setMaxScore] = useState<number | null>(null);

  // Debounce search and reload when filters change
  useEffect(() => {
    const timer = setTimeout(() => {
      loadLeads();
    }, 300); // Wait 300ms after user stops typing

    return () => clearTimeout(timer);
  }, [searchQuery, sourceFilter, qualityFilter, minScore, maxScore]);

  const loadLeads = async (customFilters?: Record<string, any>) => {
    try {
      setLoading(true);
      const filters: Record<string, any> = customFilters || {};
      if (!customFilters) {
        if (searchQuery.trim()) {
          filters.search = searchQuery.trim();
        }
        if (sourceFilter) {
          filters.source = sourceFilter;
        }
        if (qualityFilter !== "all") {
          filters.quality = qualityFilter;
        }
        if (minScore !== null) {
          filters.min_score = minScore;
        }
        if (maxScore !== null) {
          filters.max_score = maxScore;
        }
      }
      const data = await apiClient.getLeads(undefined, filters);
      setLeads(data);
    } catch (error) {
      console.error("Failed to load leads:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyView = (view: SavedView) => {
    // Apply the saved view's filters
    if (view.filters.search) {
      setSearchQuery(view.filters.search);
    } else {
      setSearchQuery("");
    }
    if (view.filters.source) {
      setSourceFilter(view.filters.source);
    } else {
      setSourceFilter(null);
    }
    if (view.filters.quality) {
      setQualityFilter(view.filters.quality as "all" | "high" | "medium" | "low");
    } else {
      setQualityFilter("all");
    }
    if (view.filters.min_score !== undefined) {
      setMinScore(view.filters.min_score);
    } else {
      setMinScore(null);
    }
    if (view.filters.max_score !== undefined) {
      setMaxScore(view.filters.max_score);
    } else {
      setMaxScore(null);
    }
    // Load leads with the view's filters
    loadLeads(view.filters);
  };

  const handleExport = async (format: "csv" | "excel") => {
    if (leads.length === 0) {
      alert("No leads available to export. Please wait for leads to load or create a job first.");
      return;
    }

    try {
      setExporting(true);
      
      // If there are selected leads, export only those; otherwise export all visible leads
      const filters: Record<string, any> = {};
      if (searchQuery.trim()) {
        filters.search = searchQuery.trim();
      }
      
      // If specific leads are selected, we'll need to handle that differently
      // For now, export all visible leads (respecting search filter)
      const blob = await apiClient.exportLeads(format, filters);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const timestamp = new Date().toISOString().split('T')[0];
      a.download = `leads_${timestamp}.${format === "csv" ? "csv" : "xlsx"}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      // Show success toast
      showToast({
        type: "success",
        title: "Export Successful",
        message: `Exported ${leads.length} leads as ${format.toUpperCase()}`,
      });
    } catch (error: any) {
      console.error("Failed to export leads:", error);
      const errorMessage = error?.response?.data?.detail || error?.message || "Failed to export leads. Please try again.";
      showToast({
        type: "error",
        title: "Export Failed",
        message: errorMessage,
      });
    } finally {
      setExporting(false);
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
  };

  return (
    <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Leads</h1>
            <p className="text-sm text-slate-400 mt-1">
              Browse and explore your enriched leads
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("csv")}
              disabled={exporting || leads.length === 0}
              title={leads.length === 0 ? "No leads to export" : "Export all visible leads as CSV"}
            >
              <Download className="w-4 h-4 mr-2" />
              {exporting ? "Exporting..." : "Export CSV"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("excel")}
              disabled={exporting || leads.length === 0}
              title={leads.length === 0 ? "No leads to export" : "Export all visible leads as Excel"}
            >
              <Download className="w-4 h-4 mr-2" />
              {exporting ? "Exporting..." : "Export Excel"}
            </Button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search leads by name, email, website, city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>

        {/* Saved Views Bar */}
        <SavedViewsBar
          pageType="leads"
          currentFilters={{
            search: searchQuery.trim() || undefined,
            source: sourceFilter || undefined,
            quality: qualityFilter !== "all" ? qualityFilter : undefined,
            min_score: minScore !== null ? minScore : undefined,
            max_score: maxScore !== null ? maxScore : undefined,
          }}
          onApplyView={handleApplyView}
        />


        {/* Summary Row */}
        <section className="flex flex-wrap items-center justify-between gap-3 text-[11px]">
          <div className="flex flex-wrap gap-2">
            <span className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/40">
              High quality: {stats.high}
            </span>
            <span className="px-2 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/40">
              Medium: {stats.medium}
            </span>
            <span className="px-2 py-1 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/40">
              Low: {stats.low}
            </span>
          </div>
          <div className="text-slate-400">
            Showing {leads.length} leads {sourceFilter && `· source: ${sourceFilter === "linkedin_extension" ? "LinkedIn" : sourceFilter === "csv" ? "CSV" : "Manual"}`}
          </div>
        </section>

        {/* Leads Table */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden">
                 <div className="px-4 py-2.5 border-b border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                   <span>Lead List</span>
                   {selectedLeads.size > 0 && (
                     <span className="text-cyan-400">
                       {selectedLeads.size} selected
                     </span>
                   )}
                 </div>
                 {loading ? (
                   <div className="p-8 text-center text-slate-400">Loading leads...</div>
                 ) : leads.length === 0 ? (
                   <div className="p-8 text-center text-slate-400">No leads found</div>
                 ) : (
                   <div className="overflow-x-auto">
                     <table className="w-full">
                       <thead className="bg-slate-900/80 border-b border-slate-800">
                         <tr className="text-xs text-slate-400 text-left">
                           <th className="px-3 py-2 w-12">
                             <input
                               type="checkbox"
                               checked={selectedLeads.size === leads.length && leads.length > 0}
                               onChange={(e) => {
                                 if (e.target.checked) {
                                   setSelectedLeads(new Set(leads.map((l) => l.id)));
                                 } else {
                                   setSelectedLeads(new Set());
                                 }
                               }}
                               className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
                             />
                           </th>
                           <th className="px-3 py-2">Name</th>
                           <th className="px-3 py-2">Email</th>
                           <th className="px-3 py-2">Phone</th>
                           <th className="px-3 py-2">Source</th>
                           <th className="px-3 py-2">Score</th>
                           <th className="px-3 py-2">Tags</th>
                         </tr>
                       </thead>
                       <tbody>
                         <AnimatePresence>
                           {leads.map((lead) => (
                             <LeadRowComponent
                               key={lead.id}
                               lead={lead}
                               onOpenDetail={handleLeadClick}
                               selected={selectedLeads.has(lead.id)}
                               onSelect={(selected) => {
                                 const newSet = new Set(selectedLeads);
                                 if (selected) {
                                   newSet.add(lead.id);
                                 } else {
                                   newSet.delete(lead.id);
                                 }
                                 setSelectedLeads(newSet);
                               }}
                             />
                           ))}
                         </AnimatePresence>
                       </tbody>
                     </table>
                   </div>
                 )}
               </div>

               {/* Bulk Actions Toolbar */}
               <BulkActionsToolbar
                 selectedCount={selectedLeads.size}
                 onClear={() => setSelectedLeads(new Set())}
                 onMarkGood={async () => {
                   // TODO: Implement bulk mark good
                   console.log("Mark good:", Array.from(selectedLeads));
                   setSelectedLeads(new Set());
                 }}
                 onMarkBad={async () => {
                   // TODO: Implement bulk mark bad
                   console.log("Mark bad:", Array.from(selectedLeads));
                   setSelectedLeads(new Set());
                 }}
                 onVerifyEmails={async () => {
                   if (selectedLeads.size === 0) {
                     showToast({
                       type: "error",
                       title: "No leads selected",
                       message: "Please select leads to verify",
                     });
                     return;
                   }
                   
                   try {
                     const leadIds = Array.from(selectedLeads);
                     const result = await apiClient.createBulkVerifyFromLeads(leadIds);
                     
                     showToast({
                       type: "success",
                       title: "Verification job created",
                       message: `Processing ${result.total_emails} emails. Check the Verification page for progress.`,
                     });
                     
                     setSelectedLeads(new Set());
                   } catch (error: any) {
                     console.error("Failed to create verification job:", error);
                     showToast({
                       type: "error",
                       title: "Failed to create job",
                       message: error?.response?.data?.detail || "Please try again",
                     });
                   }
                 }}
                 onExport={async () => {
                   // TODO: Implement bulk export
                   await handleExport("csv");
                   setSelectedLeads(new Set());
                 }}
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


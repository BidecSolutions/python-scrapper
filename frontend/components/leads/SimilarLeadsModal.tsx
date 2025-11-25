"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ExternalLink, Search } from "lucide-react";
import { apiClient, API_URL } from "@/lib/api";
import { SmartScoreBadge } from "./SmartScoreBadge";

interface SimilarLeadsModalProps {
  leadId: number;
  open: boolean;
  onClose: () => void;
  onLeadClick?: (leadId: number) => void;
}

export function SimilarLeadsModal({
  leadId,
  open,
  onClose,
  onLeadClick,
}: SimilarLeadsModalProps) {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [scope, setScope] = useState<"workspace" | "job">("workspace");

  useEffect(() => {
    if (open && leadId) {
      loadSimilarLeads();
    }
  }, [open, leadId, scope]);

  const loadSimilarLeads = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/leads/${leadId}/similar?scope=${scope}&limit=20`
      );
      if (response.ok) {
        const data = await response.json();
        setLeads(data.similar_leads || []);
      }
    } catch (error) {
      console.error("Failed to load similar leads:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="relative w-full max-w-3xl max-h-[80vh] rounded-xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-slate-800">
            <div>
              <h2 className="text-lg font-semibold text-slate-50">Find Similar Leads</h2>
              <p className="text-xs text-slate-400 mt-1">
                AI-powered similarity search
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as "workspace" | "job")}
                className="text-xs px-2 py-1 rounded-lg border border-slate-800 bg-slate-950 text-slate-200"
              >
                <option value="workspace">Workspace</option>
                <option value="job">This Job</option>
              </select>
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-slate-300 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-slate-400">Loading similar leads...</div>
              </div>
            ) : leads.length === 0 ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Search className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400">No similar leads found</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {leads.map((lead, idx) => (
                  <motion.div
                    key={lead.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    onClick={() => onLeadClick?.(lead.id)}
                    className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 hover:bg-slate-800/60 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-sm font-medium text-slate-50 truncate">
                            {lead.name || "Unknown"}
                          </h3>
                          {lead.website && (
                            <a
                              href={lead.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="text-slate-400 hover:text-cyan-400 transition-colors"
                            >
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          {lead.city && <span>{lead.city}</span>}
                          {lead.country && <span>• {lead.country}</span>}
                          {lead.niche && <span>• {lead.niche}</span>}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {lead.smart_score !== null && (
                          <SmartScoreBadge score={lead.smart_score} mode="smart" />
                        )}
                        {lead.similarity !== undefined && (
                          <span className="text-[10px] text-slate-500">
                            {Math.round(lead.similarity * 100)}% match
                          </span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}


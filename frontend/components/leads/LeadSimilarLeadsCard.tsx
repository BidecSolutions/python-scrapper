"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Search, Sparkles, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Section } from "./LeadDetailPanel";

type SimilarLead = {
  id: number;
  name: string;
  city?: string;
  country?: string;
  score?: number;
  similarity_score?: number;
};

export function LeadSimilarLeadsCard({ leadId }: { leadId: number }) {
  const [leads, setLeads] = useState<SimilarLead[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadSimilar() {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getSimilarLeads(leadId, "workspace", 10);
      setLeads(result.leads || result.similar || []);
      setOpen(true);
    } catch (e: any) {
      if (e?.response?.status !== 404) {
        console.error("Failed to load similar leads:", e);
      }
      setError("No similar leads found yet");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Section title="Similar Leads (AI)">
      {!open && (
        <div className="space-y-2">
          <p className="text-[11px] text-slate-500">
            Use AI embeddings to find companies similar to this one.
          </p>
          <button
            onClick={loadSimilar}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900/50 px-3 py-1.5 text-xs text-slate-200 hover:border-cyan-500 hover:text-cyan-200 transition-colors disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Finding…
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5" />
                Find similar
              </>
            )}
          </button>
        </div>
      )}

      {open && loading && (
        <div className="flex items-center gap-2 text-slate-400">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span className="text-[11px]">Searching for similar leads…</span>
        </div>
      )}

      {open && error && (
        <p className="text-[11px] text-slate-500">
          No similar leads found yet. This will improve as your AI embedding index is built.
        </p>
      )}

      {open && !loading && !error && leads.length === 0 && (
        <p className="text-[11px] text-slate-500">
          No similar leads found. Try again after more leads are added to your workspace.
        </p>
      )}

      {open && !loading && !error && leads.length > 0 && (
        <ul className="space-y-1.5">
          {leads.map((lead) => (
            <motion.li
              key={lead.id}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center justify-between rounded-lg bg-slate-900/50 border border-slate-800 px-2.5 py-2 hover:bg-slate-900 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-slate-100 truncate">{lead.name}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {[lead.city, lead.country].filter(Boolean).join(", ") || "Location unknown"}
                </div>
              </div>
              {(typeof lead.score === "number" || typeof lead.similarity_score === "number") && (
                <span className="text-[10px] text-slate-400 ml-2 shrink-0">
                  {Math.round((lead.score || lead.similarity_score || 0) * 100)}% match
                </span>
              )}
            </motion.li>
          ))}
        </ul>
      )}
    </Section>
  );
}


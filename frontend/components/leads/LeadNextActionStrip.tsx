"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Zap, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api";

const labelMap: Record<string, string> = {
  email_template_a: "Send email – Template A",
  email_template_b: "Send email – Template B",
  linkedin_dm: "Send LinkedIn DM",
  linkedin_connection: "Send LinkedIn connection request",
  call: "Schedule a call",
  skip: "Skip for now",
};

export function LeadNextActionStrip({ leadId }: { leadId: number }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        const result = await apiClient.getNextAction(leadId);
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (e: any) {
        if (!cancelled) {
          // 404 or no data is fine - show empty state
          if (e?.response?.status !== 404) {
            console.error("Failed to load next action:", e);
          }
          setError("No recommendation yet");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [leadId]);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2.5"
      >
        <div className="flex items-center gap-2 text-[11px] text-slate-500">
          <Sparkles className="w-3 h-3 animate-pulse" />
          <span>AI is analyzing the best next step...</span>
        </div>
      </motion.div>
    );
  }

  if (error || !data) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2.5"
      >
        <div className="flex items-start gap-2">
          <Zap className="w-3.5 h-3.5 text-slate-500 mt-0.5 shrink-0" />
          <div className="text-[11px] text-slate-500">
            <div className="font-medium text-slate-400 mb-0.5">Recommended next step (AI)</div>
            <div>
              AI hasn't recommended a next step yet. Once you start logging outcomes, this will suggest the best channel.
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  const label = labelMap[data.action] || data.action?.replace(/_/g, " ") || "Unknown action";
  const confidence = Math.round((data.confidence || data.score || 0) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-cyan-500/40 bg-cyan-500/5 px-3 py-2.5"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <div className="text-xs font-semibold text-slate-100">Recommended next step (AI)</div>
          </div>
          <div className="text-sm text-slate-200 font-medium">{label}</div>
          {data.reason && (
            <div className="text-[11px] text-slate-400 mt-1">{data.reason}</div>
          )}
        </div>
        <div className="text-[10px] text-cyan-300 font-medium shrink-0">
          {confidence}% confidence
        </div>
      </div>
    </motion.div>
  );
}


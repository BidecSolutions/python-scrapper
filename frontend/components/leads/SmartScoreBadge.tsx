"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import { API_URL } from "@/lib/api";

interface SmartScoreBadgeProps {
  score: number | null;
  ruleScore?: number | null;
  mode?: "smart" | "rule" | "both";
  onExplain?: () => void;
}

export function SmartScoreBadge({
  score,
  ruleScore,
  mode = "smart",
  onExplain,
}: SmartScoreBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);

  const displayScore = mode === "rule" && ruleScore ? ruleScore : score;
  
  if (displayScore === null || displayScore === undefined) {
    return (
      <span className="text-xs text-slate-500">—</span>
    );
  }

  const scoreValue = typeof displayScore === "number" ? displayScore : parseFloat(displayScore);
  const normalizedScore = scoreValue > 1 ? scoreValue / 100 : scoreValue; // Handle 0-100 vs 0-1

  const level =
    normalizedScore >= 0.75 ? "High" : normalizedScore >= 0.4 ? "Medium" : "Low";

  const colorClasses = {
    High: "bg-emerald-500/15 text-emerald-200 border-emerald-400/40",
    Medium: "bg-amber-500/15 text-amber-200 border-amber-400/40",
    Low: "bg-slate-500/20 text-slate-200 border-slate-500/40",
  };

  const handleHover = async () => {
    if (!onExplain || mode !== "smart" || explanation) return;
    
    setShowTooltip(true);
    if (!explanation && !loadingExplanation) {
      setLoadingExplanation(true);
      try {
        // Fetch explanation
        const leadId = (window as any).currentLeadId; // Would need to pass this
        if (leadId) {
          const response = await fetch(`${API_URL}/api/leads/${leadId}/explanation`);
          if (response.ok) {
            const data = await response.json();
            setExplanation(data.explanation);
          }
        }
      } catch (error) {
        console.error("Failed to load explanation:", error);
      } finally {
        setLoadingExplanation(false);
      }
    }
  };

  return (
    <div className="relative inline-block">
      <motion.div
        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 border text-xs font-medium cursor-help ${colorClasses[level]}`}
        onMouseEnter={handleHover}
        onMouseLeave={() => setShowTooltip(false)}
        whileHover={{ scale: 1.05 }}
      >
        <span>{Math.round(normalizedScore * 100)}</span>
        <span className="opacity-70">•</span>
        <span className="opacity-70">{level}</span>
        {mode === "smart" && (
          <>
            <span className="opacity-50">•</span>
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span className="uppercase tracking-wide text-[9px] opacity-70">AI</span>
          </>
        )}
      </motion.div>

      {showTooltip && explanation && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-3 rounded-lg border border-slate-800 bg-slate-900 shadow-xl z-50"
        >
          <p className="text-xs text-slate-200 whitespace-pre-wrap">{explanation}</p>
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-900" />
        </motion.div>
      )}
    </div>
  );
}


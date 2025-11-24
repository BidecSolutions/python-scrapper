"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Activity, 
  CheckCircle2, 
  AlertCircle, 
  XCircle,
  Info,
  TrendingUp,
} from "lucide-react";
import { apiClient, type HealthScore } from "@/lib/api";

interface HealthScoreBadgeProps {
  leadId: number;
  score?: number;  // Optional pre-calculated score
  showDetails?: boolean;
  size?: "sm" | "md" | "lg";
}

export function HealthScoreBadge({
  leadId,
  score: initialScore,
  showDetails = false,
  size = "md",
}: HealthScoreBadgeProps) {
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    if (initialScore !== undefined) {
      // If score is provided, we can show it but won't have breakdown
      return;
    }
    loadHealthScore();
  }, [leadId, initialScore]);

  const loadHealthScore = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getLeadHealthScore(leadId);
      setHealthScore(data);
    } catch (error) {
      console.error("Failed to load health score:", error);
    } finally {
      setLoading(false);
    }
  };

  const displayScore = healthScore?.score ?? initialScore ?? 0;
  const grade = healthScore?.grade ?? getGradeFromScore(displayScore);

  const gradeConfig = {
    A: { color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-100 dark:bg-emerald-950/30", border: "border-emerald-300 dark:border-emerald-800" },
    B: { color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-100 dark:bg-blue-950/30", border: "border-blue-300 dark:border-blue-800" },
    C: { color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-100 dark:bg-amber-950/30", border: "border-amber-300 dark:border-amber-800" },
    D: { color: "text-orange-600 dark:text-orange-400", bg: "bg-orange-100 dark:bg-orange-950/30", border: "border-orange-300 dark:border-orange-800" },
    F: { color: "text-rose-600 dark:text-rose-400", bg: "bg-rose-100 dark:bg-rose-950/30", border: "border-rose-300 dark:border-rose-800" },
  };

  const config = gradeConfig[grade as keyof typeof gradeConfig] || gradeConfig.F;

  const sizeClasses = {
    sm: "text-[10px] px-1.5 py-0.5",
    md: "text-xs px-2 py-1",
    lg: "text-sm px-3 py-1.5",
  };

  if (loading && !initialScore) {
    return (
      <div className={`inline-flex items-center gap-1 ${sizeClasses[size]} rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900`}>
        <Activity className="w-3 h-3 animate-pulse text-slate-400" />
        <span className="text-slate-400">—</span>
      </div>
    );
  }

  return (
    <div className="relative inline-block">
      <div
        className={`inline-flex items-center gap-1 ${sizeClasses[size]} rounded-full border font-semibold ${config.bg} ${config.border} ${config.color} cursor-help`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <Activity className="w-3 h-3" />
        <span>{Math.round(displayScore)}</span>
        <span className="opacity-70">{grade}</span>
      </div>

      {showDetails && healthScore && (
        <AnimatePresence>
          {showTooltip && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="absolute left-0 top-full mt-2 z-50 w-80 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-xl p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-slate-900 dark:text-slate-50">
                  Health Score Breakdown
                </h4>
                <span className={`text-xs font-semibold ${config.color}`}>
                  {Math.round(displayScore)}/100 • {grade}
                </span>
              </div>

              <div className="space-y-2 mb-3">
                {Object.entries(healthScore.breakdown).map(([key, data]) => {
                  const statusIcon = {
                    good: <CheckCircle2 className="w-3 h-3 text-emerald-500" />,
                    warning: <AlertCircle className="w-3 h-3 text-amber-500" />,
                    missing: <XCircle className="w-3 h-3 text-slate-400" />,
                    na: <Info className="w-3 h-3 text-slate-400" />,
                  }[data.status] || <Info className="w-3 h-3 text-slate-400" />;

                  return (
                    <div key={key} className="flex items-start justify-between gap-2 text-xs">
                      <div className="flex items-center gap-1.5 flex-1 min-w-0">
                        {statusIcon}
                        <span className="text-slate-600 dark:text-slate-400 capitalize">
                          {key.replace("_", " ")}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <div className="w-16 bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full ${
                              data.status === "good"
                                ? "bg-emerald-500"
                                : data.status === "warning"
                                ? "bg-amber-500"
                                : "bg-slate-400"
                            }`}
                            style={{ width: `${(data.points / data.max) * 100}%` }}
                          />
                        </div>
                        <span className="text-slate-500 dark:text-slate-400 w-8 text-right">
                          {data.points}/{data.max}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {healthScore.recommendations.length > 0 && (
                <div className="pt-3 border-t border-slate-200 dark:border-slate-800">
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                    Recommendations:
                  </p>
                  <ul className="space-y-1">
                    {healthScore.recommendations.map((rec, idx) => (
                      <li key={idx} className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-1.5">
                        <TrendingUp className="w-3 h-3 text-cyan-500 mt-0.5 flex-shrink-0" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  );
}

function getGradeFromScore(score: number): "A" | "B" | "C" | "D" | "F" {
  if (score >= 90) return "A";
  if (score >= 75) return "B";
  if (score >= 60) return "C";
  if (score >= 40) return "D";
  return "F";
}


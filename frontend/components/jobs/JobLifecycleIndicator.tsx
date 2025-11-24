"use client";

import { motion } from "framer-motion";
import { Search, Globe, Brain, CheckCircle, Clock } from "lucide-react";
import { type JobStatus } from "@/lib/api";

interface JobLifecycleIndicatorProps {
  status: JobStatus;
  size?: "sm" | "md";
}

const phases = [
  { id: "discover", icon: Search, label: "Discover" },
  { id: "crawl", icon: Globe, label: "Crawl" },
  { id: "enrich", icon: Brain, label: "Enrich" },
  { id: "done", icon: CheckCircle, label: "Done" },
];

export function JobLifecycleIndicator({
  status,
  size = "sm",
}: JobLifecycleIndicatorProps) {
  const getActivePhase = () => {
    if (status === "pending") return 0;
    if (status === "running") return 1;
    if (status === "ai_pending") return 2;
    if (status === "completed" || status === "completed_with_warnings") return 3;
    if (status === "failed") return -1;
    return 0;
  };

  const activePhase = getActivePhase();
  const isFailed = status === "failed";

  const iconSize = size === "sm" ? "w-3 h-3" : "w-4 h-4";
  const gap = size === "sm" ? "gap-1" : "gap-1.5";

  return (
    <div className={`flex items-center ${gap}`}>
      {phases.map((phase, index) => {
        const Icon = phase.icon;
        const isActive = index <= activePhase && !isFailed;
        const isCurrent = index === activePhase && !isFailed;

        return (
          <div key={phase.id} className="flex items-center">
            <motion.div
              className={`${iconSize} rounded-full flex items-center justify-center transition-all ${
                isActive
                  ? "bg-cyan-500 text-slate-950"
                  : isFailed && index === activePhase
                  ? "bg-rose-500 text-white"
                  : "bg-slate-800 text-slate-500"
              }`}
              animate={
                isCurrent
                  ? {
                      scale: [1, 1.2, 1],
                      boxShadow: [
                        "0 0 0 0 rgba(34,211,238,0.4)",
                        "0 0 0 4px rgba(34,211,238,0)",
                      ],
                    }
                  : {}
              }
              transition={
                isCurrent
                  ? { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
                  : { duration: 0.2 }
              }
            >
              <Icon className={iconSize} />
            </motion.div>
            {index < phases.length - 1 && (
              <div
                className={`h-0.5 w-3 ${
                  index < activePhase ? "bg-cyan-500" : "bg-slate-800"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}


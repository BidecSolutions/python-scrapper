"use client";

import { motion } from "framer-motion";
import { Search, Globe, Brain, CheckCircle, Clock } from "lucide-react";
import { type JobStatus } from "@/lib/api";

interface JobTimelineProps {
  status: JobStatus;
  phase?: string;
}

const phases = [
  { id: "queued", label: "Queued", icon: Clock },
  { id: "discovering", label: "Discovering websites", icon: Search },
  { id: "crawling", label: "Crawling & extracting", icon: Globe },
  { id: "enriching", label: "AI enrichment", icon: Brain },
  { id: "completed", label: "Done", icon: CheckCircle },
];

export function JobTimeline({ status, phase }: JobTimelineProps) {
  const getCurrentPhase = () => {
    if (status === "pending") return "queued";
    if (status === "running") return phase === "crawling" ? "crawling" : "discovering";
    if (status === "ai_pending") return "enriching";
    if (status === "completed" || status === "completed_with_warnings") return "completed";
    if (status === "failed") return "completed";
    return "queued";
  };

  const currentPhase = getCurrentPhase();
  const currentIndex = phases.findIndex((p) => p.id === currentPhase);

  return (
    <div className="flex items-center gap-2">
      {phases.map((phase, index) => {
        const Icon = phase.icon;
        const isActive = index <= currentIndex;
        const isCurrent = index === currentIndex;

        return (
          <div key={phase.id} className="flex items-center">
            <motion.div
              className={`flex items-center gap-2 rounded-lg px-3 py-2 transition-all ${
                isActive
                  ? "bg-slate-800/60 text-slate-50"
                  : "bg-slate-900/40 text-slate-500"
              }`}
              animate={
                isCurrent
                  ? {
                      boxShadow: [
                        "0 0 0 0 rgba(34,211,238,0.4)",
                        "0 0 0 4px rgba(34,211,238,0)",
                      ],
                    }
                  : {}
              }
              transition={
                isCurrent
                  ? { duration: 2, repeat: Infinity, ease: "easeOut" }
                  : { duration: 0.2 }
              }
            >
              <Icon
                className={`w-4 h-4 ${
                  isActive ? "text-cyan-400" : "text-slate-600"
                }`}
              />
              <span className="text-xs font-medium hidden sm:inline">
                {phase.label}
              </span>
            </motion.div>
            {index < phases.length - 1 && (
              <div
                className={`h-0.5 w-8 mx-1 ${
                  index < currentIndex ? "bg-cyan-500" : "bg-slate-800"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}


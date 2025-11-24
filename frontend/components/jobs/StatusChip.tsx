"use client";

import { motion } from "framer-motion";
import { type JobStatus } from "@/lib/api";

interface StatusChipProps {
  status: JobStatus;
  className?: string;
}

export function StatusChip({ status, className = "" }: StatusChipProps) {
  const config = {
    pending: {
      label: "Queued",
      color: "border-slate-500/40 bg-slate-800/80 text-slate-200",
      dotColor: "bg-slate-400",
      glow: false,
    },
    running: {
      label: "Running",
      color: "border-emerald-500/40 bg-emerald-500/15 text-emerald-300",
      dotColor: "bg-emerald-400",
      glow: true,
      glowColor: "rgba(16,185,129,0.7)",
    },
    ai_pending: {
      label: "AI Enriching",
      color: "border-amber-500/40 bg-amber-500/15 text-amber-300",
      dotColor: "bg-amber-400",
      glow: true,
      glowColor: "rgba(251,191,36,0.7)",
    },
    completed: {
      label: "Completed",
      color: "border-cyan-500/40 bg-cyan-500/15 text-cyan-300",
      dotColor: "bg-cyan-400",
      glow: false,
    },
    failed: {
      label: "Failed",
      color: "border-rose-500/40 bg-rose-500/15 text-rose-300",
      dotColor: "bg-rose-400",
      glow: false,
    },
    completed_with_warnings: {
      label: "Completed",
      color: "border-amber-500/40 bg-amber-500/15 text-amber-300",
      dotColor: "bg-amber-400",
      glow: false,
    },
  };

  const { label, color, dotColor, glow, glowColor } = config[status];

  return (
    <motion.span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${color} ${className}`}
      animate={
        glow
          ? {
              boxShadow: [
                `0 0 0 0 ${glowColor}`,
                `0 0 0 8px ${glowColor?.replace("0.7", "0")}`,
              ],
            }
          : {}
      }
      transition={
        glow
          ? { duration: 1.5, repeat: Infinity, ease: "easeOut" }
          : { duration: 0.2 }
      }
    >
      <motion.span
        className={`h-1.5 w-1.5 rounded-full ${dotColor}`}
        animate={glow ? { scale: [1, 1.2, 1] } : {}}
        transition={
          glow
            ? { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
            : {}
        }
      />
      {label}
    </motion.span>
  );
}


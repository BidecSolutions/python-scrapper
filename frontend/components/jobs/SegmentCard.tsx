"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface SegmentCardProps {
  segment: {
    id: number;
    label: string;
    description: string;
    lead_count: number;
    avg_score?: number;
  };
  onView: () => void;
  delay?: number;
}

export function SegmentCard({ segment, onView, delay = 0 }: SegmentCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      whileHover={{ scale: 1.02, borderColor: "rgba(34,211,238,0.4)" }}
      className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 hover:bg-slate-900 transition-all cursor-pointer"
      onClick={onView}
    >
      <h3 className="text-sm font-semibold text-slate-50 mb-1">{segment.label}</h3>
      <p className="text-xs text-slate-400 line-clamp-3 mb-3">{segment.description}</p>
      
      <div className="flex items-center justify-between text-xs text-slate-300 mb-3">
        <span>{segment.lead_count} leads</span>
        {segment.avg_score !== undefined && (
          <span>Avg score {Math.round(segment.avg_score * 100)}</span>
        )}
      </div>
      
      <button className="inline-flex items-center gap-1 text-xs text-cyan-300 hover:text-cyan-200 transition-colors">
        View leads
        <ArrowRight className="w-3 h-3" />
      </button>
    </motion.div>
  );
}


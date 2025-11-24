"use client";

import { motion } from "framer-motion";

interface ProgressRingProps {
  value: number;
  max: number;
  size?: number;
  strokeWidth?: number;
  showCountdown?: boolean;
  startedAt?: string;
}

export function ProgressRing({
  value,
  max,
  size = 80,
  strokeWidth = 6,
  showCountdown = false,
  startedAt,
}: ProgressRingProps) {
  const percentage = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  // Calculate ETA
  const getETA = () => {
    if (!startedAt || value === 0) return null;
    const elapsed = Date.now() - new Date(startedAt).getTime();
    const perItem = elapsed / value;
    const remaining = max - value;
    const etaMs = remaining * perItem;
    const seconds = Math.round(etaMs / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.round(seconds / 60);
    return `${minutes}m`;
  };

  const eta = showCountdown ? getETA() : null;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-slate-800"
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className="text-cyan-400"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          style={{
            strokeDasharray: circumference,
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-sm font-semibold text-slate-50">
          {value}/{max}
        </span>
        {eta && (
          <span className="text-[10px] text-slate-400 mt-0.5">~{eta} left</span>
        )}
      </div>
    </div>
  );
}


"use client";

import { motion } from "framer-motion";

interface ScoreHeatBadgeProps {
  score: number;
  label?: string;
  size?: "sm" | "md";
}

export function ScoreHeatBadge({
  score,
  label,
  size = "sm",
}: ScoreHeatBadgeProps) {
  // Determine color based on score
  const getColor = () => {
    if (score >= 75) {
      return {
        bg: "bg-emerald-500/20",
        border: "border-emerald-400/50",
        text: "text-emerald-300",
        glow: "shadow-emerald-500/20",
      };
    } else if (score >= 50) {
      return {
        bg: "bg-amber-500/20",
        border: "border-amber-400/50",
        text: "text-amber-300",
        glow: "shadow-amber-500/20",
      };
    } else {
      return {
        bg: "bg-rose-500/20",
        border: "border-rose-400/50",
        text: "text-rose-300",
        glow: "shadow-rose-500/20",
      };
    }
  };

  const colors = getColor();
  const intensity = Math.min(1, score / 100);
  const glowIntensity = intensity * 0.5;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-[11px]",
    md: "px-3 py-1 text-xs",
  };

  return (
    <motion.span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${colors.bg} ${colors.border} ${colors.text} ${sizeClasses[size]}`}
      animate={{
        boxShadow: [
          `0 0 0 0 ${colors.glow.replace("/20", `/${Math.round(glowIntensity * 20)}`)}`,
          `0 0 ${4 * intensity}px ${colors.glow.replace("/20", `/${Math.round(glowIntensity * 20)}`)}`,
        ],
      }}
      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
    >
      <span className="font-semibold">{Math.round(score)}</span>
      {label && (
        <>
          <span className="opacity-60">•</span>
          <span className="capitalize">{label}</span>
        </>
      )}
    </motion.span>
  );
}


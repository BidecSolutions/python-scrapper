"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface ClickableStatProps {
  label: string;
  value: string | number;
  onClick?: () => void;
  description?: string;
  delay?: number;
}

export function ClickableStat({
  label,
  value,
  onClick,
  description,
  delay = 0,
}: ClickableStatProps) {
  const Component = onClick ? motion.button : motion.div;

  return (
    <Component
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay }}
      onClick={onClick}
      className={`rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 transition-all ${
        onClick
          ? "hover:bg-slate-800/80 hover:border-cyan-500/40 cursor-pointer group"
          : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-xs text-slate-400">{label}</p>
          <p className="text-xl font-semibold mt-1 text-slate-50">{value}</p>
          {description && (
            <p className="text-xs text-slate-500 mt-1">{description}</p>
          )}
        </div>
        {onClick && (
          <motion.div
            initial={{ x: 0 }}
            whileHover={{ x: 4 }}
            transition={{ duration: 0.2 }}
          >
            <ArrowRight className="w-4 h-4 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </motion.div>
        )}
      </div>
    </Component>
  );
}


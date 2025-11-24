"use client";

import { motion } from "framer-motion";

interface CoverageBarProps {
  high: number;
  medium: number;
  low: number;
  total: number;
  withEmail?: number;
  withPhone?: number;
}

export function CoverageBar({
  high,
  medium,
  low,
  total,
  withEmail,
  withPhone,
}: CoverageBarProps) {
  if (total === 0) return null;

  const highPct = (high / total) * 100;
  const mediumPct = (medium / total) * 100;
  const lowPct = (low / total) * 100;

  const emailPct = withEmail ? (withEmail / total) * 100 : 0;
  const phonePct = withPhone ? (withPhone / total) * 100 : 0;

  return (
    <div className="space-y-3">
      {/* Quality Bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-400">Lead Quality</span>
          <span className="text-xs text-slate-500">{total} total</span>
        </div>
        <div className="h-3 rounded-full bg-slate-800 overflow-hidden flex">
          {high > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${highPct}%` }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="bg-emerald-500"
              title={`${high} high quality`}
            />
          )}
          {medium > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${mediumPct}%` }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="bg-amber-500"
              title={`${medium} medium quality`}
            />
          )}
          {low > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${lowPct}%` }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="bg-slate-700"
              title={`${low} low quality`}
            />
          )}
        </div>
        <div className="flex items-center gap-4 mt-1.5 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            {high} high
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            {medium} medium
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-slate-700" />
            {low} low
          </span>
        </div>
      </div>

      {/* Contact Coverage */}
      {(withEmail !== undefined || withPhone !== undefined) && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Contact Coverage</span>
          </div>
          <div className="space-y-1.5">
            {withEmail !== undefined && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 w-16">Email:</span>
                <div className="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${emailPct}%` }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                    className="h-full bg-cyan-500"
                  />
                </div>
                <span className="text-xs text-slate-400 w-12 text-right">
                  {Math.round(emailPct)}%
                </span>
              </div>
            )}
            {withPhone !== undefined && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 w-16">Phone:</span>
                <div className="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${phonePct}%` }}
                    transition={{ duration: 0.5, delay: 0.5 }}
                    className="h-full bg-emerald-500"
                  />
                </div>
                <span className="text-xs text-slate-400 w-12 text-right">
                  {Math.round(phonePct)}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { type Lead } from "@/lib/api";
import { LeadDetailPanel } from "./LeadDetailPanel";
import { QaBadge } from "./QaBadge";
import { SmartScoreBadge } from "./SmartScoreBadge";
import { HealthScoreBadge } from "./HealthScoreBadge";

function SourceBadge({ source }: { source: string }) {
  if (source === "linkedin_extension" || source?.includes("linkedin")) {
    return (
      <Badge
        variant="outline"
        className="border-blue-500/50 bg-blue-500/10 text-blue-300 text-[10px] px-2 py-0.5 flex items-center gap-1"
      >
        <span>in</span>
        <span>LinkedIn</span>
      </Badge>
    );
  }
  
  if (source === "csv" || source?.includes("csv")) {
    return (
      <Badge
        variant="outline"
        className="border-slate-600 bg-slate-800/60 text-slate-300 text-[10px] px-2 py-0.5"
      >
        CSV
      </Badge>
    );
  }
  
  if (source === "manual") {
    return (
      <Badge
        variant="outline"
        className="border-slate-600 bg-slate-800/60 text-slate-300 text-[10px] px-2 py-0.5"
      >
        Manual
      </Badge>
    );
  }
  
  // Default: show source as-is or "Unknown"
  return (
    <Badge
      variant="outline"
      className="border-slate-600 bg-slate-800/60 text-slate-300 text-[10px] px-2 py-0.5"
    >
      {source || "Unknown"}
    </Badge>
  );
}

interface LeadRowProps {
  lead: Lead;
  onOpenDetail: (lead: Lead) => void;
  selected?: boolean;
  onSelect?: (selected: boolean) => void;
}

export function LeadRow({
  lead,
  onOpenDetail,
  selected = false,
  onSelect,
}: LeadRowProps) {
  return (
    <motion.tr
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      whileHover={{ backgroundColor: "rgba(15,23,42,0.9)" }}
      className={`border-b border-slate-800 text-sm transition-colors ${
        selected ? "bg-cyan-500/10" : ""
      }`}
    >
      <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
        {onSelect && (
          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => {
              e.stopPropagation();
              onSelect(e.target.checked);
            }}
            className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
            onClick={(e) => e.stopPropagation()}
          />
        )}
      </td>
      <td
        className="px-3 py-2 cursor-pointer"
        onClick={() => onOpenDetail(lead)}
      >
        <div className="flex flex-col gap-1">
          <span className="font-medium">{lead.name || "Unknown"}</span>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-500">
              {lead.niche || "—"}
              {lead.city && ` • ${lead.city}`}
            </span>
            {/* Source badges (for scraping sources) */}
            {(lead.sources && lead.sources.length > 0 && lead.source !== "linkedin_extension") && (
              <div className="flex gap-1">
                {lead.sources.map((source) => (
                  <Badge
                    key={source}
                    variant="outline"
                    className="border-slate-700 bg-slate-800/60 text-[10px] text-slate-300 px-1.5 py-0"
                  >
                    {source === "google_search" ? "G Search" :
                     source === "google_places" ? "G Maps" :
                     source === "yellowpages" ? "YP" :
                     source === "web_search" ? "Bing" :
                     source}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
      </td>
      <td
        className="px-3 py-2 text-xs text-slate-300 cursor-pointer"
        onClick={() => onOpenDetail(lead)}
      >
        {lead.emails[0] || "—"}
      </td>
      <td
        className="px-3 py-2 text-xs text-slate-300 cursor-pointer"
        onClick={() => onOpenDetail(lead)}
      >
        {lead.phones[0] || "—"}
      </td>
      <td
        className="px-3 py-2 cursor-pointer"
        onClick={() => onOpenDetail(lead)}
      >
        <SourceBadge source={lead.source || ""} />
      </td>
             <td
               className="px-3 py-2 cursor-pointer"
               onClick={() => onOpenDetail(lead)}
             >
               <div className="flex items-center gap-2 flex-wrap">
                 <HealthScoreBadge leadId={lead.id} size="sm" showDetails={true} />
                 <ScorePill
                   score={lead.quality_score || 0}
                   label={lead.quality_label || "low"}
                 />
                 {lead.smart_score !== null && lead.smart_score !== undefined && (
                   <SmartScoreBadge
                     score={lead.smart_score}
                     mode="smart"
                   />
                 )}
                 <QaBadge status={lead.qa_status} />
               </div>
             </td>
      <td
        className="px-3 py-2 cursor-pointer"
        onClick={() => onOpenDetail(lead)}
      >
        <div className="flex flex-wrap gap-1">
          {lead.tags.slice(0, 3).map((tag) => (
            <Badge
              key={tag}
              variant="outline"
              className="border-slate-700 bg-slate-900/80 text-[11px] text-slate-200"
            >
              {tag.replace(/_/g, " ")}
            </Badge>
          ))}
          {lead.tags.length > 3 && (
            <span className="text-[11px] text-slate-500">
              +{lead.tags.length - 3} more
            </span>
          )}
        </div>
      </td>
    </motion.tr>
  );
}

export function ScorePill({
  score,
  label,
}: {
  score: number;
  label: "low" | "medium" | "high";
}) {
  const colorMap: Record<typeof label, string> = {
    low: "from-rose-500 to-amber-500",
    medium: "from-amber-400 to-cyan-400",
    high: "from-emerald-400 to-cyan-400",
  };

  return (
    <div className="inline-flex items-center gap-2">
      <motion.div
        className={`inline-flex items-center gap-1 rounded-full bg-gradient-to-r ${colorMap[label]} px-2 py-0.5 text-[11px] font-semibold text-slate-950`}
        whileHover={{ scale: 1.03 }}
      >
        <span>{Math.round(score)}</span>
        <span className="uppercase tracking-[0.16em]">{label}</span>
      </motion.div>
    </div>
  );
}


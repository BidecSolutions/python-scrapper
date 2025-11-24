"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Code, TrendingUp, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Section } from "./LeadDetailPanel";

type TechPayload = {
  cms?: string;
  tools?: string[];
  digital_maturity?: number;
  ads_running?: boolean;
  ads_platforms?: string[];
  notes?: string;
};

export function LeadTechAndAdsCard({ leadId }: { leadId: number }) {
  const [data, setData] = useState<TechPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        const result = await apiClient.getLeadTechStack(leadId);
        if (!cancelled) {
          // Transform API response to our format
          setData({
            cms: result.cms,
            tools: result.tools || result.technologies || [],
            digital_maturity: result.digital_maturity_score || result.digital_maturity,
            ads_running: result.ads_detected || false,
            ads_platforms: result.ad_platforms || [],
            notes: result.summary,
          });
          setError(null);
        }
      } catch (e: any) {
        if (!cancelled) {
          if (e?.response?.status !== 404) {
            console.error("Failed to load tech stack:", e);
          }
          setError("No tech data yet");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [leadId]);

  return (
    <Section title="Tech & Advertising">
      {loading && (
        <div className="flex items-center gap-2 text-slate-400">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span className="text-[11px]">Detecting CMS, tools and ad pixels…</span>
        </div>
      )}

      {!loading && error && (
        <p className="text-[11px] text-slate-500">
          No tech data yet. This will populate as your scrapers run tech-detection on the website.
        </p>
      )}

      {!loading && !error && data && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5">
              <Code className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-slate-300">CMS: {data.cms || "Unknown"}</span>
            </div>
            {typeof data.digital_maturity === "number" && (
              <span className="inline-flex items-center rounded-full bg-cyan-500/15 px-2 py-0.5 text-[10px] text-cyan-300 border border-cyan-500/30">
                Maturity: {Math.round(data.digital_maturity * 100)}%
              </span>
            )}
          </div>

          {data.tools && data.tools.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {data.tools.slice(0, 8).map((tool) => (
                <span
                  key={tool}
                  className="inline-flex rounded-full bg-slate-800 px-2 py-0.5 text-[10px] text-slate-300 border border-slate-700"
                >
                  {tool}
                </span>
              ))}
              {data.tools.length > 8 && (
                <span className="text-[10px] text-slate-500">+{data.tools.length - 8} more</span>
              )}
            </div>
          )}

          <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mt-2">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>
              Ads:{" "}
              {data.ads_running
                ? `Yes (${(data.ads_platforms || []).join(", ") || "detected"})`
                : "No signals yet"}
            </span>
          </div>

          {data.notes && (
            <p className="mt-2 text-[11px] text-slate-400 leading-relaxed">{data.notes}</p>
          )}
        </div>
      )}
    </Section>
  );
}


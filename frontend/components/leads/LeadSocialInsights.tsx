"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { MessageSquare, TrendingUp, Heart, Sparkles, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Section } from "./LeadDetailPanel";

type SocialInsights = {
  posts_per_month?: number;
  avg_engagement?: number;
  topic_distribution?: Record<string, number>;
  dominant_topics?: string[];
  sentiment_distribution?: Record<string, number>;
  growth_stage?: string;
  dominant_pain?: string;
  summary?: string;
};

export function LeadSocialInsights({ leadId }: { leadId: number }) {
  const [insights, setInsights] = useState<SocialInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        const result = await apiClient.getSocialInsights(leadId);
        if (!cancelled) {
          setInsights(result);
          setError(null);
        }
      } catch (e: any) {
        if (!cancelled) {
          if (e?.response?.status !== 404) {
            console.error("Failed to load social insights:", e);
          }
          setError("No social data yet");
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
    <Section title="Social Insights (AI)">
      {loading && (
        <div className="flex items-center gap-2 text-slate-400">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span className="text-[11px]">Analyzing their recent social posts…</span>
        </div>
      )}

      {!loading && error && (
        <p className="text-[11px] text-slate-500">
          No social data yet. Add or detect their social profiles to unlock AI insights.
        </p>
      )}

      {!loading && !error && insights && (
        <div className="space-y-2.5">
          {insights.summary && (
            <p className="text-xs text-slate-300 leading-relaxed">{insights.summary}</p>
          )}

          <div className="grid grid-cols-2 gap-2 text-xs">
            {typeof insights.posts_per_month === "number" && (
              <div className="flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-slate-300">{insights.posts_per_month} posts/month</span>
              </div>
            )}
            {typeof insights.avg_engagement === "number" && (
              <div className="flex items-center gap-1.5">
                <Heart className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-slate-300">Avg: {insights.avg_engagement.toFixed(1)}</span>
              </div>
            )}
            {insights.growth_stage && (
              <div className="flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-slate-300">{insights.growth_stage}</span>
              </div>
            )}
          </div>

          {insights.dominant_topics && insights.dominant_topics.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {insights.dominant_topics.map((topic, idx) => (
                <motion.span
                  key={topic}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="inline-flex rounded-full bg-purple-600/20 px-2 py-0.5 text-[10px] text-purple-200 border border-purple-400/40"
                >
                  {topic}
                </motion.span>
              ))}
            </div>
          )}

          {insights.sentiment_distribution && (
            <div className="text-[11px] text-slate-400 mt-2">
              Sentiment: {Math.round((insights.sentiment_distribution.positive || 0) * 100)}% positive
            </div>
          )}
        </div>
      )}
    </Section>
  );
}


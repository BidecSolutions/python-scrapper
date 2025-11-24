"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp, MessageSquare, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface SocialInsightsCardProps {
  leadId: number;
}

export function SocialInsightsCard({ leadId }: SocialInsightsCardProps) {
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInsights();
  }, [leadId]);

  const loadInsights = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSocialInsights(leadId);
      setInsights(data);
    } catch (error) {
      console.error("Failed to load social insights:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2 mb-3">
          <MessageSquare className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">Social Insights</h2>
          <Sparkles className="w-3 h-3 text-cyan-400" />
        </div>
        <p className="text-xs text-slate-400">Analyzing social content...</p>
      </div>
    );
  }

  if (!insights || !insights.summary) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2 mb-3">
          <MessageSquare className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">Social Insights</h2>
          <Sparkles className="w-3 h-3 text-cyan-400" />
        </div>
        <p className="text-xs text-slate-400">
          No social insights available. Connect LinkedIn/X to analyze posts.
        </p>
      </div>
    );
  }

  const topicDistribution = insights.topic_distribution || {};
  const dominantTopics = insights.dominant_topics || [];
  const sentimentDist = insights.sentiment_distribution || {};

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center gap-2 mb-3">
        <MessageSquare className="w-4 h-4 text-cyan-400" />
        <h2 className="text-sm font-semibold text-slate-200">Social Insights</h2>
        <Sparkles className="w-3 h-3 text-cyan-400" />
      </div>

      {/* Summary */}
      {insights.summary && (
        <p className="text-xs text-slate-300 mb-3 leading-relaxed">
          {insights.summary}
        </p>
      )}

      {/* Topics */}
      {dominantTopics.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-slate-400 mb-2">Top Topics</p>
          <div className="flex flex-wrap gap-1">
            {dominantTopics.slice(0, 5).map((topic: string) => (
              <Badge
                key={topic}
                variant="outline"
                className="text-[10px] px-2 py-0.5 border-cyan-500/30 bg-cyan-500/10 text-cyan-300"
              >
                {topic.replace(/_/g, " ")}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {insights.posts_per_month !== null && (
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-3 h-3 text-slate-400" />
            <span className="text-slate-400">Posts/month:</span>
            <span className="text-slate-200 font-semibold">
              {insights.posts_per_month.toFixed(1)}
            </span>
          </div>
        )}
        {insights.avg_engagement !== null && (
          <div className="flex items-center gap-1.5">
            <MessageSquare className="w-3 h-3 text-slate-400" />
            <span className="text-slate-400">Avg engagement:</span>
            <span className="text-slate-200 font-semibold">
              {insights.avg_engagement.toFixed(0)}
            </span>
          </div>
        )}
        {insights.growth_stage && (
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Growth stage:</span>
            <span className="text-slate-200 font-semibold capitalize">
              {insights.growth_stage}
            </span>
          </div>
        )}
        {insights.dominant_pain && (
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Focus area:</span>
            <span className="text-slate-200 font-semibold capitalize">
              {insights.dominant_pain.replace(/_/g, " ")}
            </span>
          </div>
        )}
      </div>

      {/* Sentiment */}
      {Object.keys(sentimentDist).length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <p className="text-xs text-slate-400 mb-1.5">Sentiment Mix</p>
          <div className="flex gap-1">
            {Object.entries(sentimentDist).map(([sentiment, pct]: [string, any]) => (
              <div
                key={sentiment}
                className="flex-1 h-2 rounded-full overflow-hidden bg-slate-800"
                title={`${sentiment}: ${(pct * 100).toFixed(0)}%`}
              >
                <motion.div
                  className={`h-full ${
                    sentiment === "positive"
                      ? "bg-emerald-500"
                      : sentiment === "negative"
                      ? "bg-rose-500"
                      : "bg-slate-500"
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-[10px] text-slate-500 mt-3">
        Based on recent LinkedIn & X posts (with your connected accounts)
      </p>
    </div>
  );
}


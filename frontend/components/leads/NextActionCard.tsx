"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Zap, Mail, MessageSquare, Phone, Clock, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface NextActionCardProps {
  leadId: number;
}

export function NextActionCard({ leadId }: NextActionCardProps) {
  const [action, setAction] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNextAction();
  }, [leadId]);

  const loadNextAction = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getNextAction(leadId);
      setAction(data);
    } catch (error) {
      console.error("Failed to load next action:", error);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (actionType: string) => {
    if (actionType.includes("email")) return Mail;
    if (actionType.includes("linkedin")) return MessageSquare;
    if (actionType === "call") return Phone;
    if (actionType === "wait" || actionType === "skip") return Clock;
    return Zap;
  };

  const getActionLabel = (actionType: string) => {
    if (actionType === "email_template_a") return "Send Email (Template A)";
    if (actionType === "email_template_b") return "Send Email (Template B)";
    if (actionType === "email_template_c") return "Send Email (Template C)";
    if (actionType === "linkedin_dm") return "Send LinkedIn DM";
    if (actionType === "linkedin_connection") return "Connect on LinkedIn";
    if (actionType === "call") return "Make a Call";
    if (actionType === "wait") return "Wait";
    if (actionType === "skip") return "Skip";
    return actionType;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-emerald-400";
    if (confidence >= 0.6) return "text-cyan-400";
    return "text-amber-400";
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">Next Best Action (AI)</h2>
          <Sparkles className="w-3 h-3 text-cyan-400" />
        </div>
        <p className="text-xs text-slate-400">Analyzing best approach...</p>
      </div>
    );
  }

  if (!action) {
    return null;
  }

  const Icon = getActionIcon(action.action);
  const confidencePct = Math.round((action.confidence || action.score || 0) * 100);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Zap className="w-4 h-4 text-cyan-400" />
        <h2 className="text-sm font-semibold text-slate-200">Next Best Action (AI)</h2>
        <Sparkles className="w-3 h-3 text-cyan-400" />
      </div>

      <div className="space-y-3">
        {/* Recommended Action */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
          <div className="p-2 rounded-lg bg-cyan-500/20">
            <Icon className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-slate-100">
              {getActionLabel(action.action)}
            </p>
            {action.reason && (
              <p className="text-xs text-slate-400 mt-0.5">{action.reason}</p>
            )}
          </div>
          <Badge
            variant="outline"
            className={`text-[10px] ${getConfidenceColor(action.confidence)} border-current`}
          >
            {confidencePct}% confidence
          </Badge>
        </div>

        {/* Timing */}
        {action.suggested_at && (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5" />
            <span>Suggested for: {new Date(action.suggested_at).toLocaleDateString()}</span>
          </div>
        )}

        {/* Model Info */}
        {action.model_version && (
          <p className="text-[10px] text-slate-500">
            Powered by {action.model_version}
          </p>
        )}

        {/* Action Button */}
        <Button
          variant="outline"
          size="sm"
          className="w-full border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10"
          onClick={() => {
            // TODO: Export to CRM / outreach tool
            console.log("Apply action:", action.action);
          }}
        >
          Apply Action
        </Button>
      </div>
    </div>
  );
}


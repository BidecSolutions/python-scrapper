"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ThumbsUp, ThumbsDown, Star } from "lucide-react";
import { useToast } from "@/components/ui/Toast";

interface FeedbackButtonsProps {
  leadId: number;
  currentFeedback?: "good" | "bad" | "won" | null;
  onFeedback?: (label: "good" | "bad" | "won") => void;
  size?: "sm" | "md";
  variant?: "inline" | "buttons";
}

export function FeedbackButtons({
  leadId,
  currentFeedback,
  onFeedback,
  size = "sm",
  variant = "inline",
}: FeedbackButtonsProps) {
  const { showToast } = useToast();
  const [submitting, setSubmitting] = useState(false);

  const handleFeedback = async (label: "good" | "bad" | "won") => {
    if (submitting) return;
    
    setSubmitting(true);
    try {
      const response = await fetch("http://localhost:8000/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_id: leadId, label }),
      });

      if (response.ok) {
        showToast({
          type: "success",
          title: "Feedback saved",
          message: "We'll use this to improve your AI scoring",
          duration: 3000,
        });
        onFeedback?.(label);
      } else {
        showToast({
          type: "error",
          title: "Failed to save feedback",
          message: "Please try again",
        });
      }
    } catch (error) {
      showToast({
        type: "error",
        title: "Failed to save feedback",
        message: "Please try again",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const sizeClasses = {
    sm: "px-2 py-1 text-xs",
    md: "px-3 py-1.5 text-sm",
  };

  if (variant === "inline") {
    return (
      <div className="flex items-center gap-1">
        <button
          onClick={() => handleFeedback("good")}
          disabled={submitting}
          className={`${sizeClasses[size]} rounded-full transition-all ${
            currentFeedback === "good"
              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
              : "bg-slate-800/60 text-slate-400 hover:bg-emerald-500/10 hover:text-emerald-300"
          }`}
        >
          <ThumbsUp className="w-3 h-3" />
        </button>
        <button
          onClick={() => handleFeedback("bad")}
          disabled={submitting}
          className={`${sizeClasses[size]} rounded-full transition-all ${
            currentFeedback === "bad"
              ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
              : "bg-slate-800/60 text-slate-400 hover:bg-rose-500/10 hover:text-rose-300"
          }`}
        >
          <ThumbsDown className="w-3 h-3" />
        </button>
        <button
          onClick={() => handleFeedback("won")}
          disabled={submitting}
          className={`${sizeClasses[size]} rounded-full transition-all ${
            currentFeedback === "won"
              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
              : "bg-slate-800/60 text-slate-400 hover:bg-amber-500/10 hover:text-amber-300"
          }`}
        >
          <Star className="w-3 h-3" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => handleFeedback("good")}
        disabled={submitting}
        className={`flex items-center gap-2 ${sizeClasses[size]} rounded-lg font-medium transition-all ${
          currentFeedback === "good"
            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
            : "bg-slate-800/60 text-slate-300 hover:bg-emerald-500/10 hover:text-emerald-300 border border-slate-800"
        }`}
      >
        <ThumbsUp className="w-4 h-4" />
        Good fit
      </motion.button>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => handleFeedback("bad")}
        disabled={submitting}
        className={`flex items-center gap-2 ${sizeClasses[size]} rounded-lg font-medium transition-all ${
          currentFeedback === "bad"
            ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
            : "bg-slate-800/60 text-slate-300 hover:bg-rose-500/10 hover:text-rose-300 border border-slate-800"
        }`}
      >
        <ThumbsDown className="w-4 h-4" />
        Not relevant
      </motion.button>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => handleFeedback("won")}
        disabled={submitting}
        className={`flex items-center gap-2 ${sizeClasses[size]} rounded-lg font-medium transition-all ${
          currentFeedback === "won"
            ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
            : "bg-slate-800/60 text-slate-300 hover:bg-amber-500/10 hover:text-amber-300 border border-slate-800"
        }`}
      >
        <Star className="w-4 h-4" />
        Customer
      </motion.button>
    </div>
  );
}


"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Circle, ExternalLink } from "lucide-react";
import { apiClient } from "@/lib/api";
import Link from "next/link";

interface ChecklistItem {
  id: string;
  label: string;
  completed: boolean;
  actionUrl?: string;
}

export function OnboardingChecklist() {
  const [items, setItems] = useState<ChecklistItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadChecklist();
  }, []);

  const loadChecklist = async () => {
    try {
      setLoading(true);
      
      // Check each step
      const leads = await apiClient.getLeads();
      const hasLeads = leads.length > 0;
      
      // Check if any email has been verified
      const hasVerifiedEmail = leads.some(lead => 
        lead.emails && lead.emails.length > 0
      );
      
      // Check if extension has been used (LinkedIn leads exist)
      const linkedinLeads = leads.filter(lead => lead.source === "linkedin_extension");
      const hasExtensionUsed = linkedinLeads.length > 0;
      
      // Check if first LinkedIn lead captured
      const hasFirstLinkedInLead = linkedinLeads.length > 0;
      
      setItems([
        {
          id: "upload_csv",
          label: "Upload a CSV or add your first lead",
          completed: hasLeads,
          actionUrl: "/leads",
        },
        {
          id: "verify_email",
          label: "Verify at least one email",
          completed: hasVerifiedEmail,
          actionUrl: "/verification",
        },
        {
          id: "install_extension",
          label: "Install the LinkedIn Email Finder extension",
          completed: hasExtensionUsed, // Assume installed if used
          actionUrl: "/email-finder",
        },
        {
          id: "capture_lead",
          label: "Capture your first LinkedIn lead",
          completed: hasFirstLinkedInLead,
          actionUrl: "/email-finder",
        },
      ]);
    } catch (error) {
      console.error("Failed to load checklist:", error);
    } finally {
      setLoading(false);
    }
  };

  const completedCount = items.filter(item => item.completed).length;
  const allCompleted = completedCount === items.length && items.length > 0;

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 px-5 py-5 h-56 animate-pulse" />
    );
  }

  if (allCompleted) {
    return null; // Hide checklist when all completed
  }

  return (
    <motion.div
      className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 px-5 py-5 shadow-sm"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-50">Getting Started</h3>
        <span className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-950/30 px-2.5 py-1 rounded-full">
          {completedCount} / {items.length} completed
        </span>
      </div>

      <div className="space-y-3">
        {items.map((item, index) => (
          <motion.div
            key={item.id}
            className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            {item.completed ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-500 dark:text-emerald-400 flex-shrink-0" />
            ) : (
              <Circle className="w-5 h-5 text-slate-400 dark:text-slate-600 flex-shrink-0" />
            )}
            <span
              className={`text-sm flex-1 font-medium ${
                item.completed 
                  ? "text-slate-500 dark:text-slate-500 line-through" 
                  : "text-slate-700 dark:text-slate-200"
              }`}
            >
              {item.label}
            </span>
            {!item.completed && item.actionUrl && (
              <Link
                href={item.actionUrl}
                className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 inline-flex items-center gap-1 transition-colors"
              >
                <span>Go</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}


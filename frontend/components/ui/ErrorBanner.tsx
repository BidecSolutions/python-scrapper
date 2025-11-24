"use client";

import { motion } from "framer-motion";
import { AlertCircle, RefreshCw, ExternalLink, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

interface ErrorBannerProps {
  title: string;
  message: string;
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: "primary" | "secondary";
  }>;
  onDismiss?: () => void;
  type?: "error" | "warning";
}

export function ErrorBanner({
  title,
  message,
  actions = [],
  onDismiss,
  type = "error",
}: ErrorBannerProps) {
  const router = useRouter();

  const defaultActions = [
    {
      label: "Open Integrations",
      onClick: () => router.push("/settings"),
      variant: "primary" as const,
    },
    {
      label: "Retry",
      onClick: () => window.location.reload(),
      variant: "secondary" as const,
    },
  ];

  const allActions = actions.length > 0 ? actions : defaultActions;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`rounded-xl border p-4 ${
        type === "error"
          ? "border-rose-500/30 bg-rose-500/10"
          : "border-amber-500/30 bg-amber-500/10"
      }`}
    >
      <div className="flex items-start gap-3">
        <AlertCircle
          className={`w-5 h-5 mt-0.5 ${
            type === "error" ? "text-rose-400" : "text-amber-400"
          }`}
        />
        <div className="flex-1">
          <h3
            className={`text-sm font-semibold mb-1 ${
              type === "error" ? "text-rose-300" : "text-amber-300"
            }`}
          >
            {title}
          </h3>
          <p
            className={`text-sm ${
              type === "error" ? "text-rose-200/80" : "text-amber-200/80"
            }`}
          >
            {message}
          </p>
          {allActions.length > 0 && (
            <div className="flex items-center gap-2 mt-3">
              {allActions.map((action, idx) => (
                <Button
                  key={idx}
                  size="sm"
                  variant={action.variant === "primary" ? "default" : "outline"}
                  onClick={action.onClick}
                  className={
                    action.variant === "primary"
                      ? "bg-cyan-500 hover:bg-cyan-400 text-slate-950"
                      : ""
                  }
                >
                  {action.label}
                </Button>
              ))}
            </div>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-slate-400 hover:text-slate-300 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </motion.div>
  );
}


"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AICopilotProps {
  context?: string;
  suggestions?: string[];
  onSend?: (query: string) => Promise<string>;
  placeholder?: string;
}

export function AICopilot({
  context,
  suggestions = [],
  onSend,
  placeholder = "Ask AI about this job...",
}: AICopilotProps) {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleSend = async () => {
    if (!query.trim() || !onSend) return;

    setLoading(true);
    try {
      const result = await onSend(query);
      setResponse(result);
      setQuery("");
    } catch (error) {
      setResponse("Sorry, I couldn't process that request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-left hover:bg-slate-800/60 transition-colors group"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-emerald-500/20 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-50">Ask AI</p>
            <p className="text-xs text-slate-400 mt-0.5">
              Get insights about this job
            </p>
          </div>
          <Send className="w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition-colors" />
        </div>
      </button>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden"
    >
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-medium">AI Copilot</span>
        </div>
        <button
          onClick={() => {
            setExpanded(false);
            setResponse(null);
            setQuery("");
          }}
          className="text-slate-400 hover:text-slate-300 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Suggestions */}
        {suggestions.length > 0 && !response && (
          <div className="space-y-2">
            <p className="text-xs text-slate-400">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuery(suggestion)}
                  className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-800/60 text-slate-300 hover:bg-slate-800 hover:border-cyan-500/40 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Response */}
        {response && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-3 rounded-lg bg-slate-800/60 border border-slate-700"
          >
            <p className="text-sm text-slate-200 whitespace-pre-wrap">
              {response}
            </p>
          </motion.div>
        )}

        {/* Input */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={placeholder}
            className="flex-1 px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm"
            disabled={loading}
          />
          <Button
            onClick={handleSend}
            disabled={!query.trim() || loading}
            size="sm"
            className="bg-cyan-500 hover:bg-cyan-400 text-slate-950"
          >
            {loading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="w-4 h-4" />
              </motion.div>
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}


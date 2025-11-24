"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Briefcase, Users, Settings, Plus, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { apiClient, type Job } from "@/lib/api";

interface Command {
  id: string;
  label: string;
  icon: React.ElementType;
  action: () => void;
  category: string;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    if (open) {
      loadJobs();
    }
  }, [open]);

  const loadJobs = async () => {
    try {
      const data = await apiClient.getJobs();
      setJobs(data.slice(0, 10)); // Limit to recent 10
    } catch (error) {
      console.error("Failed to load jobs:", error);
    }
  };

  const commands: Command[] = [
    {
      id: "new-job",
      label: "Create new job",
      icon: Plus,
      action: () => {
        router.push("/jobs/new");
        onClose();
      },
      category: "Actions",
    },
    {
      id: "jobs",
      label: "Go to Jobs",
      icon: Briefcase,
      action: () => {
        router.push("/jobs");
        onClose();
      },
      category: "Navigation",
    },
    {
      id: "leads",
      label: "Go to Leads",
      icon: Users,
      action: () => {
        router.push("/leads");
        onClose();
      },
      category: "Navigation",
    },
    {
      id: "settings",
      label: "Go to Settings",
      icon: Settings,
      action: () => {
        router.push("/settings");
        onClose();
      },
      category: "Navigation",
    },
    ...jobs.map((job) => ({
      id: `job-${job.id}`,
      label: `${job.niche}${job.location ? ` - ${job.location}` : ""}`,
      icon: Briefcase,
      action: () => {
        router.push(`/jobs/${job.id}`);
        onClose();
      },
      category: "Recent Jobs",
    })),
  ];

  const filteredCommands = commands.filter((cmd) =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, selectedIndex, filteredCommands]);

  if (!open) return null;

  return (
    <AnimatePresence>
      <div
        className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
        onClick={onClose}
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
        />

        {/* Palette */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          transition={{ duration: 0.2 }}
          onClick={(e) => e.stopPropagation()}
          className="relative w-full max-w-2xl mx-4"
        >
          <div className="rounded-xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden">
            {/* Search Input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800">
              <Search className="w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Type a command or search..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
                className="flex-1 bg-transparent text-slate-50 placeholder:text-slate-500 focus:outline-none"
              />
              <kbd className="px-2 py-1 text-xs rounded bg-slate-800 text-slate-400 border border-slate-700">
                ESC
              </kbd>
            </div>

            {/* Results */}
            <div className="max-h-96 overflow-y-auto">
              {filteredCommands.length === 0 ? (
                <div className="px-4 py-8 text-center text-slate-400">
                  <p>No results found</p>
                </div>
              ) : (
                <div className="py-2">
                  {Object.entries(
                    filteredCommands.reduce((acc, cmd) => {
                      if (!acc[cmd.category]) acc[cmd.category] = [];
                      acc[cmd.category].push(cmd);
                      return acc;
                    }, {} as Record<string, Command[]>)
                  ).map(([category, cmds]) => (
                    <div key={category} className="mb-4">
                      <div className="px-4 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        {category}
                      </div>
                      {cmds.map((cmd, idx) => {
                        const globalIdx = filteredCommands.indexOf(cmd);
                        const Icon = cmd.icon;
                        const isSelected = globalIdx === selectedIndex;

                        return (
                          <button
                            key={cmd.id}
                            onClick={cmd.action}
                            className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                              isSelected
                                ? "bg-cyan-500/10 text-cyan-300"
                                : "text-slate-300 hover:bg-slate-800/60"
                            }`}
                          >
                            <Icon className="w-4 h-4" />
                            <span className="flex-1">{cmd.label}</span>
                            {isSelected && (
                              <ArrowRight className="w-4 h-4 text-cyan-400" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}


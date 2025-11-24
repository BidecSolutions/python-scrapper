"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Bot, Plus, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function RobotsPage() {
  const [robots, setRobots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    loadRobots();
  }, []);

  const loadRobots = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getRobots();
      setRobots(data);
    } catch (error) {
      console.error("Failed to load robots:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  const totalRuns = robots.reduce((sum, r) => sum + (r.runs_count || 0), 0);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-slate-950/90 backdrop-blur border-b border-slate-800">
          <div className="px-6 py-4 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
                Universal Robots
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                AI-powered web scrapers that extract custom data from any website.
              </p>
            </div>
            <Link href="/robots/new">
              <button className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 text-xs font-medium px-4 py-2 shadow-sm transition-colors">
                <Plus className="w-4 h-4 mr-1.5" />
                New Robot
              </button>
            </Link>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto px-6 pt-6 pb-10 space-y-4">
          <p className="text-[11px] text-slate-400">
            {robots.length} robots • {totalRuns} total runs this week
          </p>

          {robots.length === 0 ? (
            <section className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 text-xs text-slate-400 text-center">
              <Bot className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-100 mb-2 text-sm">No robots created yet</p>
              <p className="mb-4">
                Create your first AI-powered robot to extract custom data from websites
              </p>
              <Link href="/robots/new">
                <button className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 text-xs font-medium px-4 py-2 shadow-sm transition-colors">
                  <Plus className="w-4 h-4 mr-1.5" />
                  Create Robot
                </button>
              </Link>
            </section>
          ) : (
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {robots.map((robot, idx) => (
                <motion.article
                  key={robot.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  onClick={() => router.push(`/robots/${robot.id}`)}
                  className="rounded-2xl bg-slate-900/80 border border-slate-800 p-4 hover:border-cyan-400/60 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h2 className="text-sm font-semibold line-clamp-2 text-slate-100">
                      {robot.name}
                    </h2>
                    <button
                      className="text-[11px] text-slate-400 hover:text-slate-200"
                      onClick={(e) => {
                        e.stopPropagation();
                        // TODO: Add menu
                      }}
                    >
                      ⋮
                    </button>
                  </div>
                  {robot.description && (
                    <p className="text-[11px] text-slate-400 mb-4 line-clamp-2">
                      {robot.description}
                    </p>
                  )}
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span>{robot.runs_count || 0} runs</span>
                    <span>Created {new Date(robot.created_at).toLocaleDateString()}</span>
                  </div>
                  <button
                    className="mt-3 text-[11px] font-medium text-cyan-300 hover:text-cyan-200"
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/robots/${robot.id}`);
                    }}
                  >
                    ▶ View Robot
                  </button>
                </motion.article>
              ))}
            </section>
          )}
        </main>
      </div>
  );
}


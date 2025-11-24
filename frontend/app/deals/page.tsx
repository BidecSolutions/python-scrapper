"use client";

import { useEffect, useState } from "react";
import { apiClient, type SavedView } from "@/lib/api";
import type { Deal, DealStage } from "@/types/deals";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Plus, ChevronDown } from "lucide-react";
import { SavedViewsBar } from "@/components/saved-views/SavedViewsBar";

const STAGES: DealStage[] = [
  "new",
  "contacted",
  "qualified",
  "meeting_scheduled",
  "proposal",
  "won",
  "lost",
];

const STAGE_LABELS: Record<DealStage, string> = {
  new: "New",
  contacted: "Contacted",
  qualified: "Qualified",
  meeting_scheduled: "Meeting",
  proposal: "Proposal",
  won: "Won",
  lost: "Lost",
};

export default function DealsPipelinePage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [ownerFilter, setOwnerFilter] = useState<"all" | "mine">("all");
  const router = useRouter();

  async function load(customFilters?: Record<string, any>) {
    setLoading(true);
    try {
      // Load all deals without stage filter to show complete pipeline
      const res = await apiClient.getDeals({
        page_size: 1000,
        ...customFilters,
        // Don't filter by stage - we want all deals to show in their respective stages
      });
      setDeals(res.items);
    } catch (error) {
      console.error("Failed to load deals:", error);
    } finally {
      setLoading(false);
    }
  }

  const handleApplyView = (view: SavedView) => {
    if (view.filters.owner) {
      setOwnerFilter(view.filters.owner as "all" | "mine");
    }
    load(view.filters);
  };

  useEffect(() => {
    load();
  }, []);

  const dealsByStage = STAGES.reduce((acc, stage) => {
    acc[stage] = deals.filter((d) => d.stage === stage);
    return acc;
  }, {} as Record<DealStage, Deal[]>);

  async function handleStageChange(dealId: number, newStage: DealStage) {
    try {
      const updated = await apiClient.updateDeal(dealId, { stage: newStage });
      setDeals((prev) => prev.map((d) => (d.id === dealId ? updated : d)));
    } catch (err) {
      console.error("Error updating deal stage:", err);
    }
  }

  function formatCurrency(value: number | null | undefined, currency: string = "USD"): string {
    if (!value) return "—";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  function getDaysOpen(deal: Deal): number {
    const created = new Date(deal.created_at);
    const now = new Date();
    return Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-slate-950/90 backdrop-blur border-b border-slate-800">
          <div className="px-6 py-4 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
                Deals Pipeline
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Drag deals between stages to update progress.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative">
                <select
                  value={ownerFilter}
                  onChange={(e) => setOwnerFilter(e.target.value as "all" | "mine")}
                  className="appearance-none bg-slate-900 border border-slate-700 text-xs text-slate-200 px-4 py-2 pr-8 rounded-lg hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent cursor-pointer"
                >
                  <option value="all">All deals</option>
                  <option value="mine">My deals</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
              <button
                onClick={() => router.push("/deals/new")}
                className="inline-flex items-center rounded-lg bg-indigo-500 hover:bg-indigo-400 text-xs font-medium px-4 py-2 shadow-sm transition-colors"
              >
                <Plus className="w-4 h-4 mr-1.5" />
                New Deal
              </button>
            </div>
          </div>
        </header>

        {/* Columns */}
        <main className="flex-1 overflow-hidden px-6 pt-6 pb-10">
          {loading ? (
            <div className="text-center py-12 text-slate-400">
              Loading deals...
            </div>
          ) : (
            <div className="flex gap-4 overflow-x-auto pb-3 h-full no-scrollbar">
              {STAGES.map((stage) => {
                const stageDeals = dealsByStage[stage];
                const totalValue = stageDeals.reduce(
                  (sum, d) => sum + (d.value || 0),
                  0
                );

                return (
                  <motion.section
                    key={stage}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="flex-shrink-0 w-72 bg-slate-900/80 border border-slate-800 rounded-2xl p-3 flex flex-col h-fit"
                  >
                    {/* Column header */}
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <div>
                        <h2 className="text-sm font-semibold text-slate-100">
                          {STAGE_LABELS[stage]}
                        </h2>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {stageDeals.length} deal{stageDeals.length !== 1 ? "s" : ""}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] uppercase tracking-wide text-slate-400">
                          Total
                        </p>
                        <p className="text-xs font-semibold text-slate-100">
                          {totalValue > 0 ? formatCurrency(totalValue) : "—"}
                        </p>
                      </div>
                    </div>

                    {/* Deals list */}
                    <div className="mt-1 space-y-2 flex-1 min-h-[120px] max-h-[calc(100vh-280px)] overflow-y-auto no-scrollbar">
                      {stageDeals.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/60 text-[11px] text-slate-400 py-8 px-4">
                          <span>No deals</span>
                          <span className="mt-1 text-[10px]">
                            Drop deals here
                          </span>
                        </div>
                      ) : (
                        stageDeals.map((deal) => (
                          <motion.article
                            key={deal.id}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.2 }}
                            className="rounded-xl bg-slate-900 border border-slate-800 px-3 py-2.5 shadow-sm cursor-pointer hover:border-indigo-400 hover:bg-slate-900/90 transition-all duration-200 group"
                            onClick={() => router.push(`/deals/${deal.id}`)}
                          >
                            <div className="flex justify-between items-start gap-2 mb-1.5">
                              <h3 className="text-xs font-semibold text-slate-100 truncate flex-1 group-hover:text-indigo-300 transition-colors">
                                {deal.name}
                              </h3>
                              {deal.value && (
                                <span className="text-[11px] font-semibold text-emerald-300 whitespace-nowrap">
                                  {formatCurrency(deal.value, deal.currency)}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2">
                              <span>{getDaysOpen(deal)}d ago</span>
                              {deal.owner_user_id && (
                                <div className="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-[10px] font-medium text-indigo-300">
                                  {deal.owner_user_id % 10}
                                </div>
                              )}
                            </div>
                          </motion.article>
                        ))
                      )}
                    </div>
                  </motion.section>
                );
              })}
            </div>
          )}
        </main>
      </div>
  );
}

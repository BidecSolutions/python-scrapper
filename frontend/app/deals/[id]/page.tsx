"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import type { Deal, DealStage } from "@/types/deals";

const STAGE_LABELS: Record<DealStage, string> = {
  new: "New",
  contacted: "Contacted",
  qualified: "Qualified",
  meeting_scheduled: "Meeting Scheduled",
  proposal: "Proposal",
  won: "Won",
  lost: "Lost",
};

export default function DealDetailPage() {
  const params = useParams();
  const router = useRouter();
  const dealId = Number(params.id);
  const [deal, setDeal] = useState<Deal | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "timeline" | "tasks">("overview");

  async function load() {
    setLoading(true);
    try {
      const data = await apiClient.getDeal(dealId);
      setDeal(data);
    } catch (err) {
      console.error("Error loading deal:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (dealId) {
      load();
    }
  }, [dealId]);

  if (loading) {
    return <div className="p-6">Loading deal...</div>;
  }

  if (!deal) {
    return <div className="p-6">Deal not found</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{deal.name}</h1>
          <p className="text-sm text-gray-500 mt-1">
            Created {new Date(deal.created_at).toLocaleDateString()}
          </p>
        </div>
        <button
          onClick={() => router.push("/deals")}
          className="px-4 py-2 border rounded hover:bg-gray-50 text-sm"
        >
          Back to Pipeline
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-4">
          {(["overview", "timeline", "tasks"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 border-b-2 -mb-px transition-colors ${
                activeTab === tab
                  ? "border-blue-600 text-blue-600 font-medium"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Stage</label>
              <div className="mt-1">
                <span className="inline-flex px-3 py-1 rounded bg-blue-100 text-blue-800 text-sm">
                  {STAGE_LABELS[deal.stage as DealStage]}
                </span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Value</label>
              <div className="mt-1 text-lg font-semibold">
                {deal.value
                  ? new Intl.NumberFormat("en-US", {
                      style: "currency",
                      currency: deal.currency,
                    }).format(deal.value)
                  : "—"}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Expected Close Date</label>
              <div className="mt-1">
                {deal.expected_close_date
                  ? new Date(deal.expected_close_date).toLocaleDateString()
                  : "—"}
              </div>
            </div>

            {deal.lost_reason && (
              <div>
                <label className="text-sm font-medium text-gray-700">Lost Reason</label>
                <div className="mt-1 text-sm">{deal.lost_reason}</div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Owner</label>
              <div className="mt-1">
                {deal.owner_user_id ? `User #${deal.owner_user_id}` : "Unassigned"}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Company</label>
              <div className="mt-1">
                {deal.company_id ? `Company #${deal.company_id}` : "—"}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Primary Lead</label>
              <div className="mt-1">
                {deal.primary_lead_id ? (
                  <button
                    onClick={() => router.push(`/leads/${deal.primary_lead_id}`)}
                    className="text-blue-600 hover:underline"
                  >
                    Lead #{deal.primary_lead_id}
                  </button>
                ) : (
                  "—"
                )}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Source</label>
              <div className="mt-1 text-sm">
                {deal.source_campaign_id && `Campaign #${deal.source_campaign_id}`}
                {deal.source_segment_id && ` • Segment #${deal.source_segment_id}`}
                {!deal.source_campaign_id && !deal.source_segment_id && "Manual"}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "timeline" && (
        <div className="text-sm text-gray-500">
          Timeline view - Activity for this deal will appear here
        </div>
      )}

      {activeTab === "tasks" && (
        <div className="text-sm text-gray-500">
          Tasks & Notes - Tasks and notes for this deal will appear here
        </div>
      )}
    </div>
  );
}


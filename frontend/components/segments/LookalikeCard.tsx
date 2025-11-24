"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";

interface LookalikeCardProps {
  segmentId: number;
  positiveLeadCount?: number;
}

export function LookalikeCard({ segmentId, positiveLeadCount }: LookalikeCardProps) {
  const router = useRouter();
  const [creating, setCreating] = useState(false);

  async function handleCreateLookalike() {
    setCreating(true);
    try {
      const job = await apiClient.createLookalikeJob({
        source_segment_id: segmentId,
        min_score: 0.7,
        max_results: 1000,
      });
      router.push(`/lookalike/jobs/${job.id}`);
    } catch (err) {
      console.error("Error creating lookalike job:", err);
      alert("Failed to create lookalike job. Please try again.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="font-semibold text-sm">AI Lookalikes</h3>
          <p className="text-xs text-gray-500 mt-1">
            {positiveLeadCount
              ? `You have ${positiveLeadCount} high-quality examples here.`
              : "Find similar leads based on this segment"}
          </p>
        </div>
      </div>
      <button
        onClick={handleCreateLookalike}
        disabled={creating}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
      >
        {creating ? "Creating..." : "Find Lookalike Leads"}
      </button>
    </div>
  );
}


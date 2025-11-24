"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import type { LookalikeJobDetail, LookalikeCandidate } from "@/types/lookalike";

export default function LookalikeJobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = Number(params.id);
  const [job, setJob] = useState<LookalikeJobDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedCandidates, setSelectedCandidates] = useState<Set<number>>(new Set());

  async function load() {
    setLoading(true);
    try {
      const data = await apiClient.getLookalikeJob(jobId, 100, 0);
      setJob(data as any);
    } catch (err) {
      console.error("Error loading lookalike job:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (jobId) {
      load();
      // Poll if job is still running
      const interval = setInterval(() => {
        if (job?.status === "running" || job?.status === "pending") {
          load();
        }
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [jobId]);

  function handleSelectCandidate(candidateId: number) {
    setSelectedCandidates((prev) => {
      const next = new Set(prev);
      if (next.has(candidateId)) {
        next.delete(candidateId);
      } else {
        next.add(candidateId);
      }
      return next;
    });
  }

  function handleSelectAll() {
    if (!job) return;
    if (selectedCandidates.size === job.candidates.length) {
      setSelectedCandidates(new Set());
    } else {
      setSelectedCandidates(new Set(job.candidates.map((c) => c.id)));
    }
  }

  if (loading && !job) {
    return <div className="p-6">Loading lookalike job...</div>;
  }

  if (!job) {
    return <div className="p-6">Lookalike job not found</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Lookalike Results</h1>
          <p className="text-sm text-gray-500 mt-1">
            Found {job.candidates_found} similar leads from {job.positive_lead_count} examples
          </p>
        </div>
        <div className="flex items-center gap-3">
          {selectedCandidates.size > 0 && (
            <button
              onClick={() => {
                // TODO: Add to list/segment
                alert(`Add ${selectedCandidates.size} candidates to list (to be implemented)`);
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            >
              Add {selectedCandidates.size} to List
            </button>
          )}
          <button
            onClick={() => router.push("/lookalike/jobs")}
            className="px-4 py-2 border rounded hover:bg-gray-50 text-sm"
          >
            Back to Jobs
          </button>
        </div>
      </div>

      {/* Job Status */}
      <div className="border rounded-lg p-4 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Status</div>
            <div className="text-lg font-semibold mt-1">
              {job.status === "completed" && "✅ Completed"}
              {job.status === "running" && "⏳ Running..."}
              {job.status === "pending" && "⏳ Pending"}
              {job.status === "failed" && "❌ Failed"}
            </div>
          </div>
          <div className="text-sm text-gray-500">
            Created {new Date(job.created_at).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Candidates Table */}
      {job.status === "completed" && job.candidates.length > 0 && (
        <div className="border rounded-md overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={selectedCandidates.size === job.candidates.length}
                onChange={handleSelectAll}
                className="rounded"
              />
              <span className="text-sm font-medium">
                {selectedCandidates.size > 0
                  ? `${selectedCandidates.size} selected`
                  : "Select candidates"}
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Showing {job.candidates.length} of {job.candidates_found} candidates
            </div>
          </div>
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 w-12"></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Score</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Lead</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Why Similar</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {job.candidates.map((candidate) => (
                <tr key={candidate.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedCandidates.has(candidate.id)}
                      onChange={() => handleSelectCandidate(candidate.id)}
                      className="rounded"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="text-lg font-semibold">
                        {Math.round(candidate.score * 100)}
                      </div>
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-600"
                          style={{ width: `${candidate.score * 100}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {candidate.lead_id ? (
                      <button
                        onClick={() => router.push(`/leads/${candidate.lead_id}`)}
                        className="text-blue-600 hover:underline text-sm"
                      >
                        Lead #{candidate.lead_id}
                      </button>
                    ) : (
                      <span className="text-gray-400 text-sm">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {candidate.reason_vector ? (
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(candidate.reason_vector).map(([key, value]) => (
                          <span
                            key={key}
                            className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs"
                            title={`${key}: ${(value * 100).toFixed(0)}%`}
                          >
                            {key}: {Math.round(value * 100)}%
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400 text-sm">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {candidate.lead_id && (
                      <button
                        onClick={() => router.push(`/leads/${candidate.lead_id}`)}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        View Lead
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {job.status === "completed" && job.candidates.length === 0 && (
        <div className="border rounded-lg p-8 text-center text-gray-500">
          No lookalike candidates found. Try lowering the minimum similarity score.
        </div>
      )}

      {(job.status === "running" || job.status === "pending") && (
        <div className="border rounded-lg p-8 text-center">
          <div className="text-lg font-medium mb-2">Processing lookalike job...</div>
          <div className="text-sm text-gray-500">
            Finding similar leads based on your examples
          </div>
        </div>
      )}
    </div>
  );
}


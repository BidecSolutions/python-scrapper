"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { WorkspaceActivityItem, ActivityType } from "@/types/workspaceActivity";

type ActivityTypeFilter = ActivityType | "all";

export default function WorkspaceActivityPage() {
  const [items, setItems] = useState<WorkspaceActivityItem[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [total, setTotal] = useState(0);
  const [typeFilter, setTypeFilter] = useState<ActivityTypeFilter>("all");
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await apiClient.getWorkspaceActivity({
        page,
        page_size: pageSize,
        type: typeFilter !== "all" ? typeFilter : undefined,
      });
      setItems(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, typeFilter]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const typeOptions: ActivityTypeFilter[] = [
    "all",
    "lead_created",
    "lead_updated",
    "email_found",
    "email_verified",
    "lead_added_to_list",
    "lead_removed_from_list",
    "campaign_created",
    "campaign_sent",
    "campaign_event",
    "task_created",
    "task_completed",
    "note_added",
    "playbook_run",
    "playbook_completed",
    "list_created",
    "list_marked_campaign_ready",
    "job_created",
    "job_completed",
    "job_failed",
  ];

  function renderMeta(meta: any) {
    if (!meta) return "—";
    try {
      const keys = Object.keys(meta);
      if (keys.length === 0) return "—";
      const snippets = keys.slice(0, 2).map((k) => `${k}: ${String(meta[k])}`);
      return snippets.join(" · ");
    } catch {
      return "—";
    }
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Workspace Activity</h1>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as ActivityTypeFilter)}
          className="border rounded px-3 py-2 text-sm"
        >
          {typeOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt === "all" ? "All types" : opt}
            </option>
          ))}
        </select>
      </div>

      <div className="border rounded-md overflow-hidden">
        <table className="min-w-full text-xs">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Time</th>
              <th className="px-4 py-3 text-left font-medium">User</th>
              <th className="px-4 py-3 text-left font-medium">Type</th>
              <th className="px-4 py-3 text-left font-medium">Details</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                  No activity yet.
                </td>
              </tr>
            )}
            {!loading &&
              items.map((act) => (
                <tr key={act.id} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-3">
                    {new Date(act.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    {act.actor_user_id ? `User #${act.actor_user_id}` : "System"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex px-2 py-0.5 rounded bg-gray-100 text-xs">
                      {act.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{renderMeta(act.meta)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>
            Page {page} of {totalPages} • {total} events
          </span>
          <div className="space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="border rounded px-3 py-1 disabled:opacity-50 hover:bg-gray-50"
            >
              Prev
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="border rounded px-3 py-1 disabled:opacity-50 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


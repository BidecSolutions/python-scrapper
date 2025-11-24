export type StatusBadgeStatus = "pending" | "running" | "completed" | "failed" | "ai_pending" | "completed_with_warnings";

export function StatusBadge({ status }: { status: StatusBadgeStatus }) {
  const style: Record<StatusBadgeStatus, string> = {
    pending: "bg-slate-700 text-slate-100 border border-slate-600",
    running: "bg-amber-500/15 text-amber-300 border border-amber-400/60",
    completed: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/60",
    failed: "bg-rose-500/15 text-rose-300 border border-rose-400/60",
    ai_pending: "bg-blue-500/15 text-blue-300 border border-blue-400/60",
    completed_with_warnings: "bg-yellow-500/15 text-yellow-300 border border-yellow-400/60",
  };

  const label: Record<StatusBadgeStatus, string> = {
    pending: "Queued",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    ai_pending: "AI Processing",
    completed_with_warnings: "Completed (Warnings)",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${style[status] || style.pending}`}
    >
      {label[status] || "Unknown"}
    </span>
  );
}


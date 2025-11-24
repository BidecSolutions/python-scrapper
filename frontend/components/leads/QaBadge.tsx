"use client";

interface QaBadgeProps {
  status: string | null | undefined;
  reason?: string | null;
  showReason?: boolean;
}

export function QaBadge({ status, reason, showReason = false }: QaBadgeProps) {
  if (!status || status === "unknown") {
    return null;
  }

  if (status === "ok") {
    return (
      <span className="inline-flex items-center rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 px-1.5 py-0.5 text-[10px]">
        OK
      </span>
    );
  }

  if (status === "review") {
    return (
      <div className="inline-flex flex-col gap-1">
        <span className="inline-flex items-center rounded-full bg-amber-500/10 text-amber-200 border border-amber-500/30 px-1.5 py-0.5 text-[10px]">
          Review
        </span>
        {showReason && reason && (
          <span className="text-[10px] text-amber-300/80">{reason}</span>
        )}
      </div>
    );
  }

  if (status === "bad") {
    return (
      <div className="inline-flex flex-col gap-1">
        <span className="inline-flex items-center rounded-full bg-rose-500/10 text-rose-200 border border-rose-500/30 px-1.5 py-0.5 text-[10px]">
          Bad
        </span>
        {showReason && reason && (
          <span className="text-[10px] text-rose-300/80">{reason}</span>
        )}
      </div>
    );
  }

  return null;
}


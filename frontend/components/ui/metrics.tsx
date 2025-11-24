export function MetricCard({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string | number;
  tone?: "default" | "info" | "success" | "danger";
}) {
  const colors: Record<string, string> = {
    default: "text-slate-900 dark:text-slate-50",
    info: "text-cyan-600 dark:text-cyan-400",
    success: "text-emerald-600 dark:text-emerald-400",
    danger: "text-rose-600 dark:text-rose-400",
  };

  const bgColors: Record<string, string> = {
    default: "bg-white dark:bg-slate-900/80",
    info: "bg-cyan-50 dark:bg-cyan-950/20",
    success: "bg-emerald-50 dark:bg-emerald-950/20",
    danger: "bg-rose-50 dark:bg-rose-950/20",
  };

  const borderColors: Record<string, string> = {
    default: "border-slate-200 dark:border-slate-800",
    info: "border-cyan-200 dark:border-cyan-900/50",
    success: "border-emerald-200 dark:border-emerald-900/50",
    danger: "border-rose-200 dark:border-rose-900/50",
  };

  return (
    <div className={`rounded-xl ${bgColors[tone]} border ${borderColors[tone]} px-5 py-4 shadow-sm hover:shadow-md transition-shadow`}>
      <p className="text-[11px] text-slate-500 dark:text-slate-400 uppercase tracking-wide font-medium mb-2">{label}</p>
      <p className={`text-2xl font-bold ${colors[tone]}`}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
    </div>
  );
}


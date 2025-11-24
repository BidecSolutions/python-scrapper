"use client";

interface LeadTechCardProps {
  tech_stack?: {
    cms?: string;
    tools?: string[];
    notes?: string;
  } | null;
  digital_maturity?: number | null;
}

export function LeadTechCard({ tech_stack, digital_maturity }: LeadTechCardProps) {
  if (!tech_stack || !tech_stack.cms) {
    return null;
  }

  const tools = tech_stack.tools || [];
  const maturity = digital_maturity !== null ? Math.round(digital_maturity) : null;

  const getMaturityColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-cyan-400";
    if (score >= 40) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/50 p-3">
      <h4 className="text-xs font-semibold text-slate-200 mb-2">Tech & Digital Maturity</h4>
      
      <div className="flex items-center justify-between text-xs text-slate-300 mb-2">
        <span>CMS: <span className="text-slate-100">{tech_stack.cms}</span></span>
        {maturity !== null && (
          <span className={`flex items-center gap-1 font-medium ${getMaturityColor(maturity)}`}>
            <span>Maturity</span>
            <span className="inline-flex items-center rounded-full bg-slate-800 px-2 py-0.5">
              {maturity}/100
            </span>
          </span>
        )}
      </div>

      {tools.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {tools.map((tool) => (
            <span
              key={tool}
              className="inline-flex items-center rounded-full bg-slate-800/80 px-2 py-0.5 text-[10px] text-slate-200"
            >
              {tool}
            </span>
          ))}
        </div>
      )}

      {tech_stack.notes && (
        <p className="mt-2 text-[11px] text-slate-400">{tech_stack.notes}</p>
      )}
    </div>
  );
}


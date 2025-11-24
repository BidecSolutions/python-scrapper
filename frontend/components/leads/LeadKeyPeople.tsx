"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Users, Linkedin, ExternalLink, Sparkles, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Section } from "./LeadDetailPanel";

type Person = {
  id: number;
  name: string;
  title?: string;
  decision_maker_score?: number;
  decision_maker_role?: string;
  reason?: string;
  linkedin_url?: string;
  profile_url?: string;
};

export function LeadKeyPeople({ leadId }: { leadId: number }) {
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        const result = await apiClient.getKeyPeople(leadId);
        if (!cancelled) {
          setPeople(result.people || []);
          setError(null);
        }
      } catch (e: any) {
        if (!cancelled) {
          if (e?.response?.status !== 404) {
            console.error("Failed to load key people:", e);
          }
          setError("No key people found yet");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [leadId]);

  return (
    <Section title="Key People (AI)">
      {loading && (
        <div className="flex items-center gap-2 text-slate-400">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span className="text-[11px]">Finding decision makers from LinkedIn and other sources…</span>
        </div>
      )}

      {!loading && error && (
        <p className="text-[11px] text-slate-500">
          No key people found yet. Connect LinkedIn or add company socials to unlock this.
        </p>
      )}

      {!loading && !error && people.length === 0 && (
        <p className="text-[11px] text-slate-500">
          No key people identified yet. This will populate as AI discovers decision makers from web and social data.
        </p>
      )}

      {!loading && !error && people.length > 0 && (
        <ul className="space-y-2.5">
          {people.map((p) => (
            <motion.li
              key={p.id}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-start justify-between gap-3 p-2.5 rounded-lg bg-slate-900/50 border border-slate-800"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className="font-medium text-sm text-slate-100">{p.name}</div>
                  {p.decision_maker_role && (
                    <span className="inline-flex items-center rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] text-emerald-300 border border-emerald-500/30">
                      {p.decision_maker_role}
                    </span>
                  )}
                </div>
                {p.title && (
                  <div className="text-xs text-slate-400 mb-1">{p.title}</div>
                )}
                {p.reason && (
                  <div className="mt-1 text-[10px] text-slate-500">{p.reason}</div>
                )}
              </div>
              <div className="flex flex-col items-end gap-1.5 shrink-0">
                {typeof p.decision_maker_score === "number" && (
                  <span className="inline-flex items-center rounded-full bg-cyan-500/15 px-2 py-0.5 text-[10px] text-cyan-300 border border-cyan-500/30">
                    {Math.round(p.decision_maker_score * 100)} / 100
                  </span>
                )}
                {p.linkedin_url && (
                  <a
                    href={p.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[10px] text-cyan-300 hover:text-cyan-200 transition-colors"
                  >
                    <Linkedin className="w-3 h-3" />
                    LinkedIn
                  </a>
                )}
              </div>
            </motion.li>
          ))}
        </ul>
      )}
    </Section>
  );
}


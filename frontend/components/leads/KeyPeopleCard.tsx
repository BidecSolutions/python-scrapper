"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Users, Linkedin, ExternalLink, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface KeyPerson {
  id: number;
  name: string;
  title: string;
  decision_maker_score: number;
  decision_maker_role: string;
  linkedin_url?: string;
  profile_url?: string;
}

interface KeyPeopleCardProps {
  leadId: number;
}

export function KeyPeopleCard({ leadId }: KeyPeopleCardProps) {
  const [people, setPeople] = useState<KeyPerson[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadKeyPeople();
  }, [leadId]);

  const loadKeyPeople = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getKeyPeople(leadId, 5);
      setPeople(data.people || []);
    } catch (error) {
      console.error("Failed to load key people:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">Key People (AI)</h2>
          <Sparkles className="w-3 h-3 text-cyan-400" />
        </div>
        <p className="text-xs text-slate-400">Loading decision makers...</p>
      </div>
    );
  }

  if (people.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">Key People (AI)</h2>
          <Sparkles className="w-3 h-3 text-cyan-400" />
        </div>
        <p className="text-xs text-slate-400">
          No decision makers identified yet. Connect LinkedIn to discover key people.
        </p>
      </div>
    );
  }

  const getRoleColor = (role: string) => {
    if (role === "Primary") return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
    if (role === "Secondary") return "bg-cyan-500/20 text-cyan-300 border-cyan-500/40";
    return "bg-slate-500/20 text-slate-300 border-slate-500/40";
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Users className="w-4 h-4 text-cyan-400" />
        <h2 className="text-sm font-semibold text-slate-200">Key People (AI)</h2>
        <Sparkles className="w-3 h-3 text-cyan-400" />
        <span className="ml-auto text-[10px] text-slate-500">
          Suggested using graph AI
        </span>
      </div>
      <div className="space-y-2">
        {people.map((person) => (
          <motion.div
            key={person.id}
            className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-700/50"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-slate-100 truncate">
                  {person.name}
                </span>
                <Badge
                  variant="outline"
                  className={`text-[10px] px-1.5 py-0 ${getRoleColor(person.decision_maker_role)}`}
                >
                  {person.decision_maker_role}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 truncate">{person.title}</span>
                <span className="text-xs text-slate-500">
                  • {Math.round(person.decision_maker_score * 100)}% match
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1 ml-2">
              {person.linkedin_url && (
                <a
                  href={person.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-cyan-400 transition-colors"
                  title="View LinkedIn profile"
                >
                  <Linkedin className="w-4 h-4" />
                </a>
              )}
              {person.profile_url && (
                <a
                  href={person.profile_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-cyan-400 transition-colors"
                  title="View profile"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}


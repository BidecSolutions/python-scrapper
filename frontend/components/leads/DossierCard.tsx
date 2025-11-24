"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Sparkles, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { CopyButton } from "@/components/ui/CopyButton";

interface DossierCardProps {
  leadId: number;
  leadName?: string;
}

export function DossierCard({ leadId, leadName }: DossierCardProps) {
  const [dossier, setDossier] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    loadDossier();
  }, [leadId]);

  const loadDossier = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getDossier(leadId);
      // New API returns sections directly
      setDossier(data.sections || data.dossier);
    } catch (error: any) {
      if (error?.response?.status === 404) {
        // Dossier doesn't exist yet
        setDossier(null);
      } else {
        console.error("Failed to load dossier:", error);
      }
    } finally {
      setLoading(false);
    }
  };

  const generateDossier = async () => {
    try {
      setGenerating(true);
      const data = await apiClient.generateDossier(leadId);
      // Poll for completion if status is running
      if (data.status === "running") {
        // Poll until completed
        const pollInterval = setInterval(async () => {
          try {
            const updated = await apiClient.getDossier(leadId);
            if (updated.status === "completed") {
              clearInterval(pollInterval);
              setDossier(updated.sections);
              setGenerating(false);
            } else if (updated.status === "failed") {
              clearInterval(pollInterval);
              setGenerating(false);
              console.error("Dossier generation failed");
            }
          } catch (e) {
            clearInterval(pollInterval);
            setGenerating(false);
          }
        }, 2000);
        // Timeout after 60 seconds
        setTimeout(() => {
          clearInterval(pollInterval);
          setGenerating(false);
        }, 60000);
      } else {
        setDossier(data.sections || data.dossier);
        setGenerating(false);
      }
    } catch (error) {
      console.error("Failed to generate dossier:", error);
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">Deep AI Dossier</h2>
          <Sparkles className="w-3 h-3 text-cyan-400" />
        </div>
        <p className="text-xs text-slate-400">Loading dossier...</p>
      </div>
    );
  }

  if (!dossier) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">Deep AI Dossier</h2>
          <Sparkles className="w-3 h-3 text-cyan-400" />
        </div>
        <p className="text-xs text-slate-400 mb-3">
          Generate a comprehensive research dossier using multi-agent AI analysis.
        </p>
        <Button
          onClick={generateDossier}
          disabled={generating}
          className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
          size="sm"
        >
          {generating ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Generate Dossier
            </>
          )}
        </Button>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">Deep AI Dossier</h2>
          <Sparkles className="w-3 h-3 text-cyan-400" />
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200"
        >
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-4 text-sm"
          >
            {/* Overview */}
            {dossier.overview && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-1">Overview</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {dossier.overview}
                </p>
              </div>
            )}

            {/* Offer */}
            {dossier.offer && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-1">What They Offer</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {typeof dossier.offer === "string" ? dossier.offer : dossier.offer.join(", ")}
                </p>
              </div>
            )}

            {/* Audience */}
            {dossier.audience && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-1">Who They Serve</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {dossier.audience}
                </p>
              </div>
            )}

            {/* Digital Presence */}
            {dossier.digital_presence && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-1">Digital Presence</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {dossier.digital_presence}
                </p>
              </div>
            )}

            {/* Social Topics */}
            {dossier.social_topics && Array.isArray(dossier.social_topics) && dossier.social_topics.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-1">Social Topics</h3>
                <div className="flex flex-wrap gap-1">
                  {dossier.social_topics.map((topic: string, idx: number) => (
                    <span
                      key={idx}
                      className="inline-block px-2 py-0.5 rounded text-xs bg-purple-600/20 text-purple-200 border border-purple-400/40"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Risks */}
            {dossier.risks && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-1">Risks & Constraints</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {dossier.risks}
                </p>
              </div>
            )}

            {/* Angle */}
            {dossier.angle && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-1">How to Pitch Them</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {dossier.angle}
                </p>
              </div>
            )}

            {/* Sample Email */}
            {dossier.email && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-xs font-semibold text-slate-300">Sample Email</h3>
                  <CopyButton textToCopy={dossier.email} size="icon" className="h-6 w-6" />
                </div>
                <div className="p-2 rounded bg-slate-800/60 border border-slate-700">
                  <p className="text-xs text-slate-300 whitespace-pre-wrap">
                    {dossier.email}
                  </p>
                </div>
              </div>
            )}

            {/* Sample LinkedIn Message */}
            {dossier.linkedin_dm && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-xs font-semibold text-slate-300">Sample LinkedIn Message</h3>
                  <CopyButton
                    textToCopy={dossier.linkedin_dm}
                    size="icon"
                    className="h-6 w-6"
                  />
                </div>
                <div className="p-2 rounded bg-slate-800/60 border border-slate-700">
                  <p className="text-xs text-slate-300 whitespace-pre-wrap">
                    {dossier.linkedin_dm}
                  </p>
                </div>
              </div>
            )}
            
            {/* Fallback to legacy fields if sections not available */}
            {!dossier.overview && dossier.business_summary && (
              <>
                {dossier.business_summary && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-300 mb-1">Overview</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {dossier.business_summary}
                    </p>
                  </div>
                )}
                {dossier.offerings && dossier.offerings.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-300 mb-1">What They Offer</h3>
                    <ul className="list-disc list-inside text-xs text-slate-400 space-y-0.5">
                      {dossier.offerings.map((offering: string, idx: number) => (
                        <li key={idx}>{offering}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {dossier.target_audience && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-300 mb-1">Who They Serve</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {dossier.target_audience}
                    </p>
                  </div>
                )}
                {dossier.digital_maturity && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-300 mb-1">Digital Presence</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {dossier.digital_maturity}
                    </p>
                  </div>
                )}
                {dossier.suggested_outreach_angle && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-300 mb-1">How to Pitch Them</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {dossier.suggested_outreach_angle}
                    </p>
                  </div>
                )}
                {dossier.sample_email && (
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-xs font-semibold text-slate-300">Sample Email</h3>
                      <CopyButton textToCopy={dossier.sample_email} size="icon" className="h-6 w-6" />
                    </div>
                    <div className="p-2 rounded bg-slate-800/60 border border-slate-700">
                      <p className="text-xs text-slate-300 whitespace-pre-wrap">
                        {dossier.sample_email}
                      </p>
                    </div>
                  </div>
                )}
                {dossier.sample_linkedin_message && (
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-xs font-semibold text-slate-300">Sample LinkedIn Message</h3>
                      <CopyButton
                        textToCopy={dossier.sample_linkedin_message}
                        size="icon"
                        className="h-6 w-6"
                      />
                    </div>
                    <div className="p-2 rounded bg-slate-800/60 border border-slate-700">
                      <p className="text-xs text-slate-300 whitespace-pre-wrap">
                        {dossier.sample_linkedin_message}
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {!expanded && (
        <p className="text-xs text-slate-400 mt-2">
          Click to expand and view full dossier
        </p>
      )}

      <p className="text-[10px] text-slate-500 mt-3">
        Generated by multi-step AI research (web + social + tech analysis)
      </p>
    </div>
  );
}


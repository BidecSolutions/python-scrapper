"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Search, Sparkles, ExternalLink } from "lucide-react";
import { type Lead } from "@/lib/api";
import { SimilarLeadsModal } from "./SimilarLeadsModal";
import { LeadTechCard } from "./LeadTechCard";
import { QaBadge } from "./QaBadge";
import { FeedbackButtons } from "./FeedbackButtons";
import { DossierCard } from "./DossierCard";
import { LeadNextActionStrip } from "./LeadNextActionStrip";
import { LeadKeyPeople } from "./LeadKeyPeople";
import { LeadSocialInsights } from "./LeadSocialInsights";
import { LeadTechAndAdsCard } from "./LeadTechAndAdsCard";
import { LeadSimilarLeadsCard } from "./LeadSimilarLeadsCard";
import { LeadEmailsCard, type LeadEmail } from "./LeadEmailsCard";
import { HealthScoreBadge } from "./HealthScoreBadge";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";

interface LeadDetailPanelProps {
  open: boolean;
  onClose: () => void;
  lead: Lead | null;
}

export function LeadDetailPanel({
  open,
  onClose,
  lead,
}: LeadDetailPanelProps) {
  const router = useRouter();
  const [similarModalOpen, setSimilarModalOpen] = useState(false);
  const [leadEmails, setLeadEmails] = useState<LeadEmail[]>([]);
  const [loadingEmails, setLoadingEmails] = useState(false);
  const [creatingDeal, setCreatingDeal] = useState(false);
  
  // Load email records when lead changes
  useEffect(() => {
    if (lead?.id) {
      loadLeadEmails();
    }
  }, [lead?.id]);
  
  const loadLeadEmails = async () => {
    if (!lead?.id) return;
    
    try {
      setLoadingEmails(true);
      // For now, convert legacy emails array to LeadEmail format
      // TODO: Fetch from /api/leads/{id}/emails endpoint when available
      const emails: LeadEmail[] = (lead.emails || []).map((email, idx) => ({
        id: idx,
        email: typeof email === 'string' ? email : email.email || '',
        label: idx === 0 ? 'primary' : 'secondary',
      }));
      setLeadEmails(emails);
    } catch (error) {
      console.error("Failed to load lead emails:", error);
    } finally {
      setLoadingEmails(false);
    }
  };
  
  if (!lead) return null;
  
  // Extract domain from website
  const domain = lead.website 
    ? lead.website.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0]
    : undefined;
  
  // Extract contact name (use contact_person_name or name)
  const contactName = lead.contact_person_name || lead.name || undefined;

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            className="fixed inset-y-0 right-0 w-full max-w-md bg-slate-950 border-l border-slate-800 z-50 flex flex-col"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 260, damping: 26 }}
          >
            <header className="flex items-center justify-between px-4 py-3 border-b border-slate-800 shrink-0">
              <div className="flex-1">
                <p className="text-xs text-slate-500">Lead Detail</p>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-sm font-semibold">{lead.name || "Unknown business"}</p>
                  <HealthScoreBadge leadId={lead.id} size="sm" showDetails={true} />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSimilarModalOpen(true)}
                  className="inline-flex items-center gap-1 rounded-full border border-slate-700 px-2 py-1 text-[11px] text-slate-200 hover:border-cyan-500 hover:text-cyan-200 transition-colors"
                >
                  <Search className="w-3 h-3" />
                  Find similar
                </button>
                <button
                  onClick={onClose}
                  className="p-1 rounded-full hover:bg-slate-800 text-slate-400 hover:text-slate-100 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </header>

            <motion.div
              className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
              initial="hidden"
              animate="visible"
              variants={{
                hidden: { opacity: 0 },
                visible: {
                  opacity: 1,
                  transition: { staggerChildren: 0.06 },
                },
              }}
            >
              {/* LinkedIn Source Badge */}
              {lead.source === "linkedin_extension" && (
                <div className="rounded-xl border border-blue-500/40 bg-blue-500/10 px-3 py-2 text-[11px] text-blue-100">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold mb-1 flex items-center gap-1">
                        <span>in</span>
                        <span>Captured from LinkedIn</span>
                      </div>
                      {lead.social_links?.linkedin && (
                        <a
                          href={lead.social_links.linkedin}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-300 hover:text-blue-200 inline-flex items-center gap-1"
                        >
                          <span>Open profile</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* QA Status Alert */}
              {lead.qa_status && lead.qa_status !== "ok" && (
                <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100">
                  <div className="font-semibold mb-1">Needs review</div>
                  <div>{lead.qa_reason || "AI flagged this lead for manual check."}</div>
                </div>
              )}

              <Section title="Score & Quality">
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs py-0.5">
                    <span className="text-slate-500">Quality Score</span>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-semibold">
                        {Math.round(lead.quality_score || 0)} / 100
                      </span>
                      <QaBadge status={lead.qa_status} />
                    </div>
                  </div>
                  <div className="flex justify-between text-xs py-0.5">
                    <span className="text-slate-500">Quality Label</span>
                    <span className="text-slate-200 font-semibold uppercase">
                      {lead.quality_label || "low"}
                    </span>
                  </div>
                </div>
              </Section>

              {/* Feedback Buttons */}
              <Section title="Feedback">
                <FeedbackButtons
                  leadId={lead.id}
                  currentFeedback={lead.fit_label as "good" | "bad" | "won" | null}
                  variant="buttons"
                  size="sm"
                />
              </Section>

              <Section title="Contact Information">
                <Field label="Phone" value={lead.phones?.join(", ") || undefined} />
                <Field label="Address" value={lead.address || undefined} />
                <Field
                  label="Location"
                  value={
                    [lead.city, lead.country].filter(Boolean).join(", ") || undefined
                  }
                />
                <Field label="Website" value={lead.website || undefined} />
              </Section>

              {/* Email Records Card - New component */}
              <LeadEmailsCard
                leadId={lead.id}
                emails={leadEmails}
                contactName={contactName}
                domain={domain}
                onEmailAdded={loadLeadEmails}
              />

              {lead.metadata?.services && lead.metadata.services.length > 0 && (
                <Section title="Services (AI)">
                  <div className="flex flex-wrap gap-1">
                    {lead.metadata.services.map((service: string, idx: number) => (
                      <span
                        key={idx}
                        className="inline-block px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-200"
                      >
                        {service}
                      </span>
                    ))}
                  </div>
                </Section>
              )}

              {lead.metadata?.languages && lead.metadata.languages.length > 0 && (
                <Section title="Languages">
                  <div className="flex flex-wrap gap-1">
                    {lead.metadata.languages.map((lang: string, idx: number) => (
                      <span
                        key={idx}
                        className="inline-block px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-200"
                      >
                        {lang}
                      </span>
                    ))}
                  </div>
                </Section>
              )}

              {lead.social_links && Object.keys(lead.social_links).length > 0 && (
                <Section title="Social Links">
                  <div className="space-y-1">
                    {Object.entries(lead.social_links)
                      .filter(([_, url]) => url)
                      .map(([platform, url]) => (
                        <div key={platform} className="flex justify-between text-xs py-0.5">
                          <span className="text-slate-500 capitalize">{platform}</span>
                          <a
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-cyan-400 hover:text-cyan-300 truncate max-w-[200px]"
                          >
                            {url}
                          </a>
                        </div>
                      ))}
                  </div>
                </Section>
              )}

              {/* Tech Stack & Digital Maturity */}
              <LeadTechCard
                tech_stack={
                  typeof lead.tech_stack === "object" && lead.tech_stack !== null && !Array.isArray(lead.tech_stack)
                    ? lead.tech_stack
                    : undefined
                }
                digital_maturity={lead.digital_maturity}
              />

              {/* AI Features Section Header */}
              <div className="pt-2 pb-1 border-t border-slate-800">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                    AI-Powered Insights
                  </h3>
                </div>
              </div>

              {/* Next Best Action Strip - Show first as it's most actionable */}
              <LeadNextActionStrip leadId={lead.id} />

              {/* Score + QA summary */}
              <Section title="Score & Quality">
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs py-0.5">
                    <span className="text-slate-500">Quality Score</span>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-semibold">
                        {Math.round(lead.quality_score || 0)} / 100
                      </span>
                      <QaBadge status={lead.qa_status} />
                    </div>
                  </div>
                  {lead.smart_score !== null && lead.smart_score !== undefined && (
                    <div className="flex justify-between text-xs py-0.5">
                      <span className="text-slate-500">AI Smart Score</span>
                      <span className="text-cyan-300 font-semibold">
                        {Math.round(lead.smart_score * 100)} / 100
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between text-xs py-0.5">
                    <span className="text-slate-500">Quality Label</span>
                    <span className="text-slate-200 font-semibold uppercase">
                      {lead.quality_label || "low"}
                    </span>
                  </div>
                </div>
              </Section>

              {/* Key People (AI) - New component */}
              <LeadKeyPeople leadId={lead.id} />

              {/* Social Insights - New component */}
              <LeadSocialInsights leadId={lead.id} />

              {/* Tech & Ads - New component */}
              <LeadTechAndAdsCard leadId={lead.id} />

              {/* Deep AI Dossier */}
              <DossierCard leadId={lead.id} leadName={lead.name || undefined} />

              {/* Similar Leads / Lookalike - New component */}
              <LeadSimilarLeadsCard leadId={lead.id} />

              <Section title="AI Notes">
                <p className="text-sm text-slate-300">
                  {lead.metadata?.notes || "No notes generated yet."}
                </p>
              </Section>

              <Section title="Metadata">
                <div className="space-y-1 text-xs">
                  <Field label="Source" value={lead.source} />
                  <Field label="Niche" value={lead.niche || undefined} />
                  {lead.cms && <Field label="CMS" value={lead.cms} />}
                </div>
              </Section>
            </motion.div>
          </motion.div>

          {/* Similar Leads Modal */}
          <SimilarLeadsModal
            leadId={lead.id}
            open={similarModalOpen}
            onClose={() => setSimilarModalOpen(false)}
            onLeadClick={(leadId) => {
              setSimilarModalOpen(false);
              // Could navigate to that lead or refresh
            }}
          />
        </>
      )}
    </AnimatePresence>
  );
}

export function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <motion.section
      variants={{
        hidden: { opacity: 0, y: 4 },
        visible: { opacity: 1, y: 0 },
      }}
      className="border border-slate-800 rounded-xl px-3 py-2.5 bg-slate-900/60"
    >
      <h3 className="text-xs font-semibold text-slate-400 mb-2">{title}</h3>
      <div>{children}</div>
    </motion.section>
  );
}

function Field({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex justify-between text-xs py-0.5">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-200 truncate max-w-[180px] text-right">
        {value || "—"}
      </span>
    </div>
  );
}


"use client";

import { useState, useEffect } from "react";
import { CheckCircle2, XCircle, AlertCircle, Loader2, Search } from "lucide-react";
import { apiClient } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

export interface LeadEmail {
  id: number;
  email: string;
  label?: string;
  verify_status?: string;
  verify_reason?: string;
  verify_confidence?: number;
  verified_at?: string;
  found_via?: string;
}

interface LeadEmailsCardProps {
  leadId: number;
  emails: LeadEmail[];
  contactName?: string;
  domain?: string;
  onEmailAdded?: () => void;
}

export function LeadEmailsCard({
  leadId,
  emails: initialEmails,
  contactName,
  domain,
  onEmailAdded,
}: LeadEmailsCardProps) {
  const { showToast } = useToast();
  const [emails, setEmails] = useState<LeadEmail[]>(initialEmails || []);
  const [loadingId, setLoadingId] = useState<number | null>(null);
  const [finderLoading, setFinderLoading] = useState(false);

  useEffect(() => {
    setEmails(initialEmails || []);
  }, [initialEmails]);

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case "valid":
        return <CheckCircle2 className="w-3 h-3 text-green-500" />;
      case "invalid":
      case "syntax_error":
        return <XCircle className="w-3 h-3 text-red-500" />;
      case "risky":
        return <AlertCircle className="w-3 h-3 text-yellow-500" />;
      case "disposable":
      case "gibberish":
        return <XCircle className="w-3 h-3 text-orange-500" />;
      default:
        return <AlertCircle className="w-3 h-3 text-slate-500" />;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "valid":
        return "text-green-400 bg-green-500/10 border-green-500/20";
      case "invalid":
      case "syntax_error":
        return "text-red-400 bg-red-500/10 border-red-500/20";
      case "risky":
        return "text-yellow-400 bg-yellow-500/10 border-yellow-500/20";
      case "disposable":
      case "gibberish":
        return "text-orange-400 bg-orange-500/10 border-orange-500/20";
      default:
        return "text-slate-400 bg-slate-500/10 border-slate-500/20";
    }
  };

  async function handleVerify(emailId: number, email: string) {
    setLoadingId(emailId);
    try {
      const result = await apiClient.verifyEmailForLead(email, leadId);
      
      setEmails((prev) =>
        prev.map((item) =>
          item.id === emailId
            ? {
                ...item,
                verify_status: result.status,
                verify_reason: result.reason,
                verify_confidence: result.confidence,
                verified_at: new Date().toISOString(),
              }
            : item
        )
      );
      
      showToast({
        type: result.status === "valid" ? "success" : "info",
        title: `Email ${result.status}`,
        message: result.reason,
      });
    } catch (error: any) {
      console.error("Verify email error:", error);
      showToast({
        type: "error",
        title: "Verification failed",
        message: error?.response?.data?.detail || "Failed to verify email",
      });
    } finally {
      setLoadingId(null);
    }
  }

  async function handleFindEmail() {
    if (!contactName || !domain) {
      showToast({
        type: "error",
        title: "Missing information",
        message: "Contact name and domain are required to find email",
      });
      return;
    }

    const nameParts = contactName.trim().split(" ");
    const firstName = nameParts[0] || "";
    const lastName = nameParts.slice(1).join(" ") || "";

    if (!firstName) {
      showToast({
        type: "error",
        title: "Invalid name",
        message: "Please provide a valid contact name",
      });
      return;
    }

    setFinderLoading(true);
    try {
      const result = await apiClient.findEmailForLead(
        leadId,
        firstName,
        lastName,
        domain
      );

      if (result.email) {
        const newEmail: LeadEmail = {
          id: result.email_id || Date.now(),
          email: result.email,
          label: "primary",
          verify_status: result.status || undefined,
          verify_reason: result.reason || undefined,
          verify_confidence: result.confidence || undefined,
          verified_at: new Date().toISOString(),
          found_via: "finder",
        };

        setEmails((prev) => [...prev, newEmail]);
        
        showToast({
          type: "success",
          title: "Email found!",
          message: `Found: ${result.email} (${((result.confidence || 0) * 100).toFixed(0)}% confidence)`,
        });

        if (onEmailAdded) {
          onEmailAdded();
        }
      } else {
        showToast({
          type: "warning",
          title: "No email found",
          message: "Could not find a confident email address",
        });
      }
    } catch (error: any) {
      console.error("Find email error:", error);
      const errorMessage = error?.response?.data?.detail || "Failed to find email";
      
      if (error?.response?.status === 404) {
        showToast({
          type: "warning",
          title: "No email found",
          message: "Could not find a confident email address",
        });
      } else {
        showToast({
          type: "error",
          title: "Error",
          message: errorMessage,
        });
      }
    } finally {
      setFinderLoading(false);
    }
  }

  // Extract domain from website if domain prop not provided
  const emailDomain = domain || (emails.length > 0 && emails[0].email.includes("@") 
    ? emails[0].email.split("@")[1] 
    : undefined);

  return (
    <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
      <div className="mb-2 flex items-center justify-between">
        <h4 className="text-xs font-semibold text-slate-200">Emails</h4>
        {emails.length === 0 && contactName && emailDomain && (
          <button
            onClick={handleFindEmail}
            disabled={finderLoading}
            className="text-[11px] text-cyan-300 hover:text-cyan-200 disabled:opacity-50 flex items-center gap-1"
          >
            {finderLoading ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                Finding…
              </>
            ) : (
              <>
                <Search className="w-3 h-3" />
                Find email (AI)
              </>
            )}
          </button>
        )}
      </div>

      {emails.length === 0 && (
        <div className="space-y-2">
          <p className="text-[11px] text-slate-500">
            No emails on record.
          </p>
          {contactName && emailDomain && (
            <p className="text-[10px] text-slate-600">
              If we know their name and domain, you can try "Find email (AI)".
            </p>
          )}
        </div>
      )}

      {emails.length > 0 && (
        <ul className="space-y-1.5">
          {emails.map((e) => (
            <li
              key={e.id}
              className="flex items-start justify-between gap-2 rounded-lg bg-slate-900/50 px-2.5 py-2 border border-slate-800/50"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-slate-100 truncate">
                    {e.email}
                  </span>
                  {e.found_via === "finder" && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      AI Found
                    </span>
                  )}
                </div>
                
                {e.verify_status ? (
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium border ${getStatusColor(
                        e.verify_status
                      )}`}
                    >
                      {getStatusIcon(e.verify_status)}
                      <span className="capitalize">{e.verify_status}</span>
                      {e.verify_confidence != null && (
                        <span className="text-[9px] opacity-75">
                          {Math.round(e.verify_confidence * 100)}%
                        </span>
                      )}
                    </span>
                    {e.verify_reason && (
                      <span className="text-[9px] text-slate-500 truncate">
                        {e.verify_reason}
                      </span>
                    )}
                  </div>
                ) : (
                  <div className="text-[10px] text-slate-500">
                    Not verified yet
                  </div>
                )}
              </div>

              <button
                onClick={() => handleVerify(e.id, e.email)}
                disabled={loadingId === e.id}
                className="flex-shrink-0 rounded-full border border-cyan-500/60 px-2.5 py-1 text-[10px] text-cyan-200 hover:bg-cyan-500/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="Verify email address"
              >
                {loadingId === e.id ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  "Verify"
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      {emails.length > 0 && contactName && emailDomain && (
        <button
          onClick={handleFindEmail}
          disabled={finderLoading}
          className="mt-2 text-[11px] text-cyan-300 hover:text-cyan-200 disabled:opacity-50 flex items-center gap-1"
        >
          {finderLoading ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin" />
              Finding…
            </>
          ) : (
            <>
              <Search className="w-3 h-3" />
              Try alternate email (AI finder)
            </>
          )}
        </button>
      )}
    </div>
  );
}


"use client";

import { useState } from "react";
import { useToast } from "@/components/ui/Toast";
import { apiClient } from "@/lib/api";
import {
  Mail,
  Search,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Save,
  Download,
  ExternalLink,
} from "lucide-react";
import { motion } from "framer-motion";

type TabKey = "find" | "verify" | "bulk";

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] text-slate-300">{label}</span>
      {children}
    </label>
  );
}

function FindEmailCard({
  finderForm,
  setFinderForm,
  finderLoading,
  finderResult,
  handleFindEmail,
  getStatusIcon,
  getStatusColor,
  showToast,
}: any) {
  return (
    <section className="grid gap-5 md:grid-cols-[2fr,1fr]">
      {/* Form */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5">
        <h3 className="text-sm font-semibold mb-1 text-slate-100">Find Email Address</h3>
        <p className="text-[11px] text-slate-400 mb-4">
          Use first name, last name, and company domain. We'll try common patterns
          and optionally validate via SMTP.
        </p>

        <form
          className="space-y-3 text-xs"
          onSubmit={(e) => {
            e.preventDefault();
            handleFindEmail();
          }}
        >
          <div className="grid gap-3 md:grid-cols-3">
            <Field label="First Name">
              <input
                type="text"
                value={finderForm.firstName}
                onChange={(e) =>
                  setFinderForm({ ...finderForm, firstName: e.target.value })
                }
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-400 placeholder:text-slate-500"
                placeholder="John"
              />
            </Field>
            <Field label="Last Name">
              <input
                type="text"
                value={finderForm.lastName}
                onChange={(e) =>
                  setFinderForm({ ...finderForm, lastName: e.target.value })
                }
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-400 placeholder:text-slate-500"
                placeholder="Doe"
              />
            </Field>
            <Field label="Company Domain">
              <input
                type="text"
                value={finderForm.domain}
                onChange={(e) =>
                  setFinderForm({ ...finderForm, domain: e.target.value })
                }
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-400 placeholder:text-slate-500"
                placeholder="example.com"
              />
            </Field>
          </div>

          <label className="flex items-center gap-2 text-[11px] text-slate-300">
            <input
              type="checkbox"
              checked={finderForm.skipSmtp}
              onChange={(e) =>
                setFinderForm({ ...finderForm, skipSmtp: e.target.checked })
              }
              className="h-3 w-3 rounded border-slate-600 bg-slate-950 text-cyan-500 focus:ring-cyan-400"
            />
            Skip SMTP check{" "}
            <span className="text-slate-500">(faster but less accurate)</span>
          </label>

          <div className="pt-1">
            <button
              type="submit"
              disabled={finderLoading}
              className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-medium px-4 py-2 shadow-sm transition-colors"
            >
              {finderLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                  Finding...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-1.5" />
                  Find Email
                </>
              )}
            </button>
          </div>
        </form>

        {/* Results */}
        {finderResult && (
          <div className="mt-4 pt-4 border-t border-slate-800">
            {finderResult.email ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  {getStatusIcon(finderResult.status || "unknown")}
                  <div className="flex-1">
                    <div className="text-slate-100 font-medium text-sm">{finderResult.email}</div>
                    <div className="text-[11px] text-slate-400">
                      Confidence: {((finderResult.confidence || 0) * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
                <div
                  className={`px-3 py-2 rounded-lg border text-xs ${getStatusColor(
                    finderResult.status || "unknown"
                  )}`}
                >
                  <div className="font-medium capitalize">
                    {finderResult.status || "unknown"}
                  </div>
                  <div className="text-[11px] mt-1 opacity-80">{finderResult.reason || ""}</div>
                </div>
                <button
                  onClick={async () => {
                    try {
                      const result = await apiClient.saveEmailToLeads({
                        first_name: finderForm.firstName,
                        last_name: finderForm.lastName,
                        email: finderResult.email!,
                        domain: finderForm.domain,
                        confidence: finderResult.confidence || undefined,
                      });
                      showToast({
                        type: "success",
                        title: "Saved to leads",
                        message: `Lead created with ID: ${result.lead_id}`,
                      });
                    } catch (error: any) {
                      showToast({
                        type: "error",
                        title: "Error",
                        message: error?.response?.data?.detail || "Failed to save lead",
                      });
                    }
                  }}
                  className="inline-flex items-center rounded-lg bg-emerald-500 hover:bg-emerald-400 text-xs font-medium px-3 py-1.5 shadow-sm transition-colors"
                >
                  <Save className="w-4 h-4 mr-1.5" />
                  Save to Leads
                </button>
              </div>
            ) : (
              <div className="text-slate-400 text-xs">
                No confident email match found. Try adjusting the search or enabling SMTP
                verification.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tips / helper card */}
      <aside className="rounded-2xl bg-slate-900/60 border border-slate-800 p-4 text-[11px] space-y-3">
        <p className="text-xs font-semibold text-slate-100 mb-1">Tips for better matches</p>
        <ul className="space-y-2 text-slate-400">
          <li>• Use the company's primary domain (not tracking or subdomains).</li>
          <li>• Fill both first and last name for best pattern guesses.</li>
          <li>• Keep SMTP check enabled when quality matters more than speed.</li>
          <li>• Save successful results as templates for similar companies.</li>
        </ul>
      </aside>
    </section>
  );
}

function VerifyEmailPlaceholder({
  verifierEmail,
  setVerifierEmail,
  verifierLoading,
  verifierResult,
  handleVerifyEmail,
  getStatusIcon,
  getStatusColor,
}: any) {
  return (
    <section className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5">
      <h3 className="text-sm font-semibold mb-1 text-slate-100">Verify Email Address</h3>
      <p className="text-[11px] text-slate-400 mb-4">
        Check if an email address is valid, deliverable, and safe to send to.
      </p>

      <form
        className="space-y-3 text-xs"
        onSubmit={(e) => {
          e.preventDefault();
          handleVerifyEmail();
        }}
      >
        <Field label="Email Address">
          <input
            type="email"
            value={verifierEmail}
            onChange={(e) => setVerifierEmail(e.target.value)}
            className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-400 placeholder:text-slate-500"
            placeholder="john.doe@example.com"
          />
        </Field>

        <div className="pt-1">
          <button
            type="submit"
            disabled={verifierLoading}
            className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-medium px-4 py-2 shadow-sm transition-colors"
          >
            {verifierLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 mr-1.5" />
                Verify Email
              </>
            )}
          </button>
        </div>
      </form>

      {verifierResult && (
        <div className="mt-4 pt-4 border-t border-slate-800 space-y-3">
          <div className="flex items-center gap-3">
            {getStatusIcon(verifierResult.status)}
            <div>
              <div className="text-slate-100 font-medium text-sm">{verifierResult.email}</div>
              {verifierResult.cached && (
                <div className="text-[11px] text-slate-400">(Cached result)</div>
              )}
            </div>
          </div>
          <div
            className={`px-3 py-2 rounded-lg border text-xs ${getStatusColor(verifierResult.status)}`}
          >
            <div className="font-medium capitalize">{verifierResult.status}</div>
            <div className="text-[11px] mt-1 opacity-80">{verifierResult.reason}</div>
            {verifierResult.confidence !== null && (
              <div className="text-[11px] mt-1 opacity-80">
                Confidence: {(verifierResult.confidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function BulkVerifyPlaceholder({
  bulkEmails,
  setBulkEmails,
  bulkLoading,
  bulkResults,
  handleBulkVerify,
  getStatusIcon,
  getStatusColor,
  showToast,
}: any) {
  const emailCount = bulkEmails.split("\n").filter((e: string) => e.trim()).length;

  return (
    <section className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold mb-1 text-slate-100">Bulk Email Verification</h3>
          <p className="text-[11px] text-slate-400">
            Verify up to 100 email addresses at once (one per line).
          </p>
        </div>
        {bulkResults.length > 0 && (
          <button
            onClick={async () => {
              try {
                const response = await fetch(
                  `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002"}/api/email-verifier/export/csv`
                );
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `email_verifications_${new Date().toISOString().split("T")[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                showToast({
                  type: "success",
                  title: "Export successful",
                  message: "Verification results downloaded",
                });
              } catch (error: any) {
                showToast({
                  type: "error",
                  title: "Export failed",
                  message: "Failed to export results",
                });
              }
            }}
            className="inline-flex items-center rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium px-3 py-1.5 shadow-sm transition-colors"
          >
            <Download className="w-4 h-4 mr-1.5" />
            Export CSV
          </button>
        )}
      </div>

      <form
        className="space-y-3 text-xs"
        onSubmit={(e) => {
          e.preventDefault();
          handleBulkVerify();
        }}
      >
        <Field label={`Email Addresses (${emailCount} entered, max 100)`}>
          <textarea
            value={bulkEmails}
            onChange={(e) => setBulkEmails(e.target.value)}
            rows={10}
            className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-400 placeholder:text-slate-500 font-mono resize-none"
            placeholder="john.doe@example.com&#10;jane.smith@example.com&#10;..."
          />
        </Field>

        <div className="pt-1">
          <button
            type="submit"
            disabled={bulkLoading || emailCount === 0}
            className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-medium px-4 py-2 shadow-sm transition-colors"
          >
            {bulkLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 mr-1.5" />
                Verify All ({emailCount} emails)
              </>
            )}
          </button>
        </div>
      </form>

      {bulkResults.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <h4 className="text-xs font-semibold text-slate-100 mb-3">
            Results ({bulkResults.length})
          </h4>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {bulkResults.map((result: any, idx: number) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950"
              >
                <div className="flex items-center gap-3 flex-1">
                  {getStatusIcon(result.status)}
                  <div className="flex-1">
                    <div className="text-slate-100 font-medium text-xs">{result.email}</div>
                    <div className="text-[10px] text-slate-400">{result.reason}</div>
                  </div>
                </div>
                <div
                  className={`px-2 py-1 rounded text-[10px] font-medium ${getStatusColor(
                    result.status
                  )}`}
                >
                  {result.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default function EmailFinderPage() {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<TabKey>("find");

  // Finder state
  const [finderLoading, setFinderLoading] = useState(false);
  const [finderResult, setFinderResult] = useState<any>(null);
  const [finderForm, setFinderForm] = useState({
    firstName: "",
    lastName: "",
    domain: "",
    skipSmtp: false,
  });

  // Verifier state
  const [verifierLoading, setVerifierLoading] = useState(false);
  const [verifierResult, setVerifierResult] = useState<any>(null);
  const [verifierEmail, setVerifierEmail] = useState("");

  // Bulk state
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkEmails, setBulkEmails] = useState("");
  const [bulkResults, setBulkResults] = useState<any[]>([]);

  const handleFindEmail = async () => {
    if (!finderForm.firstName || !finderForm.lastName || !finderForm.domain) {
      showToast({
        type: "error",
        title: "Missing fields",
        message: "Please fill in first name, last name, and domain",
      });
      return;
    }

    setFinderLoading(true);
    setFinderResult(null);
    try {
      const result = await apiClient.findEmail(
        finderForm.firstName,
        finderForm.lastName,
        finderForm.domain,
        finderForm.skipSmtp
      );
      setFinderResult(result);
      if (result.email) {
        showToast({
          type: "success",
          title: "Email found!",
          message: `Found: ${result.email} (${((result.confidence || 0) * 100).toFixed(0)}% confidence)`,
        });
      } else {
        showToast({
          type: "info",
          title: "No email found",
          message: "Could not find a confident email match",
        });
      }
    } catch (error: any) {
      console.error("Failed to find email:", error);
      showToast({
        type: "error",
        title: "Error",
        message: error?.response?.data?.detail || "Failed to find email. Please try again.",
      });
    } finally {
      setFinderLoading(false);
    }
  };

  const handleVerifyEmail = async () => {
    if (!verifierEmail) {
      showToast({
        type: "error",
        title: "Missing email",
        message: "Please enter an email address",
      });
      return;
    }

    setVerifierLoading(true);
    setVerifierResult(null);
    try {
      const result = await apiClient.verifyEmail(verifierEmail);
      setVerifierResult(result);
      showToast({
        type: "success",
        title: "Verification complete",
        message: `Status: ${result.status} (${result.reason})`,
      });
    } catch (error: any) {
      console.error("Failed to verify email:", error);
      showToast({
        type: "error",
        title: "Error",
        message: error?.response?.data?.detail || "Failed to verify email. Please try again.",
      });
    } finally {
      setVerifierLoading(false);
    }
  };

  const handleBulkVerify = async () => {
    const emails = bulkEmails
      .split("\n")
      .map((e) => e.trim())
      .filter((e) => e.length > 0);

    if (emails.length === 0) {
      showToast({
        type: "error",
        title: "No emails",
        message: "Please enter at least one email address",
      });
      return;
    }

    if (emails.length > 100) {
      showToast({
        type: "error",
        title: "Too many emails",
        message: "Maximum 100 emails per request",
      });
      return;
    }

    setBulkLoading(true);
    setBulkResults([]);
    try {
      const result = await apiClient.verifyEmailsBulk(emails);
      setBulkResults(result.results);
      showToast({
        type: "success",
        title: "Bulk verification complete",
        message: `Verified ${result.total} emails`,
      });
    } catch (error: any) {
      console.error("Failed to verify emails:", error);
      showToast({
        type: "error",
        title: "Error",
        message: error?.response?.data?.detail || "Failed to verify emails. Please try again.",
      });
    } finally {
      setBulkLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "valid":
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case "invalid":
        return <XCircle className="w-5 h-5 text-rose-400" />;
      case "risky":
        return <AlertCircle className="w-5 h-5 text-amber-400" />;
      default:
        return <AlertCircle className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "valid":
        return "text-emerald-300 bg-emerald-500/15 border-emerald-400/60";
      case "invalid":
        return "text-rose-300 bg-rose-500/15 border-rose-400/60";
      case "risky":
        return "text-amber-300 bg-amber-500/15 border-amber-400/60";
      default:
        return "text-slate-400 bg-slate-500/15 border-slate-500/60";
    }
  };

  const handleDownloadExtension = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002"}/api/extension/download`
      );
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "leadflux-email-finder-extension.zip";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showToast({
        type: "success",
        title: "Extension downloaded",
        message: "Check the installation instructions below",
      });
    } catch (error: any) {
      showToast({
        type: "error",
        title: "Download failed",
        message: "Failed to download extension. Please try again.",
      });
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-slate-950/90 backdrop-blur border-b border-slate-800">
          <div className="px-6 py-4 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
                Email Finder & Verifier
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Find and verify email addresses using pattern matching and SMTP checks.
              </p>
            </div>

            <button
              onClick={handleDownloadExtension}
              className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 text-xs font-medium px-4 py-2 shadow-sm transition-colors"
            >
              <Download className="w-4 h-4 mr-1.5" />
              Download Chrome Extension
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto px-6 pt-6 pb-10 space-y-6">
          {/* LinkedIn Extension hero */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 px-6 py-5 flex flex-col md:flex-row md:items-start gap-5"
          >
            <div className="flex-shrink-0">
              <div className="h-12 w-12 rounded-2xl bg-cyan-500/15 border border-cyan-400/60 flex items-center justify-center">
                <span className="text-2xl font-semibold text-cyan-300">in</span>
              </div>
            </div>

            <div className="flex-1 space-y-2 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold text-slate-100">
                  LinkedIn Email Finder Extension
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-400/40">
                  Works on any LinkedIn profile
                </span>
              </div>

              <p className="text-xs text-slate-300 max-w-2xl">
                Install our Chrome extension to capture emails directly from LinkedIn
                profiles while you browse. Perfect for manual prospecting and quick
                research.
              </p>

              <div className="mt-3 grid gap-2 text-xs text-slate-200 md:grid-cols-2 lg:grid-cols-4">
                <div className="flex items-center gap-2">
                  <span className="text-cyan-400 text-sm font-semibold">①</span>
                  <span>Download and unzip the extension.</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-cyan-400 text-sm font-semibold">②</span>
                  <span>
                    Go to{" "}
                    <code className="px-1 bg-slate-900 rounded text-cyan-300">chrome://extensions</code>.
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-cyan-400 text-sm font-semibold">③</span>
                  <span>
                    Enable <strong>Developer mode</strong> and click <strong>Load unpacked</strong>.
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-cyan-400 text-sm font-semibold">④</span>
                  <span>Select the extension folder and start browsing LinkedIn.</span>
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-3 text-xs">
                <button
                  onClick={handleDownloadExtension}
                  className="inline-flex items-center rounded-lg bg-cyan-500 hover:bg-cyan-400 px-3 py-1.5 font-medium shadow-sm transition-colors"
                >
                  Download Extension ZIP
                </button>
                <a
                  href="chrome://extensions"
                  className="inline-flex items-center text-cyan-300 hover:text-cyan-200 underline underline-offset-4"
                >
                  Open Chrome Extensions Page →
                </a>
              </div>
            </div>
          </motion.section>

          {/* Tabs */}
          <nav className="flex items-center gap-6 border-b border-slate-800">
            {[
              { key: "find" as TabKey, label: "Find Email" },
              { key: "verify" as TabKey, label: "Verify Email" },
              { key: "bulk" as TabKey, label: "Bulk Verify" },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`py-2 text-xs font-medium border-b-2 -mb-px transition-colors ${
                  activeTab === tab.key
                    ? "border-cyan-400 text-slate-50"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          {/* Tab content */}
          {activeTab === "find" && (
            <FindEmailCard
              finderForm={finderForm}
              setFinderForm={setFinderForm}
              finderLoading={finderLoading}
              finderResult={finderResult}
              handleFindEmail={handleFindEmail}
              getStatusIcon={getStatusIcon}
              getStatusColor={getStatusColor}
              showToast={showToast}
            />
          )}
          {activeTab === "verify" && (
            <VerifyEmailPlaceholder
              verifierEmail={verifierEmail}
              setVerifierEmail={setVerifierEmail}
              verifierLoading={verifierLoading}
              verifierResult={verifierResult}
              handleVerifyEmail={handleVerifyEmail}
              getStatusIcon={getStatusIcon}
              getStatusColor={getStatusColor}
            />
          )}
          {activeTab === "bulk" && (
            <BulkVerifyPlaceholder
              bulkEmails={bulkEmails}
              setBulkEmails={setBulkEmails}
              bulkLoading={bulkLoading}
              bulkResults={bulkResults}
              handleBulkVerify={handleBulkVerify}
              getStatusIcon={getStatusIcon}
              getStatusColor={getStatusColor}
              showToast={showToast}
            />
          )}
        </main>
      </div>
  );
}

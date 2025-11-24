"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ui/Toast";
import {
  Search,
  MapPin,
  Database,
  Settings,
  Mail,
  Phone,
  Globe,
  Users,
  FileText,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowLeft,
} from "lucide-react";

export default function NewJobPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    niche: "",
    location: "",
    max_results: 20,
    max_pages_per_site: 5,
    sources: {
      google_search: true,
      google_places: false,
      web_search: false,
      crawling: true,
    },
    extract: {
      emails: true,
      phones: true,
      website_content: false,
      services: true,
      social_links: true,
      social_numbers: true,
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Build sources array from checkboxes
      const sources: string[] = [];
      if (formData.sources.google_search) sources.push("google_search");
      if (formData.sources.google_places) sources.push("google_places");
      if (formData.sources.web_search) sources.push("web_search");
      if (formData.sources.crawling) sources.push("crawling");
      
      const job = await apiClient.createJob({
        niche: formData.niche,
        location: formData.location || undefined,
        max_results: formData.max_results,
        max_pages_per_site: formData.max_pages_per_site,
        sources: sources.length > 0 ? sources : undefined,
        extract: formData.extract,
      });

      // Show success toast with action
      showToast({
        type: "success",
        title: `Job "${formData.niche}${formData.location ? ` - ${formData.location}` : ""}" created`,
        message: "View progress to see real-time updates",
        action: {
          label: "View progress →",
          onClick: () => router.push(`/jobs/${job.id}`),
        },
      });

      router.push(`/jobs/${job.id}`);
    } catch (error: any) {
      console.error("Failed to create job:", error);
      
      // Show actual error message
      let errorMessage = "Failed to create job. Please try again.";
      if (error?.response?.data?.detail) {
        errorMessage = `Failed to create job: ${error.response.data.detail}`;
      } else if (error?.message) {
        errorMessage = `Failed to create job: ${error.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-50 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Jobs
          </button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
              New Scrape Job
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Create a new lead scraping and enrichment job to discover and collect business information
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 pt-6 pb-10">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-400 px-4 py-3 flex items-start gap-3"
          >
            <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
            <div>
              <strong className="font-semibold">Error:</strong> {error}
            </div>
          </motion.div>
        )}

        <motion.form
          onSubmit={handleSubmit}
          className="space-y-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Basic Information */}
          <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-6 space-y-6">
            <div className="flex items-center gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
              <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/30">
                <Search className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Basic Information</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Define what you're looking for</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                  <Search className="w-4 h-4" />
                  Niche *
                </label>
                <input
                  type="text"
                  required
                  value={formData.niche}
                  onChange={(e) =>
                    setFormData({ ...formData, niche: e.target.value })
                  }
                  placeholder="e.g. dentist clinic, restaurant, hospital"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                  <MapPin className="w-4 h-4" />
                  Location
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) =>
                    setFormData({ ...formData, location: e.target.value })
                  }
                  placeholder="e.g. Karachi, London, Dubai"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Max Results
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="500"
                    value={formData.max_results}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        max_results: parseInt(e.target.value) || 20,
                      })
                    }
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Max Pages Per Site
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={formData.max_pages_per_site}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        max_pages_per_site: parseInt(e.target.value) || 5,
                      })
                    }
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Data Sources */}
          <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-6 space-y-6">
            <div className="flex items-center gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
              <div className="p-2 rounded-lg bg-cyan-50 dark:bg-cyan-950/30">
                <Database className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Data Sources</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Select which sources to use for finding leads</p>
              </div>
            </div>
            
            <div className="grid gap-3 md:grid-cols-2">
              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.sources.google_search}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      sources: { ...formData.sources, google_search: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Search className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Google Custom Search</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Search Google for business listings</p>
                </div>
              </label>

              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.sources.google_places}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      sources: { ...formData.sources, google_places: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Google Places</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 font-medium">API Key</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Requires Google Places API key</p>
                </div>
              </label>

              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.sources.web_search}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      sources: { ...formData.sources, web_search: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Web Search (Bing)</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 font-medium">API Key</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Requires Bing Search API key</p>
                </div>
              </label>

              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.sources.crawling}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      sources: { ...formData.sources, crawling: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Settings className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Website Crawling</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 font-medium">Enrichment</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Crawl websites for additional data</p>
                </div>
              </label>
            </div>
          </section>

          {/* Data Extraction */}
          <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-6 space-y-6">
            <div className="flex items-center gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
              <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-950/30">
                <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">What data to extract</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Choose what information to collect from websites</p>
              </div>
            </div>
            
            <div className="grid gap-3 md:grid-cols-2">
              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.extract.emails}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      extract: { ...formData.extract, emails: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Email addresses</span>
                  </div>
                </div>
              </label>

              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.extract.phones}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      extract: { ...formData.extract, phones: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Phone numbers</span>
                  </div>
                </div>
              </label>

              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.extract.services}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      extract: { ...formData.extract, services: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Services / Categories</span>
                  </div>
                </div>
              </label>

              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.extract.social_links}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      extract: { ...formData.extract, social_links: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Social media links</span>
                  </div>
                </div>
              </label>

              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.extract.social_numbers}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      extract: { ...formData.extract, social_numbers: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Contacts from social pages</span>
                  </div>
                </div>
              </label>

              <label className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={formData.extract.website_content}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      extract: { ...formData.extract, website_content: e.target.checked },
                    })
                  }
                  className="mt-0.5 w-5 h-5 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-2 cursor-pointer"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-50">Full website content</span>
                  </div>
                </div>
              </label>
            </div>
          </section>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <Button
              type="submit"
              disabled={loading}
              className="flex-1 bg-indigo-500 hover:bg-indigo-400 text-white shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating Job...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Create Job
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
              disabled={loading}
              className="px-6"
            >
              Cancel
            </Button>
          </div>
        </motion.form>
      </main>
    </div>
  );
}

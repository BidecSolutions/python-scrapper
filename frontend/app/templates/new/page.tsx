"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ui/Toast";
import {
  FileText,
  Mail,
  Tag,
  Globe,
  Lock,
  Loader2,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Type,
  AlignLeft,
} from "lucide-react";
import type { TemplateKind, TemplateScope } from "@/types/templates";

export default function NewTemplatePage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    kind: "email" as TemplateKind,
    subject: "",
    body: "",
    tags: [] as string[],
    scope: "workspace" as TemplateScope,
  });
  const [tagInput, setTagInput] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (!formData.name.trim()) {
      setError("Template name is required");
      setLoading(false);
      return;
    }

    if (formData.kind === "email" && !formData.body.trim()) {
      setError("Email body is required for email templates");
      setLoading(false);
      return;
    }

    try {
      const template = await apiClient.createTemplate({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        kind: formData.kind,
        subject: formData.subject.trim() || undefined,
        body: formData.body.trim() || undefined,
        tags: formData.tags.length > 0 ? formData.tags : undefined,
        scope: formData.scope,
      });

      showToast({
        type: "success",
        title: `Template "${formData.name}" created`,
        message: "Your template has been saved successfully",
        action: {
          label: "View Template →",
          onClick: () => router.push(`/templates/${template.id}`),
        },
      });

      router.push(`/templates/${template.id}`);
    } catch (error: any) {
      console.error("Failed to create template:", error);
      
      let errorMessage = "Failed to create template. Please try again.";
      if (error?.response?.data?.detail) {
        errorMessage = `Failed to create template: ${error.response.data.detail}`;
      } else if (error?.message) {
        errorMessage = `Failed to create template: ${error.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim().toLowerCase();
      if (!formData.tags.includes(newTag)) {
        setFormData({
          ...formData,
          tags: [...formData.tags, newTag],
        });
      }
      setTagInput("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter((tag) => tag !== tagToRemove),
    });
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
            Back to Templates
          </button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
              New Template
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Create a new email template for consistent messaging across your team
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
                <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Basic Information</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Template name and description</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                  <FileText className="w-4 h-4" />
                  Template Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder="e.g. Cold Outreach - SaaS Companies"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                  <AlignLeft className="w-4 h-4" />
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="Brief description of when and how to use this template..."
                  rows={3}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm resize-none"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                    <Type className="w-4 h-4" />
                    Template Type
                  </label>
                  <select
                    value={formData.kind}
                    onChange={(e) =>
                      setFormData({ ...formData, kind: e.target.value as TemplateKind })
                    }
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                  >
                    <option value="email">Email</option>
                    <option value="subject">Subject Line</option>
                    <option value="sequence_step">Sequence Step</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                    <Globe className="w-4 h-4" />
                    Scope
                  </label>
                  <select
                    value={formData.scope}
                    onChange={(e) =>
                      setFormData({ ...formData, scope: e.target.value as TemplateScope })
                    }
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                  >
                    <option value="workspace">Workspace</option>
                    <option value="global">Global</option>
                  </select>
                </div>
              </div>
            </div>
          </section>

          {/* Email Content */}
          {formData.kind === "email" && (
            <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-6 space-y-6">
              <div className="flex items-center gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
                <div className="p-2 rounded-lg bg-cyan-50 dark:bg-cyan-950/30">
                  <Mail className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Email Content</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Subject line and email body</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                    <Type className="w-4 h-4" />
                    Subject Line
                  </label>
                  <input
                    type="text"
                    value={formData.subject}
                    onChange={(e) =>
                      setFormData({ ...formData, subject: e.target.value })
                    }
                    placeholder="e.g. Quick question about [Company Name]"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                  />
                </div>

                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                    <AlignLeft className="w-4 h-4" />
                    Email Body *
                  </label>
                  <textarea
                    required
                    value={formData.body}
                    onChange={(e) =>
                      setFormData({ ...formData, body: e.target.value })
                    }
                    placeholder="Hi {{first_name}},\n\nI noticed that {{company_name}}...\n\nBest regards,\n{{sender_name}}"
                    rows={12}
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm font-mono resize-none"
                  />
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Use <code className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">{"{{variable_name}}"}</code> for dynamic content
                  </p>
                </div>
              </div>
            </section>
          )}

          {/* Tags */}
          <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-6 space-y-6">
            <div className="flex items-center gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
              <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-950/30">
                <Tag className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Tags</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Add tags to organize and find templates easily</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2 flex-wrap">
                {formData.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300 text-xs font-medium"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-indigo-900 dark:hover:text-indigo-100"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleAddTag}
                placeholder="Type a tag and press Enter..."
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
              />
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
                  Creating Template...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Create Template
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


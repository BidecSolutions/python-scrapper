"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/ui/Toast";
import { Bot, Sparkles, Loader2, ArrowLeft, Check } from "lucide-react";

export default function NewRobotPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"prompt" | "review" | "saving">("prompt");
  const [formData, setFormData] = useState({
    prompt: "",
    sample_url: "",
  });
  const [generatedRobot, setGeneratedRobot] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [robotName, setRobotName] = useState("");

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.prompt.trim()) {
      showToast({
        type: "error",
        title: "Prompt required",
        message: "Please enter a description of what you want to extract",
      });
      return;
    }

    setLoading(true);
    try {
      const result = await apiClient.createRobotFromPrompt(
        formData.prompt,
        formData.sample_url || undefined
      );
      setGeneratedRobot(result);
      setRobotName(result.name || "My Robot");
      setStep("review");
    } catch (error: any) {
      console.error("Failed to generate robot:", error);
      showToast({
        type: "error",
        title: "Generation failed",
        message: error?.response?.data?.detail || "Failed to generate robot. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!generatedRobot) return;

    setSaving(true);
    try {
      const robot = await apiClient.saveRobot({
        name: robotName,
        description: `AI-generated robot: ${formData.prompt}`,
        prompt: formData.prompt,
        sample_url: formData.sample_url || undefined,
        schema: generatedRobot.schema || [],
        workflow_spec: generatedRobot.workflow_spec || {},
      });

      showToast({
        type: "success",
        title: "Robot created!",
        message: `"${robotName}" has been saved successfully`,
        action: {
          label: "View Robot →",
          onClick: () => router.push(`/robots/${robot.id}`),
        },
      });

      router.push(`/robots/${robot.id}`);
    } catch (error: any) {
      console.error("Failed to save robot:", error);
      showToast({
        type: "error",
        title: "Save failed",
        message: error?.response?.data?.detail || "Failed to save robot. Please try again.",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
      <div className="space-y-6 max-w-4xl">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/robots">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">Create New Robot</h1>
            <p className="text-sm text-slate-400 mt-1">
              Describe what data you want to extract, and AI will generate a custom scraper
            </p>
          </div>
        </div>

        {step === "prompt" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-slate-800 bg-slate-900/60 p-6"
          >
            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-200 mb-2">
                  What do you want to extract?
                </label>
                <textarea
                  value={formData.prompt}
                  onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                  placeholder="Example: Extract product name, price, description, and image URL from e-commerce product pages"
                  className="w-full h-32 px-4 py-3 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 resize-none"
                  required
                />
                <p className="text-xs text-slate-500 mt-1.5">
                  Be specific about the fields you want to extract. AI will generate a schema and workflow.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-200 mb-2">
                  Sample URL (optional)
                </label>
                <input
                  type="url"
                  value={formData.sample_url}
                  onChange={(e) => setFormData({ ...formData, sample_url: e.target.value })}
                  placeholder="https://example.com/product-page"
                  className="w-full px-4 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
                <p className="text-xs text-slate-500 mt-1.5">
                  Provide a sample URL to help AI understand the page structure
                </p>
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 mt-2">
                  <p className="text-xs text-amber-300 font-medium mb-1">⚠️ Legal Notice</p>
                  <p className="text-xs text-amber-200/80">
                    Only scrape websites that explicitly allow automated access. 
                    Check their <code className="text-amber-300">robots.txt</code> and Terms of Service. 
                    Sites like YellowPages, LinkedIn, and many others explicitly forbid scraping.
                  </p>
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating robot...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate Robot
                  </>
                )}
              </Button>
            </form>
          </motion.div>
        )}

        {step === "review" && generatedRobot && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Bot className="w-5 h-5 text-cyan-400" />
                <h2 className="text-lg font-semibold">Review Generated Robot</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-200 mb-2">
                    Robot Name
                  </label>
                  <input
                    type="text"
                    value={robotName}
                    onChange={(e) => setRobotName(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="My Robot"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-200 mb-2">
                    Fields to Extract ({generatedRobot.schema?.length || 0} fields)
                  </label>
                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-4 max-h-64 overflow-y-auto">
                    {generatedRobot.schema && generatedRobot.schema.length > 0 ? (
                      <div className="space-y-2">
                        {generatedRobot.schema.map((field: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-2 rounded bg-slate-900"
                          >
                            <div>
                              <span className="text-sm font-medium text-slate-200">
                                {field.name || field.field}
                              </span>
                              {field.type && (
                                <span className="text-xs text-slate-500 ml-2">({field.type})</span>
                              )}
                            </div>
                            {field.selector && (
                              <code className="text-xs text-slate-400">{field.selector}</code>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-slate-500">No fields defined</p>
                    )}
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    onClick={() => setStep("prompt")}
                    variant="outline"
                    className="flex-1"
                  >
                    Back
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={saving || !robotName.trim()}
                    className="flex-1 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Check className="w-4 h-4 mr-2" />
                        Save Robot
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
  );
}


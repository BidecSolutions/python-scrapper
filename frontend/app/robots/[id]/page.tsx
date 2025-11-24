"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Bot, Sparkles, Play, Loader2, ArrowLeft, Settings, FileText } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useToast } from "@/components/ui/Toast";

export default function RobotDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  
  // Safely parse robot ID
  const robotIdParam = params?.id as string | undefined;
  const robotId = robotIdParam ? parseInt(robotIdParam, 10) : null;
  
  const [robot, setRobot] = useState<any>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [testUrl, setTestUrl] = useState("");
  const [testSearchQuery, setTestSearchQuery] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    if (robotId && !isNaN(robotId)) {
      loadRobot();
      loadRuns();
    } else {
      setLoading(false);
      showToast({
        type: "error",
        title: "Invalid Robot ID",
        message: "The robot ID is invalid or missing.",
      });
    }
  }, [robotId]);

  const loadRobot = async () => {
    if (!robotId || isNaN(robotId)) {
      return;
    }
    
    try {
      setLoading(true);
      const data = await apiClient.getRobot(robotId);
      setRobot(data);
    } catch (error: any) {
      console.error("Failed to load robot:", error);
      if (error?.response?.status === 404) {
        showToast({
          type: "error",
          title: "Robot Not Found",
          message: "The robot you're looking for doesn't exist.",
        });
        router.push("/robots");
      } else {
        showToast({
          type: "error",
          title: "Error",
          message: error?.response?.data?.detail || "Failed to load robot details",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const loadRuns = async () => {
    if (!robotId || isNaN(robotId)) {
      return;
    }
    
    try {
      const data = await apiClient.getRobotRuns(robotId);
      setRuns(data.runs || []);
    } catch (error) {
      console.error("Failed to load runs:", error);
    }
  };

  const handleTest = async () => {
    if (!testUrl.trim()) {
      showToast({
        type: "error",
        title: "URL required",
        message: "Please enter a URL to test",
      });
      return;
    }

    setTesting(true);
    setTestResult(null);
    try {
      const result = await apiClient.testRobot(robotId, testUrl, testSearchQuery || undefined);
      setTestResult(result);
      showToast({
        type: "success",
        title: "Test successful",
        message: "Robot extracted data successfully",
      });
    } catch (error: any) {
      console.error("Test failed:", error);
      showToast({
        type: "error",
        title: "Test failed",
        message: error?.response?.data?.detail || "Failed to test robot",
      });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!robot) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Robot not found</p>
        <Link href="/robots">
          <Button variant="outline" className="mt-4">
            Back to Robots
          </Button>
        </Link>
      </div>
    );
  }

  return (
      <div className="space-y-6 max-w-6xl">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/robots">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-cyan-400" />
              <h1 className="text-2xl font-semibold">{robot.name}</h1>
              <Sparkles className="w-4 h-4 text-cyan-400" />
            </div>
            {robot.description && (
              <p className="text-sm text-slate-400 mt-1">{robot.description}</p>
            )}
          </div>
        </div>

        {/* Test Robot Section */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Test Robot</h2>
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-1.5">
              <p className="text-xs text-amber-300">
                ⚠️ Only test on sites that allow scraping
              </p>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex gap-3">
              <input
                type="url"
                value={testUrl}
                onChange={(e) => setTestUrl(e.target.value)}
                placeholder="Enter URL to test..."
                className="flex-1 px-4 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
              <Button
                onClick={handleTest}
                disabled={testing || !testUrl.trim()}
                className="bg-cyan-500 hover:bg-cyan-400 text-slate-950"
              >
                {testing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Test
                  </>
                )}
              </Button>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Search Query (for interactive scraping)
              </label>
              <input
                type="text"
                value={testSearchQuery}
                onChange={(e) => setTestSearchQuery(e.target.value)}
                placeholder="e.g. 'orthopedic doctor' (required if robot uses search box)"
                className="w-full px-4 py-2 rounded-lg border border-slate-800 bg-slate-950 text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
              <p className="text-xs text-slate-500 mt-1">
                Only needed if the robot requires interaction (search box, form submission, etc.)
              </p>
            </div>
          </div>

          {testResult && (
            <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h3 className="text-sm font-semibold mb-2">Test Results:</h3>
              <pre className="text-xs text-slate-300 overflow-auto">
                {JSON.stringify(testResult.data || testResult, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Schema */}
        {robot.schema && robot.schema.length > 0 && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-5 h-5 text-slate-400" />
              <h2 className="text-lg font-semibold">Extraction Schema</h2>
            </div>
            <div className="space-y-2">
              {robot.schema.map((field: any, idx: number) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800"
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
          </div>
        )}

        {/* Recent Runs */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Runs</h2>
          {runs.length === 0 ? (
            <p className="text-sm text-slate-500">No runs yet. Test the robot or create a run to get started.</p>
          ) : (
            <div className="space-y-2">
              {runs.map((run) => (
                <Link
                  key={run.id}
                  href={`/robots/runs/${run.id}`}
                  className="block p-3 rounded-lg bg-slate-950 border border-slate-800 hover:bg-slate-900 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium">Run #{run.id}</div>
                      <div className="text-xs text-slate-500">
                        {new Date(run.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-xs text-slate-400">
                      {run.status} • {run.urls_processed || 0} URLs
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
  );
}


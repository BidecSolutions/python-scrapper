"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bookmark, BookmarkCheck, Pin, PinOff, Trash2, Edit2, Plus, X } from "lucide-react";
import { apiClient, type SavedView } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

interface SavedViewsBarProps {
  pageType: "leads" | "jobs" | "deals" | "verification";
  currentFilters: Record<string, any>;
  currentSortBy?: string;
  currentSortOrder?: string;
  onApplyView: (view: SavedView) => void;
}

export function SavedViewsBar({
  pageType,
  currentFilters,
  currentSortBy,
  currentSortOrder,
  onApplyView,
}: SavedViewsBarProps) {
  const { showToast } = useToast();
  const [views, setViews] = useState<SavedView[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [viewName, setViewName] = useState("");
  const [isPinned, setIsPinned] = useState(false);
  const [isShared, setIsShared] = useState(false);
  const [editingView, setEditingView] = useState<SavedView | null>(null);

  useEffect(() => {
    loadViews();
  }, [pageType]);

  const loadViews = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSavedViews(pageType);
      setViews(data);
    } catch (error) {
      console.error("Failed to load saved views:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveView = async () => {
    if (!viewName.trim()) {
      showToast({
        type: "error",
        title: "Name required",
        message: "Please enter a name for this view",
      });
      return;
    }

    try {
      if (editingView) {
        await apiClient.updateSavedView(editingView.id, {
          name: viewName.trim(),
          filters: currentFilters,
          sort_by: currentSortBy,
          sort_order: currentSortOrder,
          is_pinned: isPinned,
          is_shared: isShared,
        });
        showToast({
          type: "success",
          title: "View updated",
          message: `"${viewName}" has been updated`,
        });
      } else {
        await apiClient.createSavedView({
          name: viewName.trim(),
          page_type: pageType,
          filters: currentFilters,
          sort_by: currentSortBy,
          sort_order: currentSortOrder || "desc",
          is_pinned: isPinned,
          is_shared: isShared,
        });
        showToast({
          type: "success",
          title: "View saved",
          message: `"${viewName}" has been saved`,
        });
      }

      setShowSaveModal(false);
      setViewName("");
      setIsPinned(false);
      setIsShared(false);
      setEditingView(null);
      loadViews();
    } catch (error: any) {
      showToast({
        type: "error",
        title: "Failed to save view",
        message: error?.response?.data?.detail || "Please try again",
      });
    }
  };

  const handleApplyView = async (view: SavedView) => {
    try {
      await apiClient.useSavedView(view.id);
      onApplyView(view);
      loadViews(); // Refresh to update usage stats
    } catch (error) {
      console.error("Failed to track view usage:", error);
      // Still apply the view even if tracking fails
      onApplyView(view);
    }
  };

  const handleTogglePin = async (view: SavedView) => {
    try {
      await apiClient.updateSavedView(view.id, {
        is_pinned: !view.is_pinned,
      });
      loadViews();
    } catch (error: any) {
      showToast({
        type: "error",
        title: "Failed to update view",
        message: error?.response?.data?.detail || "Please try again",
      });
    }
  };

  const handleDeleteView = async (view: SavedView) => {
    if (!confirm(`Are you sure you want to delete "${view.name}"?`)) {
      return;
    }

    try {
      await apiClient.deleteSavedView(view.id);
      showToast({
        type: "success",
        title: "View deleted",
        message: `"${view.name}" has been deleted`,
      });
      loadViews();
    } catch (error: any) {
      showToast({
        type: "error",
        title: "Failed to delete view",
        message: error?.response?.data?.detail || "Please try again",
      });
    }
  };

  const handleEditView = (view: SavedView) => {
    setEditingView(view);
    setViewName(view.name);
    setIsPinned(view.is_pinned);
    setIsShared(view.is_shared);
    setShowSaveModal(true);
  };

  const pinnedViews = views.filter((v) => v.is_pinned);
  const unpinnedViews = views.filter((v) => !v.is_pinned);

  if (loading && views.length === 0) {
    return null;
  }

  return (
    <>
      <div className="flex items-center gap-2 flex-wrap">
        {pinnedViews.map((view) => (
          <ViewChip
            key={view.id}
            view={view}
            onApply={() => handleApplyView(view)}
            onTogglePin={() => handleTogglePin(view)}
            onDelete={() => handleDeleteView(view)}
            onEdit={() => handleEditView(view)}
          />
        ))}
        {unpinnedViews.map((view) => (
          <ViewChip
            key={view.id}
            view={view}
            onApply={() => handleApplyView(view)}
            onTogglePin={() => handleTogglePin(view)}
            onDelete={() => handleDeleteView(view)}
            onEdit={() => handleEditView(view)}
          />
        ))}
        <button
          onClick={() => {
            setEditingView(null);
            setViewName("");
            setIsPinned(false);
            setIsShared(false);
            setShowSaveModal(true);
          }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900/80 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Save view
        </button>
      </div>

      {/* Save View Modal */}
      <AnimatePresence>
        {showSaveModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 max-w-md w-full shadow-xl"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
                  {editingView ? "Edit View" : "Save Current View"}
                </h3>
                <button
                  onClick={() => {
                    setShowSaveModal(false);
                    setEditingView(null);
                    setViewName("");
                  }}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    View Name
                  </label>
                  <input
                    type="text"
                    value={viewName}
                    onChange={(e) => setViewName(e.target.value)}
                    placeholder="e.g., My hot LinkedIn leads"
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-cyan-400"
                    autoFocus
                  />
                </div>

                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isPinned}
                      onChange={(e) => setIsPinned(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 dark:border-slate-700 text-cyan-600 focus:ring-cyan-500"
                    />
                    <span className="text-xs text-slate-700 dark:text-slate-300">Pin to top</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isShared}
                      onChange={(e) => setIsShared(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 dark:border-slate-700 text-cyan-600 focus:ring-cyan-500"
                    />
                    <span className="text-xs text-slate-700 dark:text-slate-300">Share with team</span>
                  </label>
                </div>

                <div className="pt-2 flex gap-2">
                  <button
                    onClick={handleSaveView}
                    className="flex-1 inline-flex items-center justify-center rounded-lg bg-cyan-600 hover:bg-cyan-700 text-xs font-semibold px-4 py-2.5 text-white transition-colors"
                  >
                    {editingView ? "Update View" : "Save View"}
                  </button>
                  <button
                    onClick={() => {
                      setShowSaveModal(false);
                      setEditingView(null);
                      setViewName("");
                    }}
                    className="px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

function ViewChip({
  view,
  onApply,
  onTogglePin,
  onDelete,
  onEdit,
}: {
  view: SavedView;
  onApply: () => void;
  onTogglePin: () => void;
  onDelete: () => void;
  onEdit: () => void;
}) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="relative">
      <div className="inline-flex items-center gap-1">
        <button
          onClick={onApply}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900/80 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 hover:border-cyan-400 dark:hover:border-cyan-500 transition-colors"
        >
          {view.is_pinned && <Pin className="w-3.5 h-3.5 text-cyan-500" />}
          {view.is_shared && (
            <span className="text-[10px] text-slate-500 dark:text-slate-400">Team</span>
          )}
          <span>{view.name}</span>
          {view.usage_count > 0 && (
            <span className="text-[10px] text-slate-400 dark:text-slate-500">
              ({view.usage_count})
            </span>
          )}
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu(!showMenu);
          }}
          className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded"
        >
          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
          </svg>
        </button>
      </div>

      {showMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-0 top-full mt-1 z-20 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-lg p-1 min-w-[140px]">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onTogglePin();
                setShowMenu(false);
              }}
              className="w-full text-left px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded flex items-center gap-2"
            >
              {view.is_pinned ? (
                <>
                  <PinOff className="w-3.5 h-3.5" />
                  Unpin
                </>
              ) : (
                <>
                  <Pin className="w-3.5 h-3.5" />
                  Pin
                </>
              )}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
                setShowMenu(false);
              }}
              className="w-full text-left px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded flex items-center gap-2"
            >
              <Edit2 className="w-3.5 h-3.5" />
              Edit
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
                setShowMenu(false);
              }}
              className="w-full text-left px-3 py-1.5 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded flex items-center gap-2"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
}


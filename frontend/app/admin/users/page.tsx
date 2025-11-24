"use client";

import { useEffect, useState, useMemo } from "react";
import { apiClient } from "@/lib/api";
import type { AdminUser, UserStatus } from "@/types/adminUser";
import React from "react";
import { useAuth } from "@/contexts/AuthContext";
import { MetricCard } from "@/components/ui/metrics";
import { motion, AnimatePresence } from "framer-motion";

type StatusFilter = UserStatus | "all";

export default function AdminUsersPage() {
  const { user, isSuperAdmin, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [loading, setLoading] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const metrics = useMemo(() => {
    const active = users.filter((u) => u.status === "active").length;
    const pending = users.filter((u) => u.status === "pending").length;
    const suspended = users.filter((u) => u.status === "suspended").length;
    const superAdmins = users.filter((u) => u.is_super_admin).length;
    return { total: users.length, active, pending, suspended, superAdmins };
  }, [users]);

  async function load() {
    setLoading(true);
    setError(null);
    
    const token = localStorage.getItem("auth_token");
    if (!token) {
      setError("No authentication token found. Please log in again.");
      setLoading(false);
      return;
    }
    
    apiClient.setToken(token);
    
    try {
      const res = await apiClient.getAdminUsers({
        page,
        page_size: pageSize,
        q: q || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      });
      
      if (!res || typeof res !== 'object' || !Array.isArray(res.items)) {
        throw new Error(`Invalid response format`);
      }
      
      setUsers(res.items);
      setTotal(res.total);
    } catch (err: any) {
      console.error("Error loading users:", err);
      
      let errorMessage = "Failed to load users";
      
      if (err?.response) {
        const status = err.response.status;
        const detail = err.response.data?.detail || err.response.data?.message;
        
        if (status === 401) {
          errorMessage = "Authentication failed. Please log in again.";
        } else if (status === 403) {
          errorMessage = "Access denied. Super admin permissions required.";
        } else if (status === 404) {
          errorMessage = "Endpoint not found. Please check if the backend is running.";
        } else if (status >= 500) {
          errorMessage = "Server error. Please try again later.";
        } else {
          errorMessage = detail || `Error ${status}: Failed to load users`;
        }
      } else if (err?.request) {
        errorMessage = `Network error. Please check if the backend server is running on http://localhost:8000`;
      } else {
        errorMessage = err?.message || "Failed to load users";
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading && user && isSuperAdmin) {
      load();
    } else if (!authLoading && (!user || !isSuperAdmin)) {
      setError("You must be logged in as a super admin to access this page.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter, authLoading, user, isSuperAdmin]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  async function handleUpdate(
    id: number,
    patch: Partial<{
      status: UserStatus;
      can_use_advanced: boolean;
      is_super_admin: boolean;
    }>
  ) {
    setSavingId(id);
    setError(null);
    try {
      const updated = await apiClient.updateAdminUser(id, patch);
      setUsers((prev) => prev.map((u) => (u.id === id ? updated : u)));
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to update user");
      console.error("Error updating user:", err);
    } finally {
      setSavingId(null);
    }
  }

  const onSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    load();
  };

  function StatusBadge({ status }: { status: UserStatus }) {
    const styles: Record<UserStatus, string> = {
      active: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/60",
      pending: "bg-amber-500/15 text-amber-300 border border-amber-400/60",
      suspended: "bg-rose-500/15 text-rose-300 border border-rose-400/60",
    };
    
    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${styles[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
              Users (Super Admin)
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Manage user accounts, permissions, and access levels across all workspaces.
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center rounded-lg bg-indigo-500 hover:bg-indigo-400 text-xs font-medium px-4 py-2 shadow-sm text-white transition-colors"
          >
            + Create User
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 pt-6 pb-10 space-y-6">
        {error && (
          <div className="rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-400 px-4 py-3">
            <strong className="font-semibold">Error:</strong> {error}
          </div>
        )}

        {/* Metrics */}
        <section className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          <MetricCard label="Total Users" value={metrics.total} />
          <MetricCard label="Active" value={metrics.active} tone="success" />
          <MetricCard label="Pending" value={metrics.pending} tone="info" />
          <MetricCard label="Suspended" value={metrics.suspended} tone="danger" />
          <MetricCard label="Super Admins" value={metrics.superAdmins} tone="default" />
        </section>

        {/* Search & Filters */}
        <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-4">
          <form onSubmit={onSearchSubmit} className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
            <div className="flex-1 flex items-center gap-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2">
              <span className="text-slate-500 text-sm">🔍</span>
              <input
                type="text"
                placeholder="Search by email or name…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className="bg-transparent border-0 outline-none text-xs flex-1 placeholder:text-slate-500 dark:placeholder:text-slate-400 text-slate-900 dark:text-slate-50"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as StatusFilter);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All statuses</option>
              <option value="pending">Pending</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
            </select>
            <button
              type="submit"
              className="inline-flex items-center rounded-xl bg-indigo-500 hover:bg-indigo-400 text-xs font-medium px-4 py-2 shadow-sm text-white transition-colors"
            >
              Search
            </button>
          </form>
        </section>

        {/* Users Table */}
        <section className="rounded-2xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead className="bg-slate-50 dark:bg-slate-900">
                <tr className="text-slate-500 dark:text-slate-400">
                  <th className="px-4 py-3 text-left font-medium">User</th>
                  <th className="px-4 py-3 text-left font-medium">Status</th>
                  <th className="px-4 py-3 text-left font-medium">Advanced</th>
                  <th className="px-4 py-3 text-left font-medium">Super Admin</th>
                  <th className="px-4 py-3 text-left font-medium">Created</th>
                  <th className="px-4 py-3 text-left font-medium">Last login</th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {loading && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                      Loading users…
                    </td>
                  </tr>
                )}
                {!loading && users.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                      No users found.
                    </td>
                  </tr>
                )}
                {!loading &&
                  users.map((u) => (
                    <motion.tr
                      key={u.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-slate-50 dark:hover:bg-slate-900/70 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900 dark:text-slate-50">
                          {u.full_name || "—"}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                          {u.email}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={u.status} />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={u.can_use_advanced}
                          disabled={savingId === u.id}
                          onChange={(e) =>
                            handleUpdate(u.id, { can_use_advanced: e.target.checked })
                          }
                          className="cursor-pointer disabled:opacity-50 w-4 h-4 rounded border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={u.is_super_admin}
                          disabled={savingId === u.id}
                          onChange={(e) =>
                            handleUpdate(u.id, { is_super_admin: e.target.checked })
                          }
                          className="cursor-pointer disabled:opacity-50 w-4 h-4 rounded border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                        {u.last_login_at
                          ? new Date(u.last_login_at).toLocaleDateString()
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        {u.status !== "active" && (
                          <button
                            className="text-[11px] px-3 py-1 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-950/50 disabled:opacity-50 transition-colors"
                            disabled={savingId === u.id}
                            onClick={() => handleUpdate(u.id, { status: "active" })}
                          >
                            Approve
                          </button>
                        )}
                        {u.status === "active" && (
                          <button
                            className="text-[11px] px-3 py-1 rounded-lg border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-950/50 disabled:opacity-50 transition-colors"
                            disabled={savingId === u.id}
                            onClick={() => handleUpdate(u.id, { status: "suspended" })}
                          >
                            Suspend
                          </button>
                        )}
                        {u.status === "pending" && (
                          <button
                            className="text-[11px] px-3 py-1 rounded-lg border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-950/50 disabled:opacity-50 transition-colors"
                            disabled={savingId === u.id}
                            onClick={() => handleUpdate(u.id, { status: "suspended" })}
                          >
                            Reject
                          </button>
                        )}
                      </td>
                    </motion.tr>
                  ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-between items-center text-xs text-slate-600 dark:text-slate-400">
            <span>
              Page {page} of {totalPages} • {total} users
            </span>
            <div className="space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 disabled:opacity-50 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
              >
                Prev
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 disabled:opacity-50 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Create User Modal */}
        <AnimatePresence>
          {showCreateModal && (
            <CreateUserModal
              onClose={() => setShowCreateModal(false)}
              onSuccess={() => {
                setShowCreateModal(false);
                load();
              }}
            />
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

function CreateUserModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [canUseAdvanced, setCanUseAdvanced] = useState(false);
  const [status, setStatus] = useState<UserStatus>("pending");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await apiClient.createUser({
        email,
        password,
        full_name: fullName || undefined,
        is_super_admin: isSuperAdmin,
        can_use_advanced: canUseAdvanced,
        status,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to create user");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 max-w-md w-full shadow-xl"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Create User</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-sm text-rose-700 dark:text-rose-400">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Email *
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Password * (min 8 characters)
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Full Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as UserStatus)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            >
              <option value="pending">Pending</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isSuperAdmin}
                onChange={(e) => setIsSuperAdmin(e.target.checked)}
                className="rounded border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">Super Admin</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={canUseAdvanced}
                onChange={(e) => setCanUseAdvanced(e.target.checked)}
                className="rounded border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">Can Use Advanced Features</span>
            </label>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-400 disabled:opacity-50 text-sm font-medium transition-colors"
            >
              {loading ? "Creating..." : "Create User"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-sm font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

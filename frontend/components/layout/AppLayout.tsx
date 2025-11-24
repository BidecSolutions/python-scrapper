"use client";

import { ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  Users,
  Settings,
  Plus,
  BookOpen,
  Pencil,
  Bot,
  Mail,
  CheckCircle2,
  TrendingUp,
  FileText,
  Activity,
  Sparkles,
  GitMerge,
} from "lucide-react";
import { useOrganization } from "@/contexts/OrganizationContext";
import { NotificationsBell } from "./NotificationsBell";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { apiClient } from "@/lib/api";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { organization, loading: orgLoading } = useOrganization();
  const { user, isSuperAdmin, logout } = useAuth();
  const [usageStats, setUsageStats] = useState<{ used: number; limit: number } | null>(null);
  
  useEffect(() => {
    loadUsageStats();
  }, []);

  const loadUsageStats = async () => {
    try {
      const stats = await apiClient.getUsageStats();
      setUsageStats({
        used: stats.leads_used_this_month,
        limit: stats.leads_limit_per_month,
      });
    } catch (error) {
      console.error("Failed to load usage stats:", error);
      // Fallback to default values
      setUsageStats({ used: 0, limit: 1000 });
    }
  };
  
  const getActiveSection = (): "dashboard" | "jobs" | "leads" | "settings" => {
    if (pathname?.startsWith("/jobs")) return "jobs";
    if (pathname?.startsWith("/leads")) return "leads";
    if (pathname?.startsWith("/settings")) return "settings";
    return "dashboard";
  };

  const activeSection = getActiveSection();

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur">
        <div className="flex items-center gap-2 px-6 py-4 border-b border-slate-200 dark:border-slate-800">
          {organization?.logo_url ? (
            <img
              src={organization.logo_url.startsWith('http') 
                ? organization.logo_url 
                : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${organization.logo_url}`}
              alt={organization.name}
              className="h-9 w-9 rounded-[12px] object-cover border border-slate-300 dark:border-slate-700"
            />
          ) : (
            <div className="h-9 w-9 rounded-[12px] bg-gradient-to-r from-cyan-500 via-cyan-400 to-emerald-300 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <span className="text-white font-bold text-sm">LF</span>
            </div>
          )}
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
              {organization?.brand_name || "LeadFlux AI"}
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">
              {organization?.tagline || "Scrape • Enrich • Score"}
            </span>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <NavItem
            href="/dashboard"
            label="Dashboard"
            icon={LayoutDashboard}
            active={activeSection === "dashboard"}
          />
          <NavItem
            href="/jobs"
            label="Jobs"
            icon={Briefcase}
            active={activeSection === "jobs"}
          />
          <NavItem
            href="/leads"
            label="Leads"
            icon={Users}
            active={activeSection === "leads"}
          />
          <NavItem
            href="/duplicates"
            label="Duplicates"
            icon={GitMerge}
            active={pathname?.startsWith("/duplicates")}
          />
          <NavItem
            href="/deals"
            label="Deals"
            icon={TrendingUp}
            active={pathname?.startsWith("/deals")}
          />
          <NavItem
            href="/templates"
            label="Templates"
            icon={FileText}
            active={pathname?.startsWith("/templates")}
          />
          <NavItem
            href="/playbooks"
            label="Playbooks"
            icon={BookOpen}
            active={pathname?.startsWith("/playbooks")}
          />
          <NavItem
            href="/health"
            label="Health"
            icon={Activity}
            active={pathname?.startsWith("/health")}
          />
          <NavItem
            href="/lookalike/jobs"
            label="Lookalikes"
            icon={Sparkles}
            active={pathname?.startsWith("/lookalike")}
          />
          <NavItem
            href="/email-finder"
            label="Email Finder"
            icon={Mail}
            active={pathname?.startsWith("/email-finder")}
          />
          <NavItem
            href="/verification"
            label="Verification"
            icon={CheckCircle2}
            active={pathname?.startsWith("/verification")}
          />
          <NavItem
            href="/robots"
            label="Robots"
            icon={Bot}
            active={pathname?.startsWith("/robots")}
          />
          <NavItem
            href="/settings"
            label="Settings"
            icon={Settings}
            active={activeSection === "settings"}
          />
          {/* Admin section - only show if user is super admin */}
          {isSuperAdmin && (
            <>
              <div className="px-3 py-2 mt-4 mb-2">
                <p className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold">
                  Admin
                </p>
              </div>
              <NavItem
                href="/admin/users"
                label="Users"
                icon={Users}
                active={pathname?.startsWith("/admin/users")}
              />
              <NavItem
                href="/admin/activity"
                label="Activity"
                icon={Activity}
                active={pathname?.startsWith("/admin/activity")}
              />
              <NavItem
                href="/admin/health"
                label="System Health"
                icon={Activity}
                active={pathname?.startsWith("/admin/health")}
              />
            </>
          )}
        </nav>

        <div className="px-4 py-4 border-t border-slate-200 dark:border-slate-800">
          <Link href="/jobs/new" className="block">
            <Button 
              type="button"
              className="w-full bg-cyan-500 hover:bg-cyan-400 text-white dark:text-slate-950 font-semibold"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Scrape Job
            </Button>
          </Link>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center justify-between px-4 md:px-8 py-3 border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-950/70 backdrop-blur shrink-0">
          <div className="flex items-center gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Organization</p>
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {orgLoading ? "Loading..." : organization?.name || "Acme Growth Agency"}
              </p>
            </div>
            <Link href="/settings">
              <button
                className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800/60 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                title="Edit organization"
              >
                <Pencil className="w-3.5 h-3.5" />
              </button>
            </Link>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <NotificationsBell />
            {usageStats && <UsagePill used={usageStats.used} limit={usageStats.limit} />}
            {user && (
              <div className="flex items-center gap-2">
                <div className="text-xs text-slate-600 dark:text-slate-400">
                  {user.full_name || user.email}
                </div>
                <button
                  onClick={logout}
                  className="px-2 py-1 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                  title="Logout"
                >
                  Logout
                </button>
              </div>
            )}
            <div className="h-8 w-8 rounded-full bg-slate-300 dark:bg-slate-700" />
          </div>
        </header>

        {/* Animated main area */}
        <main className="flex-1 overflow-y-auto px-4 md:px-8 py-4 md:py-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="h-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

interface NavItemProps {
  href: string;
  label: string;
  icon: React.ElementType;
  active?: boolean;
}

function NavItem({ href, label, icon: Icon, active }: NavItemProps) {
  const router = useRouter();
  
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    router.push(href);
  };

  return (
    <a
      href={href}
      onClick={handleClick}
      className={cn(
        "block w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all cursor-pointer",
        "text-slate-700 dark:text-slate-300",
        "hover:bg-slate-100 dark:hover:bg-slate-800/70 hover:text-slate-900 dark:hover:text-slate-50",
        active && "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-50 shadow-sm shadow-cyan-500/20"
      )}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
      {active && (
        <motion.span
          className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-500 dark:bg-cyan-400"
          layoutId="activeIndicator"
          transition={{ type: "spring", stiffness: 380, damping: 30 }}
          style={{ boxShadow: "0 0 8px rgba(34,211,238,0.9)" }}
        />
      )}
    </a>
  );
}

interface UsagePillProps {
  used: number;
  limit: number;
}

function UsagePill({ used, limit }: UsagePillProps) {
  const pct = Math.min(100, Math.round((used / limit) * 100));

  return (
    <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
      <span>API</span>
      <div className="w-24 h-2.5 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500 dark:from-cyan-400 dark:to-emerald-400"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
      <span className="text-[11px] text-slate-500 dark:text-slate-400">
        {used}/{limit}
      </span>
    </div>
  );
}


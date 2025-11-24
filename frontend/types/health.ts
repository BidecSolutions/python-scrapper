export interface HealthCard {
  status: "ok" | "warning" | "bad";
  details: Record<string, any>;
}

export interface HealthResponse {
  health_score: number;
  period: string;
  cards: {
    deliverability: HealthCard;
    verification: HealthCard;
    campaigns: HealthCard;
    jobs: HealthCard;
  };
  charts: {
    bounce_rate_by_day: Array<{ date: string; value: number }>;
    verification_valid_pct_by_day: Array<{ date: string; value: number }>;
    reply_rate_by_day: Array<{ date: string; value: number }>;
  };
}

export interface WorkspaceHealthSummary {
  workspace_id: number;
  name: string;
  health_score: number;
  bounce_rate: number;
  jobs_failed_recent: number;
  linkedin_failure_rate: number;
}


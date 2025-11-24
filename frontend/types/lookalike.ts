export type LookalikeJobStatus = "pending" | "running" | "completed" | "failed";

export interface LookalikeJob {
  id: number;
  workspace_id: number;
  started_by_user_id: number;
  source_segment_id?: number | null;
  source_list_id?: number | null;
  source_campaign_id?: number | null;
  status: LookalikeJobStatus;
  positive_lead_count: number;
  candidates_found: number;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface LookalikeCandidate {
  id: number;
  lead_id?: number | null;
  company_id?: number | null;
  score: number;
  reason_vector?: Record<string, number> | null;
}

export interface LookalikeJobDetail extends LookalikeJob {
  candidates: LookalikeCandidate[];
}


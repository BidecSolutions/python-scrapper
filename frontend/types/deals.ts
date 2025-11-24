export type DealStage =
  | "new"
  | "contacted"
  | "qualified"
  | "meeting_scheduled"
  | "proposal"
  | "won"
  | "lost";

export interface Deal {
  id: number;
  name: string;
  company_id?: number | null;
  primary_lead_id?: number | null;
  owner_user_id?: number | null;
  stage: DealStage;
  value?: number | null;
  currency: string;
  expected_close_date?: string | null;
  source_campaign_id?: number | null;
  source_segment_id?: number | null;
  lost_reason?: string | null;
  lost_at?: string | null;
  won_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DealListResponse {
  items: Deal[];
  total: number;
  page: number;
  page_size: number;
}

export interface PipelineSummary {
  stage_counts: Record<DealStage, number>;
  stage_totals: Record<DealStage, number>;
  in_progress_value: number;
  in_progress_count: number;
  won_recent_value: number;
  won_recent_count: number;
  win_rate: number;
  avg_days_to_close: number | null;
  total_deals: number;
}


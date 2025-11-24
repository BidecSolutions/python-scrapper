export type ActivityType =
  | "lead_created"
  | "lead_updated"
  | "email_found"
  | "email_verified"
  | "lead_added_to_list"
  | "lead_removed_from_list"
  | "campaign_created"
  | "campaign_sent"
  | "campaign_outcome_imported"
  | "campaign_event"
  | "task_created"
  | "task_completed"
  | "task_cancelled"
  | "note_added"
  | "playbook_run"
  | "playbook_completed"
  | "list_created"
  | "list_marked_campaign_ready"
  | "job_created"
  | "job_completed"
  | "job_failed"
  | "integration_connected"
  | "integration_disconnected"
  | "workspace_created"
  | "member_invited"
  | "member_joined";

export interface WorkspaceActivityItem {
  id: number;
  actor_user_id?: number | null;
  type: ActivityType;
  meta: Record<string, any>;
  created_at: string;
}

export interface WorkspaceActivityListResponse {
  items: WorkspaceActivityItem[];
  total: number;
  page: number;
  page_size: number;
}


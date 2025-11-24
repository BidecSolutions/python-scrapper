export type TemplateScope = "workspace" | "global";
export type TemplateStatus = "draft" | "pending_approval" | "approved" | "deprecated" | "rejected";
export type TemplateKind = "email" | "subject" | "sequence_step";

export interface Template {
  id: number;
  workspace_id?: number | null;
  scope: TemplateScope;
  name: string;
  description?: string | null;
  kind: TemplateKind;
  subject?: string | null;
  body?: string | null;
  status: TemplateStatus;
  locked: boolean;
  created_by_user_id: number;
  approved_by_user_id?: number | null;
  tags?: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface TemplateListResponse {
  items: Template[];
  total: number;
}

export interface TemplateGovernance {
  workspace_id: number;
  require_approval_for_new_templates: boolean;
  restrict_to_approved_only: boolean;
  allow_personal_templates: boolean;
  require_unsubscribe: boolean;
}


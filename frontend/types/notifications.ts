export type NotificationType =
  | "task_assigned"
  | "task_due_soon"
  | "lead_assigned"
  | "reply_received"
  | "bounce_detected"
  | "playbook_failed"
  | "playbook_completed"
  | "critical_audit";

export interface NotificationItem {
  id: number;
  type: NotificationType;
  title: string;
  body?: string | null;
  target_url?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  unread_count: number;
}


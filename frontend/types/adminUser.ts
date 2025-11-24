export type UserStatus = "pending" | "active" | "suspended";

export interface AdminUser {
  id: number;
  email: string;
  full_name?: string | null;
  status: UserStatus;
  is_super_admin: boolean;
  can_use_advanced: boolean;
  organization_id?: number | null;
  created_at: string;
  last_login_at?: string | null;
}

export interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
}


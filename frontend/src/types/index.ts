/** Shared type definitions aligned with backend schemas */

// ─── User ─────────────────────────────────────────────
export interface User {
  id: number;
  username: string;
  is_active: boolean;
  created_at: string;
}

// ─── Workspace ────────────────────────────────────────
export type RoleEnum = 'owner' | 'admin' | 'member';

export interface Workspace {
  id: number;
  name: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  role: RoleEnum;
}

export interface WorkspaceMember {
  user_id: number;
  username?: string;
  role: RoleEnum;
  created_at: string;
  updated_at: string;
}

// ─── Project ──────────────────────────────────────────
export interface Project {
  id: number;
  workspace_id: number;
  name: string;
  description?: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}

// ─── Task ─────────────────────────────────────────────
export type TaskStatus = 'todo' | 'in_progress' | 'blocked' | 'done';

export interface Task {
  id: number;
  title: string;
  description?: string | null;
  status: TaskStatus;
  due_at?: string | null;
  workspace_id: number;
  project_id: number;
  assignee_id?: number | null;
  creator_id: number;
  version: number;
  created_at: string;
  updated_at: string;
}

// ─── Comment ──────────────────────────────────────────
export interface Comment {
  id: number;
  workspace_id: number;
  task_id: number;
  author_id: number;
  content: string;
  created_at: string;
  updated_at: string;
}

// ─── Tag ──────────────────────────────────────────────
export interface TaskTag {
  id: number;
  task_id: number;
  tag: string;
  created_at: string;
}

// ─── Watcher ──────────────────────────────────────────
export interface TaskWatcher {
  id: number;
  task_id: number;
  user_id: number;
  created_at: string;
}

// ─── AuditLog ─────────────────────────────────────────
export interface AuditLog {
  id: number;
  actor_user_id: number;
  workspace_id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  changes: string | null;
  created_at: string;
}

// ─── Pagination ───────────────────────────────────────
export interface PageResponse<T> {
  items: T[];
  total: number;
}

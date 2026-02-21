import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import type { Task, PageResponse } from '@/types';

const DEFAULT_LIMIT = 100;

export function useTasks(workspaceId: number, projectId?: number) {
  return useQuery({
    queryKey: ['tasks', workspaceId, projectId],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('limit', String(DEFAULT_LIMIT));
      if (projectId) params.append('project_id', projectId.toString());

      const { data } = await api.get<PageResponse<Task>>(`/workspaces/${workspaceId}/tasks?${params.toString()}`);
      return data;
    },
    enabled: !!workspaceId,
  });
}

export function useFilteredTasks(
  workspaceId: number,
  filters: {
    project_id?: number;
    status?: string;
    assignee_id?: number;
    tag?: string;
    sort_by?: string;
    sort_order?: string;
    due_at_from?: string;
    due_at_to?: string;
  }
) {
  return useQuery({
    queryKey: ['tasks', workspaceId, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('limit', String(DEFAULT_LIMIT));
      if (filters.project_id) params.append('project_id', filters.project_id.toString());
      if (filters.status) params.append('status', filters.status);
      if (filters.assignee_id) params.append('assignee_id', filters.assignee_id.toString());
      if (filters.tag) params.append('tag', filters.tag);
      if (filters.sort_by) params.append('sort_by', filters.sort_by);
      if (filters.sort_order) params.append('sort_order', filters.sort_order);
      if (filters.due_at_from) params.append('due_at_from', filters.due_at_from);
      if (filters.due_at_to) params.append('due_at_to', filters.due_at_to);

      const { data } = await api.get<PageResponse<Task>>(`/workspaces/${workspaceId}/tasks?${params.toString()}`);
      return data;
    },
    enabled: !!workspaceId,
  });
}

export function useTask(workspaceId: number, taskId: number) {
  return useQuery({
    queryKey: ['task', workspaceId, taskId],
    queryFn: async () => {
      const { data } = await api.get<Task>(`/workspaces/${workspaceId}/tasks/${taskId}`);
      return data;
    },
    enabled: !!workspaceId && !!taskId,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, projectId, data }: { workspaceId: number; projectId: number; data: { title: string; description?: string } }) => {
      const { data: task } = await api.post<Task>(`/workspaces/${workspaceId}/projects/${projectId}/tasks`, data);
      return task;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', variables.workspaceId] });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, data }: { workspaceId: number; taskId: number; data: { version: number; title?: string; description?: string | null; assignee_id?: number | null; due_at?: string | null } }) => {
      const { data: task } = await api.patch<Task>(`/workspaces/${workspaceId}/tasks/${taskId}`, data);
      return task;
    },
    onSuccess: (task, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', variables.workspaceId] });
      queryClient.setQueryData(['task', variables.workspaceId, variables.taskId], task);
    },
  });
}

export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, status }: { workspaceId: number; taskId: number; status: string }) => {
      const { data: task } = await api.post<Task>(`/workspaces/${workspaceId}/tasks/${taskId}/status-transitions`, { to_status: status });
      return task;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', variables.workspaceId] });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId }: { workspaceId: number; taskId: number }) => {
      await api.delete(`/workspaces/${workspaceId}/tasks/${taskId}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', variables.workspaceId] });
    },
  });
}

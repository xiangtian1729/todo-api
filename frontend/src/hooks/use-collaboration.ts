import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import type { Comment, TaskTag, TaskWatcher } from '@/types';

// ─── Comments ─────────────────────────────────────────
export function useComments(workspaceId: number, taskId: number) {
  return useQuery({
    queryKey: ['comments', workspaceId, taskId],
    queryFn: async () => {
      const { data } = await api.get<Comment[]>(`/workspaces/${workspaceId}/tasks/${taskId}/comments`);
      return data;
    },
    enabled: !!workspaceId && !!taskId,
  });
}

export function useCreateComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, content }: { workspaceId: number; taskId: number; content: string }) => {
      const { data } = await api.post<Comment>(`/workspaces/${workspaceId}/tasks/${taskId}/comments`, { content });
      return data;
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['comments', v.workspaceId, v.taskId] });
    },
  });
}

export function useUpdateComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, commentId, content }: { workspaceId: number; taskId: number; commentId: number; content: string }) => {
      const { data } = await api.patch<Comment>(`/workspaces/${workspaceId}/tasks/${taskId}/comments/${commentId}`, { content });
      return data;
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['comments', v.workspaceId, v.taskId] });
    },
  });
}

export function useDeleteComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, commentId }: { workspaceId: number; taskId: number; commentId: number }) => {
      await api.delete(`/workspaces/${workspaceId}/tasks/${taskId}/comments/${commentId}`);
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['comments', v.workspaceId, v.taskId] });
    },
  });
}

// ─── Tags ─────────────────────────────────────────────
export function useAddTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, tag }: { workspaceId: number; taskId: number; tag: string }) => {
      const { data } = await api.post<TaskTag>(`/workspaces/${workspaceId}/tasks/${taskId}/tags`, { tag });
      return data;
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', v.workspaceId] });
      queryClient.invalidateQueries({ queryKey: ['task', v.workspaceId, v.taskId] });
    },
  });
}

export function useDeleteTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, tag }: { workspaceId: number; taskId: number; tag: string }) => {
      await api.delete(`/workspaces/${workspaceId}/tasks/${taskId}/tags/${tag}`);
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', v.workspaceId] });
      queryClient.invalidateQueries({ queryKey: ['task', v.workspaceId, v.taskId] });
    },
  });
}

// ─── Watchers ─────────────────────────────────────────
export function useAddWatcher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, userId }: { workspaceId: number; taskId: number; userId: number }) => {
      const { data } = await api.post<TaskWatcher>(`/workspaces/${workspaceId}/tasks/${taskId}/watchers`, { user_id: userId });
      return data;
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['task', v.workspaceId, v.taskId] });
    },
  });
}

export function useDeleteWatcher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, taskId, userId }: { workspaceId: number; taskId: number; userId: number }) => {
      await api.delete(`/workspaces/${workspaceId}/tasks/${taskId}/watchers/${userId}`);
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['task', v.workspaceId, v.taskId] });
    },
  });
}

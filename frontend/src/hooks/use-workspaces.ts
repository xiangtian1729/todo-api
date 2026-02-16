import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import type { Workspace, WorkspaceMember } from '@/types';

export function useWorkspaces() {
  return useQuery({
    queryKey: ['workspaces'],
    queryFn: async () => {
      const { data } = await api.get<Workspace[]>('/workspaces');
      return { items: data, total: data.length };
    },
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { name: string }) => {
      const { data } = await api.post<Workspace>('/workspaces', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    },
  });
}

// ─── Members ──────────────────────────────────────────
export function useWorkspaceMembers(workspaceId: number) {
  return useQuery({
    queryKey: ['workspace-members', workspaceId],
    queryFn: async () => {
      const { data } = await api.get<(WorkspaceMember & { username?: string })[]>(
        `/workspaces/${workspaceId}/members`
      );
      return data;
    },
    enabled: !!workspaceId,
  });
}

/** Build a user_id → username lookup map from workspace members */
export function useUsernameLookup(workspaceId: number) {
  const { data: members } = useWorkspaceMembers(workspaceId);
  const lookup: Record<number, string> = {};
  if (members) {
    for (const m of members) {
      lookup[m.user_id] = m.username || `User #${m.user_id}`;
    }
  }
  return {
    lookup,
    resolve: (userId: number) => lookup[userId] || `User #${userId}`,
  };
}

export function useAddMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, userId, role }: { workspaceId: number; userId: number; role: string }) => {
      const { data } = await api.post<WorkspaceMember>(`/workspaces/${workspaceId}/members`, { user_id: userId, role });
      return data;
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['workspace-members', v.workspaceId] });
    },
  });
}

export function useUpdateMemberRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, userId, role }: { workspaceId: number; userId: number; role: string }) => {
      const { data } = await api.patch<WorkspaceMember>(`/workspaces/${workspaceId}/members/${userId}`, { role });
      return data;
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['workspace-members', v.workspaceId] });
    },
  });
}

export function useRemoveMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, userId }: { workspaceId: number; userId: number }) => {
      await api.delete(`/workspaces/${workspaceId}/members/${userId}`);
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['workspace-members', v.workspaceId] });
    },
  });
}

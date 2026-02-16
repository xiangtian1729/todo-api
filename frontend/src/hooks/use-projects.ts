import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import type { Project } from '@/types';

export function useProjects(workspaceId: number | null) {
  return useQuery({
    queryKey: ['projects', workspaceId],
    queryFn: async () => {
      if (!workspaceId) return { items: [], total: 0 };
      const { data } = await api.get<Project[]>(`/workspaces/${workspaceId}/projects`);
      return { items: data, total: data.length };
    },
    enabled: !!workspaceId,
  });
}

export function useProject(workspaceId: number, projectId: number) {
  return useQuery({
    queryKey: ['project', workspaceId, projectId],
    queryFn: async () => {
      const { data } = await api.get<Project>(`/workspaces/${workspaceId}/projects/${projectId}`);
      return data;
    },
    enabled: !!workspaceId && !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, name, description }: { workspaceId: number; name: string; description?: string }) => {
      const { data: project } = await api.post<Project>(`/workspaces/${workspaceId}/projects`, { name, description });
      return project;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects', variables.workspaceId] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, projectId, data }: { workspaceId: number; projectId: number; data: { name?: string; description?: string | null } }) => {
      const { data: project } = await api.patch<Project>(`/workspaces/${workspaceId}/projects/${projectId}`, data);
      return project;
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['projects', v.workspaceId] });
      queryClient.setQueryData(['project', v.workspaceId, v.projectId], (old: Project | undefined) => old ? { ...old, ...v.data } : old);
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ workspaceId, projectId }: { workspaceId: number; projectId: number }) => {
      await api.delete(`/workspaces/${workspaceId}/projects/${projectId}`);
    },
    onSuccess: (_, v) => {
      queryClient.invalidateQueries({ queryKey: ['projects', v.workspaceId] });
    },
  });
}

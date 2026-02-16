import { useQuery } from '@tanstack/react-query';
import api from '@/lib/axios';
import type { AuditLog, PageResponse } from '@/types';

export function useAuditLogs(workspaceId: number, skip = 0, limit = 20) {
  return useQuery({
    queryKey: ['audit-logs', workspaceId, skip, limit],
    queryFn: async () => {
      const { data } = await api.get<PageResponse<AuditLog>>(`/workspaces/${workspaceId}/audit-logs?skip=${skip}&limit=${limit}`);
      return data;
    },
    enabled: !!workspaceId,
  });
}

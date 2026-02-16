'use client';

import { useParams } from 'next/navigation';
import { useAuditLogs } from '@/hooks/use-audit';
import { useUsernameLookup } from '@/hooks/use-workspaces';
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollText, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';

const ACTION_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  create: 'default',
  update: 'secondary',
  delete: 'destructive',
};

export default function AuditPage() {
  const params = useParams();
  const workspaceId = parseInt(params.workspaceId as string);
  const [page, setPage] = useState(0);
  const limit = 20;
  const { data, isLoading } = useAuditLogs(workspaceId, page * limit, limit);
  const { resolve: resolveUsername } = useUsernameLookup(workspaceId);

  if (isNaN(workspaceId)) return <div>Invalid workspace</div>;

  const logs = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ScrollText className="h-6 w-6" /> Audit Log
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Track all changes in this workspace ({total} total entries)
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      ) : logs.length === 0 ? (
        <div className="rounded-lg border p-6 text-center text-sm text-muted-foreground">
          No audit logs yet. Actions like creating tasks, updating projects, etc. will appear here.
        </div>
      ) : (
        <>
          <div className="rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left p-3 font-medium">Time</th>
                  <th className="text-left p-3 font-medium">User</th>
                  <th className="text-left p-3 font-medium">Action</th>
                  <th className="text-left p-3 font-medium">Entity</th>
                  <th className="text-left p-3 font-medium">Changes</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-muted/30">
                    <td className="p-3 text-muted-foreground whitespace-nowrap">
                      {formatRelativeTime(log.created_at)}
                    </td>
                    <td className="p-3">{resolveUsername(log.actor_user_id)}</td>
                    <td className="p-3">
                      <Badge variant={ACTION_COLORS[log.action] ?? 'outline'}>
                        {log.action}
                      </Badge>
                    </td>
                    <td className="p-3">
                      <span className="text-muted-foreground">{log.entity_type}</span>
                      <span className="ml-1">#{log.entity_id}</span>
                    </td>
                    <td className="p-3 max-w-xs truncate text-xs text-muted-foreground">
                      {log.changes ? formatChanges(log.changes) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Page {page + 1} of {totalPages}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage(p => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" /> Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatChanges(changes: string): string {
  try {
    const parsed = JSON.parse(changes);
    return Object.entries(parsed)
      .map(([key, val]) => `${key}: ${JSON.stringify(val)}`)
      .join(', ');
  } catch {
    return changes;
  }
}

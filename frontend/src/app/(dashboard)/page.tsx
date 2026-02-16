'use client';

import { useAuth } from '@/hooks/use-auth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { useProjects } from '@/hooks/use-projects';
import { useWorkspaceStore } from '@/hooks/use-workspace-store';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Loader2, FolderKanban, Briefcase } from 'lucide-react';

export default function Home() {
  const { user, isAuthenticated, fetchUser } = useAuth();
  const router = useRouter();
  const { activeWorkspaceId } = useWorkspaceStore();
  const { data: workspacesData } = useWorkspaces();
  const { data: projectsData } = useProjects(activeWorkspaceId);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (!user) {
      fetchUser();
    }
  }, [isAuthenticated, user, router, fetchUser]);

  if (!isAuthenticated) return null;

  if (!user) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const workspaceCount = workspacesData?.items?.length ?? 0;
  const projectCount = projectsData?.items?.length ?? 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Welcome back, {user.username}</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Workspaces
            </CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{workspaceCount}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Use the sidebar to switch workspaces
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Projects
            </CardTitle>
            <FolderKanban className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{projectCount}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {activeWorkspaceId
                ? 'In current workspace'
                : 'Select a workspace to view projects'}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { LayoutDashboard, ListTodo, Users, ScrollText } from 'lucide-react';
import { WorkspaceSwitcher } from './workspace-switcher';
import { ProjectList } from './project-list';
import { SidebarSettings } from './sidebar-settings';
import { useWorkspaceStore } from '@/hooks/use-workspace-store';

export default function Sidebar() {
  const pathname = usePathname();
  const { activeWorkspaceId } = useWorkspaceStore();

  return (
    <div className="h-full w-64 border-r bg-gray-50/40 dark:bg-gray-800/40 flex flex-col">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <ListTodo className="h-6 w-6" />
          <span>Todo App</span>
        </Link>
      </div>
      
      <div className="flex-1 py-4 overflow-y-auto">
        <WorkspaceSwitcher />
        
        <nav className="grid gap-1 px-2 mt-4">
          <Button
            variant={pathname === '/' ? 'secondary' : 'ghost'}
            className="justify-start"
            asChild
          >
            <Link href="/">
              <LayoutDashboard className="mr-2 h-4 w-4" />
              Dashboard
            </Link>
          </Button>

          {activeWorkspaceId && (
            <>
              <Button
                variant={pathname.includes('/members') ? 'secondary' : 'ghost'}
                className="justify-start"
                asChild
              >
                <Link href={`/workspaces/${activeWorkspaceId}/members`}>
                  <Users className="mr-2 h-4 w-4" />
                  Members
                </Link>
              </Button>

              <Button
                variant={pathname.includes('/audit') ? 'secondary' : 'ghost'}
                className="justify-start"
                asChild
              >
                <Link href={`/workspaces/${activeWorkspaceId}/audit`}>
                  <ScrollText className="mr-2 h-4 w-4" />
                  Audit Log
                </Link>
              </Button>
            </>
          )}
        </nav>
        <ProjectList />
      </div>

      {/* Settings section pinned to bottom */}
      <SidebarSettings />
    </div>
  );
}

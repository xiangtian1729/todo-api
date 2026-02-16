'use client';

import { KanbanBoard } from '@/components/tasks/kanban-board';
import { CreateTaskDialog } from '@/components/tasks/create-task-dialog';
import { useParams } from 'next/navigation';

export default function ProjectPage() {
  const params = useParams();
  const workspaceId = parseInt(params.workspaceId as string);
  const projectId = parseInt(params.projectId as string);

  if (isNaN(workspaceId) || isNaN(projectId)) {
    return <div>Invalid URL</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Project Board</h1>
        <CreateTaskDialog workspaceId={workspaceId} projectId={projectId} />
      </div>
      <div className="flex-1 overflow-hidden">
        <KanbanBoard workspaceId={workspaceId} projectId={projectId} />
      </div>
    </div>
  );
}

'use client';

import { useFilteredTasks, useUpdateTaskStatus } from '@/hooks/use-tasks';
import { useWorkspaceMembers } from '@/hooks/use-workspaces';
import { getApiErrorMessage } from '@/lib/axios';
import type { Task } from '@/types';
import { TaskDetailSheet } from '@/components/tasks/task-detail-sheet';
import {
  DndContext,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
  DragStartEvent,
  DragEndEvent,
  useDroppable,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useState, useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, X } from 'lucide-react';
import { toast } from 'sonner';

const DEFAULT_LIMIT = 100;

const COLUMNS = [
  { id: 'todo', title: 'To Do', color: 'bg-blue-500/10' },
  { id: 'in_progress', title: 'In Progress', color: 'bg-amber-500/10' },
  { id: 'blocked', title: 'Blocked', color: 'bg-red-500/10' },
  { id: 'done', title: 'Done', color: 'bg-green-500/10' },
];

const STATUS_BADGE_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  todo: 'secondary',
  in_progress: 'default',
  blocked: 'destructive',
  done: 'outline',
};

// ─── Droppable Column Container ───────────────────────────────
function DroppableColumn({
  id, title, color, tasks, onTaskClick, hasFilters,
}: {
  id: string; title: string; color: string; tasks: Task[]; onTaskClick: (task: Task) => void; hasFilters: boolean;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div className="w-72 flex-shrink-0 flex flex-col">
      <div className="mb-2 flex items-center justify-between font-semibold text-sm">
        <span>{title}</span>
        <Badge variant="secondary">{tasks.length}</Badge>
      </div>
      <div
        ref={setNodeRef}
        className={`flex-1 rounded-lg p-2 space-y-2 min-h-[120px] transition-colors ${color} ${
          isOver ? 'ring-2 ring-primary/50 bg-primary/5' : ''
        }`}
      >
        <SortableContext items={tasks.map(t => t.id)} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} onTaskClick={onTaskClick} />
          ))}
          {tasks.length === 0 && (
            <div className="flex items-center justify-center h-20 text-xs text-muted-foreground">
              {hasFilters ? 'No matches' : 'Drop tasks here'}
            </div>
          )}
        </SortableContext>
      </div>
    </div>
  );
}

// ─── Main Kanban Board ────────────────────────────────────────
export function KanbanBoard({ workspaceId, projectId }: { workspaceId: number; projectId: number }) {
  // ── filter state ──────────────────────────────────────
  const [filterStatus, setFilterStatus] = useState('_all');
  const [filterAssigneeId, setFilterAssigneeId] = useState('_all');
  const [tagInput, setTagInput] = useState('');
  const [filterTag, setFilterTag] = useState('');

  const hasFilters = filterStatus !== '_all' || filterAssigneeId !== '_all' || !!filterTag;

  const { data: members } = useWorkspaceMembers(workspaceId);

  const { data, isLoading } = useFilteredTasks(workspaceId, {
    project_id: projectId,
    status: filterStatus !== '_all' ? filterStatus : undefined,
    assignee_id: filterAssigneeId !== '_all' ? parseInt(filterAssigneeId) : undefined,
    tag: filterTag || undefined,
  });

  const updateStatus = useUpdateTaskStatus();
  const [activeId, setActiveId] = useState<number | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const tasks = useMemo(() => data?.items ?? [], [data?.items]);

  // Group tasks by status
  const grouped = useMemo(() => {
    const cols: Record<string, Task[]> = { todo: [], in_progress: [], blocked: [], done: [] };
    tasks.forEach((task) => {
      if (cols[task.status]) cols[task.status].push(task);
      else cols['todo'].push(task);
    });
    return cols;
  }, [tasks]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as number);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    if (!over) return;

    const draggedTaskId = active.id as number;
    const overId = over.id;
    const task = tasks.find((t) => t.id === draggedTaskId);
    if (!task) return;

    let targetStatus: string;
    if (typeof overId === 'string' && COLUMNS.some(c => c.id === overId)) {
      targetStatus = overId;
    } else {
      const overTask = tasks.find((t) => t.id === overId);
      targetStatus = overTask ? overTask.status : task.status;
    }

    if (task.status !== targetStatus) {
      try {
        await updateStatus.mutateAsync({ workspaceId, taskId: task.id, status: targetStatus });
        toast.success(`Task moved to ${COLUMNS.find(c => c.id === targetStatus)?.title}`);
      } catch (error) {
        toast.error(getApiErrorMessage(error, 'Failed to move task'));
      }
    }
  };

  const handleTaskClick = (task: Task) => {
    setSelectedTask(task);
    setDetailOpen(true);
  };

  const clearFilters = () => {
    setFilterStatus('_all');
    setFilterAssigneeId('_all');
    setFilterTag('');
    setTagInput('');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // Only show the "no tasks yet" empty state when there are truly no tasks and no filters are set
  if (tasks.length === 0 && !hasFilters) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <p className="text-lg font-medium">No tasks yet</p>
        <p className="text-sm">Create your first task using the button above.</p>
      </div>
    );
  }

  const activeTask = activeId ? tasks.find((t) => t.id === activeId) : null;

  return (
    <>
      {/* ── Filter Bar ────────────────────────────────── */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-36 h-8 text-xs">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="_all">All statuses</SelectItem>
            <SelectItem value="todo">To Do</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="blocked">Blocked</SelectItem>
            <SelectItem value="done">Done</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filterAssigneeId} onValueChange={setFilterAssigneeId}>
          <SelectTrigger className="w-36 h-8 text-xs">
            <SelectValue placeholder="Any assignee" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="_all">Any assignee</SelectItem>
            {members?.map((m) => (
              <SelectItem key={m.user_id} value={m.user_id.toString()}>
                {m.username || `User #${m.user_id}`}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex items-center gap-1">
          <Input
            placeholder="Filter by tag..."
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') setFilterTag(tagInput.trim()); }}
            className="h-8 w-36 text-xs"
          />
          {filterTag && (
            <Badge variant="secondary" className="h-8 gap-1 px-2 text-xs">
              #{filterTag}
              <button
                onClick={() => { setFilterTag(''); setTagInput(''); }}
                className="hover:text-destructive"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
        </div>

        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters} className="h-8 text-xs">
            Clear filters
          </Button>
        )}

        {data && data.total > DEFAULT_LIMIT && (
          <span className="text-xs text-muted-foreground ml-auto">
            Showing first {DEFAULT_LIMIT} of {data.total} tasks
          </span>
        )}
      </div>

      {/* ── Board ─────────────────────────────────────── */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex h-full gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <DroppableColumn
              key={col.id}
              id={col.id}
              title={col.title}
              color={col.color}
              tasks={grouped[col.id]}
              onTaskClick={handleTaskClick}
              hasFilters={hasFilters}
            />
          ))}
        </div>
        <DragOverlay>
          {activeTask ? <TaskCard task={activeTask} isOverlay /> : null}
        </DragOverlay>
      </DndContext>

      <TaskDetailSheet
        task={selectedTask}
        open={detailOpen}
        onOpenChange={setDetailOpen}
        workspaceId={workspaceId}
      />
    </>
  );
}

// ─── Sortable Task Card ───────────────────────────────────────
function TaskCard({ task, isOverlay, onTaskClick }: { task: Task; isOverlay?: boolean; onTaskClick?: (task: Task) => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
    data: { type: 'Task', task },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.3 : 1,
  };

  return (
    <Card
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={() => onTaskClick?.(task)}
      className={`cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow ${
        isOverlay ? 'shadow-lg rotate-2' : ''
      }`}
    >
      <CardContent className="p-3">
        <div className="text-sm font-medium leading-none mb-2">{task.title}</div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>#{task.id}</span>
          <Badge variant={STATUS_BADGE_VARIANT[task.status] ?? 'secondary'} className="text-[10px] h-4 px-1">
            {task.status.replace('_', ' ')}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

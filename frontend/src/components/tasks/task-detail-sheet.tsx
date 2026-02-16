'use client';

import { useState } from 'react';
import { useUpdateTask, useDeleteTask } from '@/hooks/use-tasks';
import { useComments, useCreateComment, useDeleteComment } from '@/hooks/use-collaboration';
import { useUsernameLookup } from '@/hooks/use-workspaces';
import { getApiErrorMessage } from '@/lib/axios';
import type { Task } from '@/types';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Loader2, Trash2, Send, Calendar } from 'lucide-react';
import { toast } from 'sonner';

const STATUS_LABELS: Record<string, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  blocked: 'Blocked',
  done: 'Done',
};

export function TaskDetailSheet({
  task,
  open,
  onOpenChange,
  workspaceId,
}: {
  task: Task | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workspaceId: number;
}) {
  if (!task) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="text-left">Task #{task.id}</SheetTitle>
        </SheetHeader>
        <TaskDetailContent task={task} workspaceId={workspaceId} onClose={() => onOpenChange(false)} />
      </SheetContent>
    </Sheet>
  );
}

function TaskDetailContent({ task, workspaceId, onClose }: { task: Task; workspaceId: number; onClose: () => void }) {
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || '');
  const [dueAt, setDueAt] = useState(task.due_at?.split('T')[0] || '');
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();
  const { resolve: resolveUsername } = useUsernameLookup(workspaceId);

  const handleSave = async () => {
    try {
      await updateTask.mutateAsync({
        workspaceId,
        taskId: task.id,
        data: {
          version: task.version,
          title: title !== task.title ? title : undefined,
          description: description !== (task.description || '') ? description || null : undefined,
          due_at: dueAt ? new Date(dueAt).toISOString() : null,
        },
      });
      toast.success('Task updated');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to update task'));
    }
  };

  const handleDelete = async () => {
    try {
      await deleteTask.mutateAsync({ workspaceId, taskId: task.id });
      toast.success('Task deleted');
      onClose();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to delete task'));
    }
  };

  return (
    <div className="space-y-6 pt-4">
      {/* Status Badge */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Status</span>
        <Badge variant="secondary">{STATUS_LABELS[task.status] || task.status}</Badge>
      </div>

      {/* Title */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-muted-foreground">Title</label>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleSave}
          className="text-base font-semibold"
        />
      </div>

      {/* Description */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-muted-foreground">Description</label>
        <Textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onBlur={handleSave}
          placeholder="Add a description..."
          rows={4}
        />
      </div>

      {/* Due Date */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
          <Calendar className="h-3.5 w-3.5" /> Due Date
        </label>
        <Input
          type="date"
          value={dueAt}
          onChange={(e) => setDueAt(e.target.value)}
          onBlur={handleSave}
        />
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground border-t pt-4">
        <div>Created: {new Date(task.created_at).toLocaleDateString()}</div>
        <div>Updated: {new Date(task.updated_at).toLocaleDateString()}</div>
        <div>Creator: {resolveUsername(task.creator_id)}</div>
        <div>Version: {task.version}</div>
      </div>

      {/* Comments Section */}
      <CommentSection workspaceId={workspaceId} taskId={task.id} />

      {/* Delete Button */}
      <div className="border-t pt-4">
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="destructive" size="sm" className="w-full">
              <Trash2 className="h-4 w-4 mr-1" /> Delete Task
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete task?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete &quot;{task.title}&quot;. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}

function CommentSection({ workspaceId, taskId }: { workspaceId: number; taskId: number }) {
  const { data: comments, isLoading } = useComments(workspaceId, taskId);
  const createComment = useCreateComment();
  const deleteComment = useDeleteComment();
  const [newComment, setNewComment] = useState('');
  const { resolve: resolveUsername } = useUsernameLookup(workspaceId);

  const handleSubmit = async () => {
    if (!newComment.trim()) return;
    try {
      await createComment.mutateAsync({ workspaceId, taskId, content: newComment.trim() });
      setNewComment('');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to add comment'));
    }
  };

  return (
    <div className="border-t pt-4 space-y-3">
      <h4 className="text-sm font-semibold">Comments</h4>
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : comments && comments.length > 0 ? (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {comments.map((c) => (
            <div key={c.id} className="text-sm bg-muted/50 rounded-md p-2 group relative">
              <div className="flex justify-between items-start">
                <p className="text-foreground whitespace-pre-wrap break-words">{c.content}</p>
                <button
                  onClick={() => deleteComment.mutate({ workspaceId, taskId, commentId: c.id })}
                  className="opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive/80 transition-opacity ml-2 shrink-0"
                  title="Delete comment"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
              <span className="text-[10px] text-muted-foreground mt-1 block">
                {resolveUsername(c.author_id)} · {new Date(c.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No comments yet</p>
      )}

      {/* New Comment Input */}
      <div className="flex gap-2">
        <Input
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Write a comment..."
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
          className="text-sm"
        />
        <Button
          size="icon"
          variant="ghost"
          onClick={handleSubmit}
          disabled={createComment.isPending || !newComment.trim()}
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

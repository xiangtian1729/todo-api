'use client';

import { useState } from 'react';
import { useUpdateTask, useDeleteTask } from '@/hooks/use-tasks';
import {
  useComments, useCreateComment, useUpdateComment, useDeleteComment,
  useTaskTags, useAddTag, useDeleteTag,
  useTaskWatchers, useAddWatcher, useDeleteWatcher,
} from '@/hooks/use-collaboration';
import { useWorkspaceMembers, useUsernameLookup } from '@/hooks/use-workspaces';
import { useAuth } from '@/hooks/use-auth';
import { getApiErrorMessage } from '@/lib/axios';
import type { Task, Comment } from '@/types';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Loader2, Trash2, Send, Calendar, Tag, Eye, EyeOff, Pencil, X, Check } from 'lucide-react';
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
  const { data: members } = useWorkspaceMembers(workspaceId);
  const currentUser = useAuth((s) => s.user);

  // Only fire the API call if a field actually changed (dirty check)
  const handleSave = async () => {
    const titleChanged = title !== task.title;
    const descChanged = description !== (task.description || '');
    const dueChanged = dueAt !== (task.due_at?.split('T')[0] || '');
    if (!titleChanged && !descChanged && !dueChanged) return;

    try {
      await updateTask.mutateAsync({
        workspaceId,
        taskId: task.id,
        data: {
          version: task.version,
          title: titleChanged ? title : undefined,
          description: descChanged ? (description || null) : undefined,
          due_at: dueChanged ? (dueAt ? new Date(dueAt).toISOString() : null) : undefined,
        },
      });
      toast.success('Task updated');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to update task'));
    }
  };

  const handleAssigneeChange = async (value: string) => {
    const assigneeId = value === 'none' ? null : parseInt(value);
    try {
      await updateTask.mutateAsync({
        workspaceId,
        taskId: task.id,
        data: { version: task.version, assignee_id: assigneeId },
      });
      toast.success('Assignee updated');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to update assignee'));
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
      {/* Status + Assignee row */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Status</label>
          <Badge variant="secondary" className="block w-fit">
            {STATUS_LABELS[task.status] || task.status}
          </Badge>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Assignee</label>
          <Select
            value={task.assignee_id?.toString() ?? 'none'}
            onValueChange={handleAssigneeChange}
            disabled={updateTask.isPending}
          >
            <SelectTrigger className="h-7 text-xs">
              <SelectValue placeholder="Unassigned" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Unassigned</SelectItem>
              {members?.map((m) => (
                <SelectItem key={m.user_id} value={m.user_id.toString()}>
                  {m.username || `User #${m.user_id}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
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

      {/* Tags */}
      <TagsSection workspaceId={workspaceId} taskId={task.id} />

      {/* Watchers */}
      <WatchersSection
        workspaceId={workspaceId}
        taskId={task.id}
        currentUserId={currentUser?.id}
        resolveUsername={resolveUsername}
      />

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

// ─── Tags Section ──────────────────────────────────────
function TagsSection({ workspaceId, taskId }: { workspaceId: number; taskId: number }) {
  const { data: tags, isLoading } = useTaskTags(workspaceId, taskId);
  const addTag = useAddTag();
  const deleteTag = useDeleteTag();
  const [input, setInput] = useState('');

  const handleAdd = async () => {
    const trimmed = input.trim().toLowerCase();
    if (!trimmed) return;
    if (tags?.some((t) => t.tag === trimmed)) {
      toast.error('Tag already exists');
      return;
    }
    try {
      await addTag.mutateAsync({ workspaceId, taskId, tag: trimmed });
      setInput('');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to add tag'));
    }
  };

  return (
    <div className="space-y-2 border-t pt-4">
      <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
        <Tag className="h-3.5 w-3.5" /> Tags
      </label>
      {isLoading ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : (
        <div className="flex flex-wrap gap-1 min-h-[24px]">
          {tags?.map((t) => (
            <Badge key={t.id} variant="secondary" className="gap-1 pr-1">
              {t.tag}
              <button
                onClick={() => deleteTag.mutate({ workspaceId, taskId, tag: t.tag })}
                className="hover:text-destructive transition-colors ml-0.5"
                aria-label={`Remove tag ${t.tag}`}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {(!tags || tags.length === 0) && (
            <span className="text-xs text-muted-foreground">No tags yet</span>
          )}
        </div>
      )}
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          placeholder="Add tag..."
          className="h-7 text-xs"
        />
        <Button
          size="sm"
          variant="outline"
          onClick={handleAdd}
          disabled={addTag.isPending || !input.trim()}
          className="h-7 text-xs"
        >
          Add
        </Button>
      </div>
    </div>
  );
}

// ─── Watchers Section ──────────────────────────────────
function WatchersSection({
  workspaceId,
  taskId,
  currentUserId,
  resolveUsername,
}: {
  workspaceId: number;
  taskId: number;
  currentUserId: number | undefined;
  resolveUsername: (id: number) => string;
}) {
  const { data: watchers, isLoading } = useTaskWatchers(workspaceId, taskId);
  const addWatcher = useAddWatcher();
  const deleteWatcher = useDeleteWatcher();

  const isWatching = currentUserId !== undefined && watchers?.some((w) => w.user_id === currentUserId);

  const handleToggleWatch = async () => {
    if (currentUserId === undefined) return;
    try {
      if (isWatching) {
        await deleteWatcher.mutateAsync({ workspaceId, taskId, userId: currentUserId });
        toast.success('Unfollowed task');
      } else {
        await addWatcher.mutateAsync({ workspaceId, taskId, userId: currentUserId });
        toast.success('Now following task');
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to update watchers'));
    }
  };

  return (
    <div className="space-y-2 border-t pt-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
          <Eye className="h-3.5 w-3.5" /> Watchers
          {watchers && watchers.length > 0 && (
            <span className="ml-1 text-xs">({watchers.length})</span>
          )}
        </label>
        <Button
          size="sm"
          variant={isWatching ? 'secondary' : 'outline'}
          onClick={handleToggleWatch}
          disabled={addWatcher.isPending || deleteWatcher.isPending}
          className="h-6 text-xs px-2"
        >
          {isWatching ? (
            <><EyeOff className="h-3 w-3 mr-1" /> Unwatch</>
          ) : (
            <><Eye className="h-3 w-3 mr-1" /> Watch</>
          )}
        </Button>
      </div>
      {isLoading ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : watchers && watchers.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {watchers.map((w) => (
            <Badge key={w.id} variant="outline" className="text-xs">
              {resolveUsername(w.user_id)}
            </Badge>
          ))}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No watchers yet</p>
      )}
    </div>
  );
}

// ─── Comment Section ───────────────────────────────────
function CommentSection({ workspaceId, taskId }: { workspaceId: number; taskId: number }) {
  const { data: comments, isLoading } = useComments(workspaceId, taskId);
  const createComment = useCreateComment();
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
            <CommentItem
              key={c.id}
              comment={c}
              workspaceId={workspaceId}
              taskId={taskId}
              resolveUsername={resolveUsername}
            />
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

// ─── Individual Comment Item (with inline edit) ────────
function CommentItem({
  comment,
  workspaceId,
  taskId,
  resolveUsername,
}: {
  comment: Comment;
  workspaceId: number;
  taskId: number;
  resolveUsername: (id: number) => string;
}) {
  const updateComment = useUpdateComment();
  const deleteComment = useDeleteComment();
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);

  const handleSave = async () => {
    const trimmed = editContent.trim();
    if (!trimmed || trimmed === comment.content) {
      setIsEditing(false);
      setEditContent(comment.content);
      return;
    }
    try {
      await updateComment.mutateAsync({ workspaceId, taskId, commentId: comment.id, content: trimmed });
      setIsEditing(false);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to update comment'));
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditContent(comment.content);
  };

  return (
    <div className="text-sm bg-muted/50 rounded-md p-2 group relative">
      {isEditing ? (
        <div className="space-y-1.5">
          <Textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSave(); }
              if (e.key === 'Escape') handleCancel();
            }}
            rows={2}
            className="text-sm"
            autoFocus
          />
          <div className="flex gap-1">
            <Button size="sm" className="h-6 text-xs px-2" onClick={handleSave} disabled={updateComment.isPending}>
              <Check className="h-3 w-3 mr-1" /> Save
            </Button>
            <Button size="sm" variant="ghost" className="h-6 text-xs px-2" onClick={handleCancel}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-start">
            <p className="text-foreground whitespace-pre-wrap break-words pr-8">{comment.content}</p>
            <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
              <button
                onClick={() => setIsEditing(true)}
                className="text-muted-foreground hover:text-foreground transition-colors"
                title="Edit comment"
              >
                <Pencil className="h-3 w-3" />
              </button>
              <button
                onClick={() => deleteComment.mutate({ workspaceId, taskId, commentId: comment.id })}
                className="text-destructive hover:text-destructive/80 transition-colors"
                title="Delete comment"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          </div>
          <span className="text-[10px] text-muted-foreground mt-1 block">
            {resolveUsername(comment.author_id)} · {new Date(comment.created_at).toLocaleString()}
            {comment.updated_at !== comment.created_at && ' (edited)'}
          </span>
        </>
      )}
    </div>
  );
}

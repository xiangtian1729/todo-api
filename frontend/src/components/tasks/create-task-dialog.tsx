'use client';

import { useState } from 'react';
import { useCreateTask } from '@/hooks/use-tasks';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Plus } from 'lucide-react';

export function CreateTaskDialog({
  workspaceId,
  projectId,
}: {
  workspaceId: number;
  projectId: number;
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const createTask = useCreateTask();

  const handleCreate = async () => {
    if (!title.trim()) return;
    try {
      await createTask.mutateAsync({
        workspaceId,
        projectId,
        data: {
          title: title.trim(),
          description: description.trim() || undefined,
        },
      });
      toast.success('Task created');
      setTitle('');
      setDescription('');
      setOpen(false);
    } catch {
      toast.error('Failed to create task');
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-1" />
          New Task
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Task</DialogTitle>
          <DialogDescription>Add a new task to this project.</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="task-title">Title</Label>
            <Input
              id="task-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Implement login page"
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="task-desc">Description (optional)</Label>
            <Input
              id="task-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description..."
            />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleCreate} disabled={createTask.isPending || !title.trim()}>
            {createTask.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

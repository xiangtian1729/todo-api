'use client';

import { useWorkspaceStore } from '@/hooks/use-workspace-store';
import { useWorkspaces, useCreateWorkspace } from '@/hooks/use-workspaces';
import { useEffect, useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { PlusCircle, Loader2 } from 'lucide-react';
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

export function WorkspaceSwitcher() {
  const { data, isLoading } = useWorkspaces();
  const { activeWorkspaceId, setActiveWorkspaceId } = useWorkspaceStore();
  const [open, setOpen] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const createWorkspace = useCreateWorkspace();

  // Auto-select first workspace if none active
  useEffect(() => {
    if (data?.items && data.items.length > 0 && !activeWorkspaceId) {
      setActiveWorkspaceId(data.items[0].id);
    }
  }, [data, activeWorkspaceId, setActiveWorkspaceId]);

  const handleCreate = async () => {
    if (!newWorkspaceName.trim()) return;
    try {
      const workspace = await createWorkspace.mutateAsync({ name: newWorkspaceName });
      setActiveWorkspaceId(workspace.id);
      setOpen(false);
      setNewWorkspaceName('');
      toast.success('Workspace created');
    } catch (error) {
      toast.error('Failed to create workspace');
    }
  };

  if (isLoading) {
    return <Loader2 className="h-4 w-4 animate-spin" />;
  }

  const workspaces = data?.items || [];

  return (
    <div className="px-4 py-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-muted-foreground">Workspace</span>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="ghost" size="icon" className="h-6 w-6">
              <PlusCircle className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Workspace</DialogTitle>
              <DialogDescription>
                Add a new workspace to organize your projects.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={newWorkspaceName}
                  onChange={(e) => setNewWorkspaceName(e.target.value)}
                  placeholder="Acme Corp"
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleCreate} disabled={createWorkspace.isPending}>
                {createWorkspace.isPending ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      
      {workspaces.length > 0 ? (
        <Select
          value={activeWorkspaceId?.toString()}
          onValueChange={(val) => setActiveWorkspaceId(parseInt(val))}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select workspace" />
          </SelectTrigger>
          <SelectContent>
             {workspaces.map((ws) => (
               <SelectItem key={ws.id} value={ws.id.toString()}>
                 {ws.name}
               </SelectItem>
             ))}
          </SelectContent>
        </Select>
      ) : (
        <Button variant="outline" className="w-full" onClick={() => setOpen(true)}>
          Create Workspace
        </Button>
      )}
    </div>
  );
}

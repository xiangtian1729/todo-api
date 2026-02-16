'use client';

import { useProjects, useCreateProject, useDeleteProject, useUpdateProject } from '@/hooks/use-projects';
import { useWorkspaceStore } from '@/hooks/use-workspace-store';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Hash, Plus, Loader2, MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from '@/components/ui/dialog';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useState } from 'react';
import { toast } from 'sonner';

export function ProjectList() {
  const { activeWorkspaceId } = useWorkspaceStore();
  const { data, isLoading } = useProjects(activeWorkspaceId);
  const createProject = useCreateProject();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');

  if (!activeWorkspaceId) return null;

  const handleCreate = async () => {
    if (!name.trim()) return;
    try {
      await createProject.mutateAsync({ workspaceId: activeWorkspaceId, name });
      setOpen(false);
      setName('');
      toast.success('Project created');
    } catch {
      toast.error('Failed to create project');
    }
  };

  if (isLoading) {
    return <div className="px-4 py-2"><Loader2 className="h-4 w-4 animate-spin" /></div>;
  }

  const projects = data?.items || [];

  return (
    <div className="mt-4 px-2">
      <div className="flex items-center justify-between px-2 mb-1 text-xs font-semibold text-muted-foreground">
        <span>PROJECTS</span>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="ghost" size="icon" className="h-4 w-4">
              <Plus className="h-3 w-3" />
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Project</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="project-name">Name</Label>
                <Input
                  id="project-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Project"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleCreate} disabled={createProject.isPending}>
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <div className="space-y-1">
        {projects.map((project) => (
          <ProjectItem
            key={project.id}
            project={project}
            workspaceId={activeWorkspaceId}
            isActive={pathname.includes(`/projects/${project.id}`)}
          />
        ))}
        {projects.length === 0 && (
          <p className="px-2 text-xs text-muted-foreground">No projects yet</p>
        )}
      </div>
    </div>
  );
}

function ProjectItem({ project, workspaceId, isActive }: { project: { id: number; name: string }; workspaceId: number; isActive: boolean }) {
  const deleteProject = useDeleteProject();
  const updateProject = useUpdateProject();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [renameOpen, setRenameOpen] = useState(false);
  const [newName, setNewName] = useState(project.name);

  const handleDelete = async () => {
    try {
      await deleteProject.mutateAsync({ workspaceId, projectId: project.id });
      toast.success('Project deleted');
    } catch {
      toast.error('Failed to delete project');
    }
  };

  const handleRename = async () => {
    if (!newName.trim() || newName === project.name) { setRenameOpen(false); return; }
    try {
      await updateProject.mutateAsync({ workspaceId, projectId: project.id, data: { name: newName.trim() } });
      toast.success('Project renamed');
      setRenameOpen(false);
    } catch {
      toast.error('Failed to rename project');
    }
  };

  return (
    <div className="flex items-center group">
      <Button
        variant={isActive ? 'secondary' : 'ghost'}
        size="sm"
        className="flex-1 justify-start"
        asChild
      >
        <Link href={`/workspaces/${workspaceId}/projects/${project.id}`}>
          <Hash className="mr-2 h-3 w-3 text-muted-foreground" />
          {project.name}
        </Link>
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
            <MoreHorizontal className="h-3 w-3" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => { setNewName(project.name); setRenameOpen(true); }}>
            <Pencil className="mr-2 h-3 w-3" /> Rename
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setDeleteOpen(true)} className="text-destructive">
            <Trash2 className="mr-2 h-3 w-3" /> Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Rename Dialog */}
      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Rename Project</DialogTitle></DialogHeader>
          <Input value={newName} onChange={(e) => setNewName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleRename()} />
          <DialogFooter><Button onClick={handleRename}>Save</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm */}
      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete &quot;{project.name}&quot;?</AlertDialogTitle>
            <AlertDialogDescription>All tasks in this project will be permanently deleted.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

'use client';

import { useParams } from 'next/navigation';
import { useWorkspaceMembers, useAddMember, useRemoveMember, useUpdateMemberRole } from '@/hooks/use-workspaces';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { UserPlus, Trash2, Users, Loader2, Shield, Crown, User } from 'lucide-react';
import { toast } from 'sonner';
import { getApiErrorMessage } from '@/lib/axios';

const ROLE_CONFIG = {
  owner: { label: 'Owner', icon: Crown, variant: 'default' as const },
  admin: { label: 'Admin', icon: Shield, variant: 'secondary' as const },
  member: { label: 'Member', icon: User, variant: 'outline' as const },
};

export default function MembersPage() {
  const params = useParams();
  const workspaceId = parseInt(params.workspaceId as string);
  const { data: members, isLoading } = useWorkspaceMembers(workspaceId);
  const addMember = useAddMember();
  const removeMember = useRemoveMember();
  const updateRole = useUpdateMemberRole();

  const [inviteOpen, setInviteOpen] = useState(false);
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState('member');
  const [deleteTarget, setDeleteTarget] = useState<{ userId: number; username: string } | null>(null);

  if (isNaN(workspaceId)) return <div>Invalid workspace</div>;

  const handleInvite = async () => {
    const uid = parseInt(userId);
    if (isNaN(uid)) { toast.error('Invalid user ID'); return; }
    try {
      await addMember.mutateAsync({ workspaceId, userId: uid, role });
      toast.success('Member added');
      setInviteOpen(false);
      setUserId('');
      setRole('member');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to add member'));
    }
  };

  const handleRemove = async () => {
    if (!deleteTarget) return;
    try {
      await removeMember.mutateAsync({ workspaceId, userId: deleteTarget.userId });
      toast.success('Member removed');
      setDeleteTarget(null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to remove member'));
    }
  };

  const handleRoleChange = async (targetUserId: number, newRole: string) => {
    try {
      await updateRole.mutateAsync({ workspaceId, userId: targetUserId, role: newRole });
      toast.success('Role updated');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to update role'));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-6 w-6" /> Members
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {members ? `${members.length} member${members.length !== 1 ? 's' : ''}` : 'Loading...'}
          </p>
        </div>

        <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <UserPlus className="h-4 w-4 mr-1" /> Invite Member
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Invite Member</DialogTitle></DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <label className="text-sm font-medium">User ID</label>
                <Input
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="Enter user ID"
                  type="number"
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Role</label>
                <Select value={role} onValueChange={setRole}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="member">Member</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleInvite} disabled={addMember.isPending}>
                {addMember.isPending ? 'Adding...' : 'Add Member'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Member List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      ) : members && members.length > 0 ? (
        <div className="rounded-lg border divide-y">
          {members.map((m) => {
            const roleConfig = ROLE_CONFIG[m.role as keyof typeof ROLE_CONFIG] || ROLE_CONFIG.member;
            const Icon = roleConfig.icon;
            return (
              <div key={m.user_id} className="flex items-center justify-between p-4 hover:bg-muted/30 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold text-primary">
                    {(m.username || '?')[0].toUpperCase()}
                  </div>
                  <div>
                    <p className="font-medium text-sm">{m.username || `User #${m.user_id}`}</p>
                    <p className="text-xs text-muted-foreground">
                      Joined {new Date(m.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Select
                    value={m.role}
                    onValueChange={(newRole) => handleRoleChange(m.user_id, newRole)}
                  >
                    <SelectTrigger className="w-28 h-8 text-xs">
                      <Icon className="h-3 w-3 mr-1" />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="owner">Owner</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="member">Member</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={() => setDeleteTarget({ userId: m.user_id, username: m.username || `User #${m.user_id}` })}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-lg border p-6 text-center text-sm text-muted-foreground">
          No members found. Use the invite button to add members.
        </div>
      )}

      {/* Delete confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove {deleteTarget?.username}?</AlertDialogTitle>
            <AlertDialogDescription>This member will lose access to the workspace.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemove}>Remove</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

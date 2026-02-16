import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface WorkspaceStore {
  activeWorkspaceId: number | null;
  setActiveWorkspaceId: (id: number) => void;
}

export const useWorkspaceStore = create<WorkspaceStore>()(
  persist(
    (set) => ({
      activeWorkspaceId: null,
      setActiveWorkspaceId: (id) => set({ activeWorkspaceId: id }),
    }),
    {
      name: 'workspace-storage',
    }
  )
);

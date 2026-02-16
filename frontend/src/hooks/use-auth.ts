import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import api from '@/lib/axios';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
  setUser: (user: User) => void;
  fetchUser: () => Promise<void>;
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (token: string) => {
        set({ token, isAuthenticated: true });
      },
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      },
      setUser: (user: User) => set({ user }),
      fetchUser: async () => {
        try {
          const { data } = await api.get<User>('/auth/me');
          set({ user: data });
        } catch (error) {
          console.error('Failed to fetch user', error);
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    }
  )
);

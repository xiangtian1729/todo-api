'use client';

import { useTheme } from 'next-themes';
import { useAuth } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Settings, Sun, Moon, Monitor, LogOut } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';

export function SidebarSettings() {
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();

  return (
    <div className="border-t p-2">
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="ghost" className="w-full justify-start gap-2">
            <Settings className="h-4 w-4" />
            <span className="text-sm">Settings</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent side="top" align="start" className="w-56">
          <div className="space-y-3">
            {/* User info */}
            {user && (
              <>
                <div className="space-y-1">
                  <p className="text-sm font-medium">{user.username}</p>
                  <p className="text-xs text-muted-foreground">User ID: {user.id}</p>
                </div>
                <Separator />
              </>
            )}

            {/* Theme toggle */}
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">Theme</Label>
              <div className="flex gap-1">
                <Button
                  variant={theme === 'light' ? 'secondary' : 'ghost'}
                  size="sm"
                  className="flex-1 gap-1"
                  onClick={() => setTheme('light')}
                >
                  <Sun className="h-3.5 w-3.5" />
                  <span className="text-xs">Light</span>
                </Button>
                <Button
                  variant={theme === 'dark' ? 'secondary' : 'ghost'}
                  size="sm"
                  className="flex-1 gap-1"
                  onClick={() => setTheme('dark')}
                >
                  <Moon className="h-3.5 w-3.5" />
                  <span className="text-xs">Dark</span>
                </Button>
                <Button
                  variant={theme === 'system' ? 'secondary' : 'ghost'}
                  size="sm"
                  className="flex-1 gap-1"
                  onClick={() => setTheme('system')}
                >
                  <Monitor className="h-3.5 w-3.5" />
                  <span className="text-xs">Auto</span>
                </Button>
              </div>
            </div>

            <Separator />

            {/* Logout */}
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start gap-2 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950"
              onClick={logout}
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="text-xs">Log out</span>
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Must mock BEFORE importing the component
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}))

vi.mock('next/navigation', () => ({
  usePathname: () => '/',
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/hooks/use-workspace-store', () => ({
  useWorkspaceStore: () => ({ activeWorkspaceId: 1, setActiveWorkspaceId: vi.fn() }),
}))

vi.mock('@/hooks/use-workspaces', () => ({
  useWorkspaces: () => ({
    data: { items: [{ id: 1, name: 'Test Workspace', role: 'owner', created_by: 1, created_at: '', updated_at: '' }], total: 1 },
    isLoading: false,
  }),
  useCreateWorkspace: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useWorkspaceMembers: () => ({ data: [], isLoading: false }),
  useUsernameLookup: () => ({ lookup: {}, resolve: (id: number) => `User #${id}` }),
}))

vi.mock('@/hooks/use-projects', () => ({
  useProjects: () => ({
    data: { items: [{ id: 1, name: 'Test Project', workspace_id: 1, created_by: 1, created_at: '', updated_at: '' }], total: 1 },
    isLoading: false,
  }),
  useCreateProject: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteProject: () => ({ mutateAsync: vi.fn() }),
  useUpdateProject: () => ({ mutateAsync: vi.fn() }),
}))

vi.mock('next-themes', () => ({
  useTheme: () => ({ theme: 'system', setTheme: vi.fn() }),
}))

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

// Import after mocks
import Sidebar from '@/components/dashboard/sidebar'

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('Sidebar', () => {
  it('renders the app name', () => {
    renderWithQuery(<Sidebar />)
    expect(screen.getByText('Todo App')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    renderWithQuery(<Sidebar />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Members')).toBeInTheDocument()
    expect(screen.getByText('Audit Log')).toBeInTheDocument()
  })

  it('renders project list', () => {
    renderWithQuery(<Sidebar />)
    expect(screen.getByText('Test Project')).toBeInTheDocument()
  })
})

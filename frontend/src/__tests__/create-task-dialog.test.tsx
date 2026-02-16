import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CreateTaskDialog } from '@/components/tasks/create-task-dialog'

// Mock use-tasks hook
const mockMutateAsync = vi.fn()
vi.mock('@/hooks/use-tasks', () => ({
  useCreateTask: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useParams: () => ({ workspaceId: '1', projectId: '2' }),
}))

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

describe('CreateTaskDialog', () => {
  beforeEach(() => {
    mockMutateAsync.mockReset()
  })

  it('renders the trigger button', () => {
    renderWithQuery(<CreateTaskDialog workspaceId={1} projectId={2} />)
    expect(screen.getByText('New Task')).toBeInTheDocument()
  })

  it('opens dialog when button is clicked', async () => {
    renderWithQuery(<CreateTaskDialog workspaceId={1} projectId={2} />)
    fireEvent.click(screen.getByText('New Task'))
    await waitFor(() => {
      expect(screen.getByText('Create Task')).toBeInTheDocument()
    })
  })
})

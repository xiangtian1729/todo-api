import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ── Mocks ─────────────────────────────────────────────
const mockUpdateStatus = vi.fn()

vi.mock('@/hooks/use-tasks', () => ({
  useFilteredTasks: () => ({
    data: {
      items: [
        { id: 1, title: 'Task A', status: 'todo', workspace_id: 1, project_id: 2, creator_id: 1, version: 1, created_at: '', updated_at: '' },
        { id: 2, title: 'Task B', status: 'in_progress', workspace_id: 1, project_id: 2, creator_id: 1, version: 1, created_at: '', updated_at: '' },
        { id: 3, title: 'Task Done', status: 'done', workspace_id: 1, project_id: 2, creator_id: 1, version: 1, created_at: '', updated_at: '' },
      ],
      total: 3,
    },
    isLoading: false,
  }),
  useUpdateTaskStatus: () => ({
    mutateAsync: mockUpdateStatus,
    isPending: false,
  }),
}))

vi.mock('@/hooks/use-workspaces', () => ({
  useWorkspaceMembers: () => ({ data: [], isLoading: false }),
  useUsernameLookup: () => ({ lookup: {}, resolve: (id: number) => `User #${id}` }),
}))

vi.mock('@/components/tasks/task-detail-sheet', () => ({
  TaskDetailSheet: () => null,
}))

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

// dnd-kit stubs (no actual drag-and-drop in jsdom)
vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DragOverlay: () => null,
  closestCorners: vi.fn(),
  PointerSensor: class {},
  KeyboardSensor: class {},
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
  useDroppable: () => ({ setNodeRef: vi.fn(), isOver: false }),
}))

vi.mock('@dnd-kit/sortable', () => ({
  SortableContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  sortableKeyboardCoordinates: vi.fn(),
  verticalListSortingStrategy: vi.fn(),
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
}))

vi.mock('@dnd-kit/utilities', () => ({
  CSS: { Transform: { toString: () => '' } },
}))

import { KanbanBoard } from '@/components/tasks/kanban-board'

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('KanbanBoard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all four column headers', () => {
    renderWithQuery(<KanbanBoard workspaceId={1} projectId={2} />)
    expect(screen.getByText('To Do')).toBeInTheDocument()
    expect(screen.getByText('In Progress')).toBeInTheDocument()
    expect(screen.getByText('Blocked')).toBeInTheDocument()
    expect(screen.getByText('Done')).toBeInTheDocument()
  })

  it('renders tasks in the correct columns', () => {
    renderWithQuery(<KanbanBoard workspaceId={1} projectId={2} />)
    expect(screen.getByText('Task A')).toBeInTheDocument()
    expect(screen.getByText('Task B')).toBeInTheDocument()
    expect(screen.getByText('Task Done')).toBeInTheDocument()
  })

  it('shows filter bar with status and assignee selects', () => {
    renderWithQuery(<KanbanBoard workspaceId={1} projectId={2} />)
    expect(screen.getByText('All statuses')).toBeInTheDocument()
    expect(screen.getByText('Any assignee')).toBeInTheDocument()
  })

  it('shows tag filter input', () => {
    renderWithQuery(<KanbanBoard workspaceId={1} projectId={2} />)
    expect(screen.getByPlaceholderText('Filter by tag...')).toBeInTheDocument()
  })

  it('does not show "Clear filters" button when no filters active', () => {
    renderWithQuery(<KanbanBoard workspaceId={1} projectId={2} />)
    expect(screen.queryByText('Clear filters')).not.toBeInTheDocument()
  })

  it('shows "Clear filters" button when tag filter is applied', async () => {
    renderWithQuery(<KanbanBoard workspaceId={1} projectId={2} />)
    const tagInput = screen.getByPlaceholderText('Filter by tag...')
    fireEvent.change(tagInput, { target: { value: 'bug' } })
    fireEvent.keyDown(tagInput, { key: 'Enter' })
    await waitFor(() => {
      expect(screen.getByText('Clear filters')).toBeInTheDocument()
    })
  })
})

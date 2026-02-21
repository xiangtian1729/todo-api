import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ── Shared mocks ──────────────────────────────────────
vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

// ── Members page permission tests ─────────────────────
const mockAddMember = vi.fn()
const mockLookupUser = vi.fn()

vi.mock('@/hooks/use-workspaces', () => ({
  useWorkspaceMembers: () => ({
    data: [
      { user_id: 1, username: 'alice', role: 'owner', created_at: '2024-01-01', updated_at: '2024-01-01' },
      { user_id: 2, username: 'bob', role: 'member', created_at: '2024-01-02', updated_at: '2024-01-02' },
    ],
    isLoading: false,
  }),
  useAddMember: () => ({ mutateAsync: mockAddMember, isPending: false }),
  useRemoveMember: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUpdateMemberRole: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useLookupUserByUsername: () => ({ mutateAsync: mockLookupUser, isPending: false }),
}))

vi.mock('@/lib/axios', () => ({
  getApiErrorMessage: (_e: unknown, fb: string) => fb,
}))

// Import after mocks
import MembersPage from '@/app/(dashboard)/workspaces/[workspaceId]/members/page'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ workspaceId: '1' }),
}))

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('MembersPage – username-based invitation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders member list', () => {
    renderWithQuery(<MembersPage />)
    expect(screen.getByText('alice')).toBeInTheDocument()
    expect(screen.getByText('bob')).toBeInTheDocument()
  })

  it('shows Invite Member button', () => {
    renderWithQuery(<MembersPage />)
    expect(screen.getByRole('button', { name: /invite member/i })).toBeInTheDocument()
  })

  it('opens invite dialog with username input (not user ID)', async () => {
    renderWithQuery(<MembersPage />)
    fireEvent.click(screen.getByRole('button', { name: /invite member/i }))
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter username')).toBeInTheDocument()
      // Should NOT have a numeric user-id input
      expect(screen.queryByPlaceholderText(/user id/i)).not.toBeInTheDocument()
    })
  })

  it('looks up user by username and enables Add Member', async () => {
    mockLookupUser.mockResolvedValueOnce({ id: 99, username: 'charlie', is_active: true, created_at: '' })

    renderWithQuery(<MembersPage />)
    fireEvent.click(screen.getByRole('button', { name: /invite member/i }))

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter username')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText('Enter username'), { target: { value: 'charlie' } })
    fireEvent.keyDown(screen.getByPlaceholderText('Enter username'), { key: 'Enter' })

    await waitFor(() => {
      expect(mockLookupUser).toHaveBeenCalledWith('charlie')
      expect(screen.getByText('charlie')).toBeInTheDocument()
    })
  })

  it('calls addMember with resolved user ID after lookup', async () => {
    mockLookupUser.mockResolvedValueOnce({ id: 99, username: 'charlie', is_active: true, created_at: '' })
    mockAddMember.mockResolvedValueOnce({})

    renderWithQuery(<MembersPage />)
    fireEvent.click(screen.getByRole('button', { name: /invite member/i }))

    await waitFor(() => screen.getByPlaceholderText('Enter username'))
    fireEvent.change(screen.getByPlaceholderText('Enter username'), { target: { value: 'charlie' } })
    fireEvent.keyDown(screen.getByPlaceholderText('Enter username'), { key: 'Enter' })

    await waitFor(() => screen.getByText('found'))

    const addBtn = screen.getByRole('button', { name: /add member/i })
    fireEvent.click(addBtn)

    await waitFor(() => {
      expect(mockAddMember).toHaveBeenCalledWith(
        expect.objectContaining({ userId: 99, role: 'member' })
      )
    })
  })
})

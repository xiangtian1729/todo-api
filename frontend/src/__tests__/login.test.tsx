import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ── Mocks ─────────────────────────────────────────────
// NOTE: vi.mock factories are hoisted to the top of the file by Vitest, so
// variables defined in the test module scope are NOT available inside them.
// We use vi.fn() inside the factory and access the mock via a module import.

const mockPush = vi.fn()
const mockReplace = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
}))

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}))

const mockLogin = vi.fn()
const mockFetchUser = vi.fn()

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({
    login: mockLogin,
    fetchUser: mockFetchUser,
    isAuthenticated: false,
  }),
}))

// Use the async factory form so that Vitest resolves the real module first,
// then we override only `default.post` — this avoids the hoisting variable issue.
vi.mock('@/lib/axios', () => ({
  default: { post: vi.fn() },
  getApiErrorMessage: (_e: unknown, fb: string) => fb,
}))

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

// Import AFTER mocks
import LoginPage from '@/app/(auth)/login/page'
import api from '@/lib/axios'
import { toast } from 'sonner'

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the login form', () => {
    renderWithQuery(<LoginPage />)
    expect(screen.getByText('Login to Todo App')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter your username')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('shows a link to the register page', () => {
    renderWithQuery(<LoginPage />)
    const link = screen.getByRole('link', { name: /register/i })
    expect(link).toHaveAttribute('href', '/register')
  })

  it('submits credentials and calls login on success', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { access_token: 'test-token' } })
    mockFetchUser.mockResolvedValueOnce(undefined)

    renderWithQuery(<LoginPage />)

    fireEvent.change(screen.getByPlaceholderText('Enter your username'), {
      target: { value: 'alice' },
    })
    fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
      target: { value: 'secret' },
    })
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test-token')
      expect(mockFetchUser).toHaveBeenCalled()
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  it('shows error toast on login failure', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Unauthorized'))

    renderWithQuery(<LoginPage />)

    fireEvent.change(screen.getByPlaceholderText('Enter your username'), {
      target: { value: 'bad' },
    })
    fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
      target: { value: 'wrong' },
    })
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled()
      expect(mockLogin).not.toHaveBeenCalled()
    })
  })

  it('disables the submit button while loading', async () => {
    vi.mocked(api.post).mockReturnValueOnce(new Promise(() => {}))

    renderWithQuery(<LoginPage />)

    fireEvent.change(screen.getByPlaceholderText('Enter your username'), {
      target: { value: 'alice' },
    })
    fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
      target: { value: 'secret' },
    })

    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /logging in/i })).toBeDisabled()
    })
  })
})

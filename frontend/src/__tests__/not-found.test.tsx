import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import NotFound from '@/app/not-found'

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}))

describe('NotFound page', () => {
  it('renders heading and back button', () => {
    render(<NotFound />)
    expect(screen.getByText('Page Not Found')).toBeInTheDocument()
    expect(screen.getByText('Back to Dashboard')).toBeInTheDocument()
  })

  it('links back to dashboard', () => {
    render(<NotFound />)
    const link = screen.getByRole('link', { name: 'Back to Dashboard' })
    expect(link).toHaveAttribute('href', '/')
  })
})

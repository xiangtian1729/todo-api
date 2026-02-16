import { test, expect } from '@playwright/test'

// ─── Core User Flow E2E ──────────────────────────────────────
// Prerequisites:
//   1. Backend running on http://localhost:8000 with clean DB
//   2. Frontend running on http://localhost:3000
//
// Run: npx playwright test

const TEST_USER = {
  username: `e2e_user_${Date.now()}`,
  password: 'TestPassword123!',
}

test.describe('Core User Flow', () => {

  test('Register → Login → Dashboard', async ({ page }) => {
    // ─── Step 1: Register ─────────────────────────────
    await page.goto('/register')
    await expect(page.getByText('Register for Todo App')).toBeVisible()

    await page.getByPlaceholder('Choose a username').fill(TEST_USER.username)
    await page.getByPlaceholder('Choose a password').fill(TEST_USER.password)
    await page.getByPlaceholder('Confirm your password').fill(TEST_USER.password)

    await page.getByRole('button', { name: 'Register' }).click()

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 })

    // ─── Step 2: Login ────────────────────────────────
    await page.getByPlaceholder('Enter your username').fill(TEST_USER.username)
    await page.getByPlaceholder('Enter your password').fill(TEST_USER.password)
    await page.getByRole('button', { name: 'Login' }).click()

    // Should reach dashboard (sidebar with Todo App title)
    await expect(page.getByText('Todo App')).toBeVisible({ timeout: 5000 })
  })

  test('Login page renders correctly', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('Login to Todo App')).toBeVisible()
    await expect(page.getByPlaceholder('Enter your username')).toBeVisible()
    await expect(page.getByPlaceholder('Enter your password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible()
    await expect(page.getByText("Don't have an account?")).toBeVisible()
  })

  test('Register page renders correctly', async ({ page }) => {
    await page.goto('/register')
    await expect(page.getByText('Register for Todo App')).toBeVisible()
    await expect(page.getByPlaceholder('Choose a username')).toBeVisible()
    await expect(page.getByPlaceholder('Choose a password')).toBeVisible()
    await expect(page.getByPlaceholder('Confirm your password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Register' })).toBeVisible()
  })

  test('Unauthenticated user redirected to login', async ({ page }) => {
    await page.goto('/')
    // Middleware should redirect to /login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
  })

  test('404 page renders', async ({ page }) => {
    await page.goto('/this-page-does-not-exist')
    await expect(page.getByText(/not found/i)).toBeVisible({ timeout: 5000 })
  })
})

# Master-Level Frontend Development Prompt: Todo API V2 Client

You are an expert Senior Frontend Engineer and UI/UX Designer specializing in building production-grade, scalable, and aesthetically pleasing web applications. Your task is to build a modern frontend for the **Todo API V2** backend.

## 🎯 Objective
Build a robust, responsive, and type-safe frontend application using the **Next.js 14+ (App Router)** framework that fully consumes the Todo API V2. The application must support multi-tenant workspaces, project management, task boards, and real-time-like collaboration features.

## 🛠 Tech Stack Requirements
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript (Strict Mode)
- **Styling:** Tailwind CSS (Utility-first) + **Shadcn UI** (Component Library) + **Lucide React** (Icons)
- **State Management:**
  - **Server State:** TanStack Query (React Query) v5 — *Critical for async handling, caching, and optimistic updates.*
  - **Client State:** Zustand (for global UI state like sidebar toggle, current workspace specific context).
- **Form Handling:** React Hook Form + Zod (Schema validation).
- **Routing:** Next.js App Router (dynamic segments, layouts, loading UIs).
- **HTTP Client:** Axios (or strongly-typed fetch wrapper) with Interceptors for JWT handling.
- **Date Handling:** date-fns.

## 🎨 Design & UX Guidelines
- **Visual Style:** Clean, minimalist, modern "SaaS" aesthetic. Use a refined color palette (e.g., Slate/Gray neutrals with a primary brand color like Indigo or Violet).
- **Responsiveness:** Mobile-first approach. Sidebar should be collapsible/drawer on mobile.
- **Feedback:** Use "Toast" notifications (Sonner) for all success/error actions.
- **Loading States:** Use Skeleton loaders instead of spinning spinners where possible.
- **Dark Mode:** Support light/dark theme switching (next-themes).

## 🏗 Architecture & Implementation Steps

### 1. Project Initialization & Core Structure
- Initialize Next.js app with TypeScript, Tailwind, ESLint.
- Setup `src/` directory structure:
  - `components/ui` (Shadcn components)
  - `components/features` (Feature-based: `auth`, `workspace`, `tasks`)
  - `lib/` (Utils, API client, types)
  - `hooks/` (Custom hooks)
  - `app/` (Pages and Layouts)

### 2. Authentication & Security
- Implement Login (`/login`) and Register (`/register`) pages.
- Create an **AuthGuard** (HOC or Middleware) to protect private routes.
- Implement JWT handling:
  - Store Access Token in `localStorage` (or HTTP-only cookie if via Proxy).
  - Axios Interceptor to auto-inject `Authorization: Bearer <token>`.
  - Handle `401 Unauthorized` causing auto-logout.

### 3. Workspace Domain (Multi-tenancy)
- **Layout:** A persistent Sidebar layout that lists user's workspaces.
- **Switching:** Ability to switch active workspace context.
- **Creation:** Modal to create new workspaces.
- **Members:** View and manage workspace members (RBAC display).

### 4. Project & Task Management
- **Projects List:** Sidebar navigation for projects within a workspace.
- **Task Board (Kanban):** Drag-and-drop interface (using `dnd-kit`) for task status (`todo` -> `in_progress` -> `done`).
- **Task List (Table):** Datatable view with sorting and filtering.
- **Filters:** Implement URL-driven filtering (e.g., `?status=todo&assignee=1`).
- **Task Details:** Slide-over or Modal view for editing task details, adding comments, and tags.

### 5. Advanced Features
- **Optimistic Updates:** When moving a task card, UI updates immediately before server confirms.
- **Infinite Scroll/Pagination:** For Audit Logs and long Task lists.
- **Error Boundaries:** Graceful handling of component crashes.

## 📝 Code Quality Checklist
- [ ] **Strict Typing:** No `any`. Define interfaces for all API responses (User, Workspace, Task, etc.).
- [ ] **Component Composition:** Break down complex views into small, single-responsibility components.
- [ ] **Server vs Client:** Use Server Components for initial data fetching where appropriate, Client Components for interactivity.
- **Comments:** Document complex logic, especially in hooks and state managers.

## 🚀 Deliverables
Start by setting up the project structure and the Authentication flow. Once that is robust, proceed to the Workspace and Project dashboard layouts.

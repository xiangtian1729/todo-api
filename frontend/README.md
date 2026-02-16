# Todo API Frontend

基于 Next.js 16 + Shadcn UI 构建的任务管理前端。

## Quick Start

### 前置条件

- Node.js 18.17+
- 后端 API 运行在 `http://localhost:8000`

### 安装 & 启动

```bash
cd frontend
npm install
cp .env.example .env.local   # 配置 API 地址
npm run dev
```

打开 [http://localhost:3000](http://localhost:3000)

### Docker 部署

```bash
docker build -t todo-frontend .
docker run -p 3000:3000 todo-frontend
```

> 或直接在项目根目录使用 `docker-compose up --build` 一键启动全栈。

## 功能列表

| 模块 | 功能 |
|------|------|
| **认证** | 登录 / 注册，JWT Token 管理，已登录自动跳转 |
| **Workspace** | 创建 / 切换工作空间 |
| **成员管理** | 邀请成员、分配角色（owner / admin / member）、移除 |
| **项目** | 创建 / 重命名 / 删除项目，侧边栏导航 |
| **任务看板** | Kanban 拖拽状态切换（To Do → In Progress → Blocked → Done） |
| **任务详情** | 滑出面板：编辑标题 / 描述 / 截止日期，删除确认 |
| **评论** | 任务评论的查看 / 发表 / 删除 |
| **标签 & 关注** | 通过 API hooks 支持标签和关注者管理 |
| **审计日志** | 分页表格，展示操作记录（时间 / 用户 / 动作 / 变更详情） |
| **主题** | 亮色 / 暗色 / 跟随系统 |

## 项目结构

```
frontend/
├── src/
│   ├── app/                         # Next.js App Router 路由
│   │   ├── (auth)/                  # 登录 / 注册页面
│   │   ├── (dashboard)/             # 认证后页面（共享 Sidebar 布局）
│   │   │   ├── page.tsx             # Dashboard 首页
│   │   │   └── workspaces/[wid]/
│   │   │       ├── members/         # 成员管理页
│   │   │       ├── audit/           # 审计日志页
│   │   │       └── projects/[pid]/  # 项目 Kanban 页
│   │   ├── error.tsx                # 全局错误边界
│   │   └── not-found.tsx            # 自定义 404
│   ├── components/
│   │   ├── dashboard/               # Sidebar, WorkspaceSwitcher, ProjectList
│   │   ├── tasks/                   # KanbanBoard, TaskDetailSheet, CreateTaskDialog
│   │   └── ui/                      # Shadcn UI 基础组件
│   ├── hooks/                       # React Query + Zustand hooks
│   │   ├── use-auth.ts              # 登录 / 注册 / 登出
│   │   ├── use-workspaces.ts        # Workspace + 成员管理 CRUD
│   │   ├── use-projects.ts          # Project CRUD
│   │   ├── use-tasks.ts             # Task CRUD + 筛选
│   │   ├── use-collaboration.ts     # 评论 / 标签 / 关注者
│   │   └── use-audit.ts             # 审计日志
│   ├── lib/
│   │   └── axios.ts                 # API 客户端（环境变量 + 错误处理）
│   └── types/
│       └── index.ts                 # 共享类型定义
├── .env.example                     # 环境变量模板
├── Dockerfile                       # 多阶段生产构建
├── .dockerignore                    # Docker 构建排除
└── next.config.ts                   # Next.js 配置（standalone 输出）
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Next.js 16 (App Router, Turbopack) |
| UI 库 | Shadcn UI + Tailwind CSS v4 |
| 服务端状态 | TanStack Query v5 |
| 客户端状态 | Zustand (persist) |
| 表单 | React Hook Form + Zod |
| 拖拽 | @dnd-kit |
| HTTP | Axios |
| 主题 | next-themes |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8000` |

## npm 脚本

| 命令 | 说明 |
|------|------|
| `npm run dev` | 开发服务器（Turbopack） |
| `npm run build` | 生产构建 |
| `npm run start` | 运行生产构建 |
| `npm run lint` | ESLint 检查 |

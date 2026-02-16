# ==========================================
# Todo Frontend Dockerfile (Multi-stage)
# ==========================================
# 利用 Next.js standalone 输出模式，最终镜像只包含运行时需要的文件。
#
# 构建镜像: docker build -t todo-frontend .
# 运行容器: docker run -p 3000:3000 todo-frontend
# ==========================================

# ---------- Stage 1: 依赖安装 ----------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# ---------- Stage 2: 构建 ----------
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# 构建时传入 API URL（可通过 docker-compose 的 build args 覆盖）
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

# ---------- Stage 3: 运行 ----------
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制 standalone 输出（包含 server.js + 最小化的 node_modules）
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]

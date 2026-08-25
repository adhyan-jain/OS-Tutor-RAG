# Frontend image for the os-tutor-rag Next.js UI.
#
# Build context is frontend/ itself (unlike api/Dockerfile, nothing here
# needs the repo root):
#
#   docker build -f frontend/Dockerfile -t os-tutor-rag-frontend frontend/
#
# NEXT_PUBLIC_API_BASE is a *browser*-visible env var: Chat.tsx ("use client")
# calls fetch()/postChat() from inside the user's browser, not from the
# Next.js server, so this must be a URL the browser itself can reach -- e.g.
# http://localhost:8000, the backend's port as published on the host --
# never the compose-network name (http://backend:8000), which only resolves
# between containers, not from the host browser. Because Next.js inlines
# NEXT_PUBLIC_* vars into the client bundle at build time, it must be passed
# as a build ARG here, not just a runtime `environment:` entry in
# docker-compose.yml (a runtime-only env var would have no effect on the
# already-built client bundle).

# ---- build stage ----
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}

RUN npm run build

# ---- runtime stage: Next's standalone output (see next.config.ts) ----
FROM node:20-slim AS runtime

WORKDIR /app
ENV NODE_ENV=production PORT=3000

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]

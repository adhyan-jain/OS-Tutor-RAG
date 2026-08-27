# OS-Tutor-RAG frontend

Next.js (App Router) chat UI for the OS-Tutor-RAG backend. See the
[repo root README](../README.md) for the full project overview, and
[DEPLOYMENT.md](../DEPLOYMENT.md) for Docker/deployment.

## Getting started

```bash
npm install
npm run dev
```

Opens at `http://localhost:3000`, talking to the backend at
`http://localhost:8000` by default (override with `NEXT_PUBLIC_API_BASE`).
The backend must already be running (`PYTHONPATH=. .venv/bin/uvicorn
api.main:app --port 8000` from the repo root) with an index built and Ollama
reachable.

## Notable pieces

- `components/Chat.tsx` — main orchestrator: multi-session state, SSE
  streaming, stop/regenerate/copy.
- `components/Sidebar.tsx` — session list (new/rename/delete), backed by
  `lib/sessionStore.ts` (localStorage).
- `components/AuthGate.tsx` / `auth.ts` — gated Google OAuth, a no-op when
  `NEXT_PUBLIC_AUTH_ENABLED` is unset/false (the default).
- `lib/sse.ts` — hand-rolled SSE-over-fetch parser (`EventSource` can't send
  a POST body, which `/chat` needs).
- Fonts are IBM Plex Sans/Mono (`app/layout.tsx`), not the create-next-app
  default.

This app is deployed via Docker (see `Dockerfile` + the repo root's
`docker-compose.yml`), not Vercel — the backend it depends on is a local
FastAPI process talking to a local Ollama instance, which Vercel's hosting
model doesn't fit.

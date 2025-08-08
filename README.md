# Unfold – MVP (My Story + AI Coach)

This repository contains a React + FastAPI + MongoDB app implementing the Unfold MVP: a “Living Story” editor and an AI Coach with multi‑provider support.

- Frontend: React 19 + craco (port 3000)
- Backend: FastAPI (bound to 0.0.0.0:8001 via supervisor)
- Database: MongoDB (from backend/.env)
- All backend routes are under `/api`; frontend must call `REACT_APP_BACKEND_URL`

## Quick Start (Platform)
- Services are already managed by supervisor
- Restart after env or dependency changes:
```
sudo supervisorctl restart frontend
sudo supervisorctl restart backend
```
- Logs:
```
tail -n 100 /var/log/supervisor/backend.*.log
tail -n 100 /var/log/supervisor/frontend.*.log
```

## Navigation
- Dashboard: `/` – hero, quick tiles, backend status
- My Story: `/story` – Living Story editor with autosave and resonance slider
- Coach: `/coach` – AI chat with provider info

## API Endpoints (Backend)
- GET `/api/` – Hello world
- GET `/api/health` – Status
- GET `/api/provider-info` – Provider + model
- POST `/api/chat` – AI response (multi-provider)
- POST `/api/story/init` – Initialize or fetch story by `clientId`
- PUT `/api/story/save` – Save sections + resonance; increments version
- GET `/api/story/{storyId}` – Fetch story by id

## Environment & Keys
- Do not change URL/ports in `.env`
- Backend AI configuration (set in backend environment variables):
  - OpenAI: `AI_PROVIDER=openai`, `OPENAI_API_KEY=...`, optional `OPENAI_MODEL=gpt-4o`
  - Anthropic: `AI_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=...`, optional `ANTHROPIC_MODEL=claude-3.5-sonnet`
  - Gemini (optional): `AI_PROVIDER=gemini`, `GOOGLE_API_KEY=...`, optional `GEMINI_MODEL=gemini-1.5-flash`
- Database: `MONGO_URL`, `DB_NAME` already provided in `backend/.env`

## Testing
- Provider info:
```
curl -sS "$REACT_APP_BACKEND_URL/api/provider-info"
```
- Chat (after key set):
```
curl -sS -X POST "$REACT_APP_BACKEND_URL/api/chat" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hi, can you help me reflect on my week?"}]}'
```
- Story init:
```
curl -sS -X POST "$REACT_APP_BACKEND_URL/api/story/init" -H "Content-Type: application/json" \
  -d '{"clientId":"demo-client"}'
```

## Development Notes
- Follow the `/api` prefix rule for all backend routes (K8s ingress)
- Frontend must only use `process.env.REACT_APP_BACKEND_URL` for API calls
- Use `yarn` for JS deps; add Python deps to `backend/requirements.txt` then install
- Mongo ObjectIDs are not returned; only UUIDs (easier JSON handling)

## Implementation Details
See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for full design, contracts, and next milestones.
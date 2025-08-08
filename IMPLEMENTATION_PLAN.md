# Implementation Plan

This document describes what was implemented for the Unfold MVP (My Story + AI Coach), the architecture, API contracts, environment configuration, navigation, testing, and next steps aligned with the UI/UX and user flows.

## 1) Scope Delivered (Phase 1 MVP)
- Multi‑provider AI Coach endpoint with therapeutic safety prompt
  - Providers supported via env: OpenAI, Anthropic Claude, Google Gemini (optional)
  - Endpoints:
    - POST `/api/chat` – returns assistant reply and meta (provider, model)
    - GET `/api/provider-info` – shows current provider and model
    - GET `/api/health` – basic status
- My Story System (MVP)
  - Anonymous client identity in browser (UUID in localStorage)
  - Endpoints:
    - POST `/api/story/init` – init or fetch story by clientId
    - PUT `/api/story/save` – save sections and resonance; increments version, keeps small history
    - GET `/api/story/{storyId}` – fetch story
  - Only UUIDs used in payloads (Mongo `_id` removed before returning)
- Frontend Navigation and Pages
  - Navbar with tabs: Dashboard `/`, My Story `/story`, Coach `/coach`
  - Dashboard: hero + quick tiles + backend status
  - My Story: editor with autosave + resonance slider + version indicator
  - Coach: chat UI that calls `/api/chat` and shows provider info

## 2) Tech Stack & Key Rules
- Frontend: React 19 + craco + Tailwind (preconfigured), axios
- Backend: FastAPI + Motor (Mongo)
- Database: MongoDB (URL from backend/.env)
- Critical routing & env rules (per platform):
  - All backend API routes MUST be prefixed with `/api`
  - Frontend MUST call backend using `process.env.REACT_APP_BACKEND_URL`
  - Backend MUST read Mongo URL from `MONGO_URL` and DB name from `DB_NAME`
  - Backend binds to `0.0.0.0:8001` (handled by supervisor/ingress)
  - Never hardcode URLs or ports in code; use envs only

## 3) Backend Architecture
- File: `backend/server.py`
- Lazy imports for provider SDKs to avoid install issues when unused
- Provider selection strategy:
  1) `AI_PROVIDER` env in {openai|anthropic|gemini}
  2) Fallback: first available key among `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`
- Therapeutic safety prompt applied as a system instruction to all providers
- Story data model (Mongo, single document per client):
```json
{
  "storyId": "uuid",
  "clientId": "uuid",
  "version": 1,
  "sections": {
    "guidingNarrative": "",
    "turningPoints": "",
    "emergingThemes": "",
    "uniqueStrengths": "",
    "futureVision": ""
  },
  "resonanceScore": 7.0,
  "createdAt": "timestamp",
  "updatedAt": "timestamp",
  "history": [
    { "version": 1, "resonanceScore": 7.0, "sections": { ... }, "timestamp": "..." }
  ]
}
```

### API Contracts
- POST `/api/chat`
```json
{
  "messages": [ { "role": "user", "content": "..." } ],
  "temperature": 0.7,
  "max_tokens": 800
}
```
Response 200:
```json
{ "message": { "role": "assistant", "content": "..." },
  "meta": { "provider": "openai", "model": "gpt-4o", "usage": {"prompt_tokens": 10, "completion_tokens": 25, "total_tokens": 35}, "processing_time": 1.23 } }
```
Response 400 (expected until you add an API key):
```json
{ "detail": "Missing OPENAI_API_KEY in backend environment" }
```

- POST `/api/story/init`
```json
{ "clientId": "uuid" }
```
Response 200: Story document (see schema above)

- PUT `/api/story/save`
```json
{
  "storyId": "uuid",
  "clientId": "uuid",
  "sections": { "guidingNarrative": "...", ... },
  "resonanceScore": 7.5
}
```
Response 200: Updated story with incremented `version`

## 4) Frontend Architecture
- Routes (React Router):
  - `/` Dashboard – hero + tiles + provider status
  - `/story` My Story – `StoryEditor` with debounced autosave (1200ms) and resonance slider
  - `/coach` Coach – `CoachChat` component calling `/api/chat`
- Components:
  - `Navbar.jsx` – top navigation
  - `StoryEditor.jsx` – autosave + resonance + version indicator
  - `CoachChat.jsx` – chat UI with typing indicator and error surface

## 5) Environment & Keys
- Do not change existing `.env` files’ URLs/ports
- AI keys (set on backend environment):
  - OpenAI: `AI_PROVIDER=openai`, `OPENAI_API_KEY=...`, optional `OPENAI_MODEL=gpt-4o`
  - Anthropic: `AI_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=...`, optional `ANTHROPIC_MODEL=claude-3.5-sonnet`
  - Gemini (optional; requires package install): `AI_PROVIDER=gemini`, `GOOGLE_API_KEY=...`, optional `GEMINI_MODEL=gemini-1.5-flash`
- Mongo: `backend/.env` already contains `MONGO_URL` and `DB_NAME` (do not modify)

## 6) Running & Logs (Supervisor)
- Services are managed by supervisor; use:
  - `sudo supervisorctl restart all` or restart individually
- Logs:
  - Backend logs: `tail -n 100 /var/log/supervisor/backend.*.log`
  - Frontend logs: `tail -n 100 /var/log/supervisor/frontend.*.log`

## 7) Testing
- Provider info:
```
curl -sS "$REACT_APP_BACKEND_URL/api/provider-info"
```
- Chat (after adding a key):
```
curl -sS -X POST "$REACT_APP_BACKEND_URL/api/chat" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hi FAM, can you help me reflect on my week?"}]}'
```
- Story init/save:
```
curl -sS -X POST "$REACT_APP_BACKEND_URL/api/story/init" -H "Content-Type: application/json" \
  -d '{"clientId":"demo-client"}'
```

## 8) UX Alignment & Navigation
- Calm, dark palette with gentle interactions
- Visible tabs: Dashboard, My Story, Coach
- Story page reflects “Living Story” with resonance scale and autosave
- Coach maintains supportive, non‑clinical tone; clear boundary messaging

## 9) Next Milestones (from UX docs)
- Guided Journey mode for story construction (5 sections with stepper)
- Weekly review flow + resonance history chart
- Insight integration (from Coach) to suggest edits to story sections
- Version history viewer and PDF export
- “Coming soon” placeholders for Pathways, Growth Areas, Routine/Rhythm

## 10) Known Limitations & Mitigations
- `/api/chat` returns 400 until an AI key is provided → add key, restart backend
- Gemini support requires installing `google-generativeai` – left optional in requirements
- Story history limited to last 10 snapshots (MVP); can expand later

---

If you want, I can add sidebar navigation and “Coming soon” tabs for Pathways, Growth Areas, and Routine to match the larger product map.
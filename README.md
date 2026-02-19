# Social Wishlist MVP

Production-ready wishlist app with anonymous reservations, group contributions, realtime updates, and URL metadata parsing.

- Deployed URL: `<FILL_ME>`
- GitHub URL: `<FILL_ME>`

## Monorepo

- `apps/web` — Next.js App Router + Tailwind + TypeScript
- `apps/api` — FastAPI + SQLAlchemy async + Alembic
- `packages/shared` — shared zod types
- `infra` — docker compose (Postgres)

## Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.11
- Docker

## Local Setup

1. Install JS deps:
```bash
pnpm install
```

2. Install API deps:
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cd ../..
```

3. Copy env vars:
```bash
cp .env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

4. Start Postgres:
```bash
make db-up
```

5. Run migrations:
```bash
cd apps/api && alembic upgrade head
```

6. Seed demo data:
```bash
cd apps/api && python seed.py
```

7. Start app:
```bash
make dev
```

- Web: `http://localhost:3000`
- API: `http://localhost:8000`

## Env Vars

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async SQLAlchemy URL |
| `SYNC_DATABASE_URL` | Alembic sync URL |
| `JWT_SECRET` | Access token signing |
| `REFRESH_SECRET` | Refresh token signing |
| `VIEWER_TOKEN_PEPPER` | Hashing anonymous viewer token |
| `WEB_ORIGIN` | Allowed CORS frontend URL |
| `API_ORIGIN` | Backend public URL (for OAuth callback default) |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend -> backend base URL |
| `COOKIE_SECURE` | Secure cookie toggle for production |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret |
| `GOOGLE_REDIRECT_URI` | Optional explicit callback URL |
| `TEST_DATABASE_URL` | Optional isolated DB URL for pytest |
| `TEST_SYNC_DATABASE_URL` | Optional sync URL for pytest DB setup |

## Tests and Lint

```bash
# backend
cd apps/api && pytest
cd apps/api && ruff check . && mypy .

# frontend
cd apps/web && pnpm lint && pnpm typecheck
cd apps/web && pnpm test:e2e
```

## Deployment (Copy/Paste)

### 1) Database (Neon / Supabase / Render)
- Create Postgres instance.
- Copy connection strings:
  - async: `postgresql+asyncpg://...`
  - sync: `postgresql+psycopg://...`

### 2) Backend (Render example)
1. Create new Web Service from repo root, set root directory `apps/api`.
2. Build command:
```bash
pip install -r requirements.txt
```
3. Start command:
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
4. Set env vars:
```bash
DATABASE_URL=postgresql+asyncpg://...
SYNC_DATABASE_URL=postgresql+psycopg://...
JWT_SECRET=<strong-random>
REFRESH_SECRET=<strong-random>
VIEWER_TOKEN_PEPPER=<strong-random>
WEB_ORIGIN=https://<your-vercel-domain>
COOKIE_SECURE=true
```

### 3) Frontend (Vercel)
1. Import repo and set project root to `apps/web`.
2. Set env var:
```bash
NEXT_PUBLIC_API_BASE_URL=https://<your-backend-domain>
```
3. Deploy.

### 4) Final production checks
- Register/login works
- Create wishlist and item works
- Public `/w/{public_id}` opens without auth
- Reservation and contribution update in realtime in multiple tabs
- Owner view shows only anonymous/aggregate data
### Google OAuth setup
1. Create OAuth 2.0 Web credentials in Google Cloud Console.
2. Add authorized redirect URI:
   - local: `http://localhost:8000/api/auth/google/callback`
   - prod: `https://<your-backend-domain>/api/auth/google/callback`
3. Set:
```bash
GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<client-secret>
# optional override, otherwise API_ORIGIN + /api/auth/google/callback is used
GOOGLE_REDIRECT_URI=
```
If client ID/secret are empty, `/api/auth/google/start` redirects back with `oauth_error=google_not_configured`.

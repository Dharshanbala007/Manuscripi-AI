# Hosted deployment

The local app is unchanged (`scripts/dev.sh`). This is the optional hosted demo.

```
Browser ──► Cloudflare (static UI)  https://manuscript-ai.dharshanbala007007.workers.dev
   │
   └──────► Render (FastAPI + LibreOffice, Docker)   https://manuscript-ai-api.onrender.com
                 │
                 └─► Cloudflare Worker ─► D1 (history table)
                     https://manuscript-ai-history.dharshanbala007007.workers.dev
```

| Piece | Where | Source |
|---|---|---|
| UI | Cloudflare Workers static assets | `frontend/wrangler.toml` |
| History API + database | Cloudflare Worker + D1 | `cloudflare/history-worker/` |
| API | Render web service (Docker) | `render.yaml`, `backend/Dockerfile` |

Cloudflare cannot run the Python backend (python-docx, LibreOffice), which is why the API is on Render.
Render's disk is ephemeral, so history is kept in D1 instead of SQLite.

## Privacy is different when hosted

Locally nothing leaves your machine. In the hosted build the `.docx` is **uploaded to the Render server**,
held in `/tmp`, and swept after `WORKSPACE_TTL_MIN` minutes (checked every `WORKSPACE_SWEEP_INTERVAL_MIN`).
History rows hold only the file name, size, state, scores and counts — never manuscript text.
The UI switches its copy on `VITE_HOSTED=true` so it does not claim otherwise.

History is per visitor: the browser sends an anonymous `X-Client-Id` (kept in `localStorage`) and the
server, with `HISTORY_SCOPE_BY_OWNER=true`, only lists or deletes that visitor's rows. No id → empty history.
It is a separator, not a login; anyone who knows another visitor's id could read their history.

## One-time setup

### 1. History database and Worker (Cloudflare)

```bash
cd cloudflare/history-worker
npx wrangler login                          # once
npx wrangler d1 create manuscript-ai-history   # put the printed id in wrangler.toml
npx wrangler d1 execute manuscript-ai-history --remote --file schema.sql
npx wrangler deploy
openssl rand -hex 32                        # generate a token
npx wrangler secret put HISTORY_TOKEN       # paste it
```

### 2. API (Render)

1. Render dashboard → **New → Blueprint** → connect this GitHub repo, branch `master`.
2. Render reads `render.yaml`. When asked for `HISTORY_API_TOKEN`, paste the **same** token as above.
3. Apply. The first build installs LibreOffice and takes several minutes.
4. Check the service URL is `https://manuscript-ai-api.onrender.com`. If Render gave a different one,
   rebuild the UI with that URL (step 3) and update `HISTORY_API_URL`/`CORS_ORIGINS` if you changed those.

### 3. UI (Cloudflare)

```bash
cd frontend
VITE_API_BASE=https://manuscript-ai-api.onrender.com VITE_HOSTED=true npm run build
npx wrangler deploy
```

`VITE_API_BASE` is baked in at build time, so changing the API URL means rebuilding.
`CORS_ORIGINS` on Render must contain the UI's exact origin.

## Operations

- **Rotate the token:** `npx wrangler secret put HISTORY_TOKEN`, then update `HISTORY_API_TOKEN` in Render.
- **Redeploy the Worker:** `cd cloudflare/history-worker && npx wrangler deploy`.
- **Inspect history:** `npx wrangler d1 execute manuscript-ai-history --remote --command "SELECT id, filename, state FROM history LIMIT 20"`.
- A history outage never breaks formatting: writes are best-effort and lists fall back to empty.

## Limits worth knowing

- **Render free plan:** the service sleeps after ~15 minutes idle; the next request takes about a minute.
  Working sessions are in memory, so a restart or sleep ends them (re-upload to continue).
  512 MB RAM is tight for LibreOffice on large documents; move to a paid instance if PDF export fails.
- `backend/Dockerfile` was written without a local Docker install and has not been built on the author's
  machine; the first Render build is its first test. The same backend was run locally with the production
  environment against the live Worker and D1 (upload, format, validate, PDF, history scoping, CORS).
- The UI's `wrangler.toml` deploys Workers static assets, not classic Pages projects, which wrangler now
  steers away from.

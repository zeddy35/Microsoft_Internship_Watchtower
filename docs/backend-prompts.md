# Watchtower — backend prompts (FastAPI)

Stack: FastAPI · Pydantic v2 · DuckDB · ChromaDB · sentence-transformers (bge-m3) ·
openai SDK against a local OpenAI-compatible endpoint (Foundry Local or Ollama) ·
httpx + PyGithub · APScheduler.

Ownership: **Erden** owns the AI core (phases 4–5). **Partner** owns collectors and
notifications (phases 3, 8). Phases 1–2, 6–7, 9 are shared groundwork.

Target layout:

```
apps/backend/
  app/
    main.py            # FastAPI app + startup
    config.py          # pydantic-settings from .env
    core/
      db.py            # DuckDB connection + schema
      schemas.py       # Pydantic models (shared contract with frontend zod types)
    collectors/
      github.py        # GitHub REST -> raw events
      ado.py           # Azure DevOps (optional)
    anomaly/
      engine.py        # rolling baseline + z-score + flags
      bus_factor.py    # ownership concentration
    ai/
      phi4_client.py   # OpenAI-compatible chat client
      embeddings.py    # bge-m3 embeddings
      vectorstore.py   # ChromaDB wrapper
      summarizer.py    # anomalies -> natural-language insight + on-goal scoring
    notify/
      teams.py         # Teams webhook
    api/routes/
      teams.py  metrics.py  anomalies.py  summary.py
  tests/
  requirements.txt
  .env.example
```

Setup once before phase 1:

```bash
cd apps/backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
```

Run each prompt in Claude Code, review the diff, commit, then continue.

---

### Phase 1 — app skeleton + config

```
In apps/backend, create the FastAPI skeleton. app/config.py loads settings from .env
with pydantic-settings (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, EMBEDDING_MODEL,
GITHUB_TOKEN, GITHUB_REPOS, DUCKDB_PATH, CHROMA_PATH, TEAMS_WEBHOOK_URL, CORS_ORIGINS,
API_HOST, API_PORT). app/main.py builds the FastAPI app, adds CORS from CORS_ORIGINS,
and exposes GET /health returning status ok. Add a run script (uvicorn app.main:app
--reload). Keep everything typed.
```

### Phase 2 — DuckDB storage layer

```
Build app/core/db.py: a DuckDB connection helper (path from settings) and a schema
init that creates tables — repos, commits (sha, repo, author, message, additions,
deletions, committed_at), pushes (repo, author, ref, pushed_at), pull_requests (id,
repo, author, opened_at, first_review_at, merged_at, state), and a metrics_daily
rollup (team, metric, day, value). Add typed insert + query helpers for time-series
reads (rolling windows, per-team aggregates). No ORM, plain SQL with parameters.
```

### Phase 3 — GitHub collector  (partner)

```
Build app/collectors/github.py using httpx (async) and PyGithub. For each repo in
GITHUB_REPOS, pull recent commits, pushes, and pull requests, normalize them into the
DuckDB tables from core/db.py, and be incremental (only fetch since the last stored
timestamp). Handle rate limits with backoff. Expose an async collect_all() entrypoint.
Add a thin app/collectors/ado.py stub with the same interface for Azure DevOps, to be
filled if access is granted.
```

### Phase 4 — anomaly engine + bus factor  (Erden)

```
Build app/anomaly/engine.py: compute rolling baselines (mean + std over a trailing
window) per team and metric from metrics_daily, then flag anomalies with z-score plus
rule thresholds — stale PRs (open > 7 days), review-time spike, commit-frequency drop,
push-frequency drop. Return typed Anomaly objects (severity, title, description,
detectedAt, metric, observed vs baseline). Build app/anomaly/bus_factor.py: from commit
authorship per code area, compute ownership concentration and return risk levels
(High > 70%, Medium 50-70%, Low < 50%) with the top owner and their last activity.
```

### Phase 5 — AI core: Phi-4 client, embeddings, vector store, summarizer  (Erden)

```
Build the AI layer against the local OpenAI-compatible endpoint:
- app/ai/phi4_client.py: an openai client using LLM_BASE_URL / LLM_API_KEY / LLM_MODEL,
  with a typed ask(prompt) and a stream(prompt) generator.
- app/ai/embeddings.py: sentence-transformers with EMBEDDING_MODEL (bge-m3), an
  embed(texts) helper.
- app/ai/vectorstore.py: a ChromaDB wrapper (persistent at CHROMA_PATH) to index commit
  messages + PR descriptions and retrieve context for a team.
- app/ai/summarizer.py: given a team's anomalies + retrieved context, prompt Phi-4 to
  produce (1) a plain-English weekly summary, (2) one recommended action, and (3) an
  "on-goal" score — the share of recent commits whose message/diff matches the team's
  stated sprint goal. Return typed results, keep prompts short and deterministic
  (low temperature).
```

### Phase 6 — API routes

```
Build app/api/routes with typed responses that match the frontend zod schemas:
GET /teams (list + status), GET /teams/{id} (detail), GET /teams/{id}/metrics
(KPIs with baseline + delta), GET /teams/{id}/anomalies, GET /teams/{id}/bus-factor,
GET /teams/{id}/summary (Phi-4 summary + on-goal score), and POST /teams/{id}/ask
(streams a Phi-4 answer to a free-text question about the team). Wire routers into
app/main.py. Add response models in core/schemas.py.
```

### Phase 7 — scheduler

```
Add APScheduler to app/main.py: on startup, schedule collectors.collect_all() plus a
metrics rollup and the anomaly pass to run every N minutes (interval from settings).
Guard against overlapping runs. Expose POST /admin/refresh to trigger a run on demand
for demos.
```

### Phase 8 — Teams notifier + weekly digest  (partner)

```
Build app/notify/teams.py: post an adaptive-card style message to TEAMS_WEBHOOK_URL via
httpx when a High-severity anomaly is detected (title, team, the Phi-4 explanation, and
the recommended action). Add a weekly digest job that summarizes the week per team via
the summarizer and posts it. Make posting a no-op with a warning if TEAMS_WEBHOOK_URL
is unset.
```

### Phase 9 — tests

```
Add pytest tests under apps/backend/tests: unit tests for the anomaly engine (feed
synthetic series, assert the right flags fire), the bus-factor calculator, and the
DuckDB helpers; and API tests with FastAPI TestClient for each route using a seeded
in-memory DuckDB and a mocked Phi-4 client. Add a pytest config and a make/psake style
task to run them.
```

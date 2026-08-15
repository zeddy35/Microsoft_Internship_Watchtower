# Watchtower

Engineering-health monitoring for software teams: collect delivery signals,
flag what deviates from a team's own baseline, explain it with a **local**
Phi-4, and check afterwards whether the advice worked.

The last part is the point. Every anomaly Watchtower raises is tracked until it
clears, and the outcome is written back with how long it stayed open and what
was recommended at the time. That log is a labeled dataset the system produced
about itself, which is what the predictive layer trains on.

```
GitHub ──► DuckDB ──► daily rollup ──► anomaly engine ──► resolver (Phi-4 + RAG)
                          ▲                  │                    │
                          │                  ▼                    ▼
                     verify pass ◄──── anomaly_events        Teams alerts
                          │                                  Next.js dashboard
                          ▼
                     resolutions  ← labeled training data
```

Nothing leaves the machine: the model runs against a local OpenAI-compatible
endpoint (Foundry Local or Ollama), embeddings are local, storage is a local
DuckDB file.

## Running it

Two processes. Backend first.

```bash
cd apps/backend
python -m venv .venv && .venv\Scripts\activate      # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env                              # then fill in GITHUB_REPOS
uvicorn app.main:app --reload
```

```bash
cd apps/frontend
npm install
copy .env.example .env.local
npm run dev
```

Then open http://localhost:3000. The API serves http://localhost:8000, with
interactive docs at `/docs`.

The dashboard is empty until the first collection runs. Either wait for the
scheduler tick (`REFRESH_INTERVAL_MINUTES`, default 30) or force one:

```bash
curl -X POST "http://localhost:8000/admin/refresh"
```

Add `?resolve=false` to skip the model, `?collect=false` to skip GitHub.

## What the backend does

| Module | Responsibility |
| --- | --- |
| `app/collectors/github.py` | Incremental pull of commits, pushes, and PRs into DuckDB |
| `app/metrics/rollup.py` | Raw rows → daily per-team series (`metrics_daily`) |
| `app/anomaly/engine.py` | Rolling-baseline z-scores plus rules (stale PRs, drops, spikes) |
| `app/anomaly/bus_factor.py` | Ownership concentration → High/Medium/Low risk |
| `app/ai/vectorstore.py` | ChromaDB index of commit text, embedded with bge-m3 |
| `app/ai/resolver.py` | Phi-4 verdict: summary, root cause, ranked actions, verify signal |
| `app/jobs.py` | The detect → verify → resolve cycle, and the labeling loop |
| `app/notify/teams.py` | Adaptive cards on critical anomalies, weekly digest |
| `app/scheduler.py` | APScheduler jobs, overlap-guarded |

### Design decisions worth knowing

- **Commit and push series are zero-filled; review time is not.** A day with no
  commits is a real zero and has to drag the baseline down. A day with no
  reviewed PR is missing data, and calling it a zero-hour review would make a
  stalled team look fast.
- **The engine only flags moves in the bad direction.** A commit surge is three
  standard deviations from baseline and is not a problem.
- **Summaries are cached, not generated on request.** The scheduled resolver
  pass writes to a `summaries` table, so a page load never blocks on local
  inference, and a model that is not running degrades one card instead of the
  dashboard.
- **Each anomaly alerts exactly once.** `anomaly_events.notified_at` is the
  guard, so a 30-minute refresh is not a 30-minute notification.
- **Timestamps are naive UTC everywhere**, because that is what DuckDB stores;
  the API serializes them with an explicit `Z` so the browser cannot read them
  as local time.

## API

| Endpoint | Returns |
| --- | --- |
| `GET /teams` | Every team, worst health first, with members, bus factor, sparkline |
| `GET /teams/{id}` | One team |
| `GET /teams/{id}/metrics` | Four KPI cards plus the 30-day review-time series |
| `GET /teams/{id}/anomalies` | Open anomalies for the team |
| `GET /teams/{id}/bus-factor` | Ownership concentration per area |
| `GET /teams/{id}/summary` | Cached Phi-4 verdict (404 until one is generated) |
| `POST /teams/{id}/ask` | Streams a grounded Phi-4 answer as plain text |
| `GET /anomalies` | Cross-team feed, filterable by severity |
| `POST /admin/refresh` | Run one full cycle now |
| `GET /admin/resolutions` | The labeled outcome log |

## Tests

```bash
cd apps/backend
pytest          # 58 tests: engine, rollup, bus factor, DuckDB, jobs, API
ruff check app tests
```

The suite touches no network, no filesystem, and no language model: the API
tests run against a seeded in-memory DuckDB with a fake Phi-4 client, so a
failure points at Watchtower's logic rather than at whether the local model
happened to be up.

## Layout

```
apps/backend    FastAPI + DuckDB + ChromaDB + Phi-4
apps/frontend   Next.js dashboard (see apps/frontend/README.md)
docs/           Stitch design exports and the build prompts
DISPATCH.md     The step-by-step build plan this was assembled from
```

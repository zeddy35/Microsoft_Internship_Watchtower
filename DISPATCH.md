# Watchtower — dispatch prompts

Phone-friendly, compact prompts. Send one at a time to Claude Code. Review diff, commit,
next. Claude Code already has CLAUDE.md, the Stitch exports in apps/frontend/docs/stitch/,
and the Fluent tokens in apps/frontend/tailwind.config.ts, so prompts stay short.

Order: F1–F7 (frontend on mock) → B1–B6 (backend) → F8 + B7–B9 (wire up) → F9 (auth) → P1 (later).

## Setup (run in terminal once)

```
cd apps/frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
npm i -D tailwindcss@3 postcss autoprefixer @tailwindcss/forms
npm i chart.js react-chartjs-2 @tanstack/react-query clsx tailwind-merge zod
git checkout apps/frontend/tailwind.config.ts   # restore our Stitch tokens
```

Backend: `cd apps/backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && copy .env.example .env`

---

## Frontend

**F1 — design system**
```
In apps/frontend, match docs/stitch/*.html. In globals.css load Segoe UI (Inter fallback) and Material Symbols Outlined, set body bg to `background` and text to `on-surface`. Keep the existing tailwind.config.ts. Create ui/Icon.tsx (Material Symbols wrapper: name, filled, size) and ui/FluentCard.tsx (shadow-card, border-outline-variant, rounded-lg, hover shadow-card-hover). Material Symbols only, no @tabler.
```

**F2 — shell + nav rail**
```
Build the shell from the sidebar in docs/stitch/team-drilldown.html. AppNav.tsx: 200px rail (brand, nav items Overview/Teams[active]/Anomalies/Weekly digest/Settings, Favorite teams with status dots, Support/Account), active item border-l-4 border-primary bg-secondary-container/30 text-primary, plus a collapse toggle at the rail top-right to a ~56px icons-only strip via React state (no localStorage). TopBar.tsx (search, actions, Export, avatar). (dashboard)/layout.tsx composes them and wraps children in a TanStack Query provider. Keep Stitch classes, swap raw hex for token classes.
```

**F3 — primitives**
```
From docs/stitch, extract typed components into src/components/ui: StatusPill (critical/at-risk/healthy → error-container/tertiary-fixed/green with a leading dot), KpiCard (label, text-display-lg value, trend chip), SectionCard (FluentCard + title + optional action), Avatar (initials, color by seed). Use clsx + tailwind-merge. Sentence case.
```

**F4 — sign-in**
```
Port docs/stitch/signin.html to src/app/(auth)/signin/page.tsx, pixel-faithful: centered FluentCard, tower mark (inline SVG, not an image), wordmark, tagline, "Sign in with Microsoft" button with the four-square MS logo built from divs, "Trouble signing in?" link, footer line. Button calls signIn("microsoft-entra-id") (stub for now).
```

**F5 — teams overview**
```
Port docs/stitch/teams-overview.html to src/app/(dashboard)/page.tsx: the team health cards (name, status pill, score/100, sparkline, 3-up stats), the bento section (trend + global-average donut), the Critical anomalies table. Replace every fake inline SVG with react-chartjs-2 (charts/Sparkline.tsx no axes/legend colored by status, plus the bar and donut). Mock data from src/lib/mock/teams.ts. Sort critical/at-risk first. Keep Stitch layout and classes.
```

**F6 — team drill-down**
```
Port docs/stitch/team-drilldown.html to src/app/(dashboard)/teams/[teamId]/page.tsx, keeping the 12-col grid exactly (AI summary col-span-8 + Bus-factor col-span-4, 4-up metrics, chart col-span-7 + Active anomalies col-span-5, full-width Team members table). Replace the hand-drawn SVG line with charts/ReviewTimeChart.tsx (react-chartjs-2: blue #0078D4 line, final point enlarged red #ba1a1a, dashed baseline, y ticks "Nd", no legend). Make the Phi-4 card interactive: chips and the input both call an onAsk(question) prop, stub to console.log. Mock from src/lib/mock/azure-core-networking.ts.
```

**F7 — types + mock**
```
Add src/lib/types.ts with zod schemas + inferred types: Team, TeamMember, Metric (value, delta, direction, baseline), BusFactorArea, Anomaly (severity, title, description, detectedAt), TeamSummary (Phi-4 text + on-goal score), TeamHealthCard. Fill src/lib/mock/*.ts to match the Stitch numbers (Azure Core Networking: score 47, commit 38/wk -60%, push 9/wk -35%, review 4.2d +280%, on-goal 64%, roster, anomalies). All mock must validate against the schemas.
```

**F8 — data layer (after B6)**
```
Add src/lib/api.ts (typed fetch, zod-validated) and src/lib/queries.ts (TanStack hooks: useTeams, useTeam, useTeamMetrics, useAnomalies, useTeamSummary) against the FastAPI base URL from an env var. Swap the overview and drill-down pages from mock to these hooks with Fluent skeletons and error states. Wire the Phi-4 onAsk to POST /teams/{id}/ask and stream the answer.
```

**F9 — auth**
```
Add next-auth v5 with the Microsoft Entra ID provider. Protect the (dashboard) route group, connect the sign-in button, show the user's avatar in TopBar, read client id / tenant / secret from env vars, document them in the README.
```

---

## Backend

**B1 — skeleton + config**
```
In apps/backend, build the FastAPI skeleton. app/config.py loads .env via pydantic-settings (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, EMBEDDING_MODEL, GITHUB_TOKEN, GITHUB_REPOS, DUCKDB_PATH, CHROMA_PATH, TEAMS_WEBHOOK_URL, CORS_ORIGINS, API_HOST, API_PORT). app/main.py builds the app, adds CORS, exposes GET /health. Everything typed.
```

**B2 — DuckDB storage**
```
Build app/core/db.py: a DuckDB connection helper and schema init for repos, commits (sha, repo, author, message, additions, deletions, committed_at), pushes, pull_requests (opened_at, first_review_at, merged_at, state), metrics_daily, and resolutions (anomaly_id, action, outcome, resolved_at) for the solver loop. Typed insert + time-series query helpers. Plain parameterized SQL, no ORM.
```

**B3 — GitHub collector**
```
Build app/collectors/github.py with httpx + PyGithub: for each repo in GITHUB_REPOS pull recent commits, pushes, PRs, normalize into the DuckDB tables, incrementally (since last stored timestamp), with rate-limit backoff. Expose async collect_all(). Add app/collectors/ado.py stub with the same interface.
```

**B4 — anomaly + bus factor**
```
Build app/anomaly/engine.py: rolling baseline (mean+std trailing window) per team/metric from metrics_daily, flag anomalies via z-score + rules (stale PR >7d, review-time spike, commit-drop, push-drop), return typed Anomaly (severity, title, description, detectedAt, observed vs baseline). Build app/anomaly/bus_factor.py: ownership concentration per code area → risk (High >70%, Medium 50-70%, Low <50%) with top owner + last activity.
```

**B5 — AI core (resolver loop)**
```
Build the AI layer against the local OpenAI-compatible endpoint. phi4_client.py: openai client from LLM_* settings with ask(prompt) and stream(prompt). embeddings.py: sentence-transformers bge-m3, embed(texts). vectorstore.py: persistent ChromaDB at CHROMA_PATH indexing commit messages + PR descriptions, retrieve context per team. resolver.py: given a team's anomalies + retrieved context, prompt Phi-4 for (1) plain-English summary, (2) root cause, (3) ranked remediation steps, (4) a verify signal to watch, and (5) an on-goal score (share of recent commits matching the sprint goal). Typed results, low temperature.
```

**B6 — API routes**
```
Build app/api/routes with typed responses matching the frontend zod schemas: GET /teams, GET /teams/{id}, GET /teams/{id}/metrics, /anomalies, /bus-factor, /summary, and POST /teams/{id}/ask (stream a Phi-4 answer). Response models in core/schemas.py. Wire routers into app/main.py.
```

**B7 — scheduler + verify**
```
Add APScheduler to app/main.py: on startup schedule collect_all() + metrics rollup + anomaly pass every N minutes (interval from settings), guarded against overlap. Add a verify pass that checks whether flagged anomalies have cleared and writes the outcome to the resolutions table as a labeled example. Expose POST /admin/refresh to run on demand for demos.
```

**B8 — Teams notifier**
```
Build app/notify/teams.py: post an adaptive-card message to TEAMS_WEBHOOK_URL via httpx on High-severity anomalies (title, team, Phi-4 explanation, recommended action). Add a weekly digest job that summarizes each team via the resolver and posts it. No-op with a warning if TEAMS_WEBHOOK_URL is unset.
```

**B9 — tests**
```
Add pytest tests in apps/backend/tests: unit tests for the anomaly engine (synthetic series → correct flags), the bus-factor calculator, and the DuckDB helpers; API tests with FastAPI TestClient using a seeded in-memory DuckDB and a mocked Phi-4 client. Add pytest config and a run task.
```

---

## Individual phase (later)

**P1 — predictor**
```
Add a predictive layer that trains on the resolutions table: features = review-time trend, commit/push drop, bus-factor, off-goal rate; target = whether the anomaly escalated to an incident. Start with gradient boosting (XGBoost), evaluate with precision/recall + a time-based split, and expose GET /teams/{id}/forecast returning an escalation risk. This is where the model actually trains.
```

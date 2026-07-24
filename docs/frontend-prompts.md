# Watchtower — frontend build prompts (from Stitch)

The visual design is locked from Stitch. These prompts tell Claude Code to port the
Stitch exports into real Next.js components, pixel-faithful, on our stack.

Stack: Next.js (App Router) · TypeScript · Tailwind v3 · Material Symbols Outlined
(icons) · `chart.js` + `react-chartjs-2` · `@tanstack/react-query` · `clsx` +
`tailwind-merge` · `zod` · `next-auth@beta` (later).

Design system: Segoe UI (Inter fallback), Material-3 token names, sharp Fluent corners.
All tokens already live in `apps/frontend/tailwind.config.ts` — the Stitch class names
(`bg-surface`, `text-on-surface`, `border-outline-variant`, `text-headline-md`,
`p-margin_page`, `shadow-card`, etc.) map straight through.

## Step 0 — drop the Stitch exports into the repo

Save the three Stitch HTML exports so Claude Code can read them as the source of truth:

```
apps/frontend/docs/stitch/signin.html
apps/frontend/docs/stitch/team-drilldown.html
apps/frontend/docs/stitch/teams-overview.html
```

Two global rules that apply to every port below (state them once, they carry through
CLAUDE.md): replace Stitch's `<script src="https://cdn.tailwindcss.com">` and inline
`tailwind.config` with our project Tailwind; and replace every placeholder
`lh3.googleusercontent.com` image with an initials avatar or a real asset — never ship
those URLs.

---

### Phase 1 — setup: fonts, icons, primitives

```
In apps/frontend, wire up the design system to match docs/stitch/*.html. In globals.css,
load Segoe UI with an Inter fallback and load the Material Symbols Outlined font, and set
body background to the `background` token and text to `on-surface`. Keep the existing
apps/frontend/tailwind.config.ts (it already holds the Stitch tokens) and install
@tailwindcss/forms. Create src/components/ui/Icon.tsx: a typed wrapper over Material
Symbols Outlined with `name`, `filled`, and `size` props (uses font-variation-settings
for FILL). Create src/components/ui/FluentCard.tsx applying `shadow-card`, the
`border-outline-variant` border, `rounded-lg`, and a hover `shadow-card-hover`. We are
using Material Symbols to match Stitch, so @tabler/icons-react is not needed.
```

### Phase 2 — app shell + collapsible nav rail

```
Build the shared shell from the sidebar in docs/stitch/team-drilldown.html and
teams-overview.html. Create src/components/layout/AppNav.tsx: a 200px (nav_rail_width)
left rail with the Watchtower brand block, nav items (Overview, Teams [active], Anomalies,
Weekly digest, Settings) using the Icon component with the active item styled
`border-l-4 border-primary bg-secondary-container/30 text-primary`, a "Favorite teams"
list with colored status dots, and Support/Account at the bottom. Add a collapse toggle
at the rail's top-right that shrinks it to a ~56px icons-only strip via React state (no
localStorage). Build src/components/layout/TopBar.tsx (search field, right-side actions,
Export button, avatar) and a src/app/(dashboard)/layout.tsx that composes AppNav + TopBar
and wraps children in a TanStack Query provider. Match the Stitch markup and classes
exactly; only swap raw hex for the token classes already defined.
```

### Phase 3 — shared UI primitives

```
Extract the repeating pieces from docs/stitch into typed components in
src/components/ui: StatusPill (variants critical/at-risk/healthy mapping to
error-container / tertiary-fixed / green tokens with a leading dot), KpiCard (label,
big value in text-display-lg, trend chip), SectionCard (FluentCard + title + optional
header action), and Avatar (initials, color by seed). Use clsx + tailwind-merge for
variants. Keep sentence case and the exact Fluent spacing from the exports.
```

### Phase 4 — sign-in screen

```
Port docs/stitch/signin.html to src/app/(auth)/signin/page.tsx as a React component,
pixel-faithful: centered FluentCard, the Watchtower logo and wordmark, the tagline, the
"Sign in with Microsoft" button with the four-square Microsoft logo (recreate it with
divs, do not use an image), the "Trouble signing in?" link, and the footer line. Wire the
button to call signIn("microsoft-entra-id") from next-auth (stub the handler for now).
Keep all classes; replace the placeholder logo image with an inline SVG tower/castle mark.
```

### Phase 5 — teams overview (landing)

```
Port docs/stitch/teams-overview.html to src/app/(dashboard)/page.tsx. Build the
responsive grid of team health cards (name, status pill, score /100, sparkline, and the
three-up Open PRs / Avg review / Anomalies stats), the bento section (historical trend +
the global-average donut), and the Critical anomalies table. Replace every fake inline
SVG sparkline with a small react-chartjs-2 sparkline component
(src/components/charts/Sparkline.tsx, no axes, no legend, colored by status), and the
bar/donut with react-chartjs-2. Feed typed mock data from src/lib/mock/teams.ts. Sort
critical and at-risk teams first. Keep the Stitch layout and classes.
```

### Phase 6 — team drill-down

```
Port docs/stitch/team-drilldown.html to src/app/(dashboard)/teams/[teamId]/page.tsx,
keeping the 12-column grid exactly: AI summary (col-span-8) + Bus-factor risk
(col-span-4), the four-up metrics row, the PR review-time chart (col-span-7) + Active
anomalies (col-span-5), then the full-width Team members table. Replace the hand-drawn
SVG line chart with src/components/charts/ReviewTimeChart.tsx (react-chartjs-2: blue
#0078D4 line, final point enlarged and red #ba1a1a, dashed baseline, y ticks as "Nd",
no legend). Make the Phi-4 summary card interactive: suggestion chips and the
"Ask about this team" input both call an onAsk(question) prop; stub it to console.log for
now. Feed typed mock data from src/lib/mock/azure-core-networking.ts. Keep classes and
spacing faithful to the export.
```

### Phase 7 — types + mock data

```
Add src/lib/types.ts with zod schemas + inferred types for Team, TeamMember, Metric
(value, delta, direction, baseline), BusFactorArea, Anomaly (severity, title, description,
detectedAt), TeamSummary (Phi-4 text + on-goal score), and TeamHealthCard. Fill
src/lib/mock/*.ts with realistic data matching the numbers shown in the Stitch exports
(Azure Core Networking: score 47, commit 38/wk down 60%, push 9/wk down 35%, review 4.2d
up 280%, on-goal 64%, plus the roster and anomalies). All mock objects must validate
against the schemas.
```

### Phase 8 — data layer (when the backend is ready)

```
Add src/lib/api.ts (typed fetch client, zod-validated responses) and TanStack Query hooks
in src/lib/queries.ts (useTeams, useTeam, useTeamMetrics, useAnomalies, useTeamSummary)
pointing at the FastAPI base URL from an env var. Swap the overview and drill-down pages
from mock data to these hooks with Fluent loading skeletons and error states. Wire the
Phi-4 card onAsk to POST /teams/{id}/ask and stream the answer.
```

### Phase 9 — auth (Microsoft Entra ID)

```
Add next-auth v5 with the Microsoft Entra ID provider. Protect the (dashboard) route
group, connect the sign-in page's button, show the signed-in user's avatar in the TopBar,
and read client id / tenant / secret from env vars. Document the env vars in the README.
```

---

## Reference: Stitch prompts (to regenerate or add screens)

Keep these for adding new screens later (anomalies list, weekly digest). Each is one
generation; include the palette so Stitch stays on-brand: Segoe UI / Inter, primary
#0078D4, background #FAF9F8, white cards, #EDEBE9 borders, "at risk" in amber #974700,
error #ba1a1a, Material Symbols icons, sharp Fluent corners, light theme, desktop.

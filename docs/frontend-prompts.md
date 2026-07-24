# Watchtower — frontend prompts

Two sets of prompts:
1. **Stitch prompts** — paste into Stitch to generate the visual design (one screen per prompt).
2. **Claude Code CLI prompts** — paste in order to build the real code on the agreed stack.

Stack of record: Next.js (App Router) · TypeScript · Tailwind v3 · `@tabler/icons-react` · `chart.js` + `react-chartjs-2` · `@tanstack/react-query` · `clsx` + `tailwind-merge` · `zod` · `next-auth@beta` (later).

Design language: Microsoft Fluent. Segoe UI. Primary blue `#0078D4`. Page `#FAF9F8`. White cards, `#EDEBE9` borders. Text `#323130` / secondary `#605E5C`.

---

## 1. Stitch prompts

Stitch designs one screen at a time. Run each prompt as its own generation, then use the short follow-ups to refine in place.

### 1a. Team drill-down (primary screen)

```
Design a desktop web dashboard for "Watchtower", an internal engineering-team
health monitoring tool for Microsoft. Microsoft Fluent Design aesthetic: Segoe UI
font, communication blue #0078D4 as the primary accent, near-white page background
#FAF9F8, white cards with thin #EDEBE9 borders and a subtle shadow, heading text
#323130 and secondary text #605E5C. Clean, professional, data-dense but airy.
Light theme.

Left navigation rail (~200px): a small tower logo with a "Watchtower" wordmark at
the top and a collapse chevron at the rail's top-right; nav items Overview, Teams
(selected), Anomalies, Weekly digest, Settings, each with an outline icon; below,
a "Teams" section listing teams, each with a colored status dot (red, amber, or
green) and a name.

Main content, top to bottom:
- Header: team name "Azure Core Networking" in large semibold, an amber "At risk"
  pill beside it, and a subline "12 engineers · GitHub · health score 47/100". On
  the right, a "Last 30 days" dropdown button and a solid blue "Export digest" button.
- AI summary card with a left blue accent border: a small "Phi-4 summary" pill, one
  paragraph of plain-English insight, three suggestion chips, and a text input
  "Ask about this team" with a send button.
- A row of four metric cards: "Commit activity 38/wk, down 60%", "Push frequency
  9/wk, down 35%", "PR review time 4.2d, up 280%", "On-goal commits 64%". Each has a
  small icon+label, a large number, and a colored trend pill (red for bad, amber for
  caution).
- Line chart card titled "PR review time · last 30 days": a rising blue line with the
  final point highlighted red, against a dashed gray baseline.
- "Bus-factor risk" card: three code areas, each with an ownership percentage, a
  colored progress bar (red/amber/green), and a risk label.
- "Active anomalies" card: rows with a severity dot, a bold title, a description, and
  a timestamp.
- "Team members" card: rows with a circular initials avatar, name and role,
  commit/review/on-goal stats, and an activity status.
```

Refine follow-ups (run after the first generation):
- `Collapse the left nav rail to an icons-only strip when the chevron is clicked.`
- `Add a dark-theme variant of this screen using #1B1A19 surfaces and #2D2C2B cards.`
- `Tighten spacing and make the four metric cards a single row on wide screens.`

### 1b. Teams overview (landing)

```
Design a desktop web "Teams overview" screen for Watchtower, same Microsoft Fluent
style (Segoe UI, #0078D4 accent, #FAF9F8 background, white cards, #EDEBE9 borders,
light theme) and the same left navigation rail as the team drill-down.

Main content: a page title "Team health", a search field and a "Last 30 days"
filter on the right, then a responsive grid of team health cards. Each card shows
the team name, a status pill (Healthy green / At risk amber / Critical red), a large
health score out of 100, a tiny sparkline, and three compact stats (open PRs, avg
review time, active anomalies). Sort so at-risk and critical teams appear first.
```

### 1c. Sign-in (for the Entra ID auth step)

```
Design a minimal desktop web sign-in screen for Watchtower, Microsoft Fluent style,
light theme, Segoe UI. Centered white card on a #FAF9F8 background: the tower logo,
the "Watchtower" wordmark, a one-line tagline "Engineering team health, watched by
local AI", and a single primary button "Sign in with Microsoft" in #0078D4 with the
Microsoft logo. Small footer text "Internal tool · access limited to your org".
```

---

## 2. Claude Code CLI prompts

Paste these in order inside the repo. Each assumes `CLAUDE.md` is at the repo root so
Claude Code already has project context. Run one, review the diff, commit, then move on.

### Phase 1 — scaffold and tokens

```
Scaffold the Next.js frontend in apps/frontend using the App Router, TypeScript,
Tailwind, ESLint, the src directory, and the "@/*" import alias. Then pin Tailwind to
v3 (tailwindcss@3, postcss, autoprefixer) and install: @tabler/icons-react, chart.js,
react-chartjs-2, @tanstack/react-query, clsx, tailwind-merge, zod. Add prettier and
prettier-plugin-tailwindcss as dev deps. Keep the existing apps/frontend/tailwind.config.ts
(it holds our Fluent design tokens) — do not overwrite it. Set the app font to Segoe UI
in globals.css and set the page background to the neutral-lighter-alt token.
```

### Phase 2 — app shell and collapsible nav rail

```
Build the app shell in apps/frontend/src/app and src/components/layout. Create a
collapsible left navigation rail (AppNav) ~200px wide that collapses to a ~52px
icons-only strip via a chevron button at the rail's top-right, with the collapsed
state held in React state (no localStorage). The rail has: a tower logo + "Watchtower"
wordmark, nav items (Overview, Teams, Anomalies, Weekly digest, Settings) using
@tabler/icons-react outline icons, and a "Teams" list where each item has a colored
status dot and a name. Use only the Fluent Tailwind tokens (bg-brand, text-neutral-*,
border-neutral-light, etc.), never raw hex. Sentence case everywhere. Wrap the app in
a TanStack Query provider.
```

### Phase 3 — Fluent UI primitives

```
Create reusable Fluent-styled primitives in apps/frontend/src/components/ui, each
typed and using the Tailwind design tokens (no raw hex): Card (white surface, thin
neutral-light border, rounded-card, shadow-card), Badge/Pill (variants: neutral,
success, warning, severe, error — background + matching foreground token), Button
(variants: primary solid brand, secondary outline), and KpiCard (icon+label, large
number, trend pill with up/down arrow). Use clsx + tailwind-merge for variant classes.
Add a short usage comment at the top of each file.
```

### Phase 4 — types and mock data

```
Add apps/frontend/src/lib/types.ts with zod schemas + inferred TS types for: Team,
TeamMember, Metric (value, delta, direction, baseline), BusFactorArea, Anomaly
(severity, title, description, detectedAt), and the Phi-4 TeamSummary. Add
apps/frontend/src/lib/mock/azure-core-networking.ts with realistic mock data matching
these schemas, mirroring the demo: commit activity 38/wk down 60%, push frequency
9/wk down 35%, PR review time 4.2d up 280%, on-goal commits 64%, three bus-factor
areas, four anomalies, and the team roster with commit/review/on-goal stats.
```

### Phase 5 — the review-time chart

```
Build apps/frontend/src/components/charts/ReviewTimeChart.tsx using react-chartjs-2
(register only the Chart.js pieces you need). A line chart of PR review time over 30
days: a blue (#0078D4) line with a soft fill, the final point rendered larger and red
(#D13438) to flag the anomaly, and a dashed gray baseline dataset. No legend, y-axis
ticks formatted as "Nd", x gridlines hidden. Accept data via typed props. Wrap the
canvas so it is responsive with a fixed height.
```

### Phase 6 — interactive Phi-4 card

```
Build apps/frontend/src/components/team/Phi4Summary.tsx: a Card with a left blue
accent border, a "Phi-4 summary" pill, the summary paragraph, three suggestion chips,
and an "Ask about this team" input with a send button. Accept an onAsk(question:
string) callback prop and suggestion strings via props; clicking a chip or submitting
the input calls onAsk. Keep it presentational — no fetching yet. Include an optional
isStreaming state that shows a subtle "Phi-4 is thinking" indicator.
```

### Phase 7 — assemble the team drill-down page

```
Assemble apps/frontend/src/app/teams/[teamId]/page.tsx as the team drill-down,
composing AppNav, the header (team name + status pill + subline + Last 30 days +
Export digest), Phi4Summary, a four-up KpiCard row, ReviewTimeChart, the Bus-factor
risk card, the Active anomalies card, and the Team members card. Feed it the mock data
for now and stub onAsk to console.log. Match the spacing and Fluent look from the
approved design. Full-width dashboard layout on desktop.
```

### Phase 8 — data layer (when the backend is ready)

```
Add apps/frontend/src/lib/api.ts with a typed fetch client and zod-validated responses,
and TanStack Query hooks in src/lib/queries.ts (useTeam, useTeamMetrics, useAnomalies,
useTeamSummary) pointing at the FastAPI backend base URL from an env var. Swap the team
drill-down page from mock data to these hooks, with loading skeletons and error states
using the Fluent primitives. Wire Phi4Summary onAsk to POST the question and stream the
answer.
```

### Phase 9 — auth (Microsoft Entra ID)

```
Add authentication with next-auth v5 (Auth.js) using the Microsoft Entra ID provider.
Protect the dashboard routes, add the sign-in screen (centered Fluent card, "Sign in
with Microsoft" button), show the signed-in user's avatar in the nav rail, and read
client id / tenant / secret from env vars. Document the required env vars in the README.
```

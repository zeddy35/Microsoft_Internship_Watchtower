# Watchtower — frontend

Next.js dashboard for Watchtower. Fluent-styled, fully typed, and validated
against the FastAPI backend with the same zod schemas the UI renders from.

## Running it

```bash
npm install
cp .env.example .env.local   # then edit if needed
npm run dev
```

Open http://localhost:3000. The backend needs to be running too:

```bash
cd ../backend && uvicorn app.main:app --reload
```

## Environment variables

| Variable | Required | What it does |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | no | Watchtower API base URL. Defaults to `http://localhost:8000`. |
| `AUTH_SECRET` | for auth | Session encryption key. Generate with `npx auth secret`. |
| `AUTH_MICROSOFT_ENTRA_ID_ID` | for auth | Application (client) ID of the Entra app registration. |
| `AUTH_MICROSOFT_ENTRA_ID_SECRET` | for auth | Client secret value from that app registration. |
| `AUTH_MICROSOFT_ENTRA_ID_ISSUER` | no | `https://login.microsoftonline.com/<tenant-id>/v2.0/`. Omit to allow any Microsoft account. |

**Auth is opt-in.** With no Entra app configured the dashboard stays open, so
`npm run dev` works on a laptop with nothing but the API running. Set the
client ID and secret and the same routes start redirecting to `/signin` — no
code change.

### Registering the Entra app

1. Entra admin center → App registrations → New registration.
2. Redirect URI (Web): `http://localhost:3000/api/auth/callback/microsoft-entra-id`.
3. Certificates & secrets → New client secret → copy the **value**.
4. Put the client ID, secret, and (optionally) your tenant issuer in `.env.local`.

## Structure

```
src/
  app/
    (auth)/signin       sign-in card, no nav rail
    (dashboard)/        everything behind the rail; guarded when auth is on
      page.tsx          overview: stat tiles, team cards, critical anomalies
      teams/            team table + [teamId] drill-down
      anomalies/        cross-team anomaly feed with severity filter
    api/auth/           next-auth route handlers
  components/
    charts/             Chart.js wrappers (review-time line, sparkline)
    layout/             nav rail, top bar, shell
    team/               drill-down cards
    ui/                 Fluent primitives and loading/error/empty states
  lib/
    api.ts              typed fetch, zod-validated, streaming ask
    queries.ts          TanStack hooks
    types.ts            zod schemas shared with the backend contract
```

## Theming

Every colour is a CSS variable defined in `src/app/globals.css`, and
`tailwind.config.ts` maps the Tailwind tokens onto them. Switching theme is a
class on `<html>`, so no component carries `dark:` variants and adding a theme
means editing one file. The token names are the light-mode Fluent ramp and
should be read as roles: `neutral-white` is "the raised surface",
`neutral-lighter-alt` is "the page behind it". A blocking inline script sets
the class before first paint so dark-mode users never see a white flash.

Charts read the same variables at runtime (`useThemeColors`) because canvas
cannot consume CSS classes, and literal hex values are how a chart ends up
unreadable in one of the two themes.

## The hosted demo

A build on Vercel sets `NEXT_PUBLIC_DEMO_MODE=1` automatically (see
`next.config.ts`), which points the API client at `/api/demo` — route handlers
that serve `src/lib/demo-snapshot.json`, a capture of what the real API
returned after seeding the demo organisation. Set `NEXT_PUBLIC_DEMO_MODE=0` in
the Vercel project to point a deployment at a real API instead.

To regenerate the snapshot, run the backend, seed it, and capture every
endpoint into `src/lib/demo-snapshot.json` with the shape
`{ teams, anomalies, settings, resolutions, byTeam: { [id]: { team, metrics,
anomalies, busFactor, summary } } }`.

## Notes

- Every API response is re-parsed with zod. A backend field rename fails at the
  boundary with a readable error instead of rendering `undefined` deep in a
  component tree.
- `POST /teams/{id}/ask` streams plain text; `useAskTeam` renders tokens as
  they arrive and aborts an in-flight answer when a new question is asked.
- Chart colours come from the theme's CSS variables at runtime, so they follow
  light and dark without a second palette to keep in step.

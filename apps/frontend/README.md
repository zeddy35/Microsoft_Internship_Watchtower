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

## Notes

- Every API response is re-parsed with zod. A backend field rename fails at the
  boundary with a readable error instead of rendering `undefined` deep in a
  component tree.
- `POST /teams/{id}/ask` streams plain text; `useAskTeam` renders tokens as
  they arrive and aborts an in-flight answer when a new question is asked.
- Chart colors are literal hex values mirroring `tailwind.config.ts`, because
  canvas cannot read Tailwind classes.

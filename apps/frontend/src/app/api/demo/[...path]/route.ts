import { NextResponse } from "next/server";
import snapshot from "@/lib/demo-snapshot.json";

/**
 * The hosted demo's stand-in for the FastAPI backend.
 *
 * Watchtower's backend needs a local DuckDB file, a background scheduler, and
 * a Phi-4 endpoint running on the same machine — none of which exist on a
 * static host. So the deployed build serves a snapshot of exactly what the
 * real API returned after seeding the demo organisation, through the same
 * routes and the same response shapes. The dashboard cannot tell the
 * difference, and every number on screen was produced by the real rollup and
 * the real anomaly engine rather than written by hand.
 *
 * What it deliberately does NOT do is pretend to be live: writes answer 403
 * with an explanation, and the question box says plainly that no model is
 * attached. A demo that quietly fakes its own capabilities is worse than one
 * that admits its edges.
 */

type Snapshot = typeof snapshot;
type TeamKey = keyof Snapshot["byTeam"];

const READ_ONLY_MESSAGE =
  "This hosted demo is read-only. Run Watchtower locally to collect from your own repositories.";

function readOnly() {
  return NextResponse.json({ detail: READ_ONLY_MESSAGE }, { status: 403 });
}

function notFound(what: string) {
  return NextResponse.json({ detail: `Unknown ${what}` }, { status: 404 });
}

function teamEntry(teamId: string) {
  return (snapshot.byTeam as Record<string, Snapshot["byTeam"][TeamKey]>)[
    teamId
  ];
}

export async function GET(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const url = new URL(request.url);

  if (path[0] === "teams") {
    if (path.length === 1) return NextResponse.json(snapshot.teams);

    const entry = teamEntry(path[1]);
    if (!entry) return notFound("team");

    if (path.length === 2) return NextResponse.json(entry.team);
    if (path[2] === "metrics") return NextResponse.json(entry.metrics);
    if (path[2] === "anomalies") return NextResponse.json(entry.anomalies);
    if (path[2] === "bus-factor") return NextResponse.json(entry.busFactor);
    if (path[2] === "summary") {
      return entry.summary
        ? NextResponse.json(entry.summary)
        : notFound("summary");
    }
  }

  if (path[0] === "anomalies") {
    const severity = url.searchParams.get("severity");
    const anomalies = severity
      ? snapshot.anomalies.filter((item) => item.severity === severity)
      : snapshot.anomalies;
    return NextResponse.json(anomalies);
  }

  if (path[0] === "admin" && path[1] === "settings") {
    return NextResponse.json(snapshot.settings);
  }
  if (path[0] === "admin" && path[1] === "resolutions") {
    return NextResponse.json(snapshot.resolutions);
  }
  if (path[0] === "health") {
    return NextResponse.json({ status: "ok" });
  }

  return notFound("endpoint");
}

export async function POST(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;

  // A refresh over a fixed snapshot is a no-op rather than a lie: re-reading
  // the same data is exactly what happens.
  if (path[0] === "admin" && path[1] === "refresh") {
    return NextResponse.json({
      collected: false,
      metricRows: 0,
      teams: snapshot.teams.length,
      anomaliesOpen: snapshot.anomalies.length,
      resolutionsWritten: 0,
      summariesWritten: 0,
    });
  }

  if (path[0] === "teams" && path[2] === "ask") {
    const entry = teamEntry(path[1]);
    if (!entry) return notFound("team");

    const cached = entry.summary?.summary ?? "";
    const answer =
      `This hosted demo has no language model attached, so here is the ` +
      `cached verdict the resolver produced for ${entry.team.name}:\n\n` +
      `${cached}\n\n` +
      `Run Watchtower locally with Foundry Local or Ollama to ask your own ` +
      `questions against a live Phi-4.`;

    // Streamed word by word, because the client renders tokens as they arrive
    // and a single blob would skip the behaviour this demo is showing.
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        for (const word of answer.split(" ")) {
          controller.enqueue(encoder.encode(word + " "));
          await new Promise((resolve) => setTimeout(resolve, 18));
        }
        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }

  return readOnly();
}

export async function PUT() {
  return readOnly();
}

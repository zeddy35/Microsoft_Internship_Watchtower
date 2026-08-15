// Top bar: product wordmark and the signed-in user, with sign out.
// Server component: it reads the session directly, no client round trip.
import { auth, isAuthConfigured, signOut } from "@/auth";

function initialsFor(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return (parts[0]?.slice(0, 2) ?? "??").toUpperCase();
}

export async function TopBar() {
  const session = isAuthConfigured ? await auth() : null;
  const user = session?.user;

  return (
    <header className="flex h-14 shrink-0 items-center border-b border-neutral-light bg-neutral-white">
      {/* Same cap and padding as the content below, so the bar's contents line
          up with the page instead of drifting to the screen edges on a wide
          display. */}
      <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between px-6">
        <p className="text-sm font-medium text-neutral-secondary">
          Engineering health
        </p>

        {user ? (
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-xs font-medium text-neutral-primary">
                {user.name ?? "Signed in"}
              </p>
              {user.email && (
                <p className="text-xs text-neutral-tertiary">{user.email}</p>
              )}
            </div>
            <span
              className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand-tint text-xs font-semibold text-brand"
              title={user.name ?? undefined}
            >
              {initialsFor(user.name ?? user.email ?? "?")}
            </span>
            <form
              action={async () => {
                "use server";
                await signOut({ redirectTo: "/signin" });
              }}
            >
              <button
                type="submit"
                className="rounded-control px-2.5 py-1.5 text-xs font-medium text-neutral-secondary transition-colors hover:bg-neutral-lighter hover:text-neutral-primary"
              >
                Sign out
              </button>
            </form>
          </div>
        ) : (
          <span className="text-xs text-neutral-tertiary">
            {isAuthConfigured ? "Not signed in" : "Local mode"}
          </span>
        )}
      </div>
    </header>
  );
}

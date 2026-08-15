import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { auth, isAuthConfigured, signIn } from "@/auth";
import { redirect } from "next/navigation";

const MS_LOGO_SQUARES = [
  { color: "bg-[#f25022]", label: "" },
  { color: "bg-[#7fba00]", label: "" },
  { color: "bg-[#00a4ef]", label: "" },
  { color: "bg-[#ffb900]", label: "" },
];

function TowerMark() {
  return (
    <svg
      viewBox="0 0 32 32"
      className="size-9 text-brand"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 4h8l1.5 6h-11L12 4Z" />
      <path d="M10.5 10h11v4h-11z" />
      <path d="M12.5 14 11 28h10l-1.5-14" />
      <path d="M9 28h14" />
      <path d="M16 4V2" />
    </svg>
  );
}

export default async function SignInPage() {
  // With auth configured there is no reason to show this page to someone who
  // already has a session.
  if (isAuthConfigured) {
    const session = await auth();
    if (session?.user) redirect("/");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-lighter-alt p-6">
      <Card className="w-full max-w-sm p-8 text-center shadow-fluent">
        <div className="flex justify-center">
          <TowerMark />
        </div>

        <h1 className="mt-4 text-xl font-semibold text-neutral-primary">
          Watchtower
        </h1>
        <p className="mt-1 text-sm text-neutral-secondary">
          Engineering health, before it becomes an incident.
        </p>

        <form
          action={async () => {
            "use server";
            await signIn("microsoft-entra-id", { redirectTo: "/" });
          }}
          className="mt-8"
        >
          <button
            type="submit"
            disabled={!isAuthConfigured}
            className="flex w-full items-center justify-center gap-2.5 rounded-control border border-neutral-light bg-neutral-white px-4 py-2.5 text-sm font-medium text-neutral-primary transition-colors hover:bg-neutral-lighter disabled:cursor-not-allowed disabled:text-neutral-tertiary"
          >
            <span
              className="grid size-4 shrink-0 grid-cols-2 gap-[1px]"
              aria-hidden="true"
            >
              {MS_LOGO_SQUARES.map((square, index) => (
                <span key={index} className={square.color} />
              ))}
            </span>
            Sign in with Microsoft
          </button>
        </form>

        {isAuthConfigured ? (
          <p className="mt-4 text-xs text-neutral-secondary">
            <Link href="/" className="text-brand hover:underline">
              Trouble signing in?
            </Link>
          </p>
        ) : (
          <p className="mt-4 text-xs text-neutral-secondary">
            No Entra app is configured yet.{" "}
            <Link href="/" className="text-brand hover:underline">
              Continue to the dashboard
            </Link>
          </p>
        )}

        <p className="mt-8 text-xs text-neutral-tertiary">
          Watchtower · Microsoft internal tooling prototype
        </p>
      </Card>
    </main>
  );
}

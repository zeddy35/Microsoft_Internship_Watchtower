"use client";

import { FluentCard } from "@/components/ui/FluentCard";

function handleMicrosoftSignIn() {
  console.log("signIn('microsoft-entra-id')");
}

function WatchtowerMark() {
  return (
    <svg viewBox="0 0 48 48" className="size-12" aria-hidden="true">
      <path
        d="M24 4 L40 14 V20 L24 30 L8 20 V14 Z"
        fill="#0078D4"
      />
      <rect x="10" y="20" width="6" height="20" fill="#0078D4" />
      <rect x="21" y="20" width="6" height="20" fill="#005A9E" />
      <rect x="32" y="20" width="6" height="20" fill="#0078D4" />
      <rect x="6" y="38" width="36" height="4" rx="1" fill="#005A9E" />
    </svg>
  );
}

function MicrosoftLogo() {
  return (
    <div className="grid grid-cols-2 gap-[2px]" style={{ width: 16, height: 16 }}>
      <div style={{ width: 7, height: 7, backgroundColor: "#f25022" }} />
      <div style={{ width: 7, height: 7, backgroundColor: "#7fbb00" }} />
      <div style={{ width: 7, height: 7, backgroundColor: "#00a4ef" }} />
      <div style={{ width: 7, height: 7, backgroundColor: "#ffb900" }} />
    </div>
  );
}

export default function SignInPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center overflow-hidden bg-background px-margin-mobile md:px-margin-desktop">
      <main className="flex w-full flex-grow flex-col items-center justify-center">
        <FluentCard className="flex w-full max-w-[440px] flex-col items-center p-lg md:p-xl">
          <div className="mb-lg">
            <WatchtowerMark />
          </div>

          <div className="mb-xl text-center">
            <h1 className="font-fluent text-headline-md font-semibold tracking-tight text-on-surface">
              Watchtower
            </h1>
            <p className="mt-xs font-body-md text-secondary">
              Engineering team health, watched by local AI
            </p>
          </div>

          <div className="w-full">
            <button
              type="button"
              onClick={handleMicrosoftSignIn}
              className="flex w-full items-center justify-center gap-md rounded-lg bg-primary px-lg py-sm font-body-md font-semibold text-white outline-none transition-all duration-200 hover:bg-[#106EBE] focus:ring-2 focus:ring-primary focus:ring-offset-2 active:bg-[#005A9E]"
            >
              <MicrosoftLogo />
              Sign in with Microsoft
            </button>
          </div>

          <div className="mt-lg w-full border-t border-outline-variant pt-lg text-center">
            <a href="#" className="font-label-md text-primary transition-all hover:underline">
              Trouble signing in?
            </a>
          </div>
        </FluentCard>
      </main>

      <footer className="flex w-full items-center justify-center py-xl">
        <p className="font-label-md uppercase tracking-wide text-secondary opacity-80">
          Internal tool · access limited to your org
        </p>
      </footer>
    </div>
  );
}

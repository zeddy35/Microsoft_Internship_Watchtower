"use client";

import { IconLoader2, IconSend2, IconSparkles, IconX } from "@tabler/icons-react";
import { useState, type FormEvent } from "react";
import { cn } from "@/lib/cn";

export interface Phi4SummaryProps {
  summary: string;
  suggestions: string[];
  onAsk: (question: string) => void;
  isStreaming?: boolean;
  /** Streamed answer to the last question, rendered under the summary. */
  answer?: string;
  errorMessage?: string | null;
  onClearAnswer?: () => void;
  className?: string;
}

export function Phi4Summary({
  summary,
  suggestions,
  onAsk,
  isStreaming = false,
  answer = "",
  errorMessage = null,
  onClearAnswer,
  className,
}: Phi4SummaryProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isStreaming) return;
    onAsk(trimmed);
    setQuestion("");
  }

  function handleChipClick(suggestion: string) {
    if (isStreaming) return;
    onAsk(suggestion);
  }

  return (
    <section
      className={cn(
        "rounded-card border border-l-4 border-neutral-light border-l-brand bg-neutral-white p-4 shadow-card sm:p-5",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-tint px-2.5 py-1 text-xs font-medium text-brand">
          <IconSparkles className="size-3.5" stroke={1.75} aria-hidden="true" />
          Phi-4 summary
        </span>

        {isStreaming && (
          <span
            role="status"
            className="inline-flex items-center gap-1.5 text-xs text-neutral-tertiary"
          >
            <IconLoader2
              className="size-3.5 animate-spin"
              stroke={1.75}
              aria-hidden="true"
            />
            Phi-4 is thinking
          </span>
        )}
      </div>

      <p className="mt-3 text-sm leading-relaxed text-neutral-primary">
        {summary}
      </p>

      {(answer || errorMessage) && (
        <div className="mt-4 rounded-control border border-neutral-light bg-neutral-lighter-alt p-3">
          <div className="flex items-start justify-between gap-3">
            <p
              className={cn(
                "whitespace-pre-wrap text-sm leading-relaxed",
                errorMessage ? "text-state-error-fg" : "text-neutral-primary",
              )}
            >
              {errorMessage ?? answer}
              {isStreaming && !errorMessage && (
                <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-brand align-middle" />
              )}
            </p>
            {onClearAnswer && (
              <button
                type="button"
                onClick={onClearAnswer}
                aria-label="Dismiss answer"
                className="shrink-0 rounded-control p-1 text-neutral-tertiary transition-colors hover:bg-neutral-lighter hover:text-neutral-primary"
              >
                <IconX className="size-3.5" stroke={1.75} aria-hidden="true" />
              </button>
            )}
          </div>
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => handleChipClick(suggestion)}
              disabled={isStreaming}
              className="rounded-control border border-neutral-light bg-neutral-lighter-alt px-3 py-1.5 text-xs font-medium text-neutral-secondary transition-colors hover:border-brand-light hover:bg-brand-tint hover:text-brand disabled:cursor-not-allowed disabled:opacity-60"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-4 flex items-center gap-2">
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about this team"
          disabled={isStreaming}
          className="flex-1 rounded-control border border-neutral-light bg-neutral-white px-3 py-2 text-sm text-neutral-primary placeholder:text-neutral-tertiary focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand disabled:cursor-not-allowed disabled:bg-neutral-lighter-alt"
        />
        <button
          type="submit"
          disabled={isStreaming || question.trim().length === 0}
          aria-label="Send question"
          className="flex size-9 shrink-0 items-center justify-center rounded-control bg-brand text-neutral-white transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:bg-neutral-tertiary-alt"
        >
          <IconSend2 className="size-4" stroke={1.75} aria-hidden="true" />
        </button>
      </form>
    </section>
  );
}

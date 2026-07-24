"use client";

import { useState, type FormEvent } from "react";
import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/cn";

export interface Phi4SummaryProps {
  summary: string;
  suggestions: string[];
  onAsk: (question: string) => void;
  isStreaming?: boolean;
  className?: string;
}

export function Phi4Summary({
  summary,
  suggestions,
  onAsk,
  isStreaming = false,
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
    <div
      className={cn(
        "rounded border border-l-4 border-outline-variant border-l-primary bg-white p-6",
        className,
      )}
    >
      <div className="mb-4 flex items-center gap-2">
        <Icon name="auto_awesome" filled className="text-primary" />
        <span className="rounded bg-primary-container/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-primary-container">
          Phi-4 summary
        </span>
        {isStreaming && (
          <span role="status" className="text-body-sm text-secondary">
            Phi-4 is thinking…
          </span>
        )}
      </div>

      <p className="mb-6 text-headline-md font-medium leading-relaxed">{summary}</p>

      {suggestions.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => handleChipClick(suggestion)}
              disabled={isStreaming}
              className="cursor-pointer rounded-full border border-outline-variant bg-surface-container px-3 py-1 text-body-sm transition-all hover:bg-primary hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="relative max-w-lg">
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about this team..."
          disabled={isStreaming}
          className="w-full rounded-lg border border-outline-variant bg-surface py-3 pl-4 pr-12 text-body-sm outline-none focus:border-transparent focus:ring-2 focus:ring-primary disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isStreaming || question.trim().length === 0}
          aria-label="Send question"
          className="absolute right-3 top-1/2 -translate-y-1/2 text-primary transition-transform hover:scale-110 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Icon name="send" />
        </button>
      </form>
    </div>
  );
}

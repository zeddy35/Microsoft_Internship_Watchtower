// Loading, error, and empty states shared by every data-backed view.
// Usage: {isPending ? <SkeletonCard /> : error ? <ErrorState error={error} /> : ...}
import { IconAlertCircle, IconInbox } from "@tabler/icons-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "animate-pulse rounded-control bg-neutral-lighter",
        className,
      )}
    />
  );
}

export function SkeletonCard({
  lines = 3,
  className,
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <Card className={cn("p-4 sm:p-5", className)} aria-busy="true">
      <Skeleton className="h-4 w-32" />
      <div className="mt-4 flex flex-col gap-2.5">
        {Array.from({ length: lines }, (_, index) => (
          <Skeleton
            key={index}
            className={cn("h-3", index === lines - 1 ? "w-2/3" : "w-full")}
          />
        ))}
      </div>
    </Card>
  );
}

export interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  className?: string;
}

function messageFor(error: unknown) {
  if (error instanceof Error && error.message) return error.message;
  return "Something went wrong loading this view.";
}

export function ErrorState({ error, onRetry, className }: ErrorStateProps) {
  return (
    <Card className={cn("p-4 sm:p-5", className)} role="alert">
      <div className="flex items-start gap-3">
        <IconAlertCircle
          className="mt-0.5 size-5 shrink-0 text-state-error"
          stroke={1.75}
          aria-hidden="true"
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-neutral-primary">
            Could not load this view
          </p>
          <p className="mt-1 text-sm text-neutral-secondary">
            {messageFor(error)}
          </p>
          {onRetry && (
            <Button variant="secondary" onClick={onRetry} className="mt-3">
              Try again
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

export interface EmptyStateProps {
  title: string;
  description?: ReactNode;
  className?: string;
}

export function EmptyState({ title, description, className }: EmptyStateProps) {
  return (
    <Card className={cn("p-6 text-center", className)}>
      <IconInbox
        className="mx-auto size-6 text-neutral-tertiary"
        stroke={1.5}
        aria-hidden="true"
      />
      <p className="mt-2 text-sm font-medium text-neutral-primary">{title}</p>
      {description && (
        <div className="mt-1 text-sm text-neutral-secondary">{description}</div>
      )}
    </Card>
  );
}

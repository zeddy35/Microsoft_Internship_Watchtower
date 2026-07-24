// Fluent pill/badge for status, trend, and risk labels.
// Usage: <Badge variant="warning">At risk</Badge>
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type BadgeVariant =
  "neutral" | "success" | "warning" | "severe" | "error";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  neutral: "bg-neutral-lighter text-neutral-secondary",
  success: "bg-state-success-bg text-state-success",
  warning: "bg-state-warning-bg text-state-warning-fg",
  severe: "bg-state-severe-bg text-state-severe-fg",
  error: "bg-state-error-bg text-state-error-fg",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({
  variant = "neutral",
  className,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...props}
    />
  );
}

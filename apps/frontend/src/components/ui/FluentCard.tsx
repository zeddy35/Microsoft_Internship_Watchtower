import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type FluentCardProps = HTMLAttributes<HTMLDivElement>;

export function FluentCard({ className, ...props }: FluentCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-outline-variant bg-surface-container-lowest shadow-card transition-shadow duration-150 hover:shadow-card-hover",
        className,
      )}
      {...props}
    />
  );
}

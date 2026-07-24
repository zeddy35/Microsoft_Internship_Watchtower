// Fluent card surface: white background, thin neutral-light border, rounded corners, subtle shadow.
// Usage: <Card className="p-4">...</Card>
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type CardProps = HTMLAttributes<HTMLDivElement>;

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-card border border-neutral-light bg-neutral-white shadow-card",
        className,
      )}
      {...props}
    />
  );
}

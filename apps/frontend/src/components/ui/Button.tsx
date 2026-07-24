// Fluent button: solid brand primary, outline secondary.
// Usage: <Button variant="primary">Export digest</Button>
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type ButtonVariant = "primary" | "secondary";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-brand text-neutral-white hover:bg-brand-hover disabled:bg-neutral-tertiary-alt disabled:text-neutral-white",
  secondary:
    "border border-neutral-light bg-neutral-white text-neutral-primary hover:bg-neutral-lighter disabled:text-neutral-tertiary",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({
  variant = "primary",
  type = "button",
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-control px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...props}
    />
  );
}

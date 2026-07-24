import { cn } from "@/lib/cn";

export type StatusPillVariant = "critical" | "at-risk" | "healthy";

const VARIANT_STYLES: Record<StatusPillVariant, { pill: string; dot: string }> = {
  critical: { pill: "bg-error-container text-on-error-container", dot: "bg-error" },
  "at-risk": { pill: "bg-tertiary-fixed text-on-tertiary-fixed-variant", dot: "bg-tertiary" },
  healthy: { pill: "bg-green-100 text-green-800", dot: "bg-green-600" },
};

const VARIANT_LABEL: Record<StatusPillVariant, string> = {
  critical: "Critical",
  "at-risk": "At risk",
  healthy: "Healthy",
};

type StatusPillProps = {
  status: StatusPillVariant;
  label?: string;
  size?: "sm" | "md";
  className?: string;
};

export function StatusPill({ status, label, size = "sm", className }: StatusPillProps) {
  const styles = VARIANT_STYLES[status];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-bold",
        styles.pill,
        size === "sm"
          ? "px-2 py-0.5 text-[10px] uppercase tracking-wide"
          : "px-3 py-0.5 text-body-sm",
        className,
      )}
    >
      <span className={cn("size-1.5 shrink-0 rounded-full", styles.dot)} />
      {label ?? VARIANT_LABEL[status]}
    </span>
  );
}

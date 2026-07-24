import type { CSSProperties } from "react";
import { cn } from "@/lib/cn";

type IconProps = {
  name: string;
  filled?: boolean;
  size?: number;
  className?: string;
};

export function Icon({ name, filled = false, size = 24, className }: IconProps) {
  const style: CSSProperties = {
    fontSize: size,
    fontVariationSettings: `'FILL' ${filled ? 1 : 0}, 'wght' 400, 'GRAD' 0, 'opsz' ${size}`,
  };

  return (
    <span
      aria-hidden="true"
      className={cn("material-symbols-outlined select-none leading-none", className)}
      style={style}
    >
      {name}
    </span>
  );
}

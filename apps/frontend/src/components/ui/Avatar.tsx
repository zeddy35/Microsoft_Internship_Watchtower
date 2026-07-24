import { cn } from "@/lib/cn";

type AvatarProps = {
  name: string;
  size?: number;
  className?: string;
};

const PALETTE = [
  "bg-primary-fixed text-on-primary-fixed",
  "bg-secondary-fixed text-on-secondary-fixed",
  "bg-tertiary-fixed text-on-tertiary-fixed",
];

function initialsFor(name: string) {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return `${first}${last}`.toUpperCase();
}

function paletteIndexFor(name: string) {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) {
    hash = (hash * 31 + name.charCodeAt(i)) % PALETTE.length;
  }
  return hash;
}

export function Avatar({ name, size = 32, className }: AvatarProps) {
  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full font-bold",
        PALETTE[paletteIndexFor(name)],
        className,
      )}
      style={{ width: size, height: size, fontSize: size * 0.375 }}
      title={name}
    >
      {initialsFor(name)}
    </div>
  );
}

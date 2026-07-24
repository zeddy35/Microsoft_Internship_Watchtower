import type { ReactNode } from "react";
import { FluentCard } from "@/components/ui/FluentCard";
import { cn } from "@/lib/cn";

type SectionCardProps = {
  title: string;
  action?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
};

export function SectionCard({
  title,
  action,
  className,
  bodyClassName,
  children,
}: SectionCardProps) {
  return (
    <FluentCard className={cn("p-6", className)}>
      <div className="mb-6 flex items-center justify-between">
        <h3 className="font-title-sm text-title-sm">{title}</h3>
        {action}
      </div>
      <div className={bodyClassName}>{children}</div>
    </FluentCard>
  );
}

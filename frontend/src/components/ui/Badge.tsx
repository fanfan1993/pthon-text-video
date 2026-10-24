import { cn } from "@/lib/cn";
import { STATUS_META } from "@/lib/constants";
import type { ProjectStatus } from "@/types";

export function StatusBadge({ status }: { status: ProjectStatus }) {
  const meta = STATUS_META[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        meta.className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", meta.dot)} />
      {meta.label}
    </span>
  );
}

export function Tag({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-slate-300",
        className,
      )}
    >
      {children}
    </span>
  );
}

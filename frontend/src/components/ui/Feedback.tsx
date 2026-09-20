import { AlertTriangle, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

export function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn("animate-spin text-current", className ?? "h-4 w-4")}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4z"
      />
    </svg>
  );
}

export function Progress({ value, label }: { value: number; label?: string }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div
      className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-200"
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div className="h-full rounded-full bg-primary transition-[width] duration-500" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-zinc-300 bg-white/60 px-6 py-10 text-center">
      {Icon ? <Icon className="h-6 w-6 text-zinc-400" aria-hidden="true" /> : null}
      <p className="text-sm font-medium text-zinc-700">{title}</p>
      {description ? <p className="max-w-sm text-xs text-zinc-500">{description}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-6 py-8 text-center"
    >
      <AlertTriangle className="h-6 w-6 text-red-500" aria-hidden="true" />
      <p className="text-sm font-medium text-red-800">{title}</p>
      {description ? <p className="max-w-sm text-xs text-red-700">{description}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}

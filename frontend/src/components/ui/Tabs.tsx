import { motion } from "motion/react";
import { useId } from "react";

import { cn } from "@/lib/cn";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
}

const SLIDE = { type: "spring", stiffness: 500, damping: 38 } as const;

export function Tabs({
  items,
  active,
  onChange,
  size = "md",
}: {
  items: TabItem[];
  active: string;
  onChange: (id: string) => void;
  size?: "sm" | "md";
}) {
  // One indicator per Tabs instance, so two tab bars on a page never trade indicators.
  const indicatorId = useId();

  return (
    <div role="tablist" className="flex items-center gap-1 overflow-x-auto rounded-xl bg-zinc-100/80 p-1 ring-1 ring-inset ring-zinc-200/60 dark:bg-white/5 dark:ring-white/10">
      {items.map((item) => {
        const selected = item.id === active;
        return (
          <button
            key={item.id}
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(item.id)}
            className={cn(
              "relative shrink-0 whitespace-nowrap rounded-lg font-medium transition-colors",
              size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm",
              selected ? "text-zinc-900 dark:text-zinc-50" : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100",
            )}
          >
            {selected ? (
              <motion.span
                layoutId={indicatorId}
                aria-hidden="true"
                className="absolute inset-0 bg-white shadow-[0_1px_2px_rgba(24,24,27,0.08),0_2px_6px_-2px_rgba(67,56,202,0.25)] dark:bg-zinc-800"
                style={{ borderRadius: 8 }}
                transition={SLIDE}
              />
            ) : null}
            <span className="relative">
              {item.label}
              {item.count !== undefined ? (
                <span className="ml-1.5 tabular-nums text-zinc-600 dark:text-zinc-400">{item.count}</span>
              ) : null}
            </span>
          </button>
        );
      })}
    </div>
  );
}

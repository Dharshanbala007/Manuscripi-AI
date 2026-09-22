import { motion } from "motion/react";
import { Check } from "lucide-react";
import { useLocation } from "react-router-dom";

import { cn } from "@/lib/cn";
import { STEPS, useFlowStage } from "@/state/flowStage";

const SLIDE = { type: "spring", stiffness: 420, damping: 34 } as const;

function currentStep(pathname: string, workspaceStage: number | null): number | null {
  if (pathname.startsWith("/upload")) return 0;
  if (pathname.startsWith("/analyze")) return 1;
  if (pathname.startsWith("/workspace")) return workspaceStage ?? 2;
  return null;
}

// A persistent progress rail: the active step gets the same glass-pill "lamp" treatment
// as GlassNavBar's tabs, so the header nav and this rail read as one system.
export function FlowRail() {
  const { pathname } = useLocation();
  const { workspaceStage } = useFlowStage();
  const current = currentStep(pathname, workspaceStage);
  if (current === null) return null;

  return (
    <nav
      aria-label="Manuscript progress"
      className="mx-auto mb-6 flex max-w-2xl items-center gap-1 rounded-full border border-border bg-background/40 p-1.5 shadow-glass backdrop-blur-xl dark:shadow-glass-dark"
    >
      <ol className="flex flex-1 items-center">
        {STEPS.map((label, i) => {
          const state = i < current ? "done" : i === current ? "active" : "todo";
          return (
            <li
              key={label}
              aria-current={state === "active" ? "step" : undefined}
              className="relative flex flex-1 items-center justify-center"
            >
              {state === "active" ? (
                <motion.span
                  layoutId="flow-rail-lamp"
                  aria-hidden="true"
                  className="absolute inset-0 -z-10 rounded-full bg-primary/10"
                  transition={SLIDE}
                >
                  <span className="absolute -top-1.5 left-1/2 h-1 w-6 -translate-x-1/2 rounded-t-full bg-primary">
                    <span className="absolute -left-3 -top-2.5 h-6 w-12 rounded-full bg-primary/30 blur-md" />
                  </span>
                </motion.span>
              ) : null}
              <span
                className={cn(
                  "relative z-10 flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium transition-colors sm:px-3",
                  state === "active" && "text-primary",
                  state === "done" && "text-emerald-700 dark:text-emerald-400",
                  state === "todo" && "text-muted-foreground",
                )}
              >
                <span
                  aria-hidden="true"
                  className={cn(
                    "grid h-4 w-4 place-items-center rounded-full text-[10px] tabular-nums",
                    state === "active" && "bg-primary/15",
                    state === "done" && "bg-emerald-100 dark:bg-emerald-500/20",
                    state === "todo" && "bg-secondary",
                  )}
                >
                  {state === "done" ? <Check className="h-2.5 w-2.5" /> : i + 1}
                </span>
                <span className={cn(state !== "active" && "sr-only sm:not-sr-only")}>{label}</span>
                {state === "done" ? <span className="sr-only">(completed)</span> : null}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

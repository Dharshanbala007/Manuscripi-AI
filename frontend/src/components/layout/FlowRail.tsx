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

// A persistent progress rail: the filled pill slides between steps as the flow advances.
export function FlowRail() {
  const { pathname } = useLocation();
  const { workspaceStage } = useFlowStage();
  const current = currentStep(pathname, workspaceStage);
  if (current === null) return null;

  return (
    <nav aria-label="Manuscript progress" className="glass mx-auto mb-6 max-w-2xl rounded-full p-1.5">
      <ol className="flex items-center">
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
                  layoutId="flow-rail-pill"
                  aria-hidden="true"
                  className="absolute inset-0 bg-primary shadow-glow"
                  style={{ borderRadius: 9999 }}
                  transition={SLIDE}
                />
              ) : null}
              <span
                className={cn(
                  "relative z-10 flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium transition-colors sm:px-3",
                  state === "active" && "text-white",
                  state === "done" && "text-emerald-700 dark:text-emerald-400",
                  state === "todo" && "text-zinc-600 dark:text-zinc-400",
                )}
              >
                <span
                  aria-hidden="true"
                  className={cn(
                    "grid h-4 w-4 place-items-center rounded-full text-[10px] tabular-nums",
                    state === "active" && "bg-white/25",
                    state === "done" && "bg-emerald-100 dark:bg-emerald-500/20",
                    state === "todo" && "bg-zinc-200/70 dark:bg-white/10",
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

import { motion } from "motion/react";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

const SURFACE = { type: "spring", stiffness: 260, damping: 30, mass: 0.9 } as const;

// The one glass surface that follows the user through the flow. Every page renders its
// primary card inside a StageSurface with the same layoutId, so on navigation the old
// surface morphs (position, size, radius) into the new one instead of being replaced.
export function StageSurface({
  children,
  className,
  radius = 24,
}: {
  children: ReactNode;
  className?: string;
  radius?: number;
}) {
  return (
    <div className={cn("relative", className)}>
      <motion.div
        layoutId="stage-surface"
        data-testid="stage-surface"
        aria-hidden="true"
        className="glass absolute inset-0"
        style={{ borderRadius: radius }}
        transition={SURFACE}
      />
      <div className="relative">{children}</div>
    </div>
  );
}

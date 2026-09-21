import { ArrowRight } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

// Adapted from a user-supplied 21st.dev-style component. Colors were switched from
// hardcoded #111111/white to the foreground/background tokens so the ink-drop hover
// (text -> filled circle -> inverted text) re-themes correctly in both light and dark
// instead of only working against a white page.
export function FlowButton({
  text = "Flow Button",
  className,
  ...rest
}: { text?: string } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "group relative flex items-center gap-1 overflow-hidden rounded-full border-[1.5px] border-foreground/35 bg-transparent px-8 py-3 text-sm font-semibold text-foreground",
        "transition-all duration-[600ms] ease-[cubic-bezier(0.23,1,0.32,1)] hover:rounded-xl hover:border-transparent hover:text-background active:scale-[0.96]",
        className,
      )}
      {...rest}
    >
      <ArrowRight
        aria-hidden="true"
        className="absolute left-[-25%] z-[9] h-4 w-4 text-foreground transition-all duration-[800ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] group-hover:left-4 group-hover:text-background"
      />
      <span className="relative z-[1] -translate-x-3 transition-transform duration-[800ms] ease-out group-hover:translate-x-3">
        {text}
      </span>
      <span
        aria-hidden="true"
        className="absolute left-1/2 top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-foreground opacity-0 transition-all duration-[800ms] ease-[cubic-bezier(0.19,1,0.22,1)] group-hover:h-[220px] group-hover:w-[220px] group-hover:opacity-100"
      />
      <ArrowRight
        aria-hidden="true"
        className="absolute right-4 z-[9] h-4 w-4 text-foreground transition-all duration-[800ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] group-hover:right-[-25%] group-hover:text-background"
      />
    </button>
  );
}

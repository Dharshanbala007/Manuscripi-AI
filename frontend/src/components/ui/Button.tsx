import { type VariantProps, cva } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";
import { Spinner } from "./Feedback";

// Skin derived from the 21st.dev @ddoemonn/loading-button: 1px hairline, inset top
// highlight, soft drop shadow, 9px radius, 1px press.
export const buttonVariants = cva(
  "relative inline-flex select-none items-center justify-center gap-2 whitespace-nowrap font-medium outline-none " +
    "transition-[background-color,border-color,box-shadow,color] duration-150 active:translate-y-px " +
    "disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "border border-primary bg-primary text-primary-foreground hover:bg-primary/90 " +
          "shadow-[inset_0_1px_0_rgba(255,255,255,0.28),0_1px_2px_rgba(49,46,129,0.35),0_10px_22px_-12px_rgba(79,70,229,0.75)]",
        secondary:
          "border border-border bg-card text-foreground hover:bg-secondary " +
          "shadow-[inset_0_1.5px_0_rgba(255,255,255,0.95),inset_0_-1px_0_rgba(28,25,23,0.06),0_1px_2px_rgba(28,25,23,0.08)] " +
          "dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.06),inset_0_-1px_0_rgba(0,0,0,0.4),0_1px_2px_rgba(0,0,0,0.4)]",
        ghost: "text-muted-foreground hover:bg-secondary hover:text-foreground",
        danger: "border border-red-700 bg-red-700 text-white hover:bg-red-800",
      },
      size: {
        sm: "h-8 rounded-[8px] px-3 text-xs",
        md: "h-9 rounded-[9px] px-3.5 text-[13px]",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export function Button({
  variant,
  size,
  loading = false,
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner className="h-3.5 w-3.5" /> : null}
      {children}
    </button>
  );
}

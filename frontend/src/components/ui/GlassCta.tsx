// Adapted from a user-supplied 21st.dev-style glassmorphism CTA. Changes: a real
// <button> (this app has no CTA that navigates via a bare href) instead of an <a href="#">,
// so it stays keyboard/test-accessible the same way every other action button here is;
// dropped the headshot avatar slot (nothing in this product needs one); the hardcoded
// indigo/near-black colors were swapped for the design system's primary/shadow-glow
// tokens so it re-themes with light/dark instead of only matching a fixed dark page.
import { WandSparkles } from "lucide-react";
import type { ButtonHTMLAttributes, CSSProperties } from "react";

import { cn } from "@/lib/cn";

export type GlassCtaProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  text: string;
  spread?: string;
  shimmerColor?: string;
  speed?: string;
};

export function GlassCta({
  text,
  spread = "90deg",
  shimmerColor = "rgba(255,255,255,0.7)",
  speed = "4s",
  className,
  ...rest
}: GlassCtaProps) {
  return (
    <button
      type="button"
      className={cn(
        "group relative isolate inline-flex overflow-hidden rounded-full p-0 shadow-glow transition-transform duration-300 hover:scale-105 active:scale-[0.98]",
        className,
      )}
      style={
        {
          "--spread": spread,
          "--shimmer-color": shimmerColor,
          "--speed": speed,
        } as CSSProperties
      }
      {...rest}
    >
      {/* rotating shimmer, visible as a thin ring around the pill's edge */}
      <span className="absolute inset-0" aria-hidden="true">
        <span className="absolute inset-[-200%] block h-[400%] w-[400%] [animation:rotate-gradient_var(--speed)_linear_infinite]">
          <span className="absolute inset-0 block [background:conic-gradient(from_calc(270deg-(var(--spread)*0.5)),transparent_0,var(--shimmer-color)_var(--spread),transparent_var(--spread))]" />
        </span>
      </span>

      <span className="relative z-10 m-[1.5px] flex items-center gap-2.5 whitespace-nowrap rounded-full bg-primary py-3 pl-5 pr-4 text-sm font-semibold text-primary-foreground">
        {/* rotating highlight sweeping through the solid fill */}
        <span
          aria-hidden="true"
          className="absolute inset-0 overflow-hidden rounded-full"
          style={{ mixBlendMode: "overlay" }}
        >
          <span
            className="absolute left-1/2 top-1/2 block h-[200%] w-[200%] [animation:border-beam-rotation_4s_linear_infinite]"
            style={{
              background:
                "linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)",
            }}
          />
        </span>
        <span className="relative">{text}</span>
        <span className="relative grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white/15">
          <WandSparkles className="h-3.5 w-3.5" strokeWidth={2} aria-hidden="true" />
        </span>
      </span>
    </button>
  );
}

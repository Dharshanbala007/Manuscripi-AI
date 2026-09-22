// Adapted from a user-supplied 21st.dev-style glassmorphism nav bar. Trimmed to this
// app's two real destinations and wired to real routing instead of local tab state;
// dropped the isMobile/dark-class plumbing the original tracked itself (Tailwind
// breakpoints and the app's own theme system already cover that). Colors switched from
// hardcoded white/black opacities to the design system's tokens so it matches both themes.
import { motion } from "motion/react";
import { Home, Upload } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { cn } from "@/lib/cn";
import { ThemeToggle, type Theme } from "./ThemeToggle";

const ITEMS = [
  { name: "Home", to: "/", icon: Home, match: (p: string) => p === "/" },
  {
    name: "Upload",
    to: "/upload",
    icon: Upload,
    match: (p: string) => p.startsWith("/upload") || p.startsWith("/analyze") || p.startsWith("/workspace"),
  },
];

export function GlassNavBar({ theme, toggleTheme }: { theme: Theme; toggleTheme: () => void }) {
  const { pathname } = useLocation();

  return (
    <nav
      aria-label="Primary"
      className="flex items-center gap-1 rounded-full border border-border bg-background/40 p-1 shadow-glass backdrop-blur-xl dark:shadow-glass-dark"
    >
      {ITEMS.map((item) => {
        const active = item.match(pathname);
        const Icon = item.icon;
        return (
          <Link
            key={item.name}
            to={item.to}
            aria-current={active ? "page" : undefined}
            className={cn(
              "relative rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
              active ? "text-primary" : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Icon className="h-4 w-4 sm:hidden" aria-hidden="true" />
            <span className="sr-only sm:not-sr-only">{item.name}</span>
            {active ? (
              <motion.span
                layoutId="nav-lamp"
                aria-hidden="true"
                className="absolute inset-0 -z-10 rounded-full bg-primary/10"
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
              >
                <span className="absolute -top-1.5 left-1/2 h-1 w-6 -translate-x-1/2 rounded-t-full bg-primary">
                  <span className="absolute -left-3 -top-2.5 h-6 w-12 rounded-full bg-primary/30 blur-md" />
                </span>
              </motion.span>
            ) : null}
          </Link>
        );
      })}
      <div className="mx-0.5 h-5 w-px bg-border" />
      <ThemeToggle theme={theme} toggle={toggleTheme} />
    </nav>
  );
}

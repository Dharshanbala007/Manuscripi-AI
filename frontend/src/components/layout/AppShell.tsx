import { Lock, FileText } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { COPY } from "../../lib/deployment";
import { FlowRail } from "./FlowRail";
import { GlassNavBar } from "./GlassNavBar";
import { SilkBackground } from "./SilkBackground";
import { useTheme } from "./ThemeToggle";

export function AppShell({ children }: { children: ReactNode }) {
  const [theme, toggleTheme] = useTheme();

  return (
    <div className="flex min-h-full flex-col font-sans">
      <SilkBackground theme={theme} />
      <header className="sticky top-0 z-40 border-b border-border bg-background/70 backdrop-blur-md">
        <div className="mx-auto grid h-16 max-w-6xl grid-cols-[1fr_auto_1fr] items-center gap-3 px-4">
          <Link
            to="/"
            className="flex items-center gap-2 justify-self-start font-semibold tracking-tight text-foreground"
          >
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-primary to-violet-500 text-white shadow-glow">
              <FileText className="h-4 w-4" />
            </span>
            <span className="sr-only sm:not-sr-only">ManuScript AI</span>
          </Link>
          <GlassNavBar theme={theme} toggleTheme={toggleTheme} />
          <span className="hidden items-center gap-1.5 justify-self-end text-xs text-muted-foreground lg:flex">
            <Lock className="h-3.5 w-3.5" aria-hidden="true" />
            {COPY.privacyBadge}
          </span>
        </div>
      </header>
      <main className="relative mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <FlowRail />
        {children}
      </main>
      <footer className="border-t border-border px-4 py-4 text-center text-xs text-muted-foreground">
        {COPY.footer}
      </footer>
    </div>
  );
}

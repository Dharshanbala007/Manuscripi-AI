import { FileText, Lock } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { FlowRail } from "./FlowRail";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full flex-col font-sans">
      <header className="sticky top-0 z-40 border-b border-white/60 bg-white/65 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight text-zinc-900">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-primary to-violet-500 text-white shadow-glow">
              <FileText className="h-4 w-4" />
            </span>
            ManuScript AI
          </Link>
          <span className="hidden items-center gap-1.5 text-xs text-zinc-600 sm:flex">
            <Lock className="h-3.5 w-3.5" aria-hidden="true" />
            Processed locally — your manuscript never leaves this machine
          </span>
        </div>
      </header>
      <main className="relative mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <FlowRail />
        {children}
      </main>
      <footer className="border-t border-white/60 px-4 py-4 text-center text-xs text-zinc-600">
        ManuScript AI · rule-based, offline-capable · IEEE and Springer format profiles
      </footer>
    </div>
  );
}

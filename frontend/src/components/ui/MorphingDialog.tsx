// Adapted from 21st.dev @ibelick/morphing-dialog (motion-primitives, id 1438).
// Changes: motion/react imports; controlled `open`/`onOpenChange`; a caller-supplied
// `layoutId` so any element (e.g. a toolbar button) can be the morph origin; real
// aria-labelledby/-describedby targets; focus restored to whatever opened it; Tab trap
// computed at keypress time (content can load after open); backdrop above sticky chrome.
import { AnimatePresence, MotionConfig, type Transition, motion } from "motion/react";
import { X } from "lucide-react";
import {
  type ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

import { useClickOutside } from "@/hooks/use-click-outside";
import { cn } from "@/lib/cn";

interface Ctx {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  layoutId: string;
  titleId: string;
  descriptionId: string;
}

const MorphingDialogContext = createContext<Ctx | null>(null);

export function useMorphingDialog(): Ctx {
  const ctx = useContext(MorphingDialogContext);
  if (!ctx) throw new Error("useMorphingDialog must be used within <MorphingDialog>");
  return ctx;
}

export function MorphingDialog({
  children,
  open,
  onOpenChange,
  layoutId,
  transition,
}: {
  children: ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  layoutId?: string;
  transition?: Transition;
}) {
  const [internal, setInternal] = useState(false);
  const generated = useId();
  const isOpen = open ?? internal;

  const setIsOpen = useCallback(
    (next: boolean) => {
      if (open === undefined) setInternal(next);
      onOpenChange?.(next);
    },
    [open, onOpenChange],
  );

  const value = useMemo<Ctx>(
    () => ({
      isOpen,
      setIsOpen,
      layoutId: layoutId ?? `morph-${generated}`,
      titleId: `morph-title-${generated}`,
      descriptionId: `morph-desc-${generated}`,
    }),
    [isOpen, setIsOpen, layoutId, generated],
  );

  return (
    <MorphingDialogContext.Provider value={value}>
      <MotionConfig transition={transition}>{children}</MotionConfig>
    </MorphingDialogContext.Provider>
  );
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function MorphingDialogContainer({ children }: { children: ReactNode }) {
  const { isOpen } = useMorphingDialog();

  return createPortal(
    <AnimatePresence initial={false} mode="sync">
      {isOpen ? (
        <>
          <motion.div
            key="backdrop"
            className="fixed inset-0 z-50 bg-zinc-900/25 backdrop-blur-sm dark:bg-black/60"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
          <div key="stage" className="pointer-events-none fixed inset-0 z-50 grid place-items-center p-4">
            {children}
          </div>
        </>
      ) : null}
    </AnimatePresence>,
    document.body,
  );
}

export function MorphingDialogContent({
  children,
  className,
  radius = 24,
}: {
  children: ReactNode;
  className?: string;
  radius?: number;
}) {
  const { isOpen, setIsOpen, layoutId, titleId, descriptionId } = useMorphingDialog();
  const containerRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    openerRef.current = document.activeElement as HTMLElement | null;
    document.body.classList.add("overflow-hidden");
    containerRef.current?.focus();
    return () => {
      document.body.classList.remove("overflow-hidden");
      openerRef.current?.focus?.();
    };
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
        return;
      }
      if (event.key !== "Tab") return;
      const items = Array.from(
        containerRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? [],
      );
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement;
      if (event.shiftKey && (active === first || active === containerRef.current)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [isOpen, setIsOpen]);

  useClickOutside(containerRef, () => {
    if (isOpen) setIsOpen(false);
  });

  return (
    <motion.div
      ref={containerRef}
      layoutId={layoutId}
      tabIndex={-1}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      style={{ borderRadius: radius }}
      className={cn(
        "pointer-events-auto relative w-full overflow-hidden outline-none",
        "glass shadow-[0_30px_80px_-20px_rgba(49,46,129,0.35)] backdrop-blur-md",
        className,
      )}
    >
      {children}
    </motion.div>
  );
}

export function MorphingDialogTitle({ children, className }: { children: ReactNode; className?: string }) {
  const { titleId } = useMorphingDialog();
  return (
    <h2 id={titleId} className={className}>
      {children}
    </h2>
  );
}

export function MorphingDialogDescription({ children, className }: { children: ReactNode; className?: string }) {
  const { descriptionId } = useMorphingDialog();
  return (
    <p id={descriptionId} className={className}>
      {children}
    </p>
  );
}

export function MorphingDialogClose({ className }: { className?: string }) {
  const { setIsOpen } = useMorphingDialog();
  return (
    <button
      type="button"
      aria-label="Close dialog"
      onClick={() => setIsOpen(false)}
      className={cn(
        "grid h-8 w-8 place-items-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-800 dark:text-zinc-400 dark:hover:bg-white/10 dark:hover:text-zinc-100",
        className,
      )}
    >
      <X className="h-4 w-4" aria-hidden="true" />
    </button>
  );
}

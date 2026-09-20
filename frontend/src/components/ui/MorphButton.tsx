// Adapted from 21st.dev @ddoemonn/loading-button (id 23536): the label morphs through
// idle -> pending -> success -> error inside a fixed grid cell, so the button never
// changes width. Changes: variants/sizes shared with <Button>, an idle-face icon, a
// success/error background morph (contrast-safe colours), `title`, `onSuccess`, and
// `disabled` only applies while idle so the result face is never dimmed.
import type { VariantProps } from "class-variance-authority";
import { motion, useReducedMotion } from "motion/react";
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";

import { cn } from "@/lib/cn";
import { buttonVariants } from "./Button";

const CELL = { type: "spring", stiffness: 520, damping: 34, mass: 0.45 } as const;
const CROSSFADE = { type: "spring", stiffness: 260, damping: 34, mass: 0.8 } as const;
const INSTANT = { duration: 0 } as const;

export type AsyncActionStatus = "idle" | "pending" | "success" | "error";

function useAsyncAction(opts: {
  action: () => unknown;
  resetAfter: number;
  onError?: (error: unknown) => void;
  onSuccess?: () => void;
}) {
  const [status, setStatus] = useState<AsyncActionStatus>("idle");
  const phase = useRef<AsyncActionStatus>("idle");
  const runId = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const alive = useRef(true);
  const latest = useRef(opts);

  useEffect(() => {
    latest.current = opts;
  });

  const clear = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  }, []);

  const run = useCallback(() => {
    if (phase.current === "pending") return;
    clear();
    const id = ++runId.current;
    phase.current = "pending";
    setStatus("pending");

    const settle = (next: "success" | "error") => {
      if (!alive.current || id !== runId.current) return;
      phase.current = next;
      setStatus(next);
      if (next === "success") latest.current.onSuccess?.();
      timer.current = setTimeout(() => {
        if (!alive.current || id !== runId.current) return;
        phase.current = "idle";
        setStatus("idle");
      }, latest.current.resetAfter);
    };

    Promise.resolve()
      .then(() => latest.current.action())
      .then(
        () => settle("success"),
        (error: unknown) => {
          latest.current.onError?.(error);
          settle("error");
        },
      );
  }, [clear]);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      clear();
    };
  }, [clear]);

  return { status, run };
}

function Spinner({ still }: { still: boolean }) {
  return (
    <motion.svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      aria-hidden="true"
      className="shrink-0"
      animate={still ? undefined : { rotate: 360 }}
      transition={still ? undefined : { duration: 0.85, repeat: Infinity, ease: "linear" }}
    >
      <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.25" />
      <path d="M10.5 6A4.5 4.5 0 0 0 6 1.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </motion.svg>
  );
}

function Glyph({ d, w = 1.7 }: { d: string; w?: number }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true" className="shrink-0">
      <path d={d} stroke="currentColor" strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export interface MorphButtonProps extends VariantProps<typeof buttonVariants> {
  onAction: () => unknown;
  children: string;
  icon?: ReactNode;
  pendingLabel?: string;
  successLabel?: string;
  errorLabel?: string;
  resetAfter?: number;
  disabled?: boolean;
  title?: string;
  className?: string;
  onError?: (error: unknown) => void;
  onSuccess?: () => void;
}

export function MorphButton({
  onAction,
  children,
  icon,
  pendingLabel = children,
  successLabel = "Done",
  errorLabel = "Try again",
  resetAfter = 1400,
  disabled = false,
  title,
  className,
  variant = "secondary",
  size,
  onError,
  onSuccess,
}: MorphButtonProps) {
  const reduced = useReducedMotion();
  const { status, run } = useAsyncAction({ action: onAction, resetAfter, onError, onSuccess });
  const pending = status === "pending";
  const solid = variant === "primary" || variant === "danger";
  const fade = reduced ? INSTANT : CROSSFADE;

  const label =
    status === "pending"
      ? pendingLabel
      : status === "success"
        ? successLabel
        : status === "error"
          ? errorLabel
          : children;

  const faces = [
    { key: "idle", text: children, icon, tone: solid ? "text-white" : "text-zinc-800" },
    {
      key: "pending",
      text: pendingLabel,
      icon: <Spinner still={reduced === true || status !== "pending"} />,
      tone: solid ? "text-white/90" : "text-zinc-600",
    },
    {
      key: "success",
      text: successLabel,
      icon: <Glyph d="M2.6 6.3 4.9 8.6 9.4 3.6" />,
      tone: solid ? "text-white" : "text-emerald-700",
    },
    {
      key: "error",
      text: errorLabel,
      icon: <Glyph d="M6 2.9v3.5M6 9.05h.01" w={1.9} />,
      tone: solid ? "text-white" : "text-red-700",
    },
  ];

  return (
    <>
      <motion.button
        type="button"
        title={title}
        data-status={status}
        disabled={disabled && status === "idle"}
        aria-label={label}
        aria-busy={pending || undefined}
        aria-disabled={pending || undefined}
        whileTap={disabled || pending || reduced ? undefined : { y: 1 }}
        transition={CELL}
        onClick={(event) => {
          if (pending) {
            event.preventDefault();
            return;
          }
          run();
        }}
        className={cn(
          buttonVariants({ variant, size }),
          status === "success" && solid && "border-emerald-700 bg-emerald-700 hover:bg-emerald-700",
          status === "error" && solid && "border-red-700 bg-red-700 hover:bg-red-700",
          className,
        )}
      >
        <span aria-hidden className="relative grid place-items-center">
          {faces.map((face) => (
            <motion.span
              key={face.key}
              initial={false}
              animate={
                face.key === status
                  ? { opacity: 1, y: 0, filter: "blur(0px)" }
                  : { opacity: 0, y: 3, filter: "blur(3px)" }
              }
              transition={fade}
              className={cn(
                "col-start-1 row-start-1 flex items-center justify-center gap-1.5 whitespace-nowrap",
                face.tone,
              )}
            >
              {face.icon}
              {face.text}
            </motion.span>
          ))}
        </span>
      </motion.button>
      <span role="status" aria-live="polite" className="sr-only">
        {status === "success" ? successLabel : status === "error" ? errorLabel : ""}
      </span>
    </>
  );
}

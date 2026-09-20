import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { FileCheck2, ListChecks, Wand2 } from "lucide-react";
import type { ReactNode } from "react";

import { titleCase } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { buttonVariants } from "../ui/Button";
import { MorphButton } from "../ui/MorphButton";
import { FORMAT_DIALOG_ID } from "./FormatPicker";

const POP = { type: "spring", stiffness: 420, damping: 30 } as const;

// Pills pop in/out and their siblings glide to make room.
function Pill({ id, children }: { id: string; children: ReactNode }) {
  return (
    <motion.span
      key={id}
      layout
      initial={{ opacity: 0, scale: 0.85, y: 4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.85 }}
      transition={POP}
      className="inline-flex"
    >
      {children}
    </motion.span>
  );
}

export function TopBar({
  filename,
  docState,
  profileId,
  healthTotal,
  formatOpen,
  onOpenFormat,
  onValidate,
}: {
  filename: string;
  docState: string;
  profileId: string | null;
  healthTotal: number | null;
  formatOpen: boolean;
  onOpenFormat: () => void;
  onValidate: () => Promise<void>;
}) {
  const formatted = ["formatted", "validated", "exported"].includes(docState);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <LayoutGroup>
        <div className="flex min-w-0 flex-wrap items-center gap-2.5">
          <motion.h1
            layout="position"
            className="truncate text-base font-semibold tracking-tight text-zinc-900"
            title={filename}
          >
            {filename || "Manuscript"}
          </motion.h1>
          <AnimatePresence mode="popLayout" initial={false}>
            <Pill id={`state-${docState}`} key={`state-${docState}`}>
              <Badge tone="neutral">{titleCase(docState)}</Badge>
            </Pill>
            {profileId ? (
              <Pill id={`profile-${profileId}`} key={`profile-${profileId}`}>
                <Badge tone="accent">{profileId.toUpperCase()} profile applied</Badge>
              </Pill>
            ) : null}
            {healthTotal !== null ? (
              <Pill id={`health-${healthTotal}`} key={`health-${healthTotal}`}>
                <Badge tone={healthTotal >= 85 ? "success" : healthTotal >= 65 ? "warning" : "danger"}>
                  Health {healthTotal}
                </Badge>
              </Pill>
            ) : null}
          </AnimatePresence>
        </div>
      </LayoutGroup>

      <div className="flex items-center gap-2">
        <motion.button
          layoutId={FORMAT_DIALOG_ID}
          type="button"
          onClick={onOpenFormat}
          aria-haspopup="dialog"
          aria-expanded={formatOpen}
          style={{ borderRadius: 8 }}
          className={buttonVariants({ variant: "secondary", size: "sm" })}
        >
          <Wand2 className="h-3.5 w-3.5" aria-hidden="true" /> {formatted ? "Change format" : "Apply format"}
        </motion.button>
        <MorphButton
          size="sm"
          icon={<ListChecks className="h-3.5 w-3.5" aria-hidden="true" />}
          disabled={!formatted}
          pendingLabel="Validating…"
          successLabel="Checked"
          onAction={onValidate}
        >
          Validate
        </MorphButton>
        <span className="hidden items-center gap-1 text-xs text-zinc-500 sm:flex">
          <FileCheck2 className="h-3.5 w-3.5" aria-hidden="true" /> local
        </span>
      </div>
    </div>
  );
}

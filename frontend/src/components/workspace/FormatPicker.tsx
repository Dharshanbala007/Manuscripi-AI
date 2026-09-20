import { motion } from "motion/react";
import { Check } from "lucide-react";
import { useEffect, useState } from "react";

import { cn } from "@/lib/cn";
import { api } from "../../lib/api";
import type { ProfileSummary } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import {
  MorphingDialog,
  MorphingDialogClose,
  MorphingDialogContainer,
  MorphingDialogContent,
  MorphingDialogDescription,
  MorphingDialogTitle,
} from "../ui/MorphingDialog";
import { MorphButton } from "../ui/MorphButton";

// The TopBar button uses the same layoutId, so the dialog expands out of it.
export const FORMAT_DIALOG_ID = "format-dialog";

export function FormatPicker({
  open,
  onClose,
  currentProfile,
  onApply,
}: {
  open: boolean;
  onClose: () => void;
  currentProfile: string | null;
  onApply: (profileId: string) => Promise<void>;
}) {
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [selected, setSelected] = useState<string>(currentProfile ?? "ieee");

  useEffect(() => {
    if (open) api.formats().then(setProfiles).catch(() => setProfiles([]));
  }, [open]);

  useEffect(() => {
    setSelected(currentProfile ?? "ieee");
  }, [currentProfile, open]);

  return (
    <MorphingDialog
      open={open}
      onOpenChange={(next) => {
        if (!next) onClose();
      }}
      layoutId={FORMAT_DIALOG_ID}
      transition={{ type: "spring", bounce: 0.05, duration: 0.4 }}
    >
      <MorphingDialogContainer>
        <MorphingDialogContent className="max-w-lg">
          <motion.div
            className="p-6"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12, duration: 0.25 }}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <MorphingDialogTitle className="text-base font-semibold tracking-tight text-zinc-900">
                  Choose a publication format
                </MorphingDialogTitle>
                <MorphingDialogDescription className="mt-1 text-sm text-zinc-600">
                  You can change this and re-apply before exporting.
                </MorphingDialogDescription>
              </div>
              <MorphingDialogClose />
            </div>

            <div className="mt-4 flex flex-col gap-3">
              {profiles.map((p) => {
                const disabled = p.status !== "available";
                const isSelected = selected === p.id && !disabled;
                return (
                  <button
                    key={p.id}
                    type="button"
                    disabled={disabled}
                    onClick={() => setSelected(p.id)}
                    className={cn(
                      "rounded-xl border p-4 text-left transition-all",
                      disabled && "cursor-not-allowed opacity-60",
                      isSelected
                        ? "border-primary bg-accent shadow-[0_8px_24px_-14px_rgba(79,70,229,0.6)]"
                        : "border-border bg-white/70 hover:border-zinc-300 hover:bg-white",
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-zinc-900">{p.name}</span>
                      {disabled ? (
                        <Badge tone="muted">Planned</Badge>
                      ) : isSelected ? (
                        <Check className="h-4 w-4 text-primary" />
                      ) : null}
                    </div>
                    <p className="mt-1 text-xs text-zinc-600">{p.summary}</p>
                    <ul className="mt-2 flex flex-wrap gap-1.5">
                      {p.features.map((f) => (
                        <li key={f} className="rounded bg-white/80 px-1.5 py-0.5 text-[11px] text-zinc-600">
                          {f}
                        </li>
                      ))}
                    </ul>
                  </button>
                );
              })}
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <MorphButton
                variant="primary"
                pendingLabel="Applying…"
                successLabel="Applied"
                onAction={() => onApply(selected)}
                onSuccess={() => window.setTimeout(onClose, 450)}
              >
                Apply format
              </MorphButton>
            </div>
          </motion.div>
        </MorphingDialogContent>
      </MorphingDialogContainer>
    </MorphingDialog>
  );
}

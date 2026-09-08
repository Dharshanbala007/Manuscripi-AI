import { Check } from "lucide-react";
import { useEffect, useState } from "react";

import { cn } from "../../lib/cn";
import { api } from "../../lib/api";
import type { ProfileSummary } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Dialog } from "../ui/Dialog";

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
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    if (open) api.formats().then(setProfiles).catch(() => setProfiles([]));
  }, [open]);

  useEffect(() => {
    setSelected(currentProfile ?? "ieee");
  }, [currentProfile, open]);

  async function apply() {
    setApplying(true);
    try {
      await onApply(selected);
      onClose();
    } finally {
      setApplying(false);
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Choose a publication format"
      description="You can change this and re-apply before exporting."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={apply} loading={applying}>
            Apply format
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-3">
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
                "rounded-xl border p-4 text-left transition-colors",
                disabled && "cursor-not-allowed opacity-60",
                isSelected ? "border-accent bg-accent-soft" : "border-zinc-200 hover:border-zinc-300",
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-zinc-900">{p.name}</span>
                {disabled ? (
                  <Badge tone="muted">Planned</Badge>
                ) : isSelected ? (
                  <Check className="h-4 w-4 text-accent" />
                ) : null}
              </div>
              <p className="mt-1 text-xs text-zinc-500">{p.summary}</p>
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {p.features.map((f) => (
                  <li key={f} className="rounded bg-white/70 px-1.5 py-0.5 text-[11px] text-zinc-600">
                    {f}
                  </li>
                ))}
              </ul>
            </button>
          );
        })}
      </div>
    </Dialog>
  );
}

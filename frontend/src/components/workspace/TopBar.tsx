import { FileCheck2, ListChecks, Wand2 } from "lucide-react";

import { titleCase } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

export function TopBar({
  filename,
  docState,
  profileId,
  healthTotal,
  onOpenFormat,
  onValidate,
  validating,
}: {
  filename: string;
  docState: string;
  profileId: string | null;
  healthTotal: number | null;
  onOpenFormat: () => void;
  onValidate: () => void;
  validating: boolean;
}) {
  const formatted = ["formatted", "validated", "exported"].includes(docState);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-200 pb-4">
      <div className="flex min-w-0 items-center gap-3">
        <h1 className="truncate text-base font-semibold tracking-tight text-zinc-900" title={filename}>
          {filename || "Manuscript"}
        </h1>
        <Badge tone="neutral">{titleCase(docState)}</Badge>
        {profileId ? <Badge tone="accent">{profileId.toUpperCase()} profile applied</Badge> : null}
        {healthTotal !== null ? (
          <Badge tone={healthTotal >= 85 ? "success" : healthTotal >= 65 ? "warning" : "danger"}>
            Health {healthTotal}
          </Badge>
        ) : null}
      </div>

      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={onOpenFormat}>
          <Wand2 className="h-3.5 w-3.5" /> {formatted ? "Change format" : "Apply format"}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={onValidate}
          disabled={!formatted}
          loading={validating}
        >
          <ListChecks className="h-3.5 w-3.5" /> Validate
        </Button>
        <span className="hidden items-center gap-1 text-xs text-zinc-500 sm:flex">
          <FileCheck2 className="h-3.5 w-3.5" /> local
        </span>
      </div>
    </div>
  );
}

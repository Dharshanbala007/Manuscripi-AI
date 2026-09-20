import { Check } from "lucide-react";

import { cn } from "../../lib/cn";
import type { StageOut } from "../../lib/types";
import { Spinner } from "../ui/Feedback";

export const STAGE_DEFS: { key: string; label: string }[] = [
  { key: "read", label: "Reading document" },
  { key: "extract", label: "Extracting content" },
  { key: "metadata", label: "Detecting metadata" },
  { key: "classify", label: "Classifying sections" },
  { key: "figures", label: "Detecting figures & tables" },
  { key: "references", label: "Detecting references" },
  { key: "structure", label: "Preparing document structure" },
];

export const pendingStages = (): StageOut[] =>
  STAGE_DEFS.map((s) => ({ ...s, status: "pending", detail: "" }));

export function StageList({ stages }: { stages: StageOut[] }) {
  const active = stages.find((s) => s.status === "active");

  return (
    <div>
      <ol className="flex flex-col">
        {stages.map((stage) => (
          <li key={stage.key} className="flex items-center gap-3 py-2">
            <StageIcon status={stage.status} />
            <span
              className={cn(
                "text-sm",
                stage.status === "done" && "text-zinc-700",
                stage.status === "active" && "font-medium text-zinc-900",
                stage.status === "pending" && "text-zinc-500",
              )}
            >
              {stage.label}
            </span>
            {stage.detail ? (
              <span className="ml-auto text-xs tabular-nums text-zinc-500">{stage.detail}</span>
            ) : null}
          </li>
        ))}
      </ol>
      <p className="sr-only" aria-live="polite">
        {active ? `${active.label}…` : "Analysis complete"}
      </p>
    </div>
  );
}

function StageIcon({ status }: { status: StageOut["status"] }) {
  if (status === "done") {
    return (
      <span className="grid h-5 w-5 place-items-center rounded-full bg-emerald-100 text-emerald-600">
        <Check className="h-3 w-3" aria-hidden="true" />
      </span>
    );
  }
  if (status === "active") {
    return <Spinner className="h-5 w-5 text-primary" />;
  }
  return <span className="h-5 w-5 rounded-full border-2 border-zinc-200" aria-hidden="true" />;
}

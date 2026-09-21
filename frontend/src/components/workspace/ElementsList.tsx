import { useState } from "react";

import { cn } from "../../lib/cn";
import { titleCase } from "../../lib/format";
import type { ElementOut } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Card, CardBody, CardHeader } from "../ui/Card";

const KINDS = [
  "title",
  "author",
  "affiliation",
  "abstract",
  "keywords",
  "heading",
  "subheading",
  "paragraph",
  "numbered_list_item",
  "bullet_list_item",
  "table",
  "figure",
  "caption",
  "equation",
  "reference_item",
  "acknowledgement",
  "appendix",
  "other",
];

export function ElementsList({
  elements,
  onReclassify,
}: {
  elements: ElementOut[];
  onReclassify: (blockId: string, patch: { kind?: string; level?: number }) => Promise<void>;
}) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const reviewCount = elements.filter((e) => e.needs_review).length;

  async function change(blockId: string, kind: string) {
    setBusyId(blockId);
    try {
      await onReclassify(blockId, { kind });
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Card>
      <CardHeader
        title="Detected elements"
        description={`${elements.length} elements${reviewCount ? ` · ${reviewCount} need review` : ""}`}
      />
      <CardBody className="max-h-[28rem] overflow-y-auto p-0">
        <ul className="divide-y divide-zinc-100 dark:divide-white/10">
          {elements.map((el) => (
            <li
              key={el.id}
              data-block-id={el.id}
              className={cn(
                "flex items-start gap-3 px-5 py-3 scroll-mt-24",
                el.needs_review && "bg-amber-50/40 dark:bg-amber-500/10",
              )}
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-zinc-800 dark:text-zinc-100">
                  {el.text_preview || <span className="italic text-zinc-500 dark:text-zinc-400">[no text]</span>}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-1.5">
                  <Badge tone="neutral">{titleCase(el.kind)}</Badge>
                  {el.level ? <Badge tone="muted">L{el.level}</Badge> : null}
                  <span className="text-[11px] tabular-nums text-zinc-500 dark:text-zinc-400">
                    {Math.round(el.confidence * 100)}%
                  </span>
                  {el.needs_review ? <Badge tone="warning">needs review</Badge> : null}
                </div>
              </div>
              <label className="shrink-0">
                <span className="sr-only">Reclassify element</span>
                <select
                  className="rounded-md border border-zinc-300 dark:border-white/15 bg-white dark:bg-zinc-900 px-2 py-1 text-xs text-zinc-700 dark:text-zinc-200 disabled:opacity-50"
                  value={el.kind}
                  disabled={busyId === el.id}
                  onChange={(e) => change(el.id, e.target.value)}
                >
                  {KINDS.map((k) => (
                    <option key={k} value={k}>
                      {titleCase(k)}
                    </option>
                  ))}
                </select>
              </label>
            </li>
          ))}
        </ul>
      </CardBody>
    </Card>
  );
}

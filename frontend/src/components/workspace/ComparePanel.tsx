import { useEffect } from "react";

import { titleCase } from "../../lib/format";
import type { ComparisonOut, MetaSummary, StatsOut } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Card, CardBody, CardHeader } from "../ui/Card";
import { EmptyState, Spinner } from "../ui/Feedback";

const STAT_ROWS: (keyof StatsOut)[] = [
  "paragraphs",
  "headings",
  "tables",
  "figures",
  "references",
];

export function ComparePanel({
  comparison,
  loading,
  ready,
  onLoad,
}: {
  comparison: ComparisonOut | null;
  loading: boolean;
  ready: boolean;
  onLoad: () => void;
}) {
  useEffect(() => {
    if (ready && !comparison && !loading) onLoad();
  }, [ready, comparison, loading, onLoad]);

  if (!ready) {
    return (
      <Card>
        <CardHeader title="Before / after" />
        <CardBody>
          <EmptyState title="Apply a format to compare the original and formatted document" />
        </CardBody>
      </Card>
    );
  }

  if (loading || !comparison) {
    return (
      <Card>
        <CardHeader title="Before / after" />
        <CardBody>
          <div className="grid place-items-center py-10">
            <Spinner className="h-5 w-5 text-accent" />
          </div>
        </CardBody>
      </Card>
    );
  }

  const { original, formatted, deltas, summary } = comparison;

  return (
    <Card>
      <CardHeader
        title="Before / after"
        description="Structural and metadata comparison — not a pixel-perfect Word diff."
      />
      <CardBody className="flex flex-col gap-5">
        <div className="rounded-lg bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
          Formatting changes <b className="text-zinc-900">{summary.formatting_changes}</b>
          {" · "}Content changes <b className="text-zinc-900">{summary.content_changes}</b>
          {" · "}Warnings remaining <b className="text-zinc-900">{summary.warnings_remaining}</b>
          {" · "}Preservation{" "}
          <b className={summary.preservation_passed ? "text-emerald-700" : "text-amber-700"}>
            {summary.preservation_passed ? "passed" : "review required"}
          </b>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-zinc-500">
                <th className="py-1 font-medium">Element</th>
                <th className="py-1 font-medium">Original</th>
                <th className="py-1 font-medium">Formatted</th>
                <th className="py-1 font-medium">Change</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {STAT_ROWS.map((key) => {
                const delta = deltas[key] ?? 0;
                return (
                  <tr key={key}>
                    <td className="py-1.5 text-zinc-600">{titleCase(key)}</td>
                    <td className="py-1.5 tabular-nums">{original.stats[key]}</td>
                    <td className="py-1.5 tabular-nums">{formatted.stats[key]}</td>
                    <td className="py-1.5">
                      <Badge tone={delta === 0 ? "success" : "warning"}>
                        {delta === 0 ? "0" : delta > 0 ? `+${delta}` : `${delta}`}
                      </Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <MetaBlock label="Original" meta={original.metadata} sections={original.sections.length} />
          <MetaBlock label="Formatted" meta={formatted.metadata} sections={formatted.sections.length} />
        </div>
      </CardBody>
    </Card>
  );
}

function MetaBlock({
  label,
  meta,
  sections,
}: {
  label: string;
  meta: MetaSummary;
  sections: number;
}) {
  return (
    <div className="rounded-lg border border-zinc-200 p-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{label}</p>
      <dl className="mt-2 flex flex-col gap-1 text-xs">
        <Row label="Title" value={meta.title || "—"} />
        <Row label="Authors" value={meta.authors.join(", ") || "—"} />
        <Row label="Abstract" value={meta.abstract_present ? "present" : "—"} />
        <Row label="Keywords" value={meta.keywords.join(", ") || "—"} />
        <Row label="Sections" value={String(sections)} />
      </dl>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <dt className="w-16 shrink-0 text-zinc-500">{label}</dt>
      <dd className="min-w-0 flex-1 truncate text-zinc-700" title={value}>
        {value}
      </dd>
    </div>
  );
}

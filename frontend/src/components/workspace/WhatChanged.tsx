import { Check, ShieldAlert, ShieldCheck } from "lucide-react";

import type { ChangeLogOut, PreservationOut } from "../../lib/types";
import { Card, CardBody, CardHeader } from "../ui/Card";
import { EmptyState } from "../ui/Feedback";

export function WhatChanged({
  changeLog,
  preservation,
}: {
  changeLog: ChangeLogOut | null;
  preservation: PreservationOut | null;
}) {
  if (!changeLog) {
    return (
      <Card>
        <CardHeader title="What changed" />
        <CardBody>
          <EmptyState title="Apply a format to see the changes" />
        </CardBody>
      </Card>
    );
  }

  const contentPreserved = changeLog.content_changes.length === 0;

  return (
    <Card>
      <CardHeader title="What changed" description={`${changeLog.warnings_remaining} warnings remaining`} />
      <CardBody className="flex flex-col gap-4">
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Formatting changes
          </h3>
          <ul className="mt-2 flex flex-col gap-1.5 text-sm text-zinc-700">
            {changeLog.formatting_changes.map((change, i) => (
              <li key={i} className="flex items-start gap-2">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                {change}
              </li>
            ))}
          </ul>
        </section>

        <section
          className={`rounded-lg border px-3 py-2 ${
            contentPreserved ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"
          }`}
        >
          <div className="flex items-center gap-2 text-sm font-medium">
            {contentPreserved ? (
              <>
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span className="text-emerald-800">Content preservation check passed</span>
              </>
            ) : (
              <>
                <ShieldAlert className="h-4 w-4 text-amber-600" />
                <span className="text-amber-800">Review required</span>
              </>
            )}
          </div>
          {contentPreserved ? (
            <ul className="mt-1 text-xs text-emerald-700">
              <li>No content removed</li>
              <li>No paragraphs reordered</li>
            </ul>
          ) : (
            <ul className="mt-1 list-disc pl-4 text-xs text-amber-800">
              {changeLog.content_changes.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          )}
          {preservation && preservation.paragraph_delta !== 0 ? (
            <p className="mt-1 text-xs text-zinc-500">
              Paragraph count changed by {preservation.paragraph_delta} (front-matter rebuild).
            </p>
          ) : null}
        </section>
      </CardBody>
    </Card>
  );
}

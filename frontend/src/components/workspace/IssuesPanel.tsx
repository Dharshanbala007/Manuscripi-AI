import { AlertCircle, AlertTriangle, ArrowRight, Info } from "lucide-react";
import { useMemo, useState } from "react";

import type { IssueOut, Severity } from "../../lib/types";
import { Card, CardBody, CardHeader } from "../ui/Card";
import { EmptyState } from "../ui/Feedback";
import { Tabs } from "../ui/Tabs";

type Filter = "all" | "error" | "warning" | "info";

const SEV_ICON = {
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
} as const;
const SEV_CLASS: Record<Severity, string> = {
  error: "text-red-500",
  warning: "text-amber-500",
  info: "text-zinc-400",
};

export function IssuesPanel({
  issues,
  onLocate,
}: {
  issues: IssueOut[];
  onLocate: (location: string) => void;
}) {
  const [filter, setFilter] = useState<Filter>("all");

  const counts = useMemo(
    () => ({
      all: issues.length,
      error: issues.filter((i) => i.severity === "error").length,
      warning: issues.filter((i) => i.severity === "warning").length,
      info: issues.filter((i) => i.severity === "info").length,
    }),
    [issues],
  );

  const visible = filter === "all" ? issues : issues.filter((i) => i.severity === filter);

  return (
    <Card>
      <CardHeader
        title={`${issues.length} issue${issues.length === 1 ? "" : "s"} found`}
        description={
          counts.error || counts.warning
            ? `${counts.error} errors · ${counts.warning} warnings · ${counts.info} suggestions`
            : "No blocking problems detected."
        }
      />
      <CardBody className="flex flex-col gap-3">
        <Tabs
          size="sm"
          active={filter}
          onChange={(id) => setFilter(id as Filter)}
          items={[
            { id: "all", label: "All", count: counts.all },
            { id: "error", label: "Errors", count: counts.error },
            { id: "warning", label: "Warnings", count: counts.warning },
            { id: "info", label: "Suggestions", count: counts.info },
          ]}
        />

        {visible.length === 0 ? (
          <EmptyState title="Nothing here" description="No issues match this filter." />
        ) : (
          <ul className="flex flex-col gap-2">
            {visible.map((issue) => {
              const Icon = SEV_ICON[issue.severity];
              return (
                <li
                  key={issue.id}
                  className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                >
                  <div className="flex items-start gap-2">
                    <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${SEV_CLASS[issue.severity]}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-zinc-800">{issue.message}</p>
                      {issue.suggested_action ? (
                        <p className="mt-0.5 text-xs text-zinc-500">{issue.suggested_action}</p>
                      ) : null}
                      {issue.location ? (
                        <button
                          type="button"
                          onClick={() => onLocate(issue.location as string)}
                          className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
                        >
                          Review <ArrowRight className="h-3 w-3" />
                        </button>
                      ) : null}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

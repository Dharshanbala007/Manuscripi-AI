import { cn } from "../../lib/cn";
import type { HealthScoreOut } from "../../lib/types";
import { Card, CardBody, CardHeader } from "../ui/Card";

function toneFor(score: number): string {
  if (score >= 85) return "text-emerald-600";
  if (score >= 65) return "text-amber-600";
  return "text-red-600";
}

function barFor(score: number): string {
  if (score >= 85) return "bg-emerald-500";
  if (score >= 65) return "bg-amber-500";
  return "bg-red-500";
}

export function HealthCard({ health }: { health: HealthScoreOut | null }) {
  if (!health) {
    return (
      <Card>
        <CardHeader title="Manuscript health" description="Available after you apply a format." />
      </Card>
    );
  }

  const categories = Object.entries(health.categories);
  const topContributors = health.contributors.slice(0, 4);

  return (
    <Card>
      <CardHeader title="Manuscript health" />
      <CardBody className="flex flex-col gap-4">
        <div className="flex items-baseline gap-2">
          <span className={cn("text-4xl font-semibold tabular-nums", toneFor(health.total))}>
            {health.total}
          </span>
          <span className="text-sm text-zinc-500 dark:text-zinc-400">/ 100</span>
        </div>

        <div className="flex flex-col gap-2">
          {categories.map(([name, score]) => (
            <div key={name}>
              <div className="flex items-center justify-between text-xs text-zinc-600 dark:text-zinc-400">
                <span>{name}</span>
                <span className="tabular-nums text-zinc-500 dark:text-zinc-400">{score}</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-white/10">
                <div className={cn("h-full rounded-full", barFor(score))} style={{ width: `${score}%` }} />
              </div>
            </div>
          ))}
        </div>

        {topContributors.length > 0 ? (
          <div className="border-t border-zinc-100 dark:border-white/5 pt-3">
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Affecting the score
            </p>
            <ul className="flex flex-col gap-1 text-xs text-zinc-600 dark:text-zinc-400">
              {topContributors.map((c, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="tabular-nums text-red-500 dark:text-red-400">{c.delta}</span>
                  <span>{c.reason}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

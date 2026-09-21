import type { StatsOut } from "../../lib/types";
import { Card, CardBody } from "../ui/Card";

export function StatsPanel({
  stats,
  pageCount,
}: {
  stats: StatsOut;
  pageCount: number | null;
}) {
  const items: [string, string | number][] = [
    ["Words", stats.words.toLocaleString()],
    ["Pages", pageCount ?? "—"],
    ["Sections", stats.sections],
    ["References", stats.references],
    ["Figures", stats.figures],
    ["Tables", stats.tables],
  ];

  return (
    <Card>
      <CardBody>
        <dl className="grid grid-cols-3 gap-3 sm:grid-cols-6">
          {items.map(([label, value]) => (
            <div key={label} className="text-center">
              <dd className="text-lg font-semibold tabular-nums text-zinc-900 dark:text-zinc-50">{value}</dd>
              <dt className="text-[11px] uppercase tracking-wide text-zinc-500 dark:text-zinc-400">{label}</dt>
            </div>
          ))}
        </dl>
      </CardBody>
    </Card>
  );
}

import { FileText, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../lib/api";
import { shortDate, titleCase } from "../../lib/format";
import type { HistoryEntry } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/Feedback";

function healthTone(score: number): "success" | "warning" | "danger" {
  if (score >= 85) return "success";
  if (score >= 65) return "warning";
  return "danger";
}

export function RecentList({ limit = 8 }: { limit?: number }) {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);

  useEffect(() => {
    api
      .history(limit)
      .then(setEntries)
      .catch(() => setEntries([]));
  }, [limit]);

  async function remove(id: string) {
    setEntries((list) => (list ?? []).filter((e) => e.id !== id));
    try {
      await api.deleteHistory(id);
    } catch {
      /* best effort — the row is already gone from view */
    }
  }

  if (entries === null) {
    return <p className="text-xs text-zinc-500">Loading…</p>;
  }
  if (entries.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No manuscripts yet"
        description="Upload a .docx to run it through the pipeline."
        action={
          <Button size="sm" variant="secondary" onClick={() => navigate("/upload")}>
            Upload a manuscript
          </Button>
        }
      />
    );
  }

  return (
    <ul className="divide-y divide-zinc-100">
      {entries.map((entry) => (
        <li key={entry.id} className="flex items-center gap-3 py-2.5">
          <button
            type="button"
            onClick={() => navigate(`/workspace/${entry.id}`)}
            className="flex min-w-0 flex-1 items-center gap-3 rounded-md px-2 py-1 text-left hover:bg-zinc-50"
          >
            <FileText className="h-4 w-4 shrink-0 text-zinc-400" aria-hidden="true" />
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm text-zinc-800">{entry.filename}</span>
              <span className="text-[11px] text-zinc-400">{shortDate(entry.updated_at)}</span>
            </span>
            {entry.profile_id ? <Badge tone="neutral">{entry.profile_id.toUpperCase()}</Badge> : null}
            <Badge tone="muted">{titleCase(entry.state)}</Badge>
            {entry.health_total !== null ? (
              <Badge tone={healthTone(entry.health_total)}>{entry.health_total}</Badge>
            ) : null}
          </button>
          <button
            type="button"
            onClick={() => remove(entry.id)}
            aria-label={`Remove ${entry.filename} from history`}
            className="rounded p-1 text-zinc-400 hover:text-zinc-700"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </li>
      ))}
    </ul>
  );
}

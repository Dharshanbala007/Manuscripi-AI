import { cn } from "../../lib/cn";
import type { OutlineNode } from "../../lib/types";
import { EmptyState } from "../ui/Feedback";

export function OutlinePanel({
  nodes,
  onLocate,
}: {
  nodes: OutlineNode[];
  onLocate: (blockId: string) => void;
}) {
  return (
    <nav aria-label="Document outline" className="text-sm">
      <p className="px-2 pb-2 text-[11px] font-semibold uppercase tracking-wide text-zinc-400">
        Outline
      </p>
      {nodes.length === 0 ? (
        <EmptyState title="No headings detected" />
      ) : (
        <ul className="flex flex-col gap-0.5">
          {nodes.map((node) => (
            <OutlineItem key={node.id} node={node} onLocate={onLocate} />
          ))}
        </ul>
      )}
    </nav>
  );
}

function OutlineItem({
  node,
  onLocate,
}: {
  node: OutlineNode;
  onLocate: (blockId: string) => void;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={() => node.block_id && onLocate(node.block_id)}
        className={cn(
          "w-full truncate rounded-md px-2 py-1 text-left hover:bg-zinc-100",
          node.level === 1 ? "font-medium text-zinc-800" : "text-zinc-600",
        )}
        style={{ paddingLeft: `${(node.level - 1) * 12 + 8}px` }}
        title={node.label}
      >
        {node.label}
      </button>
      {node.children.length > 0 ? (
        <ul>
          {node.children.map((child) => (
            <OutlineItem key={child.id} node={child} onLocate={onLocate} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

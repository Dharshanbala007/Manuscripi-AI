import { cn } from "../../lib/cn";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
}

export function Tabs({
  items,
  active,
  onChange,
  size = "md",
}: {
  items: TabItem[];
  active: string;
  onChange: (id: string) => void;
  size?: "sm" | "md";
}) {
  return (
    <div role="tablist" className="flex items-center gap-1 rounded-lg bg-zinc-100 p-1">
      {items.map((item) => {
        const selected = item.id === active;
        return (
          <button
            key={item.id}
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(item.id)}
            className={cn(
              "rounded-md font-medium transition-colors",
              size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm",
              selected ? "bg-white text-zinc-900 shadow-sm" : "text-zinc-600 hover:text-zinc-800",
            )}
          >
            {item.label}
            {item.count !== undefined ? (
              <span className="ml-1.5 tabular-nums text-zinc-600">
                {item.count}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

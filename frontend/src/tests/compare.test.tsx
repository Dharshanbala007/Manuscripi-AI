import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ComparePanel } from "../components/workspace/ComparePanel";
import { StatsPanel } from "../components/workspace/StatsPanel";
import type { ComparisonOut, StatsOut } from "../lib/types";

const STATS: StatsOut = {
  words: 1651,
  paragraphs: 27,
  headings: 11,
  tables: 3,
  figures: 4,
  references: 46,
  sections: 11,
};

const COMPARISON: ComparisonOut = {
  original: {
    stats: STATS,
    metadata: { title: "A Title", authors: ["Ada"], abstract_present: true, keywords: ["x"] },
    sections: ["1 Introduction", "2 Methods"],
  },
  formatted: {
    stats: { ...STATS, paragraphs: 26 },
    metadata: { title: "A Title", authors: ["Ada"], abstract_present: true, keywords: ["x"] },
    sections: ["1 Introduction", "2 Methods"],
  },
  deltas: { paragraphs: -1, headings: 0, tables: 0, figures: 0, references: 0 },
  summary: {
    formatting_changes: 11,
    content_changes: 0,
    warnings_remaining: 1,
    preservation_passed: true,
  },
};

describe("<StatsPanel />", () => {
  it("shows the counts and a dash when there is no page count", () => {
    const { rerender } = render(<StatsPanel stats={STATS} pageCount={12} />);
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("46")).toBeInTheDocument(); // references

    rerender(<StatsPanel stats={STATS} pageCount={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

describe("<ComparePanel />", () => {
  it("calls onLoad once when ready with no comparison yet", () => {
    const onLoad = vi.fn();
    render(<ComparePanel comparison={null} loading={false} ready onLoad={onLoad} />);
    expect(onLoad).toHaveBeenCalledTimes(1);
  });

  it("renders the counts table with a green zero chip and an amber change chip", async () => {
    render(<ComparePanel comparison={COMPARISON} loading={false} ready onLoad={vi.fn()} />);

    await waitFor(() => expect(screen.getByText("References")).toBeInTheDocument());
    expect(screen.getByText("-1")).toBeInTheDocument(); // paragraphs delta
    expect(screen.getAllByText("0").length).toBeGreaterThan(0); // zero deltas
    expect(screen.getByText(/preservation/i).textContent).toMatch(/passed/i);
  });

  it("shows an empty state before formatting", () => {
    render(<ComparePanel comparison={null} loading={false} ready={false} onLoad={vi.fn()} />);
    expect(screen.getByText(/apply a format to compare/i)).toBeInTheDocument();
  });
});

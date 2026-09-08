import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StageList } from "../components/analyze/StageList";
import { api } from "../lib/api";
import type { AnalysisOut, StageOut } from "../lib/types";
import { AnalyzePage } from "../pages/AnalyzePage";

const EMPTY_STATS = {
  words: 100,
  paragraphs: 12,
  headings: 6,
  tables: 1,
  figures: 1,
  references: 6,
  sections: 6,
};

function analysis(partial: Partial<AnalysisOut>): AnalysisOut {
  return {
    state: "analyzing",
    stages: [],
    stats: null,
    metadata: null,
    parse_warnings: [],
    issues: [],
    error: null,
    profile_id: null,
    health: null,
    change_log: null,
    preservation: null,
    ...partial,
  };
}

function renderAt(path: string) {
  return render(
    <MemoryRouter
      initialEntries={[path]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/analyze/:id" element={<AnalyzePage />} />
        <Route path="/workspace/:id" element={<div>WORKSPACE READY</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("<StageList />", () => {
  it("renders each stage and its detail count", () => {
    const stages: StageOut[] = [
      { key: "read", label: "Reading document", status: "done", detail: "40 elements" },
      { key: "extract", label: "Extracting content", status: "active", detail: "" },
      { key: "metadata", label: "Detecting metadata", status: "pending", detail: "" },
    ];
    render(<StageList stages={stages} />);
    expect(screen.getByText("Reading document")).toBeInTheDocument();
    expect(screen.getByText("40 elements")).toBeInTheDocument();
    expect(screen.getByText(/Extracting content…/)).toBeInTheDocument(); // aria-live text
  });
});

describe("<AnalyzePage />", () => {
  it("navigates to the workspace once analysis completes", async () => {
    vi.spyOn(api, "analyze").mockResolvedValue({ id: "d1", state: "analyzing" });
    vi.spyOn(api, "getAnalysis").mockResolvedValue(
      analysis({
        state: "analyzed",
        stages: [{ key: "read", label: "Reading document", status: "done", detail: "40 elements" }],
        stats: EMPTY_STATS,
      }),
    );

    renderAt("/analyze/d1");
    expect(await screen.findByText("WORKSPACE READY")).toBeInTheDocument();
  });

  it("shows a retry action when analysis errors", async () => {
    vi.spyOn(api, "analyze").mockResolvedValue({ id: "d1", state: "analyzing" });
    vi.spyOn(api, "getAnalysis").mockResolvedValue(
      analysis({ state: "error", error: "Unable to read this document." }),
    );

    renderAt("/analyze/d1");
    expect(await screen.findByText(/Unable to read this document/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });
});

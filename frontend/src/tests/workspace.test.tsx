import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ElementsList } from "../components/workspace/ElementsList";
import { ExportBar } from "../components/workspace/ExportBar";
import { FormatPicker } from "../components/workspace/FormatPicker";
import { IssuesPanel } from "../components/workspace/IssuesPanel";
import { MetadataEditor } from "../components/workspace/MetadataEditor";
import { WhatChanged } from "../components/workspace/WhatChanged";
import { ToastProvider } from "../components/ui/Toast";
import { api } from "../lib/api";
import type { ElementOut, IssueOut, MetadataOut } from "../lib/types";

afterEach(() => vi.restoreAllMocks());

const META: MetadataOut = {
  title: { value: "Old Title", confidence: 0.4, edited_by_user: false, source_index: 0 },
  authors: {
    value: [{ name: "A. One", email: null, affiliation_ids: [] }],
    confidence: 0.8,
    edited_by_user: false,
  },
  affiliations: [],
  abstract: { value: "abstract text", confidence: 0.9, edited_by_user: false, source_index: 1 },
  keywords: { value: ["alpha", "beta"], confidence: 0.9, edited_by_user: false },
};

describe("<MetadataEditor />", () => {
  it("keeps Save disabled until something changes, then submits the edit", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<MetadataEditor metadata={META} onSave={onSave} />);

    const save = screen.getByRole("button", { name: /save changes/i });
    expect(save).toBeDisabled();

    fireEvent.change(screen.getByDisplayValue("Old Title"), { target: { value: "New Title" } });
    expect(save).toBeEnabled();
    fireEvent.click(save);

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ title: "New Title", keywords: ["alpha", "beta"] });
  });

  it("shows a low-confidence tag for an uncertain field", () => {
    render(<MetadataEditor metadata={META} onSave={vi.fn()} />);
    expect(screen.getByText(/40% confidence/i)).toBeInTheDocument();
  });
});

describe("<ElementsList />", () => {
  it("calls onReclassify with the new kind", async () => {
    const onReclassify = vi.fn().mockResolvedValue(undefined);
    const els: ElementOut[] = [
      {
        id: "b2",
        kind: "paragraph",
        confidence: 0.9,
        text_preview: "hello world",
        needs_review: false,
        level: null,
        number: null,
        section: null,
      },
    ];
    render(<ElementsList elements={els} onReclassify={onReclassify} />);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "heading" } });
    await waitFor(() => expect(onReclassify).toHaveBeenCalledWith("b2", { kind: "heading" }));
  });
});

describe("<IssuesPanel />", () => {
  const issues: IssueOut[] = [
    { id: "e1", severity: "error", category: "references", message: "bad cite", location: null, suggested_action: null },
    { id: "w1", severity: "warning", category: "layout", message: "wide table", location: "b5", suggested_action: "split it" },
    { id: "i1", severity: "info", category: "structure", message: "no keywords", location: null, suggested_action: null },
  ];

  it("filters by severity", () => {
    render(<IssuesPanel issues={issues} onLocate={vi.fn()} />);
    expect(screen.getByText("3 issues found")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /errors/i }));
    expect(screen.getByText("bad cite")).toBeInTheDocument();
    expect(screen.queryByText("wide table")).not.toBeInTheDocument();
  });

  it("Review calls onLocate with the issue location", () => {
    const onLocate = vi.fn();
    render(<IssuesPanel issues={issues} onLocate={onLocate} />);
    fireEvent.click(screen.getByRole("button", { name: /review/i }));
    expect(onLocate).toHaveBeenCalledWith("b5");
  });
});

describe("<ExportBar />", () => {
  it("disables PDF and shows a hint when the server has no PDF engine", () => {
    render(
      <ToastProvider>
        <ExportBar docId="d1" profileId="ieee" ready pdfExport={false} />
      </ToastProvider>,
    );
    expect(screen.getByRole("button", { name: /export pdf/i })).toBeDisabled();
    expect(screen.getByText(/unavailable on this machine/i)).toBeInTheDocument();
  });

  it("disables both exports until the document is formatted", () => {
    render(
      <ToastProvider>
        <ExportBar docId="d1" profileId={null} ready={false} pdfExport />
      </ToastProvider>,
    );
    expect(screen.getByRole("button", { name: /export docx/i })).toBeDisabled();
  });
});

describe("<FormatPicker />", () => {
  const profiles = [
    { id: "ieee", name: "IEEE", summary: "two column", features: ["a"], status: "available" as const },
    { id: "springer", name: "Springer", summary: "planned", features: [], status: "planned" as const },
  ];

  it("applies the selected profile and marks Springer as planned", async () => {
    vi.spyOn(api, "formats").mockResolvedValue(profiles);
    const onApply = vi.fn().mockResolvedValue(undefined);
    render(
      <FormatPicker open onClose={vi.fn()} currentProfile={null} onApply={onApply} />,
    );

    const springer = (await screen.findByText("Springer")).closest("button");
    expect(springer).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: /apply format/i }));
    await waitFor(() => expect(onApply).toHaveBeenCalledWith("ieee"));
  });
});

describe("<WhatChanged />", () => {
  it("reports preservation passed when there are no content changes", () => {
    render(
      <WhatChanged
        changeLog={{ formatting_changes: ["Applied IEEE layout"], content_changes: [], warnings_remaining: 1 }}
        preservation={{ passed: true, paragraph_delta: 0, text_match: true, details: [] }}
      />,
    );
    expect(screen.getByText(/preservation check passed/i)).toBeInTheDocument();
    expect(screen.getByText("Applied IEEE layout")).toBeInTheDocument();
  });

  it("reports Review required when content changed", () => {
    render(
      <WhatChanged
        changeLog={{ formatting_changes: [], content_changes: ["Body text differs"], warnings_remaining: 0 }}
        preservation={null}
      />,
    );
    expect(screen.getByText(/review required/i)).toBeInTheDocument();
    expect(screen.getByText("Body text differs")).toBeInTheDocument();
  });
});

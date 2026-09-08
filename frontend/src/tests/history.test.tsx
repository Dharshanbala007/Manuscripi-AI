import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RecentList } from "../components/dashboard/RecentList";
import { api } from "../lib/api";
import type { HistoryEntry } from "../lib/types";

afterEach(() => vi.restoreAllMocks());

function entry(partial: Partial<HistoryEntry>): HistoryEntry {
  return {
    id: "d1",
    filename: "paper.docx",
    size: 100,
    created_at: "2026-09-08T10:00:00+00:00",
    updated_at: "2026-09-08T10:05:00+00:00",
    state: "formatted",
    profile_id: "ieee",
    health_total: 92,
    preservation_passed: true,
    words: 100,
    paragraphs: 8,
    headings: 4,
    tables: 1,
    figures: 1,
    references: 6,
    sections: 4,
    session_active: true,
    ...partial,
  };
}

function renderList() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <RecentList />
    </MemoryRouter>,
  );
}

describe("<RecentList />", () => {
  it("renders history rows with filename and health", async () => {
    vi.spyOn(api, "history").mockResolvedValue([
      entry({ id: "a", filename: "one.docx", health_total: 90 }),
      entry({ id: "b", filename: "two.docx", health_total: 60 }),
    ]);
    renderList();

    expect(await screen.findByText("one.docx")).toBeInTheDocument();
    expect(screen.getByText("two.docx")).toBeInTheDocument();
    expect(screen.getByText("90")).toBeInTheDocument();
  });

  it("removes a row and calls deleteHistory when the × is clicked", async () => {
    vi.spyOn(api, "history").mockResolvedValue([entry({ id: "a", filename: "one.docx" })]);
    const del = vi.spyOn(api, "deleteHistory").mockResolvedValue(undefined);
    renderList();

    fireEvent.click(await screen.findByRole("button", { name: /remove one.docx/i }));
    await waitFor(() => expect(del).toHaveBeenCalledWith("a"));
    expect(screen.queryByText("one.docx")).not.toBeInTheDocument();
  });

  it("shows the empty state when there is no history", async () => {
    vi.spyOn(api, "history").mockResolvedValue([]);
    renderList();
    expect(await screen.findByText(/no manuscripts yet/i)).toBeInTheDocument();
  });
});

import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { canTransition, useDocumentFlow } from "../state/useDocumentFlow";

describe("useDocumentFlow", () => {
  beforeEach(() => localStorage.clear());

  it("starts IDLE and walks the happy path to EXPORTED", () => {
    const { result } = renderHook(() => useDocumentFlow());
    expect(result.current.state).toBe("IDLE");

    const path = [
      "UPLOADING",
      "UPLOADED",
      "ANALYZING",
      "ANALYZED",
      "FORMATTING",
      "FORMATTED",
      "VALIDATING",
      "VALIDATED",
      "EXPORTING",
      "EXPORTED",
    ] as const;

    for (const step of path) {
      act(() => result.current.goto(step));
      expect(result.current.state).toBe(step);
    }
  });

  it("ignores an illegal transition", () => {
    const { result } = renderHook(() => useDocumentFlow());
    act(() => result.current.goto("EXPORTED"));
    expect(result.current.state).toBe("IDLE");
  });

  it("can reach ERROR from any state and carries a message", () => {
    const { result } = renderHook(() => useDocumentFlow());
    act(() => result.current.goto("UPLOADING"));
    act(() => result.current.goto("ERROR", { error: "boom" }));
    expect(result.current.state).toBe("ERROR");
    expect(result.current.error).toBe("boom");
  });

  it("persists the snapshot to localStorage and restores it", () => {
    const first = renderHook(() => useDocumentFlow());
    act(() => first.result.current.goto("UPLOADING"));
    act(() => first.result.current.goto("UPLOADED", { documentId: "doc-42" }));

    const second = renderHook(() => useDocumentFlow());
    expect(second.result.current.state).toBe("UPLOADED");
    expect(second.result.current.documentId).toBe("doc-42");
  });

  it("reset returns to IDLE and clears the document id", () => {
    const { result } = renderHook(() => useDocumentFlow());
    act(() => result.current.goto("UPLOADING"));
    act(() => result.current.goto("UPLOADED", { documentId: "d1" }));
    act(() => result.current.reset());
    expect(result.current.state).toBe("IDLE");
    expect(result.current.documentId).toBeNull();
  });

  it("canTransition reflects the transition table", () => {
    expect(canTransition("IDLE", "UPLOADING")).toBe(true);
    expect(canTransition("IDLE", "EXPORTED")).toBe(false);
  });
});

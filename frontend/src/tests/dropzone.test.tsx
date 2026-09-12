import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Dropzone, validateManuscriptFile } from "../components/upload/Dropzone";

function makeFile(name: string, sizeBytes = 200, type = ""): File {
  const file = new File([new Uint8Array(1)], name, { type });
  Object.defineProperty(file, "size", { value: sizeBytes });
  return file;
}

describe("validateManuscriptFile", () => {
  it("accepts a .docx within the size limit", () => {
    expect(validateManuscriptFile(makeFile("a.docx", 1000), 25)).toEqual({ ok: true });
  });
  it("rejects a non-docx", () => {
    expect(validateManuscriptFile(makeFile("a.txt", 1000), 25).ok).toBe(false);
  });
  it("rejects an oversize file", () => {
    expect(validateManuscriptFile(makeFile("a.docx", 30 * 1024 * 1024), 25).ok).toBe(false);
  });
  it("rejects an empty file", () => {
    expect(validateManuscriptFile(makeFile("a.docx", 0), 25).ok).toBe(false);
  });
});

describe("<Dropzone />", () => {
  it("rejects a non-docx with an alert and does not call onAccept", () => {
    const onAccept = vi.fn();
    render(<Dropzone onAccept={onAccept} maxMb={25} />);
    fireEvent.change(screen.getByTestId("dropzone-input"), {
      target: { files: [makeFile("notes.txt", 100, "text/plain")] },
    });
    expect(onAccept).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/\.docx/i);
  });

  it("accepts a .docx file", () => {
    const onAccept = vi.fn();
    render(<Dropzone onAccept={onAccept} maxMb={25} />);
    fireEvent.change(screen.getByTestId("dropzone-input"), {
      target: { files: [makeFile("paper.docx", 4096)] },
    });
    expect(onAccept).toHaveBeenCalledTimes(1);
  });

  it("rejects an oversize file with a helpful message", () => {
    const onAccept = vi.fn();
    render(<Dropzone onAccept={onAccept} maxMb={1} />);
    fireEvent.change(screen.getByTestId("dropzone-input"), {
      target: { files: [makeFile("big.docx", 2 * 1024 * 1024)] },
    });
    expect(onAccept).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/larger than/i);
  });

  it("associates the visible label with the file input for accessible activation", () => {
    render(<Dropzone onAccept={vi.fn()} maxMb={25} />);
    const input = screen.getByTestId("dropzone-input") as HTMLInputElement;
    const label = screen.getByTestId("dropzone");
    // Native <label for>/<input id> association is what makes clicking anywhere
    // in the label, or pressing Enter/Space while the input is focused, open
    // the file picker in a real browser — no custom keyboard handler needed.
    expect(label.getAttribute("for")).toBe(input.id);
  });
});

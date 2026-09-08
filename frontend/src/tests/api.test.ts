import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "../lib/api";

const okJson = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

describe("api client", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => vi.unstubAllGlobals());

  it("builds URLs from VITE_API_BASE and returns parsed JSON", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      okJson({ status: "ok", version: "0.1.0", capabilities: { pdf_export: true } }),
    );
    const health = await api.health();
    expect(health.capabilities.pdf_export).toBe(true);

    const [url] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/health");
  });

  it("sends multipart for upload", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      okJson({ id: "d1", filename: "p.docx", size: 10, state: "uploaded", created_at: "" }, 201),
    );
    const file = new File([new Uint8Array([1, 2, 3])], "p.docx");
    const out = await api.upload(file);
    expect(out.id).toBe("d1");

    const [, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);
  });

  it("normalizes an error envelope into ApiError", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      okJson({ error: "not_found", message: "Document not found.", hint: "Check the id." }, 404),
    );
    await expect(api.getDocument("nope")).rejects.toMatchObject({
      status: 404,
      code: "not_found",
      message: "Document not found.",
      hint: "Check the id.",
    });
  });

  it("wraps a network failure as ApiError code network_error", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new TypeError("failed to fetch"));
    await expect(api.health()).rejects.toBeInstanceOf(ApiError);
    await expect(api.health()).rejects.toMatchObject({ name: "ApiError", code: "network_error" });
  });

  it("returns undefined for 204 responses", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(new Response(null, { status: 204 }));
    await expect(api.deleteDocument("d1")).resolves.toBeUndefined();
  });

  it("exposes file URLs for preview and exports", () => {
    expect(api.previewUrl("d1")).toBe("http://localhost:8000/api/documents/d1/preview");
    expect(api.exportPdfUrl("d1")).toBe("http://localhost:8000/api/documents/d1/export/pdf");
  });

  it("builds history and comparison URLs", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(okJson([]));
    await api.history(8);
    expect((fetch as ReturnType<typeof vi.fn>).mock.calls[0][0]).toBe(
      "http://localhost:8000/api/history?limit=8",
    );

    (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(new Response(null, { status: 204 }));
    await api.deleteHistory("d1");
    const del = (fetch as ReturnType<typeof vi.fn>).mock.calls.at(-1);
    expect(del?.[0]).toBe("http://localhost:8000/api/history/d1");
    expect(del?.[1].method).toBe("DELETE");

    (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(okJson({}));
    await api.getComparison("d1").catch(() => undefined);
    expect((fetch as ReturnType<typeof vi.fn>).mock.calls.at(-1)?.[0]).toBe(
      "http://localhost:8000/api/documents/d1/comparison",
    );
  });
});

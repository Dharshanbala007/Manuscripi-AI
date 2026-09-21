import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const CLIENT_ID = /^[A-Za-z0-9_-]{16,64}$/; // what the backend's get_owner() accepts

// HOSTED is read once at import, so each case stubs the env and re-imports the modules.
async function load(hosted: boolean) {
  vi.resetModules();
  vi.stubEnv("VITE_HOSTED", hosted ? "true" : "false");
  const { api } = await import("../lib/api");
  const deployment = await import("../lib/deployment");
  return { api, ...deployment };
}

const sentHeaders = () =>
  ((fetch as ReturnType<typeof vi.fn>).mock.calls.at(-1)?.[1]?.headers ?? {}) as Record<string, string>;

describe("deployment mode", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => new Response("[]", { status: 200 })));
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("local build sends no client id and keeps the local privacy copy", async () => {
    const { api, HOSTED, COPY } = await load(false);
    await api.history();

    expect(HOSTED).toBe(false);
    expect(sentHeaders()["x-client-id"]).toBeUndefined();
    expect(COPY.privacyBadge).toMatch(/never leaves this machine/);
  });

  it("hosted build sends a stable, backend-valid client id on every request", async () => {
    const { api } = await load(true);
    await api.history();
    const first = sentHeaders()["x-client-id"];
    await api.deleteHistory("d1");

    expect(first).toMatch(CLIENT_ID);
    expect(sentHeaders()["x-client-id"]).toBe(first);
    expect(localStorage.getItem("manuscript-client-id")).toBe(first);
  });

  it("hosted build keeps the request's own headers and leaves multipart alone", async () => {
    const { api } = await load(true);
    await api.format("d1", "ieee");
    expect(sentHeaders()["content-type"]).toBe("application/json");

    await api.upload(new File([new Uint8Array([1])], "p.docx"));
    expect(sentHeaders()["content-type"]).toBeUndefined(); // the browser sets the multipart boundary
    expect(sentHeaders()["x-client-id"]).toMatch(CLIENT_ID);
  });

  it("hosted copy never claims the manuscript stays on this machine", async () => {
    const { COPY } = await load(true);
    for (const text of Object.values(COPY)) expect(text).not.toMatch(/this machine|locally|offline/i);
  });

  it("falls back to a per-page id when storage is blocked", async () => {
    const { clientId } = await load(true);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(clientId()).toMatch(CLIENT_ID);
    expect(clientId()).toBe(clientId());
  });
});

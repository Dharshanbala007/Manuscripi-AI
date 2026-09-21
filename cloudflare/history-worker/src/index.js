// Tiny authenticated JSON API in front of the D1 `history` table.
// The Python backend (hosted on Render, which has no durable disk) calls this instead of
// touching SQLite. Rows are log-only: filename, state, scores and counts. No manuscript text.

const COLUMNS = [
  "id",
  "filename",
  "size",
  "created_at",
  "updated_at",
  "state",
  "profile_id",
  "health_total",
  "preservation_passed",
  "words",
  "paragraphs",
  "headings",
  "tables",
  "figures",
  "references",
  "sections",
  "owner",
];
const COUNTS = ["size", "words", "paragraphs", "headings", "tables", "figures", "references", "sections"];

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json" } });

// Constant-time comparison so response timing doesn't leak the token.
function authorized(request, env) {
  const expected = `Bearer ${env.HISTORY_TOKEN ?? ""}`;
  const given = request.headers.get("authorization") ?? "";
  if (!env.HISTORY_TOKEN || given.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= given.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

const str = (v, max) => (typeof v === "string" && v.length <= max ? v : null);
const int = (v) => (Number.isInteger(v) && v >= 0 ? v : null);

// Validate a request body into a row of bound values, or return null if it is malformed.
function toRow(body, id) {
  const row = {
    id,
    filename: str(body.filename, 255),
    created_at: str(body.created_at, 64),
    updated_at: str(body.updated_at, 64),
    state: str(body.state, 32),
    profile_id: body.profile_id == null ? null : str(body.profile_id, 32),
    health_total: body.health_total == null ? null : int(body.health_total),
    preservation_passed:
      body.preservation_passed == null ? null : body.preservation_passed ? 1 : 0,
    owner: str(body.owner ?? "", 64),
  };
  for (const name of COUNTS) row[name] = int(body[name] ?? 0);
  const required = ["filename", "created_at", "updated_at", "state", "owner", ...COUNTS];
  const bad = required.some((k) => row[k] === null);
  const badOptional =
    (body.profile_id != null && row.profile_id === null) ||
    (body.health_total != null && row.health_total === null);
  return bad || badOptional ? null : row;
}

const fromRow = (row) => ({
  ...row,
  preservation_passed: row.preservation_passed == null ? null : row.preservation_passed === 1,
});

const quoted = (c) => `"${c}"`;
const UPSERT = `INSERT INTO history (${COLUMNS.map(quoted).join(", ")})
  VALUES (${COLUMNS.map(() => "?").join(", ")})
  ON CONFLICT(id) DO UPDATE SET ${COLUMNS.filter((c) => c !== "id")
    .map((c) => `${quoted(c)}=excluded.${quoted(c)}`)
    .join(", ")}`;

export default {
  async fetch(request, env) {
    if (!authorized(request, env)) return json({ error: "unauthorized" }, 401);

    const url = new URL(request.url);
    const [root, rawId, ...rest] = url.pathname.split("/").filter(Boolean);
    if (root !== "entries" || rest.length) return json({ error: "not_found" }, 404);
    const id = rawId === undefined ? undefined : decodeURIComponent(rawId);
    const owner = url.searchParams.get("owner"); // null = not scoped

    try {
      if (request.method === "PUT" && id) {
        if (id.length > 64) return json({ error: "invalid_id" }, 400);
        const body = await request.json().catch(() => null);
        const row = body && typeof body === "object" ? toRow(body, id) : null;
        if (!row) return json({ error: "invalid_entry" }, 400);
        await env.DB.prepare(UPSERT)
          .bind(...COLUMNS.map((c) => row[c]))
          .run();
        return json({ ok: true });
      }

      if (request.method === "GET" && id) {
        const row = await env.DB.prepare("SELECT * FROM history WHERE id = ?").bind(id).first();
        return row ? json(fromRow(row)) : json({ error: "not_found" }, 404);
      }

      if (request.method === "GET") {
        const limit = Math.min(Math.max(parseInt(url.searchParams.get("limit") ?? "20", 10) || 20, 1), 100);
        const query =
          owner === null
            ? env.DB.prepare(
                "SELECT * FROM history ORDER BY updated_at DESC, created_at DESC LIMIT ?",
              ).bind(limit)
            : env.DB.prepare(
                "SELECT * FROM history WHERE owner = ? ORDER BY updated_at DESC, created_at DESC LIMIT ?",
              ).bind(owner, limit);
        const { results } = await query.all();
        return json(results.map(fromRow));
      }

      if (request.method === "DELETE" && id) {
        const query =
          owner === null
            ? env.DB.prepare("DELETE FROM history WHERE id = ?").bind(id)
            : env.DB.prepare("DELETE FROM history WHERE id = ? AND owner = ?").bind(id, owner);
        await query.run();
        return json({ ok: true });
      }

      return json({ error: "method_not_allowed" }, 405);
    } catch (err) {
      console.error("history_worker_error", err && err.message);
      return json({ error: "internal_error" }, 500);
    }
  },
};

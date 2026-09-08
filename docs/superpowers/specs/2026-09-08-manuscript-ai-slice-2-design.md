# ManuScript AI — Slice 2 Design

**Date:** 2026-09-08
**Status:** Approved
**Builds on:** Slice 1 (merged to `master`). Additive — no rewrite of the Slice 1 pipeline.

## 0. Scope

Springer profile · SQLite document history · dashboard "recent" list · before/after
comparison · document statistics surface. The "what changed" deep view is folded into the
comparison tab rather than built as a third view of the same data.

## 1. Confirmed decisions

- **History-log-only SQLite.** A new `HistoryStore` records lightweight summary rows — no
  manuscript content or model — satisfying spec §30. The in-memory `DocumentStore` is
  unchanged and still owns the ephemeral `Manuscript` + working paths. A backend restart
  keeps the history list; a document whose working session has ended is re-uploaded.
- **Comparison as a workspace tab** (`Compare`), backed by
  `GET /api/documents/{id}/comparison`.
- **One hedged Springer profile** shipped now as `springer.yaml`, every rule tagged
  `inferred`/`configurable`, structured so template variants become additional YAML later.

---

## 2. SQLite history

### `app/storage/history.py`

- `HistoryEntry` dataclass: `id, filename, size, created_at, updated_at, state,
  profile_id, health_total, preservation_passed, words, paragraphs, headings, tables,
  figures, references, sections`. `HistoryEntry.from_record(record)` derives it from a
  `DocumentRecord`.
- `HistoryStore` ABC: `upsert(entry)`, `get(id) -> HistoryEntry | None`,
  `list(limit=20) -> list[HistoryEntry]` (newest `updated_at` first), `delete(id)`.
- `InMemoryHistoryStore` — for tests.
- `SqliteHistoryStore(db_path)` — stdlib `sqlite3`, WAL mode, one `history` table,
  connection-per-call. `ponytail:` comment — pool only if history writes ever show up in
  profiling. `CREATE TABLE IF NOT EXISTS` on construction.

### Config (`config.py`)

- `history_db: Path = Path("./.workspace/history.db")`
- `history_enabled: bool = True`

When `history_enabled` is false, `get_history` returns an `InMemoryHistoryStore` (writes
are harmless no-ops from the caller's view; nothing is persisted).

### Write points

`history.upsert(HistoryEntry.from_record(record))` is called after each lifecycle
transition — one line each:

| Location | After |
|---|---|
| `ingestion/receive.py` | record created (`uploaded`) |
| `analysis/pipeline.py` | analysis finishes (`analyzed` or `error`) |
| `formatting/run.py` | `run_format` (`formatted`), `run_validate` (`validated`) |
| `api/routes_documents.py` | export handlers (`exported`) |

### Endpoints

- `GET /api/history?limit=20` → `list[HistoryEntryOut]`. `HistoryEntryOut` adds
  `session_active: bool` = `doc_id in DocumentStore`.
- `DELETE /api/history/{id}` → 204. Explicit purge of a history row.
- `DELETE /api/documents/{id}` (existing) removes the live session and workspace but
  **leaves** the history row.

---

## 3. Springer profile

### `app/profiles/data/springer.yaml`

Full `PublisherProfile`. Single-column A4. Representative values, all `inferred` or
`configurable`, with a group note that this is one generic profile, not a journal template:

- `page`: A4, ~2.5 cm margins.
- `columns`: 1.
- `base_font`: Times New Roman ~10 pt (`inferred` — real Springer templates use a bespoke
  serif).
- `title`: centered, ~15 pt bold.
- `author` / `affiliation`: centered; affiliation italic ~9 pt.
- `abstract`: `heading_text: "Abstract"`, `inline_lead_in: false`, ~9 pt, justified.
- `keywords`: label `"Keywords"`, not italic run-in.
- `headings`: levels 1–3, decimal numbering (`1`, `1.1`, `1.1.1`), bold, left, no case
  change. (Numbering prefixes are still not injected by the engine — see Slice 1
  limitations — the note records this.)
- `paragraphs`: first-line indent, justified.
- `captions`: `Fig.` below figure, `Table` above table, both decimal, ~9 pt.
- `tables`: `Table Grid`, bold header.
- `figures`: centered, single-page width ~5.5 in (A4 single column is wider than IEEE's
  column).
- `references`: `numeric-bracket` (`configurable` — name-year is the common Springer
  alternative; not implemented).
- `validation`: same thresholds shape as IEEE.

### Loader / docs

- Remove `"springer"` from `PLANNED_PROFILES` in `loader.py`. `list_profiles` picks the
  YAML up automatically; `run.ProfileUnavailable` no longer fires for it.
- `scripts/gen_rules_doc.py` renders **every** profile YAML into `docs/RULES.md` (one
  section per profile).

### Engine

Already profile-driven. `apply_page_layout` writes `w:cols w:num="1"` for Springer.
`rebuild_frontmatter` uses the abstract-heading path when `inline_lead_in` is false
(already implemented in Slice 1). No engine code changes expected; integration tests
confirm preservation holds and the output is single-column.

---

## 4. Before/after comparison

### `GET /api/documents/{id}/comparison` (409 unless `formatted`/`validated`/`exported`)

```jsonc
{
  "original":  { "stats": StatsOut, "metadata": MetaSummary, "sections": ["1 Introduction", ...] },
  "formatted": { "stats": StatsOut, "metadata": MetaSummary, "sections": [...] },
  "deltas":    { "paragraphs": 0, "headings": 0, "tables": 0, "figures": 0, "references": 0 },
  "summary":   { "formatting_changes": 11, "content_changes": 0, "warnings_remaining": 1,
                 "preservation_passed": true }
}
```

`MetaSummary`: `{ title: str, authors: [str], abstract_present: bool, keywords: [str] }`.

### `app/analysis/comparison.py`

`build_comparison(record) -> Comparison`:

1. `original` = summaries from `record.manuscript` (already in memory).
2. `formatted` = re-parse `record.artifacts["formatted"]`, run `classify_blocks`, compute
   `DocumentStats` + `MetaSummary` + heading section list.
3. `deltas` = `formatted.stats − original.stats` per field.
4. `summary` = counts from `record.change_log` + `record.preservation.passed`.

Reuses `_compute_stats` (extract from `analysis/pipeline.py` into
`analysis/stats.py` so both call it) and the parse/classify chain used by
`check_preservation`.

### Frontend `components/workspace/ComparePanel.tsx`

Two-column layout (Original | Formatted): a counts table with a delta column
(0 → green chip, non-zero → amber chip + signed number), metadata side-by-side
(title, authors, abstract present, keywords), and the section list. Summary strip:
`Formatting changes: N · Content changes: M · Warnings remaining: W · Preservation: passed/review`.

`useWorkspace` gains `comparison: ComparisonOut | null` + `loadComparison()`, called when
the Compare tab is first opened. New `Tabs` item `{ id: "compare", label: "Compare" }` in
`WorkspacePage`.

---

## 5. Dashboard recents + document statistics

### Dashboard

Replace the empty "Recent manuscripts" card with a list from `GET /api/history?limit=8`:
each row shows filename · relative date (`shortDate`) · profile badge · state badge ·
health chip (tone by score). Row click → `/workspace/:id`. A trailing "×" calls
`DELETE /api/history/{id}` and removes the row. Empty history keeps the current
empty-state copy.

`WorkspacePage` load-failure `ErrorState` copy becomes: *"This working session has ended.
Upload the document again to continue."* (with a "Back to dashboard" action) when the
document GET 404s.

### Document statistics — `components/workspace/StatsPanel.tsx`

A compact card at the top of the Review tab: **Words · Pages · Sections · References ·
Figures · Tables** as labelled numbers. `Pages` = PDF page count.

- Backend: `DocumentRecord.page_count: int | None`. Set it whenever a PDF is generated
  (`export_pdf` / preview path in `routes_documents.py`) from the `pypdf` page count that
  `export_pdf` already computes — return it from `export_pdf` and stash on the record.
- `AnalysisOut` gains `page_count: int | None`.
- Frontend shows `page_count ?? "—"`.

---

## 6. Wiring & docs

- `main.py` lifespan: build `app.state.history` (`SqliteHistoryStore` or
  `InMemoryHistoryStore` per `history_enabled`), ensure the DB/table exist.
- `api/deps.py`: `get_history(request) -> HistoryStore`.
- `.env.example` (both), `README.md` (features, formats table → Springer *available*,
  history note), `docs/ARCHITECTURE.md` (HistoryStore + comparison), `docs/RULES.md`
  (regenerated with both profiles).
- `.gitignore` already ignores `.workspace/` so `history.db` is not committed.

---

## 7. Testing

**Backend**

- `tests/unit/test_history.py` — `SqliteHistoryStore` upsert/get/list(order)/delete against
  a tmp DB; `InMemoryHistoryStore` parity via a shared parametrized test.
- `tests/api/test_history_api.py` — upload → analyze → format, then `GET /history` shows one
  row with `state == "formatted"`, `profile_id`, `health_total`, `session_active == true`;
  `DELETE /history/{id}` → 204 then absent; `DELETE /documents/{id}` keeps the history row.
- `tests/integration/test_comparison.py` + `tests/api/test_comparison_api.py` — comparison
  on a formatted sample: `original.stats` and `formatted.stats` populated, `deltas` all
  within tolerance (0 for tables/figures/references), `summary.preservation_passed` true;
  409 before formatting.
- `tests/unit/test_profiles.py` — `load_profile("springer")`: `columns.count == 1`,
  A4 page size, every rule group provenance valid; `list_profiles` marks springer
  `available`, no `planned` entry remains; `render_rules_md` covers both profiles and
  `docs/RULES.md` mentions every group of both.
- `tests/integration/test_springer_format.py` — format `sample_basic` with `springer`:
  preservation passes, output section has `w:cols w:num="1"`, body text hash preserved.
- Existing `test_format_validate.py` — drop the "springer → 422" case, add "springer →
  200 formatted".

**Frontend**

- `src/tests/history.test.tsx` — dashboard recents render from a mocked `api.history()`;
  clicking "×" calls `api.deleteHistory`; empty → empty state.
- `src/tests/compare.test.tsx` — `ComparePanel` renders the counts table, shows a green
  chip for a 0 delta and an amber chip for a non-zero delta, and the summary strip.
- Update `src/tests/workspace.test.tsx` for the new `Compare` tab and `StatsPanel`.
- `src/tests/api.test.ts` — new client methods (`history`, `deleteHistory`,
  `getComparison`) build the right URLs.

**Done bar**: `scripts/check.sh` green + a browser walkthrough — format a sample with
Springer, open the Compare tab, see a recents row on the dashboard, delete a history row.

---

## 8. Out of scope for Slice 2

Full session persistence across restarts · Springer template variants + a variant selector
· multi-user history · the Slice 3 Playwright suite and dedicated UI-polish pass.

---

## 9. Acceptance

- A document processed with **Springer** formats, preserves content, and exports; the
  format picker offers IEEE and Springer, both `available`.
- `history.db` accumulates one row per document across its lifecycle; `GET /history`
  drives a working dashboard recents list; rows can be deleted; the DB is separate from
  any manuscript content.
- The Compare tab shows real original-vs-formatted structural and metadata differences,
  with deltas and the preservation verdict, all derived from actual re-parsing.
- The workspace shows real Words/Pages/Sections/References/Figures/Tables.
- `pytest` and `vitest` green; browser walkthrough completed; no fake data anywhere.

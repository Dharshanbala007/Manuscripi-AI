# ManuScript AI — Slice 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, autonomous per slice). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add SQLite document history, a Springer publisher profile, a before/after comparison view, dashboard recents, and a document-statistics surface — additively, on the merged Slice 1 codebase.

**Architecture:** A new `HistoryStore` (ABC + SQLite + in-memory) records log-only summary rows at each lifecycle transition; the in-memory `DocumentStore` is unchanged. Springer ships as another profile YAML (the engine is already profile-driven). Comparison re-parses the formatted DOCX and diffs it against the in-memory `Manuscript`. Frontend gains a Compare tab, a stats panel, and a real recents list.

**Tech Stack:** Existing — Python 3.12 / FastAPI / python-docx / pypdf / stdlib `sqlite3`; React 18 / TS / Vite / Tailwind / vitest.

**Spec:** `docs/superpowers/specs/2026-09-08-manuscript-ai-slice-2-design.md`

## Global Constraints

- Local-only. History stores **summary rows, no manuscript content or model** (spec §30).
- No fake data. Recents, comparison, and stats all derive from real backend state.
- Springer profile: every rule group `provenance: inferred | configurable`, with a note that it is one generic profile, not a journal template. Never claim "Springer compliant".
- Backend commands via `backend/.venv/Scripts/python.exe`. `bash scripts/check.sh` is the gate (ruff + ruff-format + pytest + tsc + vitest).
- TDD: failing test → minimal impl → green → commit. Trailer: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

---

## File Structure

### Backend

| Path | Change | Responsibility |
|---|---|---|
| `app/storage/history.py` | Create | `HistoryEntry`, `HistoryStore` ABC, `InMemoryHistoryStore`, `SqliteHistoryStore`. |
| `app/config.py` | Modify | `history_db: Path`, `history_enabled: bool`. |
| `app/main.py` | Modify | Build `app.state.history` in lifespan. |
| `app/api/deps.py` | Modify | `get_history(request)`. |
| `app/analysis/stats.py` | Create | `compute_stats(blocks) -> DocumentStats` (extracted from `pipeline.py`). |
| `app/analysis/pipeline.py` | Modify | Use `stats.compute_stats`; `history.upsert` after analysis. |
| `app/analysis/comparison.py` | Create | `build_comparison(record) -> Comparison`; `MetaSummary`, `Comparison` dataclasses. |
| `app/ingestion/receive.py` | Modify | `history.upsert` after record created. |
| `app/formatting/run.py` | Modify | `history.upsert` after `run_format` and `run_validate`. |
| `app/export/pdf_export.py` | Modify | `export_pdf` returns `PdfResult(path, page_count)`. |
| `app/storage/base.py` | Modify | `DocumentRecord.page_count: int | None`. |
| `app/api/routes_documents.py` | Modify | `history.upsert` after export; set `record.page_count`; `GET /history`, `DELETE /history/{id}`, `GET /documents/{id}/comparison`. |
| `app/api/routes_history.py` | Create | history endpoints (thin). |
| `app/profiles/data/springer.yaml` | Create | The Springer profile. |
| `app/profiles/loader.py` | Modify | Drop `"springer"` from `PLANNED_PROFILES`. |
| `app/profiles/rules_doc.py` | Modify | `render_all_rules_md(profiles)` — one section per profile. |
| `app/schemas/history.py` | Create | `HistoryEntryOut`. |
| `app/schemas/comparison.py` | Create | `ComparisonOut`, `SideOut`, `MetaSummaryOut`, `DeltasOut`, `CompareSummaryOut`. |
| `app/schemas/analysis.py` | Modify | `AnalysisOut.page_count`. |
| `scripts/gen_rules_doc.py` | Modify | Render all profiles. |
| `backend/tests/unit/test_history.py` `test_profiles.py` | Create / modify | |
| `backend/tests/api/test_history_api.py` `test_comparison_api.py` | Create | |
| `backend/tests/integration/test_comparison.py` `test_springer_format.py` | Create | |
| `backend/tests/api/test_format_validate.py` | Modify | springer 422 → 200. |

### Frontend

| Path | Change | Responsibility |
|---|---|---|
| `src/lib/types.ts` | Modify | `HistoryEntry`, `ComparisonOut` + sub-types, `AnalysisOut.page_count`. |
| `src/lib/api.ts` | Modify | `history(limit?)`, `deleteHistory(id)`, `getComparison(id)`. |
| `src/components/workspace/ComparePanel.tsx` | Create | Original vs Formatted, deltas, summary strip. |
| `src/components/workspace/StatsPanel.tsx` | Create | Words / Pages / Sections / References / Figures / Tables. |
| `src/components/dashboard/RecentList.tsx` | Create | Recents rows from `api.history()`. |
| `src/workspace/useWorkspace.ts` | Modify | `comparison`, `loadComparison()`; expose `pageCount`. |
| `src/pages/WorkspacePage.tsx` | Modify | `Compare` tab; `StatsPanel` in Review; ended-session error copy. |
| `src/pages/DashboardPage.tsx` | Modify | Use `RecentList`. |
| `src/tests/history.test.tsx` `compare.test.tsx` | Create | |
| `src/tests/workspace.test.tsx` `api.test.ts` | Modify | |

### Docs

`.env.example` (both) · `README.md` · `docs/ARCHITECTURE.md` · `docs/RULES.md` (regenerated).

---

## Tasks

### Task 1 — HistoryStore (data + in-memory + SQLite)
**Files:** `app/storage/history.py`, `app/config.py`, `backend/tests/unit/test_history.py`.
**Interfaces produced:** `HistoryEntry` (fields per spec §2); `HistoryEntry.from_record(record) -> HistoryEntry`; `HistoryStore` ABC `{upsert(entry), get(id)->entry|None, list(limit=20)->list[entry], delete(id)}`; `InMemoryHistoryStore`; `SqliteHistoryStore(db_path: Path)` (WAL, `CREATE TABLE IF NOT EXISTS` on init, connection-per-call). `Settings.history_db`, `Settings.history_enabled`.
- [ ] Test (parametrized over both stores): `upsert` then `get` round-trips; second `upsert` same id updates in place (list length stays 1); `list` returns newest `updated_at` first and respects `limit`; `delete` removes; `get` unknown → None. Sqlite store: point at `tmp_path/h.db`, new instance sees persisted rows.
- [ ] Impl: dataclass; ABC; dict-backed in-memory; sqlite with a `_conn()` helper (`sqlite3.connect(path); PRAGMA journal_mode=WAL`), `INSERT ... ON CONFLICT(id) DO UPDATE`. `ponytail:` note on connection-per-call.
- [ ] Green; commit `feat(backend): SQLite + in-memory HistoryStore`.

### Task 2 — Wire history into the app + lifecycle writes
**Files:** `app/main.py`, `app/api/deps.py`, `app/ingestion/receive.py`, `app/analysis/pipeline.py`, `app/formatting/run.py`; `backend/tests/api/test_history_api.py` (partial — write points).
**Interfaces produced:** `app.state.history` (`SqliteHistoryStore` if `history_enabled` else `InMemoryHistoryStore`); `deps.get_history(request) -> HistoryStore`. `run_analysis` / `receive_upload` / `run_format` / `run_validate` accept a `history` arg (or read from a passed store) and `upsert` after their transition.
- [ ] Test: after `receive_upload`, history has a row `state=="uploaded"`; after `run_analysis`, `state=="analyzed"` + stats populated. (Use `InMemoryHistoryStore` directly.)
- [ ] Impl: thread `history` through the call sites. `run_analysis(doc_id, store, history, threshold)` — update `routes_documents.analyze` to pass `app.state.history`. Same for format/validate/upload.
- [ ] Green; commit `feat(backend): record document history at each lifecycle transition`.

### Task 3 — History endpoints + delete semantics
**Files:** `app/schemas/history.py`, `app/api/routes_history.py`, wire in `main.py`, extend `routes_documents.py` delete; `backend/tests/api/test_history_api.py` (complete).
**Interfaces produced:** `HistoryEntryOut` (all `HistoryEntry` fields + `session_active: bool`); `GET /api/history?limit=20` → `list[HistoryEntryOut]` (`session_active = store.get(id) is not None`); `DELETE /api/history/{id}` → 204. `DELETE /api/documents/{id}` unchanged except it no longer needs to touch history (row stays).
- [ ] Test: full upload→analyze→format flow, `GET /history` → one row, `state=="formatted"`, `profile_id=="ieee"`, `health_total` int, `session_active is True`; `DELETE /history/{id}` → 204, then `GET /history` empty; separately, `DELETE /documents/{id}` then `GET /history` still shows the row with `session_active is False`.
- [ ] Green; commit `feat(backend): /api/history list + delete; DELETE /documents keeps history`.

### Task 4 — Springer profile
**Files:** `app/profiles/data/springer.yaml`, `app/profiles/loader.py`, `app/profiles/rules_doc.py`, `scripts/gen_rules_doc.py`, `docs/RULES.md` (regenerated); `backend/tests/unit/test_profiles.py` (extend), `backend/tests/api/test_formats.py` (extend), `backend/tests/api/test_format_validate.py` (modify).
**Interfaces produced:** `load_profile("springer")` returns a valid `PublisherProfile` with `columns.count == 1`, `page.size == "a4"`; `list_profiles()` returns springer `status=="available"`, no `planned` entries; `render_all_rules_md(list[PublisherProfile]) -> str`.
- [ ] Test: `load_profile("springer")` — columns 1, a4, every `rule_groups()` value has a valid `RuleProvenance`; `list_profiles()` has no `status=="planned"`; `render_all_rules_md([ieee, springer])` contains `` `ieee` `` and `` `springer` `` headings and every group key of both; `docs/RULES.md` text contains every group key of both profiles (regenerate in the test setup or assert-and-instruct). `GET /api/formats` → springer `available`. `POST /format {profile_id:"springer"}` on an analyzed doc → 200, `state=="formatted"`.
- [ ] Impl: write `springer.yaml` per spec §3; remove `"springer"` from `PLANNED_PROFILES`; `rules_doc.render_all_rules_md`; `gen_rules_doc.py` loads all `data/*.yaml`; run it to regenerate `docs/RULES.md`.
- [ ] Green; commit `feat(backend): Springer publisher profile (one hedged generic profile)`.

### Task 5 — Springer formatting integration
**Files:** `backend/tests/integration/test_springer_format.py`.
- [ ] Test: `format_document(manuscript_from(sample_basic), src, out, load_profile("springer"))` → out exists; re-parse, `check_preservation` passes; `out` section `sectPr/w:cols` has `w:num=="1"`; body-text hash unchanged. Also run on `sample_complex`.
- [ ] If the engine needs a fix for single-column (e.g. `_set_columns` when going 2→1 or removing an existing multi-col block), make it in `formatting/page.py` with its own note.
- [ ] Green; commit `test(backend): Springer format preserves content and is single-column` (+ any engine fix).

### Task 6 — Stats extraction + page_count plumbing
**Files:** `app/analysis/stats.py`, `app/analysis/pipeline.py`, `app/storage/base.py`, `app/export/pdf_export.py`, `app/api/routes_documents.py`, `app/schemas/analysis.py`; `backend/tests/unit/test_stats.py`, extend `test_export.py`.
**Interfaces produced:** `compute_stats(blocks: list[Block]) -> DocumentStats`; `export_pdf(...) -> PdfResult(path: Path, page_count: int)`; `DocumentRecord.page_count: int | None`; `AnalysisOut.page_count: int | None`.
- [ ] Test: `compute_stats` on a small block list matches expected counts (moved from pipeline — keep the existing pipeline integration test green); after `export/pdf` (or `preview` when pdf available), `GET /analysis` has `page_count >= 1`; when pdf unavailable, `page_count` stays null.
- [ ] Impl: extract `_compute_stats` → `stats.compute_stats` (pipeline imports it); `export_pdf` returns `PdfResult`; export + preview handlers set `record.page_count = result.page_count`; `AnalysisOut.from_record` passes it through.
- [ ] Green; commit `feat(backend): shared stats helper + PDF page_count on the record`.

### Task 7 — Comparison service + endpoint
**Files:** `app/analysis/comparison.py`, `app/schemas/comparison.py`, extend `routes_documents.py`; `backend/tests/integration/test_comparison.py`, `backend/tests/api/test_comparison_api.py`.
**Interfaces produced:** `MetaSummary{title,authors:[str],abstract_present:bool,keywords:[str]}`, `Comparison{original:Side, formatted:Side, deltas:dict[str,int], summary:CompareSummary}` where `Side{stats:DocumentStats, metadata:MetaSummary, sections:[str]}`, `CompareSummary{formatting_changes:int, content_changes:int, warnings_remaining:int, preservation_passed:bool}`; `build_comparison(record) -> Comparison`. `GET /api/documents/{id}/comparison` → `ComparisonOut` (409 unless state in `formatted|validated|exported`).
- [ ] Test (integration): analyze→format `sample_complex`, `build_comparison(record)` → `original.stats.tables == formatted.stats.tables`, same for figures and references; `deltas["tables"] == 0`; `summary.preservation_passed is True`; `summary.formatting_changes == len(record.change_log.formatting_changes)`. (api): `GET …/comparison` before format → 409; after → 200 with the shape.
- [ ] Impl: `build_comparison` re-parses `record.artifacts["formatted"]`, classifies, builds both `Side`s; `deltas` = field-wise difference; `summary` from `record.change_log` + `record.preservation`. `sections` = `[b.text.strip() for b in blocks if b.kind in HEADING_KINDS]`.
- [ ] Green; commit `feat(backend): before/after comparison service + endpoint`.

### Task 8 — Frontend types + api client
**Files:** `src/lib/types.ts`, `src/lib/api.ts`, `src/tests/api.test.ts` (extend).
**Interfaces produced:** `HistoryEntry`, `ComparisonOut` (+ `ComparisonSide`, `MetaSummary`, `CompareSummary`), `AnalysisOut.page_count`; `api.history(limit=20) -> HistoryEntry[]`, `api.deleteHistory(id) -> void`, `api.getComparison(id) -> ComparisonOut`.
- [ ] Test: `api.history()` → `GET http://localhost:8000/api/history?limit=20`; `api.deleteHistory("d1")` → `DELETE …/api/history/d1`; `api.getComparison("d1")` → `GET …/api/documents/d1/comparison`.
- [ ] Green; commit `feat(frontend): history + comparison types and api methods`.

### Task 9 — Dashboard recents
**Files:** `src/components/dashboard/RecentList.tsx`, `src/pages/DashboardPage.tsx`, `src/tests/history.test.tsx`.
**Interfaces produced:** `<RecentList />` — fetches `api.history(8)` on mount; rows: filename · `shortDate(updated_at)` · profile `Badge` · state `Badge` · health chip (tone by score, hidden when null); row → `navigate('/workspace/'+id)`; trailing "×" → `api.deleteHistory(id)` + optimistic remove; empty → existing `EmptyState`.
- [ ] Test: mocked `api.history` returns 2 entries → 2 rows with filenames and health; clicking "×" calls `api.deleteHistory` with that id and the row disappears; `api.history` returns `[]` → "No manuscripts yet".
- [ ] Green; commit `feat(frontend): dashboard recents from document history`.

### Task 10 — Stats panel + ended-session copy
**Files:** `src/components/workspace/StatsPanel.tsx`, `src/workspace/useWorkspace.ts`, `src/pages/WorkspacePage.tsx`, `src/tests/workspace.test.tsx` (extend).
**Interfaces produced:** `<StatsPanel stats={StatsOut} pageCount={number|null} />` — six labelled numbers, `pageCount ?? "—"`. `useWorkspace` exposes `pageCount` (from `analysis.page_count`). `WorkspacePage` renders `StatsPanel` at the top of the Review tab; the load-failure `ErrorState` shows "This working session has ended. Upload the document again." when the document fetch 404s (detect via `ApiError.status === 404`).
- [ ] Test: `StatsPanel` with a stats object + `pageCount={3}` shows "3" under Pages and the reference count; with `pageCount={null}` shows "—". `WorkspacePage` (mock `api.getDocument` → `ApiError(404)`) shows the ended-session copy.
- [ ] Green; commit `feat(frontend): workspace document statistics + ended-session state`.

### Task 11 — Compare tab
**Files:** `src/components/workspace/ComparePanel.tsx`, `src/workspace/useWorkspace.ts`, `src/pages/WorkspacePage.tsx`, `src/tests/compare.test.tsx`.
**Interfaces produced:** `<ComparePanel comparison={ComparisonOut|null} loading={bool} onLoad={()=>void} />` — calls `onLoad` on mount if `comparison` is null; renders Original | Formatted columns, a counts table with a delta column (0 → green `Badge`, non-zero → amber `Badge` with signed value), metadata side-by-side, and the summary strip (`Formatting changes · Content changes · Warnings remaining · Preservation: passed/review`). `useWorkspace`: `comparison`, `loadComparison()` (calls `api.getComparison`, caches). New `Tabs` item `{id:"compare", label:"Compare"}`.
- [ ] Test: `ComparePanel` with a fixture comparison → shows original & formatted table counts, a green chip where a delta is 0 and an amber "+1" where a delta is 1, and "Preservation: passed"; with `comparison={null}` calls `onLoad` once.
- [ ] Green; commit `feat(frontend): before/after Compare tab in the workspace`.

### Task 12 — Docs + check + walkthrough
**Files:** `backend/.env.example`, `frontend/.env.example` (no change likely), `README.md`, `docs/ARCHITECTURE.md`, `docs/RULES.md` (regenerated in Task 4).
- [ ] `backend/.env.example`: add `HISTORY_DB`, `HISTORY_ENABLED`.
- [ ] `README.md`: formats table → Springer **Available**; add a "Document history" line under Features; note `.workspace/history.db`.
- [ ] `docs/ARCHITECTURE.md`: `HistoryStore` row in the backend table; comparison + stats in the pipeline/extension sections.
- [ ] Run `bash scripts/check.sh` — fix anything red.
- [ ] Start both servers; browser walkthrough: dashboard (recents populated after a run) → upload a sample → analyze → Review shows stats → Format with **Springer** → What changed + Compare tab shows real deltas + preservation passed → back to dashboard, recents row present → delete a history row. Inspect console + network; fix root causes; retest.
- [ ] Commit `feat: Slice 2 docs, env, walkthrough green`.

---

## Self-Review

**Spec coverage:**
- §2 SQLite history (store, config, write points, endpoints, delete semantics) — Tasks 1, 2, 3. ✓
- §3 Springer profile (YAML, loader, rules doc, engine unchanged) — Tasks 4, 5. ✓
- §4 comparison (endpoint shape, service, frontend panel) — Tasks 7, 11. ✓
- §5 dashboard recents + `session_active` + ended-session copy + stats panel + `page_count` plumbing — Tasks 6, 9, 10. ✓
- §6 wiring (lifespan, deps, docs) — Tasks 2, 12. ✓
- §7 testing — each task carries its tests; §7's frontend + backend test files all mapped. ✓
- §8 out-of-scope respected — no session persistence, no Springer variants, no Playwright suite. ✓
- §9 acceptance — Task 12 walkthrough maps to it. ✓

**Placeholder scan:** none — every task names concrete assertions and interfaces. Tunable constants (`limit` defaults, WAL) are decided, not deferred.

**Type consistency:** `HistoryEntry`/`HistoryEntryOut` fields identical across Tasks 1/3; `Comparison`/`ComparisonOut` and sub-types defined in Task 7, consumed unchanged in Tasks 8/11; `PdfResult(path, page_count)` defined in Task 6 and used by the export/preview handlers in the same task; `AnalysisOut.page_count` added in Task 6 and read in Task 10. Endpoint paths identical between spec §2/§4, task interfaces, and the frontend `api` (Task 8).

**Deviation from writing-plans default:** steps at test-target + interface + commit granularity (not literal code per micro-step) — inline same-session execution with full Slice 1 context. TDD cycle still mandatory per task.

# ManuScript AI — Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, batch execution with checkpoints — chosen by the user as "autonomous per slice"). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the ManuScript AI vertical slice — upload a DOCX, analyze it with rule-based parsing/classification, apply the IEEE formatting profile in place, validate + score it, and export verified DOCX/PDF, driven from a polished React workspace.

**Architecture:** FastAPI backend, layered — `api` (routers only) → `analysis` pipeline → `parsing` / `extraction` / `classification` / `formatting` / `validation` / `export` modules over a pure-data `domain` model. State lives in an in-process `DocumentStore` (ABC + `InMemory` impl) plus per-document filesystem workspaces with TTL cleanup. Formatting transforms a *copy* of the upload (A2). Frontend is React + TS + Vite + Tailwind with a single typed processing state machine and ~400 ms polling for analysis progress (B1).

**Tech Stack:** Python 3.12, FastAPI, python-docx, Pydantic v2, Uvicorn, pytest, pypdf, PyYAML, LibreOffice (`soffice`) for PDF. React 18, TypeScript, Vite 5, Tailwind 3, lucide-react, vitest.

**Spec:** `docs/superpowers/specs/2026-09-08-manuscript-ai-slice-1-design.md`

## Global Constraints

- **Local/offline only.** No manuscript bytes to any external API/cloud. No network calls in the processing pipeline.
- **No fake functionality.** Every visible control works or is explicitly marked unavailable/planned. No fake progress, previews, downloads, compliance badges, or statistics.
- **Never claim "IEEE compliant."** Use "IEEE format profile applied" / "IEEE validation checks passed". Every formatting rule tagged `implemented | configurable | inferred | unsupported` in `docs/RULES.md`, sourced from the profile YAML.
- **Document fidelity.** Original upload never mutated. Formatting changes presentation, not research content. Body text preserved (normalized-hash equal outside the front-matter region).
- **Config, not constants.** Ports, paths, limits, thresholds, `soffice` path all env-driven with dev defaults. `.env.example` on both sides.
- **Logging never emits manuscript text** — counts, hashes, durations only.
- **Python** `python` (3.12). **Node** 24 / npm 11. Windows-first: scripts as `.ps1` + `.sh`.
- **TDD.** Failing test → minimal impl → green → commit. Frequent commits.
- Commit message trailer: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

---

## File Structure

### Backend (`backend/`)

| Path | Responsibility |
|---|---|
| `app/main.py` | App factory: mount routers, CORS, exception handlers, logging init, startup TTL sweeper task. |
| `app/config.py` | `Settings(BaseSettings)` — all env vars + defaults; `get_settings()` cached. |
| `app/logging_config.py` | Structured JSON logger; `log_stage(event, document_id, stage, duration_ms, **counts)`. |
| `app/domain/manuscript.py` | `Manuscript, Metadata, Field, Author, Affiliation, DocumentStats`. |
| `app/domain/elements.py` | `ElementType` enum, `Block`, `FormattingState`, `SourceRef`, `SectionNode`. |
| `app/domain/issues.py` | `Severity`, `IssueCategory`, `Issue`, `HealthScore`, `HealthContributor`, `ChangeLog`, `PreservationResult`. |
| `app/schemas/*.py` | Pydantic DTOs: `document.py`, `analysis.py`, `metadata.py`, `formatting.py`, `validation.py`, `errors.py`, `formats.py`. |
| `app/storage/base.py` | `DocumentRecord` dataclass, `DocumentStore` ABC. |
| `app/storage/memory.py` | `InMemoryDocumentStore`. |
| `app/storage/workspace.py` | `WorkspaceManager` — create/get/delete per-uuid dirs, `sweep_expired()`, path-safety helpers. |
| `app/ingestion/validate_upload.py` | `validate_docx_bytes(data) -> None | raises UploadValidationError` (magic bytes, zip structure, required parts, zip-bomb guard). |
| `app/ingestion/receive.py` | `receive_upload(upload, settings, store, workspaces) -> DocumentRecord`. |
| `app/parsing/blocks.py` | `ParsedBlock` + subtypes, `RunFormat`, `ParsedTable`, `ParsedImage`. |
| `app/parsing/ooxml.py` | Raw-XML helpers: iterate body elements in order, detect breaks/equations, read hyperlinks/headers/footers. |
| `app/parsing/docx_reader.py` | `parse_docx(path) -> ParsedDocument` (ordered blocks + parse_warnings). Read-only. |
| `app/extraction/metadata.py` | `extract_metadata(blocks, settings) -> Metadata` — title/author/affiliation/abstract/keywords heuristics + confidence. |
| `app/classification/classifier.py` | `classify_blocks(blocks, metadata, settings) -> list[Block]`. |
| `app/classification/structure.py` | `canonicalize_heading(text) -> CanonicalSection | None`; synonym table. |
| `app/analysis/pipeline.py` | `run_analysis(record, store, workspaces)` — staged; updates `record.analysis` with stage status + counts; builds `Manuscript`. |
| `app/profiles/base.py` | `PublisherProfile` model + `RuleProvenance`; nested rule groups. |
| `app/profiles/loader.py` | `load_profile(profile_id) -> PublisherProfile`; `list_profiles() -> list[ProfileSummary]`. |
| `app/profiles/data/ieee.yaml` | IEEE profile as configuration, every group carrying `provenance`. |
| `app/formatting/engine.py` | `format_document(manuscript, source_path, profile, out_path) -> FormatResult(change_log, issues)`. |
| `app/formatting/styles.py` | `ensure_styles(doc, profile)` — named styles, raw XML where needed. |
| `app/formatting/page.py` | `apply_page_layout(doc, profile)` — size, margins, columns per `sectPr`. |
| `app/formatting/frontmatter.py` | `rebuild_frontmatter(doc, manuscript, profile) -> list[str]` (changes applied). |
| `app/formatting/body.py` | `restyle_body(doc, manuscript, profile) -> list[str]`. |
| `app/formatting/tables.py` | `style_tables(doc, manuscript, profile) -> list[Issue]`. |
| `app/formatting/figures.py` | `check_figures(doc, manuscript, profile) -> list[Issue]`. |
| `app/validation/validators.py` | `validate(original: Manuscript, formatted_path, profile) -> list[Issue]` (all categories). |
| `app/validation/references.py` | `check_references(manuscript) -> list[Issue]`. |
| `app/validation/preservation.py` | `check_preservation(original: Manuscript, formatted_path) -> PreservationResult`. |
| `app/validation/health.py` | `score(issues, manuscript) -> HealthScore`. |
| `app/export/docx_export.py` | `export_docx(formatted_path, out_path) -> Path` (verify openable). |
| `app/export/pdf_export.py` | `export_pdf(formatted_path, out_dir, settings) -> Path` (soffice, verify `%PDF`, page count); `pdf_available(settings) -> bool`. |
| `app/api/deps.py` | `get_settings`, `get_store`, `get_workspaces`. |
| `app/api/routes_health.py` `routes_formats.py` `routes_documents.py` | Endpoints per spec §5. Routers only. |
| `app/utils/{ids,text,files}.py` | uuid, whitespace-normalize + word-count + hash, safe path join. |
| `tests/unit/…` `tests/integration/…` `tests/api/…` | Per spec §17. |
| `tests/fixtures/gen.py` | Shared tiny in-memory docx builders for unit tests. |
| `requirements.txt` `requirements-dev.txt` `pyproject.toml` `.env.example` | Deps + tool config. |

### Frontend (`frontend/`)

| Path | Responsibility |
|---|---|
| `src/main.tsx` `src/App.tsx` `src/index.css` | Bootstrap, router, Tailwind entry. |
| `src/lib/types.ts` | TS mirrors of backend DTOs. |
| `src/lib/api.ts` | Typed fetch client, one function per endpoint, error normalization. |
| `src/lib/format.ts` | bytes→human, percent, date helpers. |
| `src/state/useDocumentFlow.ts` | `ProcessingState` union + reducer + actions; `localStorage` persistence. |
| `src/hooks/usePolling.ts` `useToast.ts` `useReducedMotion.ts` | Utilities. |
| `src/components/ui/*` | `Button, Card, Badge, Field, Chip, Dialog, Progress, Toast, EmptyState, ErrorState, Tabs, Spinner`. |
| `src/components/upload/Dropzone.tsx` | Drag/drop + click, client-side type/size guard, a11y. |
| `src/components/analyze/StageList.tsx` | Staged progress from `/analysis`. |
| `src/components/workspace/{TopBar,OutlinePanel,MetadataEditor,ElementsList,IssuesPanel,HealthCard,FormatPicker,WhatChanged,PreviewPane,ExportBar}.tsx` | Workspace units per spec §15. |
| `src/pages/{DashboardPage,UploadPage,AnalyzePage,WorkspacePage}.tsx` | Screens. |
| `src/tests/*` | vitest: state machine, api client, Dropzone reject, StageList. |
| `index.html` `package.json` `vite.config.ts` `tailwind.config.ts` `postcss.config.js` `tsconfig*.json` `.env.example` `.eslintrc.cjs` | Config. |

### Root

| Path | Responsibility |
|---|---|
| `scripts/gen_samples.py` | Build `sample_documents/sample_{basic,complex,messy}.docx`. |
| `scripts/dev.ps1` `dev.sh` | Run backend (uvicorn --reload) + frontend (vite) together. |
| `scripts/check.ps1` `check.sh` | ruff + pytest + tsc + vitest. |
| `docs/ARCHITECTURE.md` | Module map + data flow. |
| `docs/RULES.md` | Every IEEE rule tagged, generated-from/checked-against `ieee.yaml`. |
| `README.md` | Overview, setup, run, test, privacy model, supported formats, limitations. |
| `LICENSE` | MIT. |

---

## Tasks

Ordered. Each task = failing test(s) → minimal impl → green → commit. Backend uses `pytest`; frontend uses `vitest`. Where a task is pure scaffolding/config it folds into the first task that needs it (noted).

### Task 1 — Repo scaffold + backend app boots
**Files:** `backend/{requirements.txt,requirements-dev.txt,pyproject.toml,.env.example}`, `backend/app/{__init__,main,config,logging_config}.py`, `backend/app/api/{__init__,deps,routes_health}.py`, `backend/tests/{__init__,conftest}.py`, `backend/tests/api/test_health.py`.
**Interfaces produced:** `create_app() -> FastAPI`; `Settings` fields (all Global-Constraints env vars); `get_settings()`, `get_store()`, `get_workspaces()` deps; `GET /api/health -> {status:"ok", version, capabilities:{pdf_export:bool}}`.
- [ ] Test: `test_health_ok` — `TestClient(create_app()).get("/api/health")` → 200, `status=="ok"`, `capabilities.pdf_export` is bool.
- [ ] Impl: `Settings` (pydantic-settings), cached `get_settings`; `create_app` mounts `routes_health`; `pdf_export` from `pdf_available()` stub returning `shutil.which(soffice_path or "soffice") is not None`.
- [ ] Green; commit `feat(backend): app factory + health endpoint`.

### Task 2 — Domain model
**Files:** `backend/app/domain/{__init__,manuscript,elements,issues}.py`, `backend/tests/unit/test_domain.py`.
**Interfaces produced:** dataclasses/pydantic per spec §4 — `Field(value, confidence, source_ref, edited_by_user)`, `Metadata`, `Author`, `Affiliation`, `Manuscript`, `DocumentStats`, `ElementType` (enum, exact members from spec §4), `Block`, `FormattingState`, `SourceRef(part, index)`, `SectionNode`, `Severity`, `IssueCategory`, `Issue`, `HealthContributor`, `HealthScore`, `ChangeLog`, `PreservationResult`.
- [ ] Test: construct a `Manuscript` with one heading `Block` + one paragraph `Block`; assert enum values, `Field` defaults (`edited_by_user is False`), `HealthScore.total` in 0..100 clamp helper.
- [ ] Impl: prefer frozen dataclasses for pure model; `ElementType`/`Severity`/`IssueCategory` as `str, Enum`.
- [ ] Green; commit `feat(backend): internal document domain model`.

### Task 3 — Workspace manager + DocumentStore
**Files:** `backend/app/storage/{__init__,base,memory,workspace}.py`, `backend/tests/unit/test_storage.py`.
**Interfaces produced:** `DocumentRecord(id, filename, size, state, created_at, source_path, manuscript, analysis, artifacts: dict, error)`; `DocumentStore` ABC: `create(record)`, `get(id)->record|None`, `update(record)`, `delete(id)`, `list()`; `InMemoryDocumentStore`. `WorkspaceManager(root)`: `create(doc_id)->Path`, `path(doc_id, *parts)->Path` (rejects traversal), `delete(doc_id)`, `sweep_expired(ttl_minutes)->int`.
- [ ] Tests: create→get round-trip; `delete` removes; `path(id, "..","x")` raises; `sweep_expired` removes an old dir (mtime backdated) and returns count; unknown `get` → None.
- [ ] Impl minimal.
- [ ] Green; commit `feat(backend): document store + filesystem workspace manager`.

### Task 4 — Upload validation
**Files:** `backend/app/ingestion/{__init__,validate_upload}.py`, `backend/tests/unit/test_validate_upload.py`, `backend/tests/fixtures/gen.py` (adds `minimal_docx_bytes()`).
**Interfaces produced:** `validate_docx_bytes(data: bytes, max_bytes: int) -> None`; raises `UploadValidationError(code, message)` with codes `too_large|not_docx|corrupt|unsafe_zip`.
- [ ] Tests: valid minimal docx passes; `b"MZ..."` → `not_docx`; truncated zip → `corrupt`; a zip missing `word/document.xml` → `corrupt`; oversize → `too_large`; a zip entry named `../evil` → `unsafe_zip`; entry-count / uncompressed-size caps trip `unsafe_zip`.
- [ ] Impl: `zipfile` inspection; caps from constants documented in code (`MAX_ZIP_ENTRIES=2000`, `MAX_UNCOMPRESSED=200*1024*1024`) — noted as `ponytail:` tunable.
- [ ] Green; commit `feat(backend): DOCX upload validation with zip-bomb + traversal guards`.

### Task 5 — Upload endpoint
**Files:** `backend/app/ingestion/receive.py`, `backend/app/schemas/{document,errors}.py`, `backend/app/api/routes_documents.py` (new, upload + GET only), wire into `main.py`; `backend/tests/api/test_documents_upload.py`.
**Interfaces produced:** `POST /api/documents/upload` (multipart `file`) → 201 `DocumentOut{id,filename,size,state}`; `GET /api/documents/{id}` → `DocumentOut` or 404; error body `ErrorOut{error,message,detail?,hint?,error_id}`; state `"uploaded"`.
- [ ] Tests: upload minimal docx → 201, state `uploaded`, id present; `GET` that id → 200; `GET` bogus → 404 `ErrorOut`; upload `.txt` → 415; oversize (set tiny `MAX_UPLOAD_MB` via settings override) → 413; filename never used as a path (upload `../../x.docx`, assert stored file is under workspace).
- [ ] Impl: stream to `workspace/source.docx`, size guard, call `validate_docx_bytes`, create record.
- [ ] Green; commit `feat(backend): document upload + retrieval endpoints`.

### Task 6 — DOCX parser
**Files:** `backend/app/parsing/{__init__,blocks,ooxml,docx_reader}.py`, `backend/tests/unit/test_parser.py`, extend `tests/fixtures/gen.py` (`docx_with(paragraphs=..., tables=..., headings=..., image=bool)`).
**Interfaces produced:** `parse_docx(path: Path) -> ParsedDocument(blocks: list[ParsedBlock], parse_warnings: list[str])`. `ParsedBlock(kind_hint, text, runs: list[RunFormat], style_name, outline_level, numbering, alignment, source_ref)`; `kind_hint ∈ {"paragraph","table","image"}`; `RunFormat(text, font, size_pt, bold, italic)`. Body order preserved.
- [ ] Tests: doc with H1 + 2 paragraphs + a 2×2 table + one image → 5 blocks in order; heading block has `style_name` starting `Heading`/`outline_level==0`; table block `kind_hint=="table"` and text is tab/newline-joined cell text; image block present; run font/size/bold captured; a deliberately broken paragraph part appends a `parse_warnings` entry, still returns blocks.
- [ ] Impl: python-docx for paragraphs/tables/runs/numbering; `ooxml.iter_body(doc)` yields elements in true document order (so tables interleave correctly); image detection via `w:drawing`/`w:pict` in runs; equations (`m:oMath`) → `kind_hint="paragraph"` with marker in `runs` and never edited later.
- [ ] Green; commit `feat(backend): read-only DOCX parser → ordered block stream`.

### Task 7 — Metadata extraction
**Files:** `backend/app/extraction/{__init__,metadata}.py`, `backend/tests/unit/test_metadata.py`.
**Interfaces produced:** `extract_metadata(blocks: list[ParsedBlock], confidence_threshold: float) -> Metadata`.
- [ ] Tests (synthetic block lists, not real docx):
  - title = biggest/centered/bold short first block; `.title.confidence >= threshold`.
  - authors line `"Ada Lovelace, Alan Turing and Grace Hopper"` → 3 `Author` names.
  - affiliation line with `"University of X"` + email → captured, email on author/affiliation.
  - `"Abstract"` heading then paragraph → `abstract.value` == that paragraph; also `"Abstract— text"` inline form.
  - `"Index Terms—a, b, c"` → keywords `["a","b","c"]`; also `"Keywords: a; b"`.
  - garbage first block (long sentence ending in period) → `title.confidence < threshold`, still returns something.
- [ ] Impl: pure scoring functions; weights as named constants (`ponytail:` tunable).
- [ ] Green; commit `feat(backend): rule-based metadata extraction with confidence`.

### Task 8 — Classification + structure
**Files:** `backend/app/classification/{__init__,classifier,structure}.py`, `backend/tests/unit/test_classifier.py`, `test_structure.py`.
**Interfaces produced:** `classify_blocks(blocks, metadata, confidence_threshold) -> list[Block]` (domain `Block`, ordered, `source_ref` carried, `needs_review` when `confidence < threshold`); `canonicalize_heading(text) -> str | None` returning canonical keys `introduction|related_work|methods|results|discussion|conclusion|references|appendix|acknowledgement`.
- [ ] Tests:
  - `"Heading 1"` style → `ElementType.heading`, `level==1`; `"1.2 Foo"` numbered short bold → heading `level==2`.
  - `"Figure 3. Caption text"` next to an image block → `caption`, `number==3`.
  - `"[12] A. Author, ..."` inside references section → `reference_item`, `number==12`.
  - numbered list item → `numbered_list_item`.
  - `canonicalize_heading("Experimental Setup") == "methods"`, `("Findings") == "results"`, `("Background") == "introduction"`, `("Totally Novel") is None`.
  - low-signal paragraph classified `paragraph` with `confidence` set; ambiguous heading → `needs_review True`.
- [ ] Impl: ordered rule cascade from spec §9; synonym dict in `structure.py`.
- [ ] Green; commit `feat(backend): element classification + canonical structure detection`.

### Task 9 — Analysis pipeline + endpoints (B1 polling)
**Files:** `backend/app/analysis/{__init__,pipeline}.py`, `backend/app/schemas/analysis.py`, extend `routes_documents.py` (`analyze`, `analysis`, `outline`, `elements`), `backend/tests/api/test_analysis.py`, `tests/integration/test_pipeline_basic.py`.
**Interfaces produced:** `run_analysis(doc_id, store, workspaces) -> None` (sync core; called via `BackgroundTasks`); stages keys/labels exactly: `read`→"Reading document", `extract`→"Extracting content", `metadata`→"Detecting metadata", `classify`→"Classifying sections", `figures`→"Detecting figures & tables", `references`→"Detecting references", `structure`→"Preparing document structure". `POST /api/documents/{id}/analyze` → 202 `{state:"analyzing"}` (409 if not `uploaded`/`error`); `GET …/analysis` → `{state, stages:[{key,label,status:"pending|active|done",detail}], stats?, metadata?, issues_preview?}`; `GET …/outline` → `{nodes:[{id,label,level,block_id,children}]}`; `GET …/elements?offset&limit` → `{items:[{id,kind,confidence,text_preview,needs_review}], total}`.
- [ ] Tests: analyze basic sample → poll `/analysis` until `state=="analyzed"`; all 7 stages `done`; `stats` has real counts (`paragraphs>0`, `headings>0`); `/outline` returns ≥1 node; `/elements` paginates; analyze twice → 409 the second time while analyzing; integration test asserts `Manuscript` persisted on the record with `body` length == parsed block count.
- [ ] Impl: pipeline updates `record.analysis.stages` after each stage with counts in `detail`; builds `Manuscript` (metadata + classified blocks + `DocumentStats` + `SectionNode` tree). Errors → `record.state="error"`, sanitized message, stack logged.
- [ ] Green; commit `feat(backend): staged analysis pipeline + analysis/outline/elements endpoints`.

### Task 10 — Metadata + classification correction endpoints
**Files:** `backend/app/schemas/metadata.py`, extend `routes_documents.py` (`PUT …/metadata`, `PATCH …/elements/{bid}`), `backend/tests/api/test_corrections.py`.
**Interfaces produced:** `PUT /api/documents/{id}/metadata` body `MetadataIn{title?,authors?,affiliations?,abstract?,keywords?}` → full `Metadata` out, edited fields `confidence==1.0`, `edited_by_user==True`; `PATCH …/elements/{bid}` body `{kind?, level?}` → updated element; both recompute outline + `issues_preview`; 404 unknown id/bid; 409 if state not in `analyzed|formatted|validated`.
- [ ] Tests: PUT new title → persisted, flagged edited; PATCH a paragraph → heading level 2 → `/outline` now includes it; bad `kind` → 422; unknown bid → 404.
- [ ] Green; commit `feat(backend): user corrections for metadata + element classification`.

### Task 11 — Publisher profile system + IEEE YAML
**Files:** `backend/app/profiles/{__init__,base,loader}.py`, `backend/app/profiles/data/ieee.yaml`, `backend/app/schemas/formats.py`, `backend/app/api/routes_formats.py`, wire to `main.py`; `backend/tests/unit/test_profiles.py`, `backend/tests/api/test_formats.py`; `docs/RULES.md`.
**Interfaces produced:** `PublisherProfile` (nested groups per spec §10, each with `provenance: RuleProvenance`); `load_profile("ieee") -> PublisherProfile`; `list_profiles() -> [ProfileSummary{id,name,summary,features,status}]` (`ieee` status `available`, `springer` `planned`); `GET /api/formats`.
- [ ] Tests: `load_profile("ieee")` parses; `columns==2`; `base_font.family=="Times New Roman"`; every top-level rule group has a `provenance` in the enum; `load_profile("nope")` raises `ProfileNotFound`; `GET /api/formats` lists IEEE available + Springer planned; a test asserts `docs/RULES.md` mentions every rule group key (keeps doc honest).
- [ ] Impl: PyYAML load → pydantic validate; `RULES.md` table generated by a tiny helper `render_rules_md(profile)` also used by the test.
- [ ] Green; commit `feat(backend): configurable publisher profiles + IEEE profile + formats endpoint`.

### Task 12 — Formatting engine: styles + page layout
**Files:** `backend/app/formatting/{__init__,styles,page}.py`, `backend/tests/unit/test_formatting_styles.py`.
**Interfaces produced:** `ensure_styles(doc, profile) -> None` (idempotent; creates/updates paragraph styles `MS Title, MS Author, MS Affiliation, MS Abstract, MS Keywords, MS Heading 1..3, MS Body, MS Caption, MS Reference`); `apply_page_layout(doc, profile) -> None` (all sections: page size, margins, `w:cols` count+space).
- [ ] Tests (python-docx `Document()` in memory): after `ensure_styles`, styles exist with expected font name/size/bold; calling twice does not duplicate; after `apply_page_layout`, `section.page_width`, `.left_margin`, and raw `sectPr/w:cols/@w:num` match profile.
- [ ] Impl: python-docx style API; raw XML (`OxmlElement`) for `w:cols` and small-caps/number-format where API is missing.
- [ ] Green; commit `feat(backend): formatting engine — named styles + page/column layout`.

### Task 13 — Formatting engine: frontmatter + body + tables + figures
**Files:** `backend/app/formatting/{frontmatter,body,tables,figures,engine}.py`, `backend/tests/unit/test_formatting_body.py`, `backend/tests/integration/test_format_preserves_content.py`.
**Interfaces produced:** `format_document(manuscript, source_path, out_path, profile) -> FormatResult(change_log: ChangeLog, issues: list[Issue])`. Sub-steps return `list[str]` (changes) / `list[Issue]`. Source file never opened for writing; work on a `shutil.copy` at `out_path`.
- [ ] Tests:
  - `restyle_body` applies `MS Heading 1` to a heading block's paragraph and `MS Body` to a paragraph; inline bold run inside a sentence is preserved.
  - `rebuild_frontmatter` replaces leading title/author/abstract/keywords paragraphs with styled ones carrying the (possibly edited) metadata text; returns change strings.
  - `style_tables` applies table style + emits a LAYOUT `Issue` when estimated width > text width (construct a wide table).
  - `check_figures` emits `warning` when a figure has no adjacent caption; never invents caption text.
  - **integration:** run full `format_document` on `sample_basic` + `sample_complex`; re-parse output; assert normalized body-text hash (excluding front-matter region) == original; paragraph count delta within tolerance; tables/images count unchanged; a `.docx` that still opens in python-docx.
- [ ] Impl per spec §11; `engine.format_document` orchestrates copy → `ensure_styles` → `apply_page_layout` → `rebuild_frontmatter` → `restyle_body` → `style_tables` → `check_figures` → save.
- [ ] Green; commit `feat(backend): formatting engine — frontmatter rebuild + body restyle + table/figure checks`.

### Task 14 — Validation + references + preservation + health
**Files:** `backend/app/validation/{__init__,validators,references,preservation,health}.py`, `backend/app/schemas/validation.py`, `backend/tests/unit/test_validation.py`, `test_references.py`, `test_health.py`, `test_preservation.py`.
**Interfaces produced:** `check_references(manuscript) -> list[Issue]`; `check_preservation(original: Manuscript, formatted_path: Path) -> PreservationResult{passed,paragraph_delta,text_match,details}`; `validate(original, formatted_path, profile) -> list[Issue]` (DOCUMENT/STRUCTURE/FORMATTING/CONTENT/REFERENCES/LAYOUT); `score(issues, manuscript) -> HealthScore` (categories Structure/Formatting/References/"Figures & Tables"/Metadata/Layout; weights .20/.20/.15/.15/.15/.15; `contributors[]` per deduction).
- [ ] Tests:
  - references: citations `[1],[2],[5]` in body, list `[1],[2]` → issue "citation [5] has no reference"; list `[1],[2],[3]` with only `[1]` cited → "reference [3] never cited"; duplicate `[2]` in list → duplicate issue; gap `[1],[3]` → numbering issue.
  - preservation: identical body → `passed True`; drop a paragraph from formatted → `passed False`, `paragraph_delta==-1`, detail names it.
  - health: zero issues → `total==100`; one `error` in Structure → Structure < 100 and `total` reduced by the category weight; `contributors` non-empty; deterministic (call twice, equal).
  - validators: missing abstract in metadata → STRUCTURE error; body font mismatch on sampled paragraph → FORMATTING warning.
- [ ] Green; commit `feat(backend): validation engine, reference consistency, preservation check, health score`.

### Task 15 — Format + validate endpoints
**Files:** extend `routes_documents.py` (`POST …/format`, `POST …/validate`), `backend/app/schemas/formatting.py`, `backend/tests/api/test_format_validate.py`, `tests/integration/test_full_pipeline.py`.
**Interfaces produced:** `POST /api/documents/{id}/format` body `{profile_id}` → `{state:"formatted", change_log, health_score, issues}` (409 unless state in `analyzed|formatted|validated`; 422 unknown profile; writes `artifacts["formatted"]`); `POST …/validate` → `{issues, health_score, preservation}` (409 unless `formatted|validated`; sets state `validated`).
- [ ] Tests: analyze→format basic sample → 200, `change_log.formatting_changes` non-empty, `change_log.content_changes == []` (preservation passed), `health_score.total` int 0..100; validate → `preservation.passed True`; format with `profile_id:"springer"` → 422 `planned`; format before analyze → 409. Integration: basic + complex + messy all the way through; messy sample yields ≥1 warning and `content_changes == []`.
- [ ] Green; commit `feat(backend): format + validate endpoints (full pipeline wired)`.

### Task 16 — Export: DOCX + PDF + preview
**Files:** `backend/app/export/{__init__,docx_export,pdf_export}.py`, extend `routes_documents.py` (`GET …/export/docx`, `…/export/pdf`, `…/preview`, `DELETE …/{id}`), `backend/tests/api/test_export.py`, `tests/integration/test_export_files.py`.
**Interfaces produced:** `export_docx(formatted_path, out_path) -> Path` (reopen to verify); `pdf_available(settings) -> bool`; `export_pdf(formatted_path, out_dir, settings) -> Path` (soffice `--headless --convert-to pdf`, timeout `PDF_TIMEOUT_S=60`, verify `%PDF-` + `pypdf` page count ≥ 1); endpoints stream `manuscript_ieee_formatted.{docx,pdf}` with `Content-Disposition`; PDF path returns 503 `{error:"pdf_unavailable"}` when `not pdf_available`; `GET …/preview` → `application/pdf` bytes when available else `{kind:"structured", html}` (post-format Manuscript rendered to labelled HTML); `DELETE` → 204 + workspace removed.
- [ ] Tests: after format, `export/docx` → 200, `content-type` docx, body starts `PK\x03\x04`, re-openable; `export/pdf` → 200 `%PDF-` **or** (if `not pdf_available`) 503 `pdf_unavailable` — test branches on `pdf_available(settings)`; `preview` returns pdf or structured html with the "Structural preview" label; `DELETE` then `GET` → 404. Integration writes real files to a tmp workspace and asserts on disk.
- [ ] Green; commit `feat(backend): verified DOCX + PDF export, preview, workspace delete`.

### Task 17 — Sample document generator + backend regression
**Files:** `scripts/gen_samples.py`, `sample_documents/*.docx` (committed), `backend/tests/conftest.py` (fixtures locating samples), `backend/tests/integration/test_samples.py`.
**Interfaces produced:** running `python scripts/gen_samples.py` writes the three docx deterministically; `sample_basic|complex|messy` pytest fixtures.
- [ ] Test: each sample parses; `complex` has ≥3 tables, ≥4 images, ≥20 reference items; `messy` has exactly one uncited reference and one caption-less figure (asserted via `check_references` / `check_figures`); full pipeline green on all three.
- [ ] Impl: python-docx builders per spec §17.
- [ ] Green; commit `feat: sample manuscripts + full-pipeline regression over samples`.

### Task 18 — Frontend scaffold + API client + state machine
**Files:** `frontend/{package.json,vite.config.ts,tailwind.config.ts,postcss.config.js,tsconfig.json,tsconfig.node.json,index.html,.env.example,.eslintrc.cjs}`, `frontend/src/{main.tsx,App.tsx,index.css}`, `frontend/src/lib/{types.ts,api.ts,format.ts}`, `frontend/src/state/useDocumentFlow.ts`, `frontend/src/tests/{state.test.ts,api.test.ts}`, `frontend/vitest.config.ts`.
**Interfaces produced:** `api` object: `health()`, `formats()`, `upload(file)`, `getDocument(id)`, `analyze(id)`, `getAnalysis(id)`, `getOutline(id)`, `getElements(id,offset,limit)`, `putMetadata(id,body)`, `patchElement(id,bid,body)`, `format(id,profileId)`, `validate(id)`, `previewUrl(id)`, `exportDocxUrl(id)`, `exportPdfUrl(id)`, `deleteDocument(id)`; `useDocumentFlow()` → `{state: ProcessingState, dispatch}` with `ProcessingState` union of the 13 spec §15 states; persists `{documentId,state}` to `localStorage`.
- [ ] Tests: reducer transitions `IDLE→UPLOADING→UPLOADED→ANALYZING→ANALYZED→…→EXPORTED`; illegal transition is a no-op; `ERROR` reachable from any; `localStorage` write/restore mocked; api client builds correct URLs from `VITE_API_BASE` and normalizes an `ErrorOut` JSON into a thrown `ApiError`.
- [ ] Impl: `fetch` wrapper; Vite + Tailwind config; `vitest` jsdom.
- [ ] Green; commit `feat(frontend): scaffold, typed API client, processing state machine`.

### Task 19 — UI primitives + Dashboard + Upload
**Files:** `frontend/src/components/ui/*`, `frontend/src/hooks/{useToast.ts,useReducedMotion.ts}`, `frontend/src/components/upload/Dropzone.tsx`, `frontend/src/pages/{DashboardPage.tsx,UploadPage.tsx}`, router in `App.tsx`, `frontend/src/tests/dropzone.test.tsx`.
**Interfaces produced:** `Button, Card, Badge, Field, Chip, Dialog, Progress, Toast, EmptyState, ErrorState, Tabs, Spinner` (typed props, `focus-visible` styles, `Dialog` focus-trapped + `aria-modal`); `Dropzone({onAccept, maxMb, disabled})` — drag/hover state, rejects non-`.docx` / oversize with visible message + retry, keyboard-openable.
- [ ] Tests: Dropzone rejects a `.txt` `File` with a message and does not call `onAccept`; accepts a `.docx` `File`; oversize rejected; `Enter`/`Space` on the zone triggers the file input.
- [ ] Impl: Tailwind design tokens in `index.css` (`--accent`, radius, borders); Dashboard cards (New manuscript / Supported formats from `api.formats()` / local-processing note / Recent empty state); Upload page wires `Dropzone`→`api.upload`→flow `UPLOADED`→document card→"Analyze manuscript".
- [ ] Green; commit `feat(frontend): UI primitives, dashboard, upload experience`.

### Task 20 — Analyze screen (staged polling)
**Files:** `frontend/src/hooks/usePolling.ts`, `frontend/src/components/analyze/StageList.tsx`, `frontend/src/pages/AnalyzePage.tsx`, `frontend/src/tests/stagelist.test.tsx`.
**Interfaces produced:** `usePolling(fn, {intervalMs, enabled, stopWhen})`; `StageList({stages})` renders 7 rows with pending/active/done states + `detail` counts; `AnalyzePage` calls `api.analyze` once then polls `api.getAnalysis` every 400 ms until `state==="analyzed"` → navigate to workspace, or `state==="error"` → `ErrorState` with retry.
- [ ] Tests: given a sequence of mocked `/analysis` responses, `StageList` shows counts as they arrive; on `analyzed` the page invokes the navigate callback; on `error` shows retry that re-dispatches `analyze`. `aria-live="polite"` region announces the active stage.
- [ ] Green; commit `feat(frontend): analysis screen with real staged progress`.

### Task 21 — Workspace: outline + metadata editor + elements
**Files:** `frontend/src/pages/WorkspacePage.tsx`, `frontend/src/components/workspace/{TopBar,OutlinePanel,MetadataEditor,ElementsList,HealthCard}.tsx`, `frontend/src/tests/metadata_editor.test.tsx`.
**Interfaces produced:** `WorkspacePage` three-pane layout (spec §15 diagram), responsive (drawers < `lg`); `MetadataEditor` edits title/authors/affiliations/abstract/keywords → `api.putMetadata`, shows confidence %, `needs_review` badge; `ElementsList` inline `<select>` reclassify → `api.patchElement`; `OutlinePanel` renders `api.getOutline` tree, click → scrolls the elements list to that `block_id`; `TopBar` shows filename + state pill + `HealthCard` score.
- [ ] Tests: editing the title field and blurring calls `api.putMetadata` with the new value and clears the `needs_review` badge on success; reclassifying an element calls `api.patchElement`; outline click scrolls (mock `scrollIntoView`).
- [ ] Green; commit `feat(frontend): review workspace — outline, metadata editor, elements list`.

### Task 22 — Workspace: format picker + what-changed + issues + preview + export
**Files:** `frontend/src/components/workspace/{FormatPicker,WhatChanged,IssuesPanel,PreviewPane,ExportBar}.tsx`, wire into `WorkspacePage`, `frontend/src/tests/{issues_panel.test.tsx,export_bar.test.tsx}`.
**Interfaces produced:** `FormatPicker` — IEEE card selectable, Springer card disabled "Planned"; confirm → `api.format` → flow `FORMATTING→FORMATTED`, toast "IEEE format profile applied"; `WhatChanged({changeLog})` — formatting-changes list + content-changes ("No content removed / No paragraphs reordered" iff `content_changes` empty, else "Review required" + list); `IssuesPanel({issues})` — count header, filter All/Errors/Warnings/Suggestions, each issue has a "Review" action calling `onLocate(location)`; `PreviewPane` — `<iframe src=previewUrl>` for PDF or rendered structured HTML with the label; `ExportBar` — DOCX button always, PDF button disabled unless `health.capabilities.pdf_export`, downloads via blob, success/one-line-error toasts.
- [ ] Tests: `IssuesPanel` filter shows only matching severities and the count updates; `ExportBar` PDF button disabled when `pdf_export` false and shows the "unavailable on this machine" hint; choosing IEEE in `FormatPicker` calls `api.format("...","ieee")`; `WhatChanged` shows "Review required" when `content_changes` non-empty.
- [ ] Green; commit `feat(frontend): format picker, what-changed, issue center, preview, export bar`.

### Task 23 — Wire-up, dev/check scripts, docs, manual walkthrough
**Files:** `scripts/{dev.ps1,dev.sh,check.ps1,check.sh}`, `docs/ARCHITECTURE.md`, `README.md`, `LICENSE`, `frontend/.env.example`, `backend/.env.example` (final), CORS origin wired to `VITE_API_BASE` host.
- [ ] Run `scripts/check.*` — ruff clean, `pytest` green, `tsc --noEmit` clean, `vitest` green. Fix what breaks.
- [ ] Start both servers via `scripts/dev.*`; in the in-app browser: dashboard → upload `sample_complex.docx` → analyze (stages + counts) → edit a metadata field → reclassify an element → pick IEEE → format → what-changed shows content unchanged → validate → health + issues render → preview shows the real PDF (soffice present) → export DOCX (opens) → export PDF (is `%PDF`). Inspect console + network for errors; fix root causes; restart; retest.
- [ ] README covers: overview, features, architecture, stack, install (`pip install -r`, `npm i`), run backend, run frontend, run tests, DOCX processing explanation, privacy model, supported formats (IEEE available / Springer planned), known limitations, extension points (SQLite `DocumentStore`, new profiles).
- [ ] Commit `feat: dev + check scripts, architecture doc, README; Slice 1 walkthrough green`.

---

## Self-Review

**Spec coverage:**
- §3 API — Tasks 1,5,9,10,11,15,16 cover every listed endpoint. ✓
- §4 domain model — Task 2. ✓
- §6 ingestion (magic bytes, zip-bomb, traversal, TTL, UUID paths) — Tasks 3,4,5. ✓
- §7 parser (order, source_ref, run formatting, equations preserved, read-only, warnings) — Task 6. ✓
- §8 metadata heuristics + confidence + user override never overwritten — Tasks 7,10. ✓
- §9 classification cascade + structure synonyms + needs_review — Task 8. ✓
- §10 profile system + provenance + RULES.md + honest formats list — Task 11. ✓
- §11 formatting engine A2 (copy, styles-first, frontmatter rebuild only, emphasis kept, flags not destruction) — Tasks 12,13. ✓
- §12 validation categories + references + preservation + health weights + determinism — Task 14. ✓
- §13 export (verify openable, soffice, %PDF check, 503 degrade, capability flag) — Task 16. ✓
- §14 preview (real PDF or labelled structural) — Task 16 + 22. ✓
- §15 frontend state machine (13 states), screens, workspace layout, design system, a11y, reduced-motion — Tasks 18–22. ✓
- §16 config + logging (no manuscript text) — Tasks 1,9. ✓
- §17 samples + test tiers — Tasks 17, plus unit/integration/api throughout. ✓
- §18 out-of-scope respected — no Springer/history/comparison/Playwright tasks. ✓
- §20 acceptance — Task 23 walkthrough maps to it. ✓

**Placeholder scan:** No "TBD/TODO/handle edge cases/similar to Task N" — each task names concrete tests and interfaces. Constant values that are genuinely tunable are marked `ponytail:` in code, not left vague. ✓

**Type consistency:** `Manuscript`, `Block`, `Metadata`, `Field`, `Issue`, `HealthScore`, `ChangeLog`, `PreservationResult`, `PublisherProfile`, `FormatResult` defined in Tasks 2/11/13/14 and consumed with the same names/shapes in 9/15/16. Endpoint paths identical between spec §5, Task interfaces, and frontend `api` (Task 18). Stage keys fixed once in Task 9 and reused in Task 20. ✓

**Deviation from writing-plans default:** steps are stated at test-target + interface + commit granularity rather than literal full code per micro-step, because execution is inline in this same session with full spec context (not a cold hand-off). The TDD cycle (failing test → minimal impl → green → commit) is still mandatory per task.

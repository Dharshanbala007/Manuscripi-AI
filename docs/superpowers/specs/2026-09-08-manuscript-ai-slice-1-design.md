# ManuScript AI — Slice 1 (Vertical Slice / MVP) Design

**Date:** 2026-09-08
**Status:** Approved
**Scope:** First of three slices. Proves the full manuscript-formatting pipeline end to end for one publisher profile (IEEE), with a polished React workspace.

---

## 0. Context

New project, empty repository. ManuScript AI transforms an unformatted academic DOCX
manuscript into a publication-ready document using **rule-based** parsing, classification,
and formatting — no external AI/cloud services. Processing is local and offline-capable.

The full product spec spans 22 phases. It is decomposed into three slices, each with its
own spec → plan → implement cycle:

| Slice | Contents |
|---|---|
| **1. Vertical slice (this doc)** | Monorepo scaffold · DOCX upload+validation · parser → internal model · rule-based metadata + element classification with confidence · IEEE profile + formatting engine · validation engine + health score · DOCX export · PDF export (LibreOffice headless) · content-preservation check · polished React workspace (upload → analyze → review → format → validate → preview → export) · pytest unit/integration/API · sample DOCX generator |
| **2. Breadth** | Springer profile · before/after comparison · "what changed" deep view · SQLite document history behind `DocumentStore` · dashboard "recent" data · document statistics surface |
| **3. Hardening** | Full Playwright browser suite + bug-fix loop · dedicated UI-polish pass · accessibility audit · final regression · README + engineering report |

## 1. Confirmed architectural decisions

- **A2 — Transform a copy in place.** The formatting engine works on a *copy* of the
  uploaded DOCX, restyling the existing document tree (styles-first) and rebuilding only
  the front-matter block. Everything python-docx does not touch (OMML equations,
  footnotes, drawing XML, hyperlinks, field codes) survives intact. The internal
  `Manuscript` model is the *plan* (classification + reviewed metadata); the DOCX copy
  remains the source of truth for content.
- **B1 — Polling.** `POST /documents/{id}/analyze` starts a FastAPI background task;
  `GET /documents/{id}/analysis` returns `stages[]` with done flags and real counts.
  ~400 ms client polling. No SSE/WebSocket.
- **C1 — In-process `DocumentStore` + filesystem workspaces.** A `DocumentStore` ABC with
  one `InMemoryDocumentStore` implementation holds record status + parsed model + paths.
  Per-document UUID working directory under a configured root; startup TTL sweeper.
  **SQLite (Slice 2) adds a second `DocumentStore` implementation — no pipeline rewrite.**

## 2. Environment (verified)

- Python 3.12, Node 24, npm 11 present.
- **LibreOffice installed** (`soffice`) → real local/offline DOCX→PDF export is available.
  Absence at runtime degrades gracefully to "PDF unavailable" with DOCX still offered.
- Platform: Windows 11. Scripts provided as both `.ps1` and `.sh`.

---

## 3. Repository shape

```
manuscript-ai/                     (repo root == D:\Manuscript-AI)
├── backend/app/
│   ├── main.py config.py logging_config.py
│   ├── api/            routers only — zero processing logic
│   ├── schemas/        Pydantic DTOs (request / response / errors)
│   ├── domain/         internal model: manuscript, elements, issues — pure data, no I/O
│   ├── storage/        DocumentStore ABC + InMemory impl + workspace mgr + TTL sweeper
│   ├── ingestion/      upload receive + validation (magic bytes, zip structure, zip-bomb guard)
│   ├── parsing/        python-docx + raw OOXML → ordered ParsedBlock stream (read-only)
│   ├── extraction/     metadata heuristics + confidence
│   ├── classification/ per-block ElementType + canonical structure detection
│   ├── analysis/       pipeline orchestrator: runs stages, records counts + timings
│   ├── profiles/       PublisherProfile model + YAML loader + data/ieee.yaml
│   ├── formatting/     engine + styles / frontmatter / body / tables / figures / page sub-steps
│   ├── validation/     categorized validators + reference consistency + preservation + health
│   ├── export/         docx_export (verify openable) + pdf_export (soffice headless)
│   └── utils/
├── backend/tests/{unit,integration,api,fixtures}
├── backend/requirements.txt requirements-dev.txt pyproject.toml .env.example
├── frontend/src/{pages,components/{upload,analyze,workspace,ui},state,hooks,lib}
├── frontend/{index.html,package.json,vite.config.ts,tailwind.config.ts,tsconfig.json,.env.example}
├── scripts/            gen_samples.py, dev.{ps1,sh}, check.{ps1,sh}
├── sample_documents/   3 generated .docx, committed
├── docs/               ARCHITECTURE.md, RULES.md (every rule tagged), superpowers/specs/
├── README.md .gitignore LICENSE (MIT)
```

Granularity is mandated by product spec §5 (separation of concerns) and §59 (no giant files).

---

## 4. Document domain model

Pure data. No python-docx objects retained past parsing.

- **`Manuscript`**: `id, source_filename, metadata, body: list[Block], stats, parse_warnings`
- **`Metadata`**: `title, authors[], affiliations[], abstract, keywords[]` — each a **`Field`**
  carrying `value, confidence ∈ [0,1], source_ref, edited_by_user`
- **`Author`**: `name, email?, affiliation_ids[], confidence`
- **`Block`** (every source paragraph / table / image → exactly one, order preserved):
  `id, kind: ElementType, text, confidence, source_ref=(part, element_index), level?,
  list_kind?, number?, formatting_state, validation_notes[]`
- **`ElementType`**: title, author, affiliation, abstract, keywords, heading, subheading,
  paragraph, numbered_list_item, bullet_list_item, table, figure, caption, equation,
  reference_item, acknowledgement, appendix, other
- **`SectionNode`**: outline tree derived from headings (`canonical: Introduction | Methods
  | Results | Discussion | Conclusion | RelatedWork | References | Appendix | None`)
- **`DocumentStats`**: words, paragraphs, headings, tables, figures, references, sections
- **`Issue`**: `id, severity (error|warning|info), category (document|structure|formatting|
  content|references|layout), message, location, suggested_action`
- **`HealthScore`**: `total, categories{}, contributors[]{category, delta, reason}`
- **`ChangeLog`**: `formatting_changes[], content_changes[], warnings_remaining`

**A2 invariant:** the formatter never regenerates body content from `Manuscript`. Blocks
match back to DOCX elements by `source_ref`. Only the front-matter region is rebuilt, and
only from user-reviewed `Metadata`.

---

## 5. API surface (Slice 1)

```
GET    /api/health                       → {status, version, capabilities:{pdf_export}}
GET    /api/formats                      → [{id, name, summary, features[], status:"available"|"planned"}]
POST   /api/documents/upload             → 201 {id, filename, size, state:"uploaded"}
GET    /api/documents/{id}               → {id, filename, size, state, created_at}
POST   /api/documents/{id}/analyze       → 202 {state:"analyzing"}   (FastAPI BackgroundTask)
GET    /api/documents/{id}/analysis      → {state, stages[]{key,label,status,detail}, stats?, metadata?, issues_preview?}
GET    /api/documents/{id}/outline       → {nodes[]}
GET    /api/documents/{id}/elements      → paged blocks {id, kind, confidence, text_preview, needs_review}
PUT    /api/documents/{id}/metadata      → updated Metadata (marks edited, recomputes issues)
PATCH  /api/documents/{id}/elements/{bid} → override classification (kind / level)
POST   /api/documents/{id}/format        {profile_id} → {state:"formatted", change_log, health_score, issues[]}
POST   /api/documents/{id}/validate      → {issues[], health_score, preservation:{passed, details}}
GET    /api/documents/{id}/preview       → PDF bytes if soffice available, else structured JSON (labelled)
GET    /api/documents/{id}/export/docx   → file (manuscript_ieee_formatted.docx)
GET    /api/documents/{id}/export/pdf    → file, or 503 {error:"pdf_unavailable"}
DELETE /api/documents/{id}               → 204 (workspace cleanup)
```

Sanitized problem model `{error, message, detail?, hint?, error_id}`. HTTP codes:
400 (bad upload) / 404 (unknown id) / 409 (wrong-state transition) / 413 (too large) /
415 (wrong type) / 422 (schema) / 503 (pdf engine down) / 500 (sanitized).

Record state machine: `uploaded → analyzing → analyzed → formatting → formatted →
validating → validated → exported`; `error` reachable from any state; recoverable
(re-analyze / re-format).

---

## 6. Ingestion & validation

- Enforce `MAX_UPLOAD_MB` (env, default 25) via Content-Length check + streamed size guard.
- Validate: magic bytes `50 4B 03 04`; open as zip; require `[Content_Types].xml` and
  `word/document.xml`; reject entries with path-traversal (`..`, absolute); cap total
  uncompressed bytes and entry count (zip-bomb guard).
- Store at `WORK_DIR/{uuid}/source.docx` — UUID on disk, never the user's filename.
- Original file never mutated; all work on copies.
- Startup background TTL sweeper removes `WORK_DIR/*` older than `WORKSPACE_TTL_MIN`
  (env, default 120).
- Error messages map to product spec §33 phrasings.

---

## 7. Parser

- python-docx for paragraphs, runs, styles, tables, inline/anchored images, numbering.
- Raw OOXML (package parts + `element`) for hyperlinks, headers/footers, drawings, breaks,
  OMML equations — **detected and preserved, never edited**.
- Emits an **ordered** `list[ParsedBlock]`; body order == source order; each carries
  `source_ref=(part, element_index)` for round-tripping.
- Captures per-run formatting summary (font family, size, bold, italic, alignment, style
  name) — feeds heuristics now and the before/after comparison in Slice 2.
- Read-only: never mutates the loaded document.
- Per-element parse failure → recorded in `parse_warnings`, block emitted as `other`.
  Whole-file failure → spec §33 "Unable to read this document."

---

## 8. Metadata extraction (heuristics + confidence)

- **Title:** first substantial block within the first ~5; scored on largest font in region,
  bold, centered, short (< 25 words), no terminal period, followed by an author-like line.
- **Authors:** block(s) immediately after the title — name-shaped tokens, comma / "and" /
  superscript separators, no sentence punctuation, optional affiliation markers → split
  into `Author[]`.
- **Affiliations:** lines after authors containing org keywords (University, Institute,
  Department, Laboratory, Inc, GmbH, …); email regex → `email`.
- **Abstract:** `^abstract$` heading (case-insensitive) → following paragraph(s) until the
  next heading / keywords line; or a lead paragraph beginning `Abstract—` / `Abstract.`.
- **Keywords:** line starting `Keywords` / `Key words` / `Index Terms` (case-insensitive,
  optional `—` / `:`); split on `, ; ·`.
- Every field carries `confidence`; `< CONFIDENCE_THRESHOLD` (env, default 0.6) flags
  `needs_review` and raises an issue. User edits set confidence 1.0 + `edited_by_user`
  and are never auto-overwritten.
- Pure functions `(list[ParsedBlock]) -> Metadata`; unit-tested against synthetic block
  lists.

---

## 9. Classification & structure detection

Rule cascade per block:

1. Structural kinds (table / image) — from the parser.
2. **heading** — style `Heading N`, or outline level, or `^\d+(\.\d+)*\s+` + short + bold;
   records `level`.
3. **caption** — `^(Figure|Fig\.|Table)\s*\d+` adjacent to an image or table.
4. **reference_item** — inside the references section AND `^\[\d+\]` or `^\d+\.`.
5. **list items** — from numbering properties.
6. **abstract / keywords / acknowledgement / appendix** — by section context.
7. else **paragraph**.

**Structure detection:** heading text → canonical section via a synonym table
(`introduction` ← background, overview; `methods` ← methodology, materials and methods,
experimental setup; `results` ← findings, experiments; `related_work` ← literature review,
prior work; `references` ← bibliography; …). Unmatched headings are kept verbatim with
`canonical = None`.

Per-block confidence; `< threshold` → `needs_review` + issue. Low-confidence headings are
styled conservatively (as a heading of the detected level) and flagged — never dropped or
restructured. The override endpoint recomputes the outline and affected issues.

---

## 10. Publisher profile system + IEEE

`PublisherProfile` is a Pydantic model loaded from `profiles/data/ieee.yaml`. Rule groups:

```
page{size, margins}  columns  base_font  spacing
title_rules  author_rules  affiliation_rules  abstract_rules  keyword_rules
heading_rules[level]  paragraph_rules  caption_rules{figure, table}
table_rules  figure_rules  reference_rules  validation_rules
```

Every group carries **`provenance: implemented | configurable | inferred | unsupported`**.
`docs/RULES.md` is kept in sync from the YAML so the product never over-claims. UI copy is
*"IEEE format profile applied"* / *"IEEE validation checks passed"* — never *"IEEE
compliant"*.

IEEE v1 values encoded as configuration: US Letter; ~0.75" side / 1" top-bottom margins;
two-column; 10 pt Times New Roman body; single line spacing; centered ~24 pt title;
`Abstract—` bold lead-in with italic body; `Index Terms—` italic; headings — roman-numeral
centered L1, `A.` italic title-case L2, run-in lowercase L3; `Fig. N.` 8 pt caption below
the figure; `TABLE N` caption above the table; 8 pt hanging-indent `[N]` references. Each
value tagged `implemented` (standard IEEE template fact) or `inferred` (a sensible chosen
number). `GET /api/formats`: IEEE `available`, Springer `planned`.

---

## 11. Formatting engine (A2)

`format(record, profile)`:

1. Copy `source.docx` → `formatted.docx` (source untouched).
2. Open the copy. `styles.py` ensures named styles matching the profile exist (Title,
   Author, Affiliation, Abstract, Keywords, Heading 1–3, Body, Caption, Reference),
   dropping to raw `styles.element` where the python-docx API is insufficient.
3. `page.py` sets page size, margins, and column count + spacing on every `sectPr`.
4. Walk body elements in order, cross-referenced to `Manuscript.body` by index:
   - **front-matter region** → `frontmatter.py` rebuilds it from the (user-reviewed)
     `Metadata` into freshly styled paragraphs. This is the *only* regeneration and is
     confined to reviewed metadata.
   - **headings** → Heading{level} style + profile numbering.
   - **paragraphs / lists** → Body / list formatting; normalize font family + size,
     **keep inline bold/italic emphasis** within sentences.
   - **captions** → Caption style + ensure the prefix pattern; never invent caption text —
     if missing, leave and flag.
   - **tables** → apply table style + `tblW`; estimated width > text width → LAYOUT
     warning (no destructive resize).
   - **figures** → center; oversize → flag only (no downscale in v1).
   - **references** → Reference style + hanging indent; numbering gaps → flag.
5. Save; return `formatted.docx` path + `ChangeLog` + new issues.

Styles-first, minimal direct run edits (spec §15). Equations, footnotes, hyperlinks, and
fields are untouched. Deterministic at the content level: the same input + profile yields
the same *normalized body text and element counts* every run (raw bytes may differ due to
DOCX-embedded timestamps) — this is what the preservation tests assert.

---

## 12. Validation + preservation + health

`validators.py` re-parses `formatted.docx` and compares it to the original `Manuscript`:

- **DOCUMENT** — both files open, zip intact, `word/document.xml` valid.
- **STRUCTURE** — title / authors / abstract / keywords present; references section
  present if any `[n]` citations exist.
- **FORMATTING** — sampled paragraphs match profile font / size; margins and columns set;
  heading and caption styles applied.
- **CONTENT** — paragraph count original vs formatted within tolerance (front-matter
  rebuild accounted for); normalized body-text hash equal except front-matter → **the
  preservation check**; no empty new sections.
- **REFERENCES** — `references.py` extracts `[n]` citations from the body and `[n]` items
  from the reference list; reports *cited but missing*, *listed but never cited*,
  duplicates, numbering gaps. Warnings only; never fabricates.
- **LAYOUT** — oversize tables / figures, missing captions.

Each issue: severity / category / message / location / suggested_action.

`health.py`: per-category score 0–100 from weighted deductions (error ≫ warning ≫ info,
capped), then a weighted total — Structure .20 · Formatting .20 · References .15 · Figures
& Tables .15 · Metadata .15 · Layout .15. `contributors[]` explains every point lost.
Deterministic; computed only from real issues — never a flat or random number.

`preservation.py` → `{passed, paragraph_delta, text_match, details[]}`. "What Changed →
Content" is empty **iff** `passed`; otherwise "Review required" + details.

---

## 13. Export

- **DOCX** — copy `formatted.docx` → `manuscript_ieee_formatted.docx`, re-open with
  python-docx to verify it loads, then stream with `Content-Disposition`. Failure →
  spec §33 "The formatted document could not be generated."
- **PDF** — `soffice --headless --convert-to pdf --outdir {ws} formatted.docx` with a
  timeout; verify the output exists, starts with `%PDF-`, and has page count ≥ 1 (pypdf);
  stream as `manuscript_ieee_formatted.pdf`. Missing / failed `soffice` → `503
  {error:"pdf_unavailable"}`; the UI keeps DOCX and shows "PDF export unavailable on this
  machine". `SOFFICE_PATH` env, auto-detected from PATH /
  `C:\Program Files\LibreOffice\program\soffice.exe`. `health.capabilities.pdf_export`
  lets the UI pre-disable the control.

---

## 14. Preview

- PDF available → generate + cache + serve the **actual generated PDF** (spec §32),
  rendered via `<iframe>` / pdf.js.
- Not available → a structured HTML preview of the post-format `Manuscript` approximating
  the profile (title / authors / abstract / headings / paragraphs / tables / figure
  placeholders / references), clearly labelled *"Structural preview — install LibreOffice
  for exact page preview."* Never a fake Word render.

---

## 15. Frontend — flow, state, screens

**Processing state machine** (`useDocumentFlow`, one typed reducer): `IDLE, UPLOADING,
UPLOADED, ANALYZING, ANALYZED, REVIEWING, FORMATTING, FORMATTED, VALIDATING, VALIDATED,
EXPORTING, EXPORTED, ERROR`. No scattered status strings (spec §35). `{documentId, state}`
persisted to `localStorage`; refresh resumes via `/analysis`.

**Screens:**

- **Dashboard** — "New manuscript" primary card; "Supported formats" (IEEE available /
  Springer planned); local-processing statement; "Recent" card present with an honest
  empty state ("No manuscripts yet" — history is Slice 2).
- **Upload** — large dropzone ("Drop your manuscript here" / "Upload a .DOCX file to
  begin" / "Browse files"); drag-hover state; inline type / size rejection with a recovery
  action; success → document card (name, size, status) → "Analyze manuscript".
- **Analyze** — `StageList` polls `/analysis` ~400 ms: *Reading document · Extracting
  content · Detecting metadata · Classifying sections · Detecting figures & tables ·
  Detecting references · Preparing structure*. Each flips to done with a **real backend
  count**. No fake timers.
- **Workspace** (product spec §26 layout):

```
┌─────────────────────────────────────────────────────────────┐
│ ManuScript AI · file.docx · [state pill] · Health 92        │
│ [Format ▾ IEEE]  [Validate]  [Preview]  [Export ▾]          │
├─────────┬─────────────────────────────────┬─────────────────┤
│ Outline │ Metadata card (editable, conf%) │ Issues (12)     │
│ tree,   │ Elements list (kind · conf ·    │ [All|Err|Warn|  │
│ click → │  needs-review, inline reclassify)│  Sugg] + Review │
│ scroll  │ Preview tab (PDF / structural)  │  → jumps to loc │
└─────────┴─────────────────────────────────┴─────────────────┘
```

  Mobile: Outline and Issues become slide-over drawers, Main is the default view, primary
  actions in a sticky bottom bar (spec §40).

- **Format picker** — IEEE card (two-column academic layout · structured headings ·
  IEEE-style references); Springer card disabled "Planned". Select → `POST /format` →
  FORMATTING → FORMATTED; health + issues refresh; toast *"IEEE format profile applied"*;
  **What Changed** panel (Formatting changes ✓ list; Content changes "No content removed /
  No paragraphs reordered" only if preservation passed, else "Review required" + details).
- **Validate / Preview / Export** — `POST /validate` refreshes IssuesPanel + HealthCard +
  preservation banner; Preview embeds the real PDF or the labelled structural HTML; Export
  offers DOCX always and PDF only if `capabilities.pdf_export`, real blob downloads,
  success toast, PDF failure inline with DOCX still offered.

**Design system:** Tailwind, restrained — neutral zinc/slate + one indigo accent, subtle
borders, shadows only on raised surfaces, a deliberate type scale, Lucide icons.
`focus-visible` rings, semantic HTML, ARIA on dropzone / dialog / tabs + a live region for
stage and toast announcements, `prefers-reduced-motion` gates transitions. Every screen
has empty / loading / error / success states. This is the "polished from the start" bar;
the *dedicated* polish pass remains Slice 3.

**Client:** typed `api.ts`, `usePolling`, `useToast`, an error boundary, `VITE_API_BASE`
env. No secrets in the frontend.

---

## 16. Config & logging

Backend `.env.example`: `APP_ENV, HOST, PORT, CORS_ORIGINS, MAX_UPLOAD_MB=25,
WORK_DIR=./.workspace, WORKSPACE_TTL_MIN=120, CONFIDENCE_THRESHOLD=0.6, SOFFICE_PATH=,
LOG_LEVEL=INFO, LOG_FORMAT=json`.
Frontend `.env.example`: `VITE_API_BASE=http://localhost:8000`.

Structured logger, one line per pipeline stage (`event, document_id, stage, duration_ms,
counts`) — **never manuscript text**, only counts and hashes. Server logs the stack with an
`error_id`; the client receives a sanitized message.

---

## 17. Testing (Slice 1 bar)

`scripts/gen_samples.py` builds three real `.docx` files (python-docx):

- **basic** — clean IEEE-ish structure.
- **complex** — multi-author with affiliations, 3 tables, 4 captioned figures, 25 `[n]`
  references, equations.
- **messy** — ambiguous title, no "Abstract" heading, inconsistent heading styles, one
  uncited reference, one missing caption.

All three committed to `sample_documents/`.

- **Unit:** metadata heuristics · classifier rules · structure synonyms · profile loader ·
  each formatter sub-step · reference consistency · health math · preservation diff.
- **Integration:** full pipeline per sample — upload → parse → classify → format(IEEE) →
  validate → export docx (+ pdf if soffice) — assert body-text hash preserved, counts
  reconcile, health computed, files openable.
- **API:** every endpoint — happy path + failures (bad file, wrong state, unknown id,
  oversize, pdf-unavailable).
- **Frontend:** vitest for state-machine transitions + api client; smoke tests for
  Dropzone rejection and StageList rendering. (Playwright E2E is Slice 3.)
- **Done bar:** green `pytest` + green `vitest` + one real browser walkthrough with a
  sample document.

---

## 18. Explicitly out of scope for Slice 1

Springer profile · before/after visual comparison screen · SQLite history + dashboard
"recent" data · full Playwright suite · dedicated UI-polish pass · Springer template
variants · figure/table auto-resize (flag only) · equation reformatting (preserve only).

---

## 19. Risks & mitigations

| Risk | Mitigation |
|---|---|
| python-docx cannot express some IEEE styling (e.g. column balancing, small caps) | Drop to raw `w:` XML in `styles.py` / `page.py`; tag anything unachievable `unsupported` in `RULES.md` and surface it honestly, never as "compliant". |
| Front-matter rebuild loses a run of content misclassified as metadata | Preservation check compares full body text minus the front-matter region; any mismatch → "Review required", export still allowed but flagged. Conservative front-matter region detection (only contiguous leading blocks classified title/author/affiliation/abstract/keywords). |
| `soffice` slow or hangs on some inputs | Subprocess timeout + `503`; DOCX export unaffected. |
| Deterministic-output assumption breaks (timestamps in docx) | Preservation/round-trip tests compare normalized body text + counts, not raw bytes. Design doc §11's "identical bytes" claim is relaxed to "identical normalized content". |
| Two-column layout makes structured HTML preview diverge from PDF | Structured preview is explicitly labelled as structural, not pixel-accurate. |

---

## 20. Acceptance for Slice 1

- Backend and frontend both run from documented commands.
- A real DOCX uploads, validates, and rejects non-DOCX / oversize with clear messages.
- Analysis reports real counts through the staged UI.
- Metadata and element classification produce confidence scores; low-confidence items are
  flagged; the user can correct both and corrections persist.
- IEEE profile applies and measurably changes the DOCX (margins, columns, fonts, heading
  styles, reference style).
- Content-preservation check runs and passes on the basic and complex samples; body text
  is not altered.
- Validation produces categorized issues and a health score derived from them.
- Outline, Issue Center, What-Changed, Preview all reflect real backend data.
- DOCX export produces a verified-openable file; PDF export produces a verified `%PDF`
  file when `soffice` is present, and degrades cleanly when it is not.
- `pytest` and `vitest` green; one manual browser walkthrough completed.
- No fake buttons, fake progress, fake previews, or unearned "compliant" claims.

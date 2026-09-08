# Architecture

ManuScript AI is a local, rule-based academic manuscript formatter. A FastAPI
backend runs the document-processing pipeline; a React + TypeScript frontend
drives it. Nothing about a manuscript leaves the machine.

## Repository

```
backend/    FastAPI service + the whole processing pipeline
frontend/   React + Vite + Tailwind workspace
scripts/    gen_samples.py, gen_rules_doc.py, dev + check scripts
sample_documents/  generated sample .docx used by tests and demos
docs/       this file, RULES.md, superpowers/ specs + plans
```

## Backend layers (`backend/app/`)

| Package | Responsibility |
|---|---|
| `api/` | HTTP routers only. Handlers parse, delegate, serialize. Uniform `ApiError` envelope. |
| `schemas/` | Pydantic DTOs — the wire format, kept separate from the domain model. |
| `domain/` | Pure-data model: `Manuscript`, `Block`, `Metadata`/`Field`, `Issue`, `HealthScore`, `AnalysisProgress`. No I/O. |
| `storage/` | `DocumentStore` ABC + `InMemoryDocumentStore` (live session state); `WorkspaceManager` (per-uuid dirs, traversal-safe, TTL sweep); `HistoryStore` ABC + `SqliteHistoryStore` / `InMemoryHistoryStore` — a **log-only** history of each document's lifecycle (no manuscript content), written at every transition. |
| `ingestion/` | Upload validation (magic bytes, ZIP structure, zip-bomb + traversal guards) and intake to a workspace. |
| `parsing/` | `parse_docx` → ordered `ParsedBlock` stream (python-docx + raw OOXML). Read-only; one bad element becomes a warning, not a crash. |
| `extraction/` | Rule-based metadata heuristics (title/authors/affiliations/abstract/keywords) with confidence. |
| `classification/` | Per-block `ElementType` cascade + canonical section detection + outline tree. |
| `analysis/` | `run_analysis` — the staged pipeline; `corrections` — user overrides; `stats` — shared count helper; `comparison` — re-parses the formatted DOCX and diffs it against the in-memory `Manuscript` (structural + metadata, not pixel-perfect). |
| `profiles/` | `PublisherProfile` model + YAML loader; every rule group tagged `implemented / configurable / inferred / unsupported`. `rules_doc` renders `docs/RULES.md`. |
| `formatting/` | The engine: work on a **copy**, `ensure_styles` + `apply_page_layout`, `restyle_body`, `style_tables`, `check_figures`, then `rebuild_frontmatter` (the only regeneration). `run` orchestrates format + validate for the API. |
| `validation/` | Categorized `validate()`, `check_references`, `check_preservation` (body-text hash outside the front-matter boundary), `score` (weighted health). |
| `export/` | `export_docx` (verify openable); `export_pdf` (headless LibreOffice, `%PDF` + page-count check); `preview` structured-HTML fallback. |

## Processing pipeline

```
upload → validate → workspace copy
      → parse (ordered blocks)
      → extract metadata (confidence)
      → classify elements (+ needs_review) → build Manuscript + outline + stats + review issues
      → [user review / corrections]
      → format(profile): copy → styles → page → body restyle → table/figure checks → frontmatter rebuild
      → preservation check → validate → health score
      → preview (PDF or structural HTML)
      → export DOCX / PDF (verified)
      → delete workspace
```

Each stage is independently testable (`backend/tests/{unit,integration,api}`).

## Frontend

- `lib/api.ts` — one typed function per endpoint; `ApiError` normalization.
- `state/useDocumentFlow.ts` — 13-state reducer with an explicit transition table, persisted to `localStorage`.
- `workspace/useWorkspace.ts` — loads `/analysis` + `/outline` + `/elements` + `/health`; `saveMetadata` / `reclassify` / `applyFormat` / `runValidate` re-sync from the backend.
- Screens: Dashboard → Upload → Analyze (staged polling) → Workspace (Review / Preview / What changed, with Outline + Issues + Health).

## Extension points

- **History** — `HistoryStore` is an ABC; `SqliteHistoryStore` is one implementation. Swap it (Postgres, a remote log) without touching the pipeline. It never holds manuscript content.
- **New publisher profile** — add `profiles/data/<id>.yaml`; `list_profiles`, `gen_rules_doc`, and the formatting engine pick it up automatically. IEEE and Springer both ship.
- **ML assist** — classification/extraction are pure functions returning confidences; a model could supplement the rule cascade behind the same interface.

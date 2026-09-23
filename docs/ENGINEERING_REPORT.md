# ManuScript AI — Engineering Report

## 1. What was built

ManuScript AI is a local, rule-based tool that turns an unformatted academic
Word manuscript into a publication-ready document. A user uploads a `.docx`;
the backend parses it, extracts and classifies its structure with confidence
scores, and surfaces everything for review. The user corrects any
low-confidence metadata or misclassified elements, picks a publisher format
profile (IEEE or Springer), and the formatting engine restyles a **copy** of
the document in place — page geometry, typography, headings, tables, figures,
references, and a rebuilt front-matter block from the reviewed metadata. The
result is validated against category-based rules, scored with a deterministic
health score, checked for content preservation (no text lost or reordered),
and can be exported as a verified DOCX or a PDF (via headless LibreOffice).
Every processed document leaves a lightweight history row (no manuscript
content) that drives a dashboard of recent work and a before/after comparison
view.

The entire pipeline runs on the user's machine. No document content is ever
sent to OpenAI, Claude, Gemini, or any other external service — there is no
LLM anywhere in the processing path. All "intelligence" (classification,
metadata extraction, validation) is deterministic, rule-based heuristics with
explicit confidence scores, not model inference.

The product was built in three slices, each independently specified,
planned, implemented, and tested: Slice 1 (core pipeline + IEEE + the
workspace UI), Slice 2 (Springer profile, SQLite history, before/after
comparison, document statistics), and Slice 3 (this report — a full
Playwright end-to-end suite, an accessibility audit with real fixes, a UI
polish pass, and final documentation).

## 2. Final architecture

A FastAPI backend holds the entire document-processing pipeline as a stack of
independently testable layers:

| Layer | Responsibility |
|---|---|
| `api/` | Thin HTTP routers — parse, delegate, serialize. Uniform `ApiError` envelope. |
| `schemas/` | Pydantic DTOs — the wire format, separate from the domain model. |
| `domain/` | Pure-data model (`Manuscript`, `Block`, `Metadata`, `Issue`, `HealthScore`). No I/O. |
| `storage/` | `DocumentStore` (in-process, live session state) + `WorkspaceManager` (per-document working dirs, TTL swept) + `HistoryStore` (SQLite, log-only). |
| `ingestion/` | Upload validation — magic bytes, ZIP structure, zip-bomb and path-traversal guards. |
| `parsing/` | `parse_docx` → an ordered block stream. One bad element becomes a warning, not a crash. |
| `extraction/` | Rule-based metadata heuristics (title/authors/affiliations/abstract/keywords) with confidence. |
| `classification/` | Per-block element-type cascade, canonical section detection, outline tree. |
| `analysis/` | The staged pipeline, user corrections, shared stats, and before/after comparison. |
| `profiles/` | `PublisherProfile` model + YAML loader; every rule group tagged by provenance. |
| `formatting/` | The engine — works on a copy, restyles the existing tree, rebuilds only the front matter. |
| `validation/` | Categorized checks, reference validation, content-preservation check, health score. |
| `export/` | Verified DOCX export, LibreOffice-based PDF export with page count, structural HTML preview fallback. |

A React + TypeScript frontend drives it: a typed API client with normalized
error handling, an explicit 13-state processing state machine persisted to
`localStorage`, and a workspace UI (outline, metadata editor, element list,
issue center, health card, preview, compare, export) built with Tailwind.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full layer-by-layer detail
and extension points.

## 3. Technology stack

| Area | Stack |
|---|---|
| Backend | Python 3.12, FastAPI, python-docx, Pydantic v2, Uvicorn, pypdf, PyYAML, stdlib `sqlite3` |
| PDF | Headless LibreOffice (`soffice`) — local, optional, auto-detected |
| Frontend | React 18, TypeScript, Vite 5, Tailwind 3, lucide-react, React Router 6 |
| Backend tests | pytest — unit, integration, and API layers |
| Frontend tests | vitest + Testing Library — state machine, API client, components |
| End-to-end tests | Playwright (Chromium) + `@axe-core/playwright` for automated accessibility scans |

## 4. Major features

- DOCX ingestion with magic-byte/ZIP validation and zip-bomb/traversal guards; the original file is never modified.
- Rule-based structural analysis: an ordered element stream, confidence-scored metadata extraction, and per-element classification with a manual reclassification path.
- Canonical section detection (Introduction, Related Work, Methods, Results, Discussion, Conclusion, References, Appendix, and common synonyms).
- Two publisher format profiles (IEEE, Springer), each defined as YAML with per-rule-group provenance (`implemented` / `configurable` / `inferred` / `unsupported`).
- A formatting engine that works on a copy of the source document, preserving equations, footnotes, hyperlinks, and field codes untouched.
- Categorized validation with a deterministic 0–100 health score.
- A content-preservation check that hashes body text outside the rebuilt front matter, so "no content changed" is only ever reported when it is actually true.
- Before/after comparison: real structural and metadata deltas between the original and formatted document, not a canned diff.
- DOCX export (verified openable) and PDF export (verified `%PDF-` header + real page count via LibreOffice), with a documented "unavailable" state when LibreOffice isn't present.
- Local, log-only SQLite document history driving a dashboard "recent manuscripts" list — no manuscript content is ever stored in it.
- A workspace UI with an interactive outline, metadata editor, element list, severity-filtered issue center, health breakdown, and document statistics panel.
- Accessibility: semantic landmarks, a real dialog focus trap, keyboard-operable upload, `aria-live` status regions, and WCAG AA text contrast — verified automatically.

## 5. Supported publication profiles

| Profile | Status | Notes |
|---|---|---|
| IEEE | Available | Two-column US Letter, 10 pt Times body, roman-numeral headings, `Abstract—`/`Index Terms—` run-in blocks, bracketed `[n]` references. |
| Springer | Available | One generic single-column A4 profile with decimal-numbered headings and bracketed references. Most rules are `inferred`/`configurable` — it is not a specific journal or LNCS template; template variants can be added as more YAML without engine changes. |

Every rule group in both profiles carries a provenance tag so the product
never overstates what it actually checked — see [`RULES.md`](RULES.md) for
the full, generated table. The formatting engine is entirely profile-driven:
adding a profile means adding a YAML file, not writing new engine code.

## 6. Document-processing pipeline

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

Each stage is independently testable and covered at the unit, integration,
and API level; the Playwright suite added in this slice exercises the whole
chain through the real browser and the real API, end to end.

## 7. Validation capabilities

Validation runs across six weighted categories — Structure (0.20), Formatting
(0.20), References (0.15), Figures & Tables (0.15), Metadata (0.15), and
Layout (0.15) — with per-issue penalties (error 25, warning 10, info 4) capped
at a 60-point deduction per category, so no single category can ever zero out
the score on its own. The health score is entirely deterministic: the same
issues always produce the same number, and every point lost traces back to a
real, listed issue. Reference formatting is checked against the active
profile's citation style; content preservation is checked by hashing body
text outside the rebuilt front-matter region and comparing it against the
original.

## 8. Export capabilities

- **DOCX** — the formatted document is verified to actually open with
  python-docx before being returned; nothing is served that isn't a valid
  Word file.
- **PDF** — produced via headless LibreOffice (`soffice --headless
  --convert-to pdf`), then verified by checking the `%PDF-` file signature and
  reading a real page count with `pypdf`. When LibreOffice isn't reachable on
  the host, the API returns a clear `pdf_unavailable` response and the UI
  shows a disabled button with an explanatory message — never a silent
  failure or a fake success.
- **Preview** — a rendered PDF when available, otherwise a structural HTML
  fallback, so the workspace always has something to show.

## 9. Test results

All suites pass on the final `master`-bound state of this branch:

| Suite | Count | Result |
|---|---|---|
| Backend (pytest: unit + integration + API) | 157 tests | ✅ all passing |
| Frontend (vitest: 8 test files) | 46 tests | ✅ all passing |
| End-to-end (Playwright, Chromium, 10 spec files) | 35 tests | ✅ all passing |
| Linting / formatting | ruff, ruff-format, tsc | ✅ clean |

`bash scripts/check.sh` runs all of the above in one command and is the
project's single source of truth for "is this green."

## 10. Playwright results

Ten spec files under `frontend/e2e/`, run against the real application
(real backend, real browser, no mocking), covering every flow in the original
QA checklist:

| Spec file | Covers |
|---|---|
| `smoke.spec.ts` | Dashboard loads with a clean console. |
| `dashboard.spec.ts` | Dashboard content, format list, navigation, empty recents state. |
| `upload.spec.ts` | Valid upload (browse + drag-and-drop), invalid-file rejection with recovery. |
| `analysis.spec.ts` | Analysis completion, outline/issues appear, metadata edit + save, element reclassification. |
| `formatting.spec.ts` | IEEE apply, validation, preview, switch to Springer, Compare tab with real deltas. |
| `export.spec.ts` | Real DOCX download; PDF download (or the documented unavailable state, decided at runtime from `/api/health`). |
| `resilience.spec.ts` | Reload mid-workflow, ended-session recovery, simulated backend outage, mobile-viewport layout. |
| `a11y.spec.ts` | Automated axe scans on every major screen/tab, keyboard-only upload, dialog focus containment. |
| `theme.spec.ts` | Dark by default with the silk canvas animating (pixel fingerprint changes between frames); a single still frame under reduced motion; the header toggle switches to a lighter, still-flowing silk and persists across reloads; both silks hold a still frame under reduced motion; the light theme passes axe; the flow button opens the upload screen. |
| `morph.spec.ts` | The morphing UI: flow rail advances with no console errors; the shared glass surface and the format dialog animate through intermediate frames (measured per animation frame); action buttons pass through pending/success; reduced motion disables the surface animation. |

**One real bug was found and fixed via the mandated reproduce → understand →
root cause → fix → restart → retest → regress loop**, plus three more caught
by the same automated suite while investigating it:

1. The format-picker dialog let `Tab` escape to elements behind the overlay.
   Fixed by adding a real focus trap to the shared `Dialog` component.
2. The upload dropzone wrapped a real, independently focusable
   `<input type="file">` inside a custom `role="button"` div with manual
   Enter/Space handling — an axe `nested-interactive` violation, and the
   input itself had no accessible name. Replaced the custom pattern with a
   native `<label htmlFor>`/`<input id>` association, which is simpler (no
   keyboard handler needed) and fixes both problems at once.
3. The Abstract textarea in the metadata editor had no label, `aria-label`,
   or placeholder, so it had no accessible name at all.
4. `text-zinc-400` — used throughout the app for secondary/muted text —
   fails WCAG AA contrast (2.45:1–4.39:1 measured, against a 4.5:1
   requirement) on the app's light backgrounds. This had been present since
   Slice 1; every real text usage (not decorative, `aria-hidden` icons) was
   bumped to `zinc-500`/`zinc-600` depending on background.

A separate, unrelated CORS gap was also found and fixed while building the
suite itself: the isolated E2E frontend origin wasn't in the backend's
`CORS_ORIGINS`, so `fetch()` calls were silently rejected and the app's
"loading" and "empty" states were indistinguishable — a good example of why
testing against a real backend, not a mock, catches configuration bugs that
component tests cannot.

## 11. Known limitations

- Heading auto-numbering (e.g. `I.`, `A.`) and run-in level-3 headings are
  **not** injected by the engine — only typography, alignment, spacing, and an
  optional upper-case transform are applied.
- Oversize tables and figures are **flagged**, never resized.
- Equations, footnotes, hyperlinks, and field codes are preserved as-is, not
  reformatted.
- The `DocumentStore` is in-process: a document's live working session is
  lost when the backend restarts (its history row survives; re-upload to
  work on it again). Working files persist on disk until the TTL sweep.
- Springer is one generic profile, not per-journal templates.
- The Playwright suite covers Chromium only — no Firefox/WebKit coverage.
- There is no CI pipeline in this repository; `scripts/check.sh` is run
  manually.

## 12. How to run the application

```bash
# Setup (see README.md for full detail)
cd backend && uv venv .venv --python 3.12 && uv pip install -r requirements-dev.txt && cp .env.example .env
cd ../frontend && npm install && cp .env.example .env

# Run both servers
bash scripts/dev.sh          # frontend :5173, backend :8000

# Run every check
bash scripts/check.sh        # ruff + pytest + tsc + vitest + playwright
```

API docs are served at `http://localhost:8000/docs`.

## 13. Recommended future improvements

- Cross-browser Playwright coverage (Firefox, WebKit) if the product ever
  needs to support browsers beyond Chromium-based ones.
- A CI pipeline that runs `scripts/check.sh` on every push, so the green bar
  this report describes is enforced automatically rather than by convention.
- Full session persistence so a document's workspace survives a backend
  restart, removing the current re-upload-after-restart limitation.
- Additional publisher profiles and Springer template variants as YAML,
  including a way for the user to pick a specific journal variant.
- Optional ML-assisted classification/extraction behind the existing
  confidence-returning interfaces, without changing the rule-based fallback.

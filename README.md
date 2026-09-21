# ManuScript AI

Turn an unformatted academic Word manuscript into a publication-ready document —
locally, with no cloud services and no LLM APIs. Upload a `.docx`, review the
detected structure, apply a publisher format profile, validate the result, and
export a verified DOCX or PDF.

> **Privacy:** manuscript content is processed entirely on your machine. Nothing
> is uploaded to OpenAI, Claude, Gemini, or any external document service. The
> processing pipeline needs no internet connection.

## Features

- **DOCX ingestion** — drag-and-drop or browse; magic-byte + ZIP-structure
  validation, zip-bomb and path-traversal guards, size limit. The original file
  is never modified.
- **Rule-based analysis** — an ordered element stream, metadata heuristics
  (title / authors / affiliations / abstract / keywords) and per-element
  classification, each with a confidence score. Low-confidence items are flagged.
- **Canonical structure detection** — Introduction, Related Work, Methods,
  Results, Discussion, Conclusion, References, Appendix, plus common synonyms.
- **Publisher profiles** — configurable YAML; every rule tagged
  *implemented / configurable / inferred / unsupported* (see `docs/RULES.md`).
  **IEEE** and **Springer** both ship as available profiles.
- **Formatting engine** — works on a copy: named styles, page geometry and
  columns, body restyle (emphasis preserved), table/figure checks, and a
  front-matter rebuild from your reviewed metadata.
- **Validation + health score** — DOCUMENT / STRUCTURE / FORMATTING / CONTENT /
  REFERENCES / LAYOUT checks; a 0–100 health score computed from real issues.
- **Content-preservation check** — body text is hashed before and after; the
  "What changed" panel only says *no content changed* when that actually holds.
- **Export** — verified DOCX; PDF via headless LibreOffice when available, with a
  clear "unavailable" state otherwise. Structural HTML preview as a fallback.
- **Workspace** — interactive outline, metadata editor, element list with inline
  reclassification, issue center with severity filters, before/after comparison
  (structural + metadata deltas), and a document-statistics panel.
- **Local document history** — a SQLite log (`./.workspace/history.db`) of every
  document's lifecycle: filename, date, profile, state, health, counts. **No
  manuscript content is stored.** Drives the dashboard "recent manuscripts" list;
  rows are deletable. Disable with `HISTORY_ENABLED=false`.
- **Accessibility** — semantic landmarks, keyboard-operable upload and dialogs
  (with a real focus trap), visible focus rings, `aria-live` status/toast
  regions, and WCAG AA text contrast — verified by an automated axe scan plus
  a manual keyboard-navigation pass in the Playwright suite.
- **Morphing interface** — one glass surface follows you through the flow: the
  dropzone morphs into the file card, the analysis card, and the workspace header;
  a progress rail's pill slides between Upload · Analyze · Review · Format · Export;
  action buttons morph through pending → success → error; and the Apply-format
  dialog expands out of its button. All motion honours `prefers-reduced-motion`,
  and a Playwright test measures the morph frame by frame.
- **Dark-first liquid glass** — a full-black theme (default) with an animated silk
  background behind frosted-glass panels, and a light theme behind a header toggle
  (persisted, applied before first paint so there is no flash). The silk renders on a
  small canvas, slows itself down if the page's frame rate sags, and draws a single
  still frame under `prefers-reduced-motion`. Both themes pass the axe scan.

The product never claims a document is "IEEE compliant" — it reports *"IEEE
format profile applied"* and *"IEEE validation checks passed"* for the checks it
actually ran.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). In short: a FastAPI backend
holding a layered, independently-testable pipeline (`ingestion → parsing →
extraction → classification → analysis → formatting → validation → export`), and
a React + TypeScript + Tailwind frontend with a typed API client and an explicit
processing state machine.

## Technology

| Area | Stack |
|---|---|
| Backend | Python 3.12, FastAPI, python-docx, Pydantic v2, Uvicorn, pypdf, PyYAML |
| PDF | headless LibreOffice (`soffice`) — local, optional |
| Frontend | React 18, TypeScript, Vite 5, Tailwind 3, motion, class-variance-authority, lucide-react |
| Tests | pytest (unit / integration / API), vitest (state machine, api client, components), Playwright + axe-core (end-to-end, accessibility) |

## Setup

Requires **Python 3.12** and **Node 20+**. On Windows, if `python` resolves to a
bundled interpreter, create the venv with an explicit interpreter (e.g. `py -3.12`
or [`uv`](https://docs.astral.sh/uv/)).

```bash
# Backend
cd backend
python -m venv .venv                      # or: uv venv .venv --python 3.12
.venv/Scripts/python -m pip install -r requirements-dev.txt   # uv pip install ... on uv
cp .env.example .env

# Frontend
cd ../frontend
npm install
cp .env.example .env
```

Optional, for real PDF export: install
[LibreOffice](https://www.libreoffice.org/). It is auto-detected; set
`SOFFICE_PATH` in `backend/.env` if it is not on `PATH`.

## Running

```bash
# Both servers (from the repo root)
bash scripts/dev.sh          # or: pwsh scripts/dev.ps1
```

Or separately:

```bash
cd backend  && .venv/Scripts/python -m uvicorn app.main:app --reload   # http://localhost:8000
cd frontend && npm run dev                                             # http://localhost:5173
```

API docs: `http://localhost:8000/docs`.

## Tests

```bash
bash scripts/check.sh        # ruff + pytest + tsc + vitest + playwright

# or individually
cd backend  && .venv/Scripts/python -m pytest
cd frontend && npm test && npx tsc -b --noEmit
cd frontend && npx playwright test    # end-to-end (Chromium) — starts both servers automatically
```

The Playwright suite (`frontend/e2e/`) drives the real application against an
isolated backend (its own port, a temp `WORK_DIR`/`HISTORY_DB`) — no mocking.
It covers upload, analysis, metadata review, IEEE/Springer formatting,
validation, preview, comparison, export, error recovery, responsive layouts,
and an automated accessibility scan (`@axe-core/playwright`) on every major
screen.

## Sample documents

```bash
python scripts/gen_samples.py     # writes sample_documents/sample_{basic,complex,messy}.docx
python scripts/gen_rules_doc.py   # regenerates docs/RULES.md from the profile YAML
```

## Supported publication formats

| Profile | Status | Notes |
|---|---|---|
| IEEE | Available | Two-column US Letter, 10 pt Times body, roman-numeral headings, `Abstract—` / `Index Terms—` blocks, bracketed `[n]` references. |
| Springer | Available | One generic single-column A4 profile with decimal-numbered headings and bracketed references. **Not** a specific journal or LNCS template — most rules are marked `inferred`/`configurable`; template variants can be added as more YAML. |

See `docs/RULES.md` for every rule's provenance in both profiles.

## Known limitations

- Heading auto-numbering (e.g. `I.`, `A.`) and run-in level-3 headings are
  **not** injected by the engine — only typography, alignment, spacing, and an
  optional upper-case transform are applied.
- Oversize tables and figures are **flagged**, never resized.
- Equations, footnotes, hyperlinks, and field codes are preserved as-is, not
  reformatted.
- The `DocumentStore` is in-process: a document's live working session is lost when
  the backend restarts (its history row survives; re-upload to work on it again).
  Working files persist on disk until the TTL sweep.
- Springer is one generic profile, not per-journal templates.

## Future extension points

- Additional publisher profiles (and Springer template variants) as YAML.
- Full session persistence so a document's workspace survives a backend restart.
- Optional ML assist behind the existing confidence-returning interfaces.

## Credits

Some UI components were retrieved from [21st.dev](https://21st.dev) with the `21st` CLI and
adapted (see `docs/superpowers/specs/2026-09-20-ui-21st-restyle-design.md` for what changed):

- `@ibelick/morphing-dialog` → `frontend/src/components/ui/MorphingDialog.tsx`
- `@ddoemonn/loading-button` → `frontend/src/components/ui/MorphButton.tsx`
- a flow-arrow button → `frontend/src/components/ui/FlowButton.tsx` (theme-token colors)
- a silk canvas background → `frontend/src/components/layout/SilkBackground.tsx`
  (quarter-resolution, adaptive frame rate, still frame under reduced motion)

The rest of the restyle (glass surfaces, flow rail, animated tabs, dropzone) is written
in-repo in the same visual language.

## License

MIT — see [`LICENSE`](LICENSE).

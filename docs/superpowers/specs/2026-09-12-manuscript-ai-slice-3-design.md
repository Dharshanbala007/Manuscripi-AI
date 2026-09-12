# ManuScript AI — Slice 3 Design

**Date:** 2026-09-12
**Status:** Approved
**Builds on:** Slices 1 and 2 (merged to `master`). QA, hardening, and polish — no new
product features.

## 0. Scope

A permanent Playwright E2E suite covering the flows in spec §44, a bug-fix loop for
anything it finds, an accessibility audit (automated + manual), a dedicated UI-polish
pass, a final regression run, and updated README + a new engineering report. Confirmed
decisions from brainstorming: a **committed** `@playwright/test` suite (not a one-off
manual pass), **Chromium only**, and **automated axe scans + manual keyboard/focus
checks** for accessibility.

---

## 1. Playwright suite architecture

- `frontend/e2e/` — new directory. New devDependencies: `@playwright/test`,
  `@axe-core/playwright`.
- `frontend/playwright.config.ts`: `testDir: "e2e"`, Chromium project only,
  `baseURL` from `E2E_BASE_URL` env var (default `http://localhost:5173`), a
  `webServer` array that starts the backend (`.venv/Scripts/python.exe -m uvicorn
  app.main:app --port 8010`) and the frontend (`vite preview --port 5173`, pointed at
  that backend via `VITE_API_BASE`) and waits on both ports before tests run — so
  `npm run test:e2e` is a single command, matching `npm test` / `pytest`.
- The E2E backend runs against an **isolated workspace**: `WORK_DIR` and `HISTORY_DB`
  set to a temp directory for the run (same isolation pattern as
  `backend/tests/conftest.py`), so E2E runs never touch a developer's real
  `.workspace/history.db` and are safe to re-run.
- Fixtures: reuse the three committed samples (`sample_documents/sample_basic.docx`,
  `sample_complex.docx`, `sample_messy.docx`) plus one new tiny fixture,
  `frontend/e2e/fixtures/not-a-docx.txt`, for the invalid-upload flow.
- `package.json` gains `"test:e2e": "playwright test"`.

## 2. Test coverage

One spec file per functional area, together covering all 24 flows in spec §44:

| File | Flows covered |
|---|---|
| `dashboard.spec.ts` | app loads, dashboard renders, recents list, navigation |
| `upload.spec.ts` | drag/drop upload, browse upload, invalid file rejected, valid DOCX accepted |
| `analysis.spec.ts` | analysis starts + completes (polling), metadata/outline/issues appear, metadata is editable, an element can be reclassified |
| `formatting.spec.ts` | IEEE selectable, Springer selectable, format applies, validation runs, preview loads, Compare tab shows real deltas |
| `export.spec.ts` | DOCX export downloads and is a valid docx; PDF export downloads when LibreOffice is available, otherwise the documented "unavailable" state is asserted instead of failing the run |
| `resilience.spec.ts` | reload mid-flow, ended-session recovery message, a simulated network failure surfaces the existing error UI, responsive layouts at mobile/tablet/desktop viewports |
| `a11y.spec.ts` | keyboard-only navigation through upload → review → format → export; axe scan on Dashboard, Upload, and each Workspace tab asserting zero serious/critical violations |

Each spec drives the real running app end-to-end (no component mocking) — uploads an
actual sample file, waits on real analysis, asserts on real DOM state.

## 3. Bug-fix loop

Any failing assertion or discovered defect follows spec §45 exactly: reproduce under
Playwright → understand → identify root cause in the relevant backend/frontend layer →
fix → restart the affected dev server → retest the one spec → re-run the **full** E2E
suite plus `bash scripts/check.sh` before moving to the next spec file. No fix is
considered done until the full regression is green again. Bugs and fixes are not
tracked in a separate document — they're visible in the commit history for this slice.

## 4. Accessibility audit

- **Automated:** `a11y.spec.ts` runs `@axe-core/playwright` against Dashboard, Upload,
  and the Workspace (Review, Preview, Compare tabs), failing the test on any `serious`
  or `critical` violation.
- **Manual:** during the same pass, tab-only navigation through the primary flow
  (upload → review → apply format → export), checking visible focus rings, that the
  upload control is keyboard-operable, and that any modal/dialog traps focus. Anything
  found is fixed the same way as any other bug (§3).

## 5. UI polish pass

Only after the suite and audit are green. A targeted refinement of existing
`frontend/src/components/` — buttons, cards, loading/empty/error/success states,
hover/transition states — per spec §64's "modern, professional, fluid, minimal,
trustworthy" language. This is CSS/class-level refinement of components that already
exist, not a redesign, new component library, or new dependency. Re-run
`npm run test:e2e` after, since visual changes can shift selectors/timings.

## 6. Final regression + deliverables

- `scripts/check.sh` gains a fourth step: `frontend: playwright` (after `vitest`),
  running `npm run test:e2e`.
- `README.md`: add the `npm run test:e2e` command under Tests; update the feature list
  if the polish pass changes any user-visible behavior.
- New `docs/ENGINEERING_REPORT.md` covering the 13 points in spec §67: what was built,
  final architecture, technology stack, major features, supported publication profiles,
  document-processing pipeline, validation capabilities, export capabilities, test
  results (unit/integration/API + Playwright), known limitations, how to run the
  application, recommended future improvements.

## 7. Out of scope for Slice 3

New backend endpoints or domain features · changes to the formatting/validation
engines beyond fixing genuine bugs the suite finds · cross-browser testing
(Firefox/WebKit) · CI pipeline configuration (no CI system exists in this repo today).
If the suite surfaces something larger than a bug fix, it will be flagged rather than
silently built.

## 8. Acceptance

- `npx playwright test` (Chromium) passes for all seven spec files against the real
  running app, using the real sample documents.
- The axe scan reports zero serious/critical violations on Dashboard, Upload, and
  Workspace; manual keyboard-navigation checks pass.
- `bash scripts/check.sh` (ruff, ruff-format, pytest, tsc, vitest, playwright) is green
  end to end after the polish pass.
- `README.md` and `docs/ENGINEERING_REPORT.md` are current and accurate — no
  unsupported compliance claims, consistent with spec §65.

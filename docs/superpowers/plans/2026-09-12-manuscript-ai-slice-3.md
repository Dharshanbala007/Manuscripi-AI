# ManuScript AI — Slice 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a permanent Playwright E2E suite covering every flow in spec §44, fix any bug it finds via the mandated bug-fix loop, run an accessibility audit, do a targeted UI-polish pass, and produce the final README + engineering report.

**Architecture:** `frontend/e2e/` holds one `@playwright/test` spec file per functional area, driven by a shared `fixtures.ts` helper (upload+analyze, drag-drop simulation). `playwright.config.ts` boots an **isolated** backend (dedicated port, temp `WORK_DIR`/`HISTORY_DB`) and the frontend dev server as a single `webServer` array, so `npm run test:e2e` is one command against the real app — no mocking.

**Tech Stack:** `@playwright/test` (Chromium project only), `@axe-core/playwright` for automated accessibility scans. No new backend dependencies.

**Spec:** [docs/superpowers/specs/2026-09-12-manuscript-ai-slice-3-design.md](../specs/2026-09-12-manuscript-ai-slice-3-design.md)

## Global Constraints

- Chromium only (no Firefox/WebKit) — confirmed decision.
- The E2E suite is committed and runs via `npm run test:e2e`; it is not a one-off manual pass.
- The E2E backend must never touch a developer's real `backend/.workspace/history.db` — always an isolated temp `WORK_DIR`/`HISTORY_DB`.
- No new backend endpoints or domain features. Fixes are limited to genuine bugs the suite finds.
- Every bug found follows: reproduce → understand → root cause → fix → restart affected service → retest → full regression (`npm run test:e2e` + `bash scripts/check.sh`) before moving to the next task.
- Product language stays accurate — no unsupported compliance claims (spec §65).

---

### Task 1: Playwright scaffold, isolated dual-server config, smoke test

**Files:**
- Modify: `frontend/package.json` (add devDependencies + `test:e2e` script)
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/fixtures.ts`
- Create: `frontend/e2e/fixtures/not-a-docx.txt`
- Create: `frontend/e2e/smoke.spec.ts`
- Modify: `.gitignore` (Playwright artifacts)
- Modify: `scripts/check.sh` (add the e2e step)

**Interfaces:**
- Produces (used by every later task): `frontend/e2e/fixtures.ts` exports `SAMPLES: string` (absolute path to `sample_documents/`), `uploadAndAnalyze(page: Page, filename: string): Promise<string>` (returns the new document id, leaves the browser on `/workspace/:id` with metadata visible), `simulateFileDrop(page: Page, selector: string, filePath: string, fileName: string, mimeType: string): Promise<void>`, and re-exports `test`/`expect` from `@playwright/test`.
- Consumes: nothing (first task).

- [ ] **Step 1: Install Playwright and axe**

```bash
cd frontend
npm install -D @playwright/test @axe-core/playwright
npx playwright install chromium
```

- [ ] **Step 2: Add the `test:e2e` script**

Edit `frontend/package.json`, in `"scripts"` add (after `"test:watch"`):

```json
    "test:e2e": "playwright test"
```

- [ ] **Step 3: Write `frontend/playwright.config.ts`**

```ts
import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";

const FRONTEND_PORT = 5183;
const BACKEND_PORT = 8010;
const ROOT = path.resolve(__dirname, "..");
const BACKEND_DIR = path.join(ROOT, "backend");

function pythonExe(): string {
  const winPy = path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe");
  return existsSync(winPy) ? winPy : path.join(BACKEND_DIR, ".venv", "bin", "python");
}

const workDir = path.join(os.tmpdir(), `manuscript-ai-e2e-${process.pid}`);

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `"${pythonExe()}" -m uvicorn app.main:app --port ${BACKEND_PORT}`,
      cwd: BACKEND_DIR,
      url: `http://localhost:${BACKEND_PORT}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        WORK_DIR: path.join(workDir, "workspace"),
        HISTORY_DB: path.join(workDir, "history.db"),
      },
    },
    {
      command: `npm run dev -- --port ${FRONTEND_PORT} --strictPort`,
      cwd: __dirname,
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        VITE_API_BASE: `http://localhost:${BACKEND_PORT}`,
      },
    },
  ],
});
```

- [ ] **Step 4: Write `frontend/e2e/fixtures.ts`**

```ts
import { test as base, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";

export const test = base;
export { expect };

export const SAMPLES = path.resolve(__dirname, "../../sample_documents");

export async function uploadAndAnalyze(page: Page, filename: string): Promise<string> {
  await page.goto("/upload");
  await page.getByTestId("dropzone-input").setInputFiles(path.join(SAMPLES, filename));
  await page.getByRole("button", { name: /Analyse manuscript/i }).click();
  await page.waitForURL(/\/workspace\//, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: "Metadata" })).toBeVisible({ timeout: 15_000 });
  const id = new URL(page.url()).pathname.split("/workspace/")[1];
  if (!id) throw new Error(`Could not extract document id from ${page.url()}`);
  return id;
}

export async function simulateFileDrop(
  page: Page,
  selector: string,
  filePath: string,
  fileName: string,
  mimeType: string,
): Promise<void> {
  const base64 = readFileSync(filePath).toString("base64");
  const dataTransfer = await page.evaluateHandle(
    async ({ base64, fileName, mimeType }) => {
      const binary = atob(base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const dt = new DataTransfer();
      dt.items.add(new File([bytes], fileName, { type: mimeType }));
      return dt;
    },
    { base64, fileName, mimeType },
  );
  await page.dispatchEvent(selector, "drop", { dataTransfer });
}
```

- [ ] **Step 5: Add the invalid-file fixture**

Create `frontend/e2e/fixtures/not-a-docx.txt` containing exactly:

```
This is not a Word document.
```

- [ ] **Step 6: Write the smoke test**

```ts
// frontend/e2e/smoke.spec.ts
import { expect, test } from "./fixtures";

test("dashboard loads with no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(err.message));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /publication-ready document/i })).toBeVisible();
  await expect(page.getByRole("link", { name: "ManuScript AI" })).toBeVisible();
  expect(errors).toEqual([]);
});
```

- [ ] **Step 7: Free ports 5183/8010, then run the smoke test**

Ensure nothing else is bound to 5183 or 8010 (these are dedicated E2E ports, separate from the normal dev ports 5173/8000):

```bash
netstat -ano | grep -E ":(5183|8010)" | grep LISTEN || echo "ports free"
```

Run:

```bash
cd frontend && npx playwright test smoke.spec.ts
```

Expected: 1 passed. If the backend `webServer` fails to become healthy, check `python -m uvicorn` starts cleanly from `backend/` with `WORK_DIR`/`HISTORY_DB` pointed at a fresh temp dir (this mirrors the isolation pattern already used in `backend/tests/conftest.py`).

- [ ] **Step 8: Wire into `.gitignore` and `scripts/check.sh`**

Append to `.gitignore` (after the `# Test tooling` block):

```
frontend/playwright-report/
frontend/test-results/
```

Edit `scripts/check.sh`, after the `frontend: vitest` block, add:

```bash
echo "== frontend: playwright e2e =="
( cd "$ROOT/frontend" && npx playwright test )
```

Run `bash scripts/check.sh` end to end once to confirm the new step executes (it will only run `smoke.spec.ts` at this point).

- [ ] **Step 9: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/playwright.config.ts \
  frontend/e2e/fixtures.ts frontend/e2e/fixtures/not-a-docx.txt frontend/e2e/smoke.spec.ts \
  .gitignore scripts/check.sh
git commit -m "test(e2e): Playwright scaffold with isolated dual-server config + smoke test"
```

---

### Task 2: Dashboard flows (`dashboard.spec.ts`)

**Files:**
- Create: `frontend/e2e/dashboard.spec.ts`

**Interfaces:**
- Consumes: `test`, `expect` from `./fixtures`.
- Produces: nothing consumed by later tasks (dashboard is a leaf flow).

Covers spec §44 flows 1–3, 20 (app opens, dashboard loads, upload page loads via navigation, navigation works) and the Slice 2 recents list on a clean history.

- [ ] **Step 1: Write the spec**

```ts
// frontend/e2e/dashboard.spec.ts
import { expect, test } from "./fixtures";

test.describe("Dashboard", () => {
  test("loads, shows both format profiles, and navigates to upload", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /publication-ready document/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Supported publication formats" })).toBeVisible();
    await expect(page.getByText("IEEE").first()).toBeVisible();
    await expect(page.getByText("Springer").first()).toBeVisible();
    await expect(page.getByText("Available").first()).toBeVisible();

    await page.getByRole("button", { name: /New manuscript/i }).click();
    await expect(page).toHaveURL(/\/upload$/);
    await expect(page.getByRole("heading", { name: "Upload a manuscript" })).toBeVisible();

    await page.getByRole("link", { name: /Back to dashboard/i }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test("shows an empty recents state before any document exists", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Recent manuscripts" })).toBeVisible();
  });
});
```

- [ ] **Step 2: Run it**

```bash
cd frontend && npx playwright test dashboard.spec.ts
```

Expected: 2 passed. If a test fails, follow the bug-fix loop (§45): reproduce with `npx playwright test dashboard.spec.ts --headed`, identify whether the failure is a real product bug or an incorrect selector, fix the root cause (product code, never the test, unless the test's expectation was factually wrong), restart the affected `webServer` process by re-running the command, retest, then re-run the full `npx playwright test` before continuing.

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/dashboard.spec.ts
git commit -m "test(e2e): dashboard load, format list, and navigation"
```

---

### Task 3: Upload flows (`upload.spec.ts`)

**Files:**
- Create: `frontend/e2e/upload.spec.ts`

**Interfaces:**
- Consumes: `test`, `expect`, `SAMPLES`, `simulateFileDrop` from `./fixtures`.

Covers spec §44 flows 4–6 (drag/drop, browse upload, invalid file handling, valid DOCX accepted).

- [ ] **Step 1: Write the spec**

```ts
// frontend/e2e/upload.spec.ts
import path from "node:path";
import { expect, test, SAMPLES, simulateFileDrop } from "./fixtures";

test.describe("Upload", () => {
  test("rejects a non-docx file with an inline, recoverable error", async ({ page }) => {
    await page.goto("/upload");
    await page
      .getByTestId("dropzone-input")
      .setInputFiles(path.resolve(__dirname, "fixtures/not-a-docx.txt"));

    const alert = page.getByRole("alert");
    await expect(alert).toContainText(/not a \.docx file/i);
    await expect(page.getByRole("button", { name: /Try another file/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Analyse manuscript/i })).toHaveCount(0);
  });

  test("accepts a valid .docx via the file browser", async ({ page }) => {
    await page.goto("/upload");
    await page.getByTestId("dropzone-input").setInputFiles(path.join(SAMPLES, "sample_basic.docx"));

    await expect(page.getByText("sample_basic.docx")).toBeVisible();
    await expect(page.getByRole("button", { name: /Analyse manuscript/i })).toBeEnabled();
  });

  test("accepts a valid .docx via drag and drop", async ({ page }) => {
    await page.goto("/upload");
    await simulateFileDrop(
      page,
      '[role="button"][aria-label*="Drop your manuscript"]',
      path.join(SAMPLES, "sample_complex.docx"),
      "sample_complex.docx",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    );

    await expect(page.getByText("sample_complex.docx")).toBeVisible({ timeout: 10_000 });
  });
});
```

- [ ] **Step 2: Run it, apply the bug-fix loop on any failure, then commit**

```bash
cd frontend && npx playwright test upload.spec.ts
```

```bash
git add frontend/e2e/upload.spec.ts
git commit -m "test(e2e): upload — valid/invalid files, drag-and-drop"
```

---

### Task 4: Analysis + review flows (`analysis.spec.ts`)

**Files:**
- Create: `frontend/e2e/analysis.spec.ts`

**Interfaces:**
- Consumes: `test`, `expect`, `uploadAndAnalyze` from `./fixtures`.

Covers spec §44 flows 7–12 (analysis starts, completes, metadata appears, metadata editable, outline appears, issues appear) plus element reclassification.

- [ ] **Step 1: Write the spec**

```ts
// frontend/e2e/analysis.spec.ts
import { expect, test, uploadAndAnalyze } from "./fixtures";

test.describe("Analysis and review", () => {
  test("completes analysis and shows metadata, outline, and issues", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_complex.docx");

    await expect(page.getByRole("navigation", { name: "Document outline" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /issues? found/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Detected elements" })).toBeVisible();
  });

  test("lets the user edit and save metadata", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");

    const titleInput = page.getByPlaceholder("Manuscript title");
    await expect(titleInput).toBeVisible();
    await titleInput.fill("A Playwright-Verified Title");

    const save = page.getByRole("button", { name: "Save changes" });
    await expect(save).toBeEnabled();
    await save.click();
    await expect(save).toBeDisabled();

    await page.reload();
    await expect(page.getByPlaceholder("Manuscript title")).toHaveValue(
      "A Playwright-Verified Title",
    );
  });

  test("lets the user reclassify a detected element", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");

    const firstSelect = page.getByLabel("Reclassify element").first();
    await firstSelect.selectOption("paragraph");
    await expect(firstSelect).toHaveValue("paragraph");
  });
});
```

- [ ] **Step 2: Run it, apply the bug-fix loop on any failure, then commit**

```bash
cd frontend && npx playwright test analysis.spec.ts
```

```bash
git add frontend/e2e/analysis.spec.ts
git commit -m "test(e2e): analysis completion, metadata editing, reclassification"
```

---

### Task 5: Formatting, validation, preview, compare (`formatting.spec.ts`)

**Files:**
- Create: `frontend/e2e/formatting.spec.ts`

**Interfaces:**
- Consumes: `test`, `expect`, `uploadAndAnalyze` from `./fixtures`.

Covers spec §44 flows 13–16 (IEEE selectable, formatting applies, validation runs, preview loads) plus Springer + the Slice 2 Compare tab. Uses `test.describe.configure({ mode: "serial" })` so the four steps share one uploaded document instead of re-running the pipeline four times.

- [ ] **Step 1: Write the spec**

```ts
// frontend/e2e/formatting.spec.ts
import { expect, test, uploadAndAnalyze } from "./fixtures";

test.describe("Formatting, validation, preview, compare", () => {
  test.describe.configure({ mode: "serial" });

  test("applies the IEEE format profile", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_complex.docx");

    await page.getByRole("button", { name: "Apply format" }).click();
    const dialog = page.getByRole("dialog", { name: "Choose a publication format" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: /IEEE/ }).click();
    await dialog.getByRole("button", { name: "Apply format" }).click();

    await expect(dialog).toBeHidden();
    await expect(page.getByText("IEEE profile applied")).toBeVisible();
    await expect(page.getByText("Content preservation check passed")).toBeVisible({
      timeout: 15_000,
    });
  });

  test("runs validation and shows a health score", async ({ page, context }) => {
    await page.goto("/"); // continue on the same worker; re-open the doc via reload below is unnecessary
    // The document from the previous serial test is still the last one uploaded; revisit it.
    const recentLink = page.getByText("sample_complex.docx").first();
    await recentLink.click();
    await expect(page.getByRole("heading", { name: "Manuscript health" })).toBeVisible();

    await page.getByRole("button", { name: "Validate" }).click();
    await expect(page.getByText(/^Validated$/)).toBeVisible({ timeout: 10_000 });
  });

  test("shows the preview once formatted", async ({ page }) => {
    await page.getByRole("tab", { name: "Preview" }).click();
    const frame = page.frameLocator('iframe[title="Document preview"]');
    await expect(page.locator('iframe[title="Document preview"]')).toHaveAttribute(
      "src",
      /\/preview/,
    );
    await expect(frame.locator("body")).toBeVisible({ timeout: 15_000 });
  });

  test("switches to Springer and the Compare tab shows real deltas", async ({ page }) => {
    await page.getByRole("button", { name: "Change format" }).click();
    const dialog = page.getByRole("dialog", { name: "Choose a publication format" });
    await dialog.getByRole("button", { name: /Springer/ }).click();
    await dialog.getByRole("button", { name: "Apply format" }).click();
    await expect(dialog).toBeHidden();
    await expect(page.getByText("Springer profile applied")).toBeVisible();

    await page.getByRole("tab", { name: "Compare" }).click();
    await expect(page.getByRole("heading", { name: "Before / after" })).toBeVisible();
    await expect(page.getByText(/Formatting changes/)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/passed|review required/)).toBeVisible();
  });
});
```

- [ ] **Step 2: Run it**

```bash
cd frontend && npx playwright test formatting.spec.ts
```

If the second test's "revisit the document from the dashboard" approach is flaky (the recents list may take a moment to reflect the just-uploaded document), replace it with capturing the document id from the first test and navigating directly — apply the bug-fix loop's REPRODUCE/UNDERSTAND steps to decide which is the real fix before changing the test.

Expected: 4 passed. Apply the bug-fix loop to any genuine product failure, restart `webServer`s, retest, then re-run the whole file.

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/formatting.spec.ts
git commit -m "test(e2e): IEEE/Springer formatting, validation, preview, compare"
```

---

### Task 6: Export flows (`export.spec.ts`)

**Files:**
- Create: `frontend/e2e/export.spec.ts`

**Interfaces:**
- Consumes: `test`, `expect`, `uploadAndAnalyze` from `./fixtures`.
- Uses Playwright's `request` fixture to read `/api/health` directly (bypassing the UI) to decide which PDF branch to assert.

Covers spec §44 flows 17–19 (DOCX export works, PDF export works, downloaded files exist).

- [ ] **Step 1: Write the spec**

```ts
// frontend/e2e/export.spec.ts
import { expect, test, uploadAndAnalyze } from "./fixtures";

const BACKEND_URL = "http://localhost:8010";

async function formatAsIeee(page: import("@playwright/test").Page) {
  await page.getByRole("button", { name: "Apply format" }).click();
  const dialog = page.getByRole("dialog", { name: "Choose a publication format" });
  await dialog.getByRole("button", { name: /IEEE/ }).click();
  await dialog.getByRole("button", { name: "Apply format" }).click();
  await expect(dialog).toBeHidden();
  await page.getByRole("tab", { name: "What changed" }).click();
}

test.describe("Export", () => {
  test("exports a real DOCX file", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");
    await formatAsIeee(page);

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Export DOCX" }).click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.docx$/);
    const savedPath = await download.path();
    expect(savedPath).toBeTruthy();
  });

  test("exports a PDF when available, otherwise shows the unavailable state", async ({
    page,
    request,
  }) => {
    const health = await (await request.get(`${BACKEND_URL}/api/health`)).json();

    await uploadAndAnalyze(page, "sample_basic.docx");
    await formatAsIeee(page);

    const pdfButton = page.getByRole("button", { name: "Export PDF" });

    if (health.capabilities.pdf_export) {
      const [download] = await Promise.all([
        page.waitForEvent("download", { timeout: 30_000 }),
        pdfButton.click(),
      ]);
      expect(download.suggestedFilename()).toMatch(/\.pdf$/);
      expect(await download.path()).toBeTruthy();
    } else {
      await expect(pdfButton).toBeDisabled();
      await expect(page.getByText("PDF export unavailable on this machine.")).toBeVisible();
    }
  });
});
```

- [ ] **Step 2: Run it, apply the bug-fix loop on any failure, then commit**

```bash
cd frontend && npx playwright test export.spec.ts
```

```bash
git add frontend/e2e/export.spec.ts
git commit -m "test(e2e): DOCX and PDF export, environment-aware PDF branch"
```

---

### Task 7: Resilience flows (`resilience.spec.ts`)

**Files:**
- Create: `frontend/e2e/resilience.spec.ts`

**Interfaces:**
- Consumes: `test`, `expect`, `uploadAndAnalyze` from `./fixtures`.

Covers spec §44 flows 21–23 (refresh/reload behavior, error recovery, responsive layouts) plus the Slice 2 ended-session state and a simulated network failure.

- [ ] **Step 1: Write the spec**

```ts
// frontend/e2e/resilience.spec.ts
import { expect, test, uploadAndAnalyze } from "./fixtures";

const BACKEND_URL = "http://localhost:8010";

test.describe("Resilience", () => {
  test("reloads mid-workflow without losing state", async ({ page }) => {
    const id = await uploadAndAnalyze(page, "sample_basic.docx");
    await page.reload();
    await expect(page.getByRole("heading", { name: "Metadata" })).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/workspace/${id}$`));
  });

  test("shows a recoverable message once the working session has ended", async ({
    page,
    request,
  }) => {
    const id = await uploadAndAnalyze(page, "sample_basic.docx");
    await request.delete(`${BACKEND_URL}/api/documents/${id}`);
    await page.reload();

    await expect(page.getByRole("heading", { name: "Session ended" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Upload a manuscript/i })).toBeVisible();
  });

  test("surfaces a clear error when the backend is unreachable", async ({ page }) => {
    const id = await uploadAndAnalyze(page, "sample_basic.docx");
    await page.route(`${BACKEND_URL}/**`, (route) => route.abort("connectionrefused"));
    await page.reload();

    await expect(page.getByRole("heading", { name: "Could not load the workspace" })).toBeVisible({
      timeout: 15_000,
    });
    await page.unroute(`${BACKEND_URL}/**`);
    void id;
  });

  test("adapts the workspace layout to a mobile viewport", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");
    await page.setViewportSize({ width: 375, height: 812 });

    await expect(page.getByRole("button", { name: "Outline" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Issues \(\d+\)/ })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Document outline" })).toBeHidden();
  });
});
```

- [ ] **Step 2: Run it, apply the bug-fix loop on any failure, then commit**

```bash
cd frontend && npx playwright test resilience.spec.ts
```

```bash
git add frontend/e2e/resilience.spec.ts
git commit -m "test(e2e): reload, ended session, network failure, responsive layout"
```

---

### Task 8: Accessibility audit (`a11y.spec.ts`) + Dialog focus trap fix

**Files:**
- Create: `frontend/e2e/a11y.spec.ts`
- Modify (only if Step 2 finds the anticipated gap): `frontend/src/components/ui/Dialog.tsx`

**Interfaces:**
- Consumes: `test`, `expect`, `uploadAndAnalyze` from `./fixtures`; `AxeBuilder` from `@axe-core/playwright`.

Covers spec §44 flow 24 (keyboard navigation) and spec §39 (accessibility) end to end: automated axe scans on Dashboard, Upload, and each Workspace tab, plus a manual-style keyboard-only check and a dialog focus-trap check. `Dialog.tsx` currently focuses its panel on open (`frontend/src/components/ui/Dialog.tsx:26`) but does not constrain Tab from leaving it — the trap test below is expected to fail until that's fixed.

- [ ] **Step 1: Write the spec**

```ts
// frontend/e2e/a11y.spec.ts
import AxeBuilder from "@axe-core/playwright";
import { expect, test, uploadAndAnalyze } from "./fixtures";

async function assertNoSeriousViolations(page: import("@playwright/test").Page) {
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter((v) => ["serious", "critical"].includes(v.impact ?? ""));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
}

test.describe("Accessibility", () => {
  test("dashboard has no serious/critical axe violations", async ({ page }) => {
    await page.goto("/");
    await assertNoSeriousViolations(page);
  });

  test("upload page has no serious/critical axe violations", async ({ page }) => {
    await page.goto("/upload");
    await assertNoSeriousViolations(page);
  });

  test("workspace tabs have no serious/critical axe violations", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");
    await assertNoSeriousViolations(page); // Review tab

    await page.getByRole("button", { name: "Apply format" }).click();
    const dialog = page.getByRole("dialog", { name: "Choose a publication format" });
    await dialog.getByRole("button", { name: /IEEE/ }).click();
    await dialog.getByRole("button", { name: "Apply format" }).click();
    await expect(dialog).toBeHidden();

    await page.getByRole("tab", { name: "Preview" }).click();
    await assertNoSeriousViolations(page);

    await page.getByRole("tab", { name: "Compare" }).click();
    await expect(page.getByRole("heading", { name: "Before / after" })).toBeVisible();
    await assertNoSeriousViolations(page);
  });

  test("the upload control is operable by keyboard alone", async ({ page }) => {
    await page.goto("/upload");
    await page.keyboard.press("Tab"); // skip the "Back to dashboard" link
    const dropzone = page.getByRole("button", { name: /Drop your manuscript here/i });
    await expect(dropzone).toBeFocused();
  });

  test("Tab cannot escape an open dialog", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");
    await page.getByRole("button", { name: "Apply format" }).click();
    const dialog = page.getByRole("dialog", { name: "Choose a publication format" });
    await expect(dialog).toBeVisible();

    for (let i = 0; i < 20; i++) {
      await page.keyboard.press("Tab");
      const stillInside = await dialog.evaluate(
        (node, active) => node.contains(active),
        await page.evaluateHandle(() => document.activeElement),
      );
      expect(stillInside).toBe(true);
    }
  });
});
```

- [ ] **Step 2: Run it**

```bash
cd frontend && npx playwright test a11y.spec.ts
```

Expected at this point: the "Tab cannot escape an open dialog" test FAILS (focus reaches elements behind the overlay), per the known gap noted above. All other tests are expected to pass given the project's existing semantic HTML, landmarks, and `focus-visible` styling (`frontend/src/index.css:26-28`).

- [ ] **Step 3: Fix the dialog focus trap (only if Step 2's failure confirms it)**

Edit `frontend/src/components/ui/Dialog.tsx`, replacing the existing `useEffect`:

```tsx
  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();

    function focusable(): HTMLElement[] {
      const panel = panelRef.current;
      if (!panel) return [];
      return Array.from(
        panel.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
    }

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const items = focusable();
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previouslyFocused?.focus();
    };
  }, [open, onClose]);
```

- [ ] **Step 4: Restart the frontend dev server (picked up automatically by Playwright's `webServer` on the next run) and retest**

```bash
cd frontend && npx playwright test a11y.spec.ts
```

Expected: all 5 pass.

- [ ] **Step 5: Regression — re-run the full suite**

```bash
cd frontend && npx playwright test
```

Expected: every spec file from Tasks 2–8 still passes (the Dialog is shared by `FormatPicker`, used in Task 5's serial formatting test).

- [ ] **Step 6: Commit**

```bash
git add frontend/e2e/a11y.spec.ts frontend/src/components/ui/Dialog.tsx
git commit -m "fix(a11y): trap focus inside open dialogs; add automated + keyboard a11y suite"
```

---

### Task 9: UI polish pass

**Files:**
- Modify: `frontend/src/components/layout/AppShell.tsx:24` (stale "IEEE format profile" footer copy — Springer has shipped since Slice 2)
- Modify: `frontend/src/components/ui/Button.tsx` (add a `transition-transform active:scale-[0.98]` press state — the only interactive state currently missing per spec §64's "hover states" / polish list; hover and disabled states already exist)
- Modify: `frontend/src/components/ui/Card.tsx` (add `transition-shadow hover:shadow-raised` so list-like cards read as interactive where they are; static cards are unaffected since only `shadow-card` → `shadow-raised` changes on hover)

**Interfaces:**
- Consumes: nothing new. Pure refinement of existing, already-tested components.

This task is intentionally small: the existing UI (built to near-final polish across Slices 1–2, per the project's own history) already has loading/empty/error/success states, hover states on buttons, focus rings, and transitions. The audit in Task 8 found the one real interaction gap (dialog focus trap, already fixed). What's left is a factual copy fix and two small, low-risk visual touches — not a redesign.

- [ ] **Step 1: Fix the stale footer copy**

In `frontend/src/components/layout/AppShell.tsx`, change:

```tsx
        ManuScript AI · rule-based, offline-capable · IEEE format profile
```

to:

```tsx
        ManuScript AI · rule-based, offline-capable · IEEE and Springer format profiles
```

- [ ] **Step 2: Add a pressed state to `Button`**

In `frontend/src/components/ui/Button.tsx`, in the `className={cn(...)}` call, add `"active:scale-[0.98]"` alongside the existing `"transition-colors"`:

```tsx
        "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium transition-colors active:scale-[0.98]",
```

- [ ] **Step 3: Add a hover elevation to `Card`**

In `frontend/src/components/ui/Card.tsx`:

```tsx
      className={cn(
        "rounded-xl border border-zinc-200 bg-white shadow-card transition-shadow",
        className,
      )}
```

(No `hover:shadow-raised` on the base `Card` — most cards are static containers, not clickable rows, and a hover elevation on every card would be visual noise inconsistent with spec §64's "avoid visual clutter." The clickable rows in `RecentList.tsx` already have their own `hover:bg-zinc-50` on the row button. This step only adds the `transition-shadow` utility so any future hover-shadow usage animates smoothly — a minimal, low-risk addition.)

- [ ] **Step 4: Re-run the frontend unit suite and the full E2E suite**

```bash
cd frontend && npm test && npx playwright test
```

Expected: unchanged pass counts (41 vitest, all Playwright specs) — this task changes no behavior, only classes/copy.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/layout/AppShell.tsx frontend/src/components/ui/Button.tsx frontend/src/components/ui/Card.tsx
git commit -m "polish: correct stale footer copy, add button press state and card transition"
```

---

### Task 10: Final regression, README, engineering report

**Files:**
- Modify: `README.md`
- Create: `docs/ENGINEERING_REPORT.md`

**Interfaces:**
- Consumes: nothing (final documentation task).

- [ ] **Step 1: Update `README.md`**

Add a line under the existing `## Tests` bash block (after the `cd frontend && npm test && npx tsc -b --noEmit` line):

```markdown
cd frontend && npx playwright test    # end-to-end (Chromium) — starts both servers automatically
```

In the "Supported publication formats" section intro or the features list, no factual change is needed (Springer already documented as Available since Slice 2) — skip unless Task 9 revealed something else stale during review.

- [ ] **Step 2: Write `docs/ENGINEERING_REPORT.md`**

Write the 13-point report required by spec §67, using real figures gathered by re-running the suites in Step 3 below. Structure:

```markdown
# ManuScript AI — Engineering Report

## 1. What was built
[2-3 paragraphs: local rule-based manuscript formatter, upload → analyze → review → format → validate → preview → export, IEEE + Springer, SQLite history, before/after comparison, Playwright-verified.]

## 2. Final architecture
[Reference docs/ARCHITECTURE.md's layer table; summarize the pipeline diagram.]

## 3. Technology stack
[Table: Python 3.12/FastAPI/python-docx/Pydantic v2/Uvicorn/pypdf/PyYAML backend; headless LibreOffice for PDF; React 18/TypeScript/Vite 5/Tailwind 3/lucide-react frontend; pytest/vitest/Playwright/axe-core for testing.]

## 4. Major features
[Bulleted, mirrors README's Features section.]

## 5. Supported publication profiles
[IEEE and Springer, with the provenance-tagging system from docs/RULES.md explained.]

## 6. Document-processing pipeline
[The 9-stage pipeline from docs/ARCHITECTURE.md.]

## 7. Validation capabilities
[Categories, health score weighting, content-preservation check.]

## 8. Export capabilities
[DOCX verified-open; PDF via LibreOffice with page count; structural HTML preview fallback.]

## 9. Test results
[Exact counts from Step 3: N backend pytest, N frontend vitest, N Playwright specs/tests, all green.]

## 10. Playwright results
[List the 8 spec files and what each covers; note the one bug found and fixed (Dialog focus trap) via the reproduce → fix → retest → regress loop.]

## 11. Known limitations
[Carry forward README's Known limitations section verbatim, since Slice 3 didn't change pipeline behavior.]

## 12. How to run the application
[bash scripts/dev.sh; bash scripts/check.sh; manual setup steps from README.]

## 13. Recommended future improvements
[Carry forward README's Future extension points; add: cross-browser E2E coverage, CI pipeline to run scripts/check.sh on push, session persistence across backend restarts.]
```

Fill in every bracketed section with real prose and real numbers — no placeholder text should remain in the committed file.

- [ ] **Step 3: Run the full regression and capture real numbers for the report**

```bash
bash scripts/check.sh
```

Copy the actual pytest/vitest/Playwright pass counts from this run's output into `docs/ENGINEERING_REPORT.md` section 9 and 10.

- [ ] **Step 4: Manual final click-through**

Using the Claude Browser tool (not Playwright, as a last human-eye check): open the dev servers (`bash scripts/dev.sh`), walk through upload → analyze → review → apply Springer → validate → preview → compare → export DOCX, and confirm the browser console and network tab are clean, matching spec §46's browser console/network QA. Fix anything found via the bug-fix loop and re-run `bash scripts/check.sh` before continuing.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/ENGINEERING_REPORT.md
git commit -m "docs: Slice 3 engineering report; document the e2e test command"
```

---

## Self-Review Notes

- **Spec coverage:** Task 1 → §44 setup; Task 2 → flows 1-3,20; Task 3 → flows 4-6; Task 4 → flows 7-12; Task 5 → flows 13-16 + Compare; Task 6 → flows 17-19; Task 7 → flows 21-23 + ended-session + network failure; Task 8 → flow 24 + §39 accessibility + the bug-fix loop (§45) with a real found-and-fixed bug; Task 9 → §64 UI polish; Task 10 → §67 final report + §46 console/network QA + §63 final regression. All design sections covered.
- **Placeholder scan:** every step has runnable code or an exact instruction; the only bracketed placeholders are inside the `ENGINEERING_REPORT.md` template in Task 10, which Step 3 explicitly requires filling with real, freshly-measured numbers before commit.
- **Type/name consistency:** `uploadAndAnalyze`, `simulateFileDrop`, `SAMPLES`, `test`, `expect` are defined once in Task 1's `fixtures.ts` and imported with matching names/signatures in every later task.

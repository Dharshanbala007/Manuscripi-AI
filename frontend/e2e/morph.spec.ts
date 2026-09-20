import path from "node:path";
import type { Page } from "@playwright/test";
import { expect, SAMPLES, test, uploadAndAnalyze } from "./fixtures";

type Rect = { x: number; y: number; w: number; h: number };

// Samples the bounding boxes of every element matching `selector`, once per animation
// frame, for `ms` milliseconds. Start it before the action that triggers the morph.
function sampleRects(page: Page, selector: string, ms: number): Promise<Rect[][]> {
  return page.evaluate(
    ({ selector, ms }) =>
      new Promise<Rect[][]>((resolve) => {
        const frames: Rect[][] = [];
        const t0 = performance.now();
        const tick = () => {
          frames.push(
            [...document.querySelectorAll(selector)].map((el) => {
              const r = el.getBoundingClientRect();
              return { x: r.x, y: r.y, w: r.width, h: r.height };
            }),
          );
          if (performance.now() - t0 < ms) requestAnimationFrame(tick);
          else resolve(frames);
        };
        requestAnimationFrame(tick);
      }),
    { selector, ms },
  );
}

const widths = (frames: Rect[][]) => frames.flat().map((r) => r.w);

async function pickFile(page: Page) {
  await page.goto("/upload");
  await page.getByTestId("dropzone-input").setInputFiles(path.join(SAMPLES, "sample_complex.docx"));
  await expect(page.getByRole("button", { name: /Analyse manuscript/i })).toBeVisible();
}

test.describe("Morphing flow", () => {
  test("the flow rail advances and the page logs no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    const rail = page.getByRole("navigation", { name: "Manuscript progress" });
    await page.goto("/upload");
    await expect(rail.locator('li[aria-current="step"]')).toContainText("Upload");

    await pickFile(page);
    await page.getByRole("button", { name: /Analyse manuscript/i }).click();
    await page.waitForURL(/\/workspace\//, { timeout: 30_000 });

    await expect(rail.locator('li[aria-current="step"]')).toContainText("Review");
    await expect(rail).toContainText(/Upload\s*\(completed\)/);
    await expect(rail).toContainText(/Analyze\s*\(completed\)/);

    await page.getByRole("button", { name: "Apply format" }).click();
    const dialog = page.getByRole("dialog", { name: "Choose a publication format" });
    await dialog.getByRole("button", { name: "Apply format" }).click();
    await expect(dialog).toBeHidden();
    await expect(rail.locator('li[aria-current="step"]')).toContainText("Format");

    expect(errors).toEqual([]);
  });

  test("the glass surface morphs between screens instead of jumping", async ({ page }) => {
    await pickFile(page);
    const sampling = sampleRects(page, '[data-testid="stage-surface"]', 1800);
    await page.getByRole("button", { name: /Analyse manuscript/i }).click();
    const w = widths(await sampling);

    const start = Math.min(...w);
    const end = Math.max(...w);
    expect(end - start).toBeGreaterThan(300); // card -> full-width header
    // at least one frame strictly between the two layouts means it animated
    expect(w.some((v) => v > start + 40 && v < end - 40)).toBe(true);
  });

  test("the format dialog expands out of its button", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");
    const sampling = sampleRects(page, '[role="dialog"]', 1200);
    await page.getByRole("button", { name: "Apply format" }).click();
    const w = widths(await sampling);

    const final = Math.max(...w);
    expect(final).toBeGreaterThan(400);
    expect(w.some((v) => v > 0 && v < final - 60)).toBe(true);
  });

  test("action buttons morph through pending and success", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");
    await page.getByRole("button", { name: "Apply format" }).click();
    const dialog = page.getByRole("dialog", { name: "Choose a publication format" });
    await dialog.getByRole("button", { name: "Apply format" }).click();
    await expect(dialog).toBeHidden();

    const validate = page.locator("button[data-status]").filter({ hasText: "Validate" });
    await expect(validate).toHaveAttribute("data-status", "idle");
    await validate.click();
    await expect(validate).toHaveAttribute("data-status", "success", { timeout: 15_000 });
    await expect(validate).toHaveAttribute("data-status", "idle", { timeout: 15_000 });
  });

  test.describe("reduced motion", () => {
    test.use({ reducedMotion: "reduce" });

    test("the surface does not animate between screens", async ({ page }) => {
      await pickFile(page);
      const sampling = sampleRects(page, '[data-testid="stage-surface"]', 1800);
      await page.getByRole("button", { name: /Analyse manuscript/i }).click();
      const w = widths(await sampling);

      const start = Math.min(...w);
      const end = Math.max(...w);
      expect(end - start).toBeGreaterThan(300);
      expect(w.some((v) => v > start + 40 && v < end - 40)).toBe(false);
    });
  });
});

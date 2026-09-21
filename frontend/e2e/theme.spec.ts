import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { expect, test } from "./fixtures";

// Sum of every pixel channel in the silk canvas; changes whenever a new frame is drawn.
const silkFingerprint = (page: Page) =>
  page.evaluate(() => {
    const c = document.querySelector<HTMLCanvasElement>('[data-testid="silk-background"] canvas');
    const ctx = c?.getContext("2d");
    if (!c || !ctx) return -1;
    const d = ctx.getImageData(0, 0, c.width, c.height).data;
    let sum = 0;
    for (let i = 0; i < d.length; i += 97) sum += d[i];
    return sum;
  });

test.describe("Theme", () => {
  test("defaults to dark with the animated silk background", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await expect(page.getByTestId("silk-background")).toBeAttached();

    const a = await silkFingerprint(page);
    await page.waitForTimeout(700);
    const b = await silkFingerprint(page);
    expect(a).toBeGreaterThan(0);
    expect(b).not.toBe(a);
  });

  test.describe("reduced motion", () => {
    test.use({ reducedMotion: "reduce" });

    for (const theme of ["dark", "light"]) {
      test(`the ${theme} silk renders one still frame`, async ({ page }) => {
        await page.addInitScript((t) => localStorage.setItem("theme", t), theme);
        await page.goto("/");
        const a = await silkFingerprint(page);
        await page.waitForTimeout(700);
        expect(a).toBeGreaterThan(0);
        expect(await silkFingerprint(page)).toBe(a);
      });
    }
  });

  test("the toggle switches to a lighter animated silk and persists across reloads", async ({ page }) => {
    await page.goto("/");
    const dark = await silkFingerprint(page);

    await page.getByRole("button", { name: "Switch to light theme" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await expect(page.getByTestId("silk-background")).toBeAttached();

    const lightA = await silkFingerprint(page);
    await page.waitForTimeout(700);
    const lightB = await silkFingerprint(page);
    expect(lightA).toBeGreaterThan(dark); // pale lavender, not deep violet
    expect(lightB).not.toBe(lightA); // and it is still flowing

    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await expect(page.getByRole("button", { name: "Switch to dark theme" })).toBeVisible();

    await page.getByRole("button", { name: "Switch to dark theme" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    expect(await silkFingerprint(page)).toBeLessThan(lightA);
  });

  test("the light theme has no serious/critical axe violations", async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem("theme", "light"));
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /publication-ready/i })).toBeVisible();
    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter((v) => ["serious", "critical"].includes(v.impact ?? ""));
    expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
  });

  test("the flow button opens the upload screen", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "New manuscript" }).click();
    await expect(page).toHaveURL(/\/upload$/);
  });
});

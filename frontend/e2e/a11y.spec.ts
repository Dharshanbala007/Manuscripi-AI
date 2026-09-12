import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { expect, test, uploadAndAnalyze } from "./fixtures";

async function assertNoSeriousViolations(page: Page) {
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
    const input = page.getByTestId("dropzone-input");
    for (let i = 0; i < 6 && !(await input.evaluate((el) => el === document.activeElement)); i++) {
      await page.keyboard.press("Tab");
    }
    await expect(input).toBeFocused();
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

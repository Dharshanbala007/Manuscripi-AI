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

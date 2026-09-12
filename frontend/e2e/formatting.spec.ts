import { expect, test, uploadAndAnalyze } from "./fixtures";

test.describe("Formatting, validation, preview, compare", () => {
  test.describe.configure({ mode: "serial" });

  let docId: string;

  test("applies the IEEE format profile", async ({ page }) => {
    docId = await uploadAndAnalyze(page, "sample_complex.docx");

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

  test("runs validation and shows a health score", async ({ page }) => {
    await page.goto(`/workspace/${docId}`);
    await expect(page.getByRole("heading", { name: "Manuscript health" })).toBeVisible();

    await page.getByRole("button", { name: "Validate" }).click();
    await expect(page.getByText(/^Validated$/)).toBeVisible({ timeout: 10_000 });
  });

  test("shows the preview once formatted", async ({ page }) => {
    await page.goto(`/workspace/${docId}`);
    await page.getByRole("tab", { name: "Preview" }).click();

    const iframe = page.locator('iframe[title="Document preview"]');
    await expect(iframe).toHaveAttribute("src", /\/preview/);
    const frame = page.frameLocator('iframe[title="Document preview"]');
    await expect(frame.locator("body")).toBeVisible({ timeout: 15_000 });
  });

  test("switches to Springer and the Compare tab shows real deltas", async ({ page }) => {
    await page.goto(`/workspace/${docId}`);
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

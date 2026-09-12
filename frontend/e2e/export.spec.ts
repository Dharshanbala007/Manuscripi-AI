import type { Page } from "@playwright/test";
import { expect, test, uploadAndAnalyze } from "./fixtures";

const BACKEND_URL = "http://localhost:8010";

async function formatAsIeee(page: Page) {
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

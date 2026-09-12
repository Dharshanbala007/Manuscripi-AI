import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test, SAMPLES, simulateFileDrop } from "./fixtures";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

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
      '[data-testid="dropzone"]',
      path.join(SAMPLES, "sample_complex.docx"),
      "sample_complex.docx",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    );

    await expect(page.getByText("sample_complex.docx")).toBeVisible({ timeout: 10_000 });
  });
});

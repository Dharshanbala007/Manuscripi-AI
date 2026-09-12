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

    await expect(page.getByRole("alert").getByText("Session ended")).toBeVisible();
    await expect(page.getByRole("button", { name: /Upload a manuscript/i })).toBeVisible();
  });

  test("surfaces a clear error when the backend is unreachable", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");
    await page.route(`${BACKEND_URL}/**`, (route) => route.abort("connectionrefused"));
    await page.reload();

    await expect(
      page.getByRole("alert").getByText("Could not load the workspace"),
    ).toBeVisible({ timeout: 15_000 });
    await page.unroute(`${BACKEND_URL}/**`);
  });

  test("adapts the workspace layout to a mobile viewport", async ({ page }) => {
    await uploadAndAnalyze(page, "sample_basic.docx");
    await page.setViewportSize({ width: 375, height: 812 });

    await expect(page.getByRole("button", { name: "Outline" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Issues \(\d+\)/ })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Document outline" })).toBeHidden();
  });
});

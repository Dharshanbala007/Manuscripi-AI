import { expect, test } from "./fixtures";

const BACKEND_URL = "http://localhost:8010";

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

  test("shows an empty recents state when there is no history", async ({ page, request }) => {
    // Other spec files share this backend session; clear history explicitly so this
    // assertion holds regardless of file execution order.
    const existing: { id: string }[] = await (
      await request.get(`${BACKEND_URL}/api/history?limit=100`)
    ).json();
    await Promise.all(existing.map((e) => request.delete(`${BACKEND_URL}/api/history/${e.id}`)));

    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Recent manuscripts" })).toBeVisible();
    await expect(page.getByText("No manuscripts yet")).toBeVisible();
  });
});

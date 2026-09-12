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

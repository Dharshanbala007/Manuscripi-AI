import { test as base, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const test = base;
export { expect };

export const SAMPLES = path.resolve(__dirname, "../../sample_documents");

export async function uploadAndAnalyze(page: Page, filename: string): Promise<string> {
  await page.goto("/upload");
  await page.getByTestId("dropzone-input").setInputFiles(path.join(SAMPLES, filename));
  await page.getByRole("button", { name: /Analyse manuscript/i }).click();
  await page.waitForURL(/\/workspace\//, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: "Metadata" })).toBeVisible({ timeout: 15_000 });
  const id = new URL(page.url()).pathname.split("/workspace/")[1];
  if (!id) throw new Error(`Could not extract document id from ${page.url()}`);
  return id;
}

export async function simulateFileDrop(
  page: Page,
  selector: string,
  filePath: string,
  fileName: string,
  mimeType: string,
): Promise<void> {
  const base64 = readFileSync(filePath).toString("base64");
  const dataTransfer = await page.evaluateHandle(
    async ({ base64, fileName, mimeType }) => {
      const binary = atob(base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const dt = new DataTransfer();
      dt.items.add(new File([bytes], fileName, { type: mimeType }));
      return dt;
    },
    { base64, fileName, mimeType },
  );
  await page.dispatchEvent(selector, "drop", { dataTransfer });
}

import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const FRONTEND_PORT = 5183;
const BACKEND_PORT = 8010;
const ROOT = path.resolve(__dirname, "..");
const BACKEND_DIR = path.join(ROOT, "backend");

function pythonExe(): string {
  const winPy = path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe");
  return existsSync(winPy) ? winPy : path.join(BACKEND_DIR, ".venv", "bin", "python");
}

const workDir = path.join(os.tmpdir(), `manuscript-ai-e2e-${process.pid}`);

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `"${pythonExe()}" -m uvicorn app.main:app --port ${BACKEND_PORT}`,
      cwd: BACKEND_DIR,
      url: `http://localhost:${BACKEND_PORT}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        WORK_DIR: path.join(workDir, "workspace"),
        HISTORY_DB: path.join(workDir, "history.db"),
      },
    },
    {
      command: `npm run dev -- --port ${FRONTEND_PORT} --strictPort`,
      cwd: __dirname,
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        VITE_API_BASE: `http://localhost:${BACKEND_PORT}`,
      },
    },
  ],
});

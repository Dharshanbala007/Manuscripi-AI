# Lint + typecheck + tests for both apps.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root "backend\.venv\Scripts\python.exe"

Write-Host "== backend: ruff =="
& $py -m ruff check (Join-Path $root "backend")
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "== backend: ruff format --check =="
& $py -m ruff format --check (Join-Path $root "backend")
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "== backend: pytest =="
Push-Location (Join-Path $root "backend")
& $py -m pytest
$backendTests = $LASTEXITCODE
Pop-Location
if ($backendTests -ne 0) { exit 1 }

Write-Host "== frontend: tsc =="
Push-Location (Join-Path $root "frontend")
npx tsc -b --noEmit
$tsc = $LASTEXITCODE
if ($tsc -eq 0) {
  Write-Host "== frontend: vitest =="
  npm test
  $vitest = $LASTEXITCODE
}
Pop-Location
if ($tsc -ne 0 -or $vitest -ne 0) { exit 1 }

Write-Host "All checks passed."

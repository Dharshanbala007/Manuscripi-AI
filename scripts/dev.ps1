# Run the backend (uvicorn --reload) and the frontend (vite) together.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root "backend\.venv\Scripts\python.exe"

$backend = Start-Process -PassThru -NoNewWindow -FilePath $py `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000" `
  -WorkingDirectory (Join-Path $root "backend")

try {
  Push-Location (Join-Path $root "frontend")
  npm run dev
}
finally {
  Pop-Location
  if ($backend -and -not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
}

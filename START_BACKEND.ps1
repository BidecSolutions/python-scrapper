# Start FastAPI Backend Server
# Run this script to start the backend API server

Write-Host "Starting LeadFlux AI Backend Server..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Start uvicorn server
Write-Host "Starting uvicorn server on http://localhost:8002" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn app.api.server:app --reload --port 8002


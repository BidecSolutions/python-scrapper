# PowerShell script to start the FastAPI backend server
# Usage: .\start-backend.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting LeadFlux Backend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
} elseif (Test-Path ".venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "WARNING: No virtual environment found. Using system Python." -ForegroundColor Yellow
    Write-Host "It's recommended to create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor Gray
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host ""
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found. Some features may not work." -ForegroundColor Yellow
    Write-Host "Create a .env file with your API keys if needed." -ForegroundColor Yellow
    Write-Host ""
}

# Check if uvicorn is installed
try {
    $uvicornCheck = python -c "import uvicorn" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing uvicorn..." -ForegroundColor Yellow
        pip install uvicorn[standard]
    }
} catch {
    Write-Host "Installing uvicorn..." -ForegroundColor Yellow
    pip install uvicorn[standard]
}

Write-Host ""
Write-Host "Starting backend server on http://localhost:8000" -ForegroundColor Green
Write-Host "API docs available at http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
try {
    python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to start server" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}


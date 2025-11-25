# PowerShell script to start the Next.js frontend server
# Usage: .\start-frontend.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting LeadFlux Frontend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check if npm is available
try {
    $npmVersion = npm --version 2>&1
    Write-Host "npm found: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: npm is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Navigate to frontend directory
if (-not (Test-Path "frontend")) {
    Write-Host "ERROR: frontend directory not found" -ForegroundColor Red
    Write-Host "Make sure you're running this script from the project root" -ForegroundColor Yellow
    exit 1
}

Set-Location frontend

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    Write-Host "This may take a few minutes..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
            exit 1
        }
        Write-Host ""
        Write-Host "Dependencies installed successfully!" -ForegroundColor Green
        Write-Host ""
    } catch {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        exit 1
    }
}

# Check if .env.local exists
if (-not (Test-Path ".env.local")) {
    Write-Host "WARNING: .env.local not found in frontend directory." -ForegroundColor Yellow
    Write-Host "Creating .env.local with default API URL..." -ForegroundColor Yellow
    
    $envContent = @"
NEXT_PUBLIC_API_URL=http://localhost:8002
"@
    Set-Content -Path ".env.local" -Value $envContent
    Write-Host ".env.local created with default settings" -ForegroundColor Green
    Write-Host ""
}

Write-Host ""
Write-Host "Starting frontend server on http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the development server
try {
    npm run dev
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to start frontend server" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}


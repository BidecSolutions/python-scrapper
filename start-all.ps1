# PowerShell script to start both backend and frontend servers
# Usage: .\start-all.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting LeadFlux (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if both scripts exist
if (-not (Test-Path "start-backend.ps1")) {
    Write-Host "ERROR: start-backend.ps1 not found" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "start-frontend.ps1")) {
    Write-Host "ERROR: start-frontend.ps1 not found" -ForegroundColor Red
    exit 1
}

Write-Host "This script will start both servers in separate windows." -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend will run on: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend will run on: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to continue or Ctrl+C to cancel..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "Starting backend server in new window..." -ForegroundColor Cyan
$backendWindow = Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-backend.ps1" -WindowStyle Normal -PassThru

# Wait a bit for backend to start
Write-Host "Waiting 3 seconds for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Starting frontend server in new window..." -ForegroundColor Cyan
$frontendWindow = Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-frontend.ps1" -WindowStyle Normal -PassThru

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Both servers are starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Backend Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Two new PowerShell windows have been opened:" -ForegroundColor Yellow
Write-Host "  - Backend window (PID: $($backendWindow.Id))" -ForegroundColor Gray
Write-Host "  - Frontend window (PID: $($frontendWindow.Id))" -ForegroundColor Gray
Write-Host ""
Write-Host "Close those windows to stop the servers." -ForegroundColor Yellow
Write-Host "Or run .\stop-all.ps1 to stop everything." -ForegroundColor Yellow
Write-Host ""


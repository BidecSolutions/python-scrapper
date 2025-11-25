# PowerShell script to stop all running servers
# Usage: .\stop-all.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stopping LeadFlux Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop processes on common ports
$ports = @(8002, 3000, 3001)

foreach ($port in $ports) {
    Write-Host "Checking for processes on port $port..." -ForegroundColor Yellow
    
    try {
        # Find processes using the port (Windows)
        $connections = netstat -ano | Select-String ":$port "
        
        if ($connections) {
            foreach ($connection in $connections) {
                $pid = ($connection -split '\s+')[-1]
                if ($pid -match '^\d+$') {
                    Write-Host "  Found process $pid on port $port" -ForegroundColor Yellow
                    
                    # Try to stop gracefully first
                    try {
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                        Write-Host "  Stopped process $pid" -ForegroundColor Green
                    } catch {
                        Write-Host "  Could not stop process $pid (may have already stopped)" -ForegroundColor Yellow
                    }
                }
            }
        } else {
            Write-Host "  No process found on port $port" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  Could not check port $port" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Also stopping common Node.js and Python processes..." -ForegroundColor Yellow

# Stop Node.js processes (Next.js)
try {
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped Node.js processes" -ForegroundColor Green
} catch {
    Write-Host "No Node.js processes found" -ForegroundColor Gray
}

# Stop Python processes (uvicorn)
try {
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*server*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped Python server processes" -ForegroundColor Green
} catch {
    Write-Host "No Python server processes found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Cleanup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""


# PowerShell Script: Copy Frontend to New Repository
# Run this from the project root directory

param(
    [Parameter(Mandatory=$true)]
    [string]$NewRepoPath
)

# Source path (current frontend folder)
$sourcePath = Join-Path $PSScriptRoot "frontend"

# Check if source exists
if (-not (Test-Path $sourcePath)) {
    Write-Host "Error: Frontend folder not found at $sourcePath" -ForegroundColor Red
    exit 1
}

# Check if destination exists
if (-not (Test-Path $NewRepoPath)) {
    Write-Host "Error: Destination path not found: $NewRepoPath" -ForegroundColor Red
    Write-Host "Please create the directory first or check the path." -ForegroundColor Yellow
    exit 1
}

Write-Host "`n=== Copying Frontend Files ===" -ForegroundColor Cyan
Write-Host "Source: $sourcePath" -ForegroundColor White
Write-Host "Destination: $NewRepoPath" -ForegroundColor White
Write-Host ""

# Get all items to copy (exclude node_modules, .next, .env.local)
$itemsToCopy = Get-ChildItem -Path $sourcePath -Exclude "node_modules", ".next", ".env.local", ".vercel"

$totalItems = $itemsToCopy.Count
$current = 0

foreach ($item in $itemsToCopy) {
    $current++
    $percentComplete = [math]::Round(($current / $totalItems) * 100, 2)
    Write-Progress -Activity "Copying files" -Status "$($item.Name)" -PercentComplete $percentComplete
    
    $destination = Join-Path $NewRepoPath $item.Name
    
    if ($item.PSIsContainer) {
        # It's a directory
        Copy-Item -Path $item.FullName -Destination $destination -Recurse -Force
    } else {
        # It's a file
        Copy-Item -Path $item.FullName -Destination $destination -Force
    }
}

Write-Progress -Activity "Copying files" -Completed

Write-Host "`n✅ Files copied successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. cd '$NewRepoPath'" -ForegroundColor White
Write-Host "  2. npm install" -ForegroundColor White
Write-Host "  3. copy .env.local.example .env.local" -ForegroundColor White
Write-Host "  4. Edit .env.local with your backend URL" -ForegroundColor White
Write-Host "  5. git add ." -ForegroundColor White
Write-Host "  6. git commit -m 'Initial commit: Frontend application'" -ForegroundColor White
Write-Host "  7. git push origin main" -ForegroundColor White
Write-Host ""


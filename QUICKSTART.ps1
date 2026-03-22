# ================================================================
# QUICKSTART — Paste this entire block into PowerShell
# Does everything in one paste
# ================================================================

# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Install winget apps if missing
function Ensure-Tool($name, $wingetId) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "Installing $name..." -ForegroundColor Yellow
        winget install --id $wingetId -e --silent
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-Host "$name installed" -ForegroundColor Green
    } else {
        Write-Host "$name already installed" -ForegroundColor Green
    }
}

Ensure-Tool "git"    "Git.Git"
Ensure-Tool "python" "Python.Python.3.11"
Ensure-Tool "gh"     "GitHub.cli"

Write-Host ""
Write-Host "Now navigate to your agency-deploy folder and run:" -ForegroundColor Cyan
Write-Host "  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force" -ForegroundColor White
Write-Host "  cd C:\Users\S\Downloads\agency-deploy" -ForegroundColor White
Write-Host "  .\INSTALL.ps1" -ForegroundColor White

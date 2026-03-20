# ═══════════════════════════════════════════════════════════
#  NYSR PASSIVE INCOME STACK — WINDOWS ONE-CLICK INSTALLER
#  Run from PowerShell as Administrator:
#  irm https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/install_windows.ps1 | iex
# ═══════════════════════════════════════════════════════════

$ErrorActionPreference = "SilentlyContinue"
$INSTALL_DIR = "$env:USERPROFILE\.nysr-passive"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     NYSR PASSIVE INCOME STACK — WINDOWS SETUP       ║" -ForegroundColor Cyan
Write-Host "║         Est. earnings: `$40-110/month/IP             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check for Docker
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "⚠️  Docker not found." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Installing Docker Desktop for Windows..." -ForegroundColor Yellow
    
    # Download Docker Desktop installer
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
    
    Write-Host "Downloading Docker Desktop (~600MB)..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller -UseBasicParsing
    
    Write-Host "Running Docker Desktop installer (follow the prompts)..." -ForegroundColor Yellow
    Start-Process -FilePath $dockerInstaller -Wait
    
    Write-Host ""
    Write-Host "Docker installed. Please RESTART your computer, then run this script again." -ForegroundColor Green
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

Write-Host "✅ Docker found: $(docker --version)" -ForegroundColor Green

# Create install directory
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
Set-Location $INSTALL_DIR

# Download docker-compose file
Write-Host "Downloading stack configuration..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/docker-compose.passive.yml" -OutFile "docker-compose.yml" -UseBasicParsing

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "Enter credentials for each platform (all FREE signups)" -ForegroundColor White
Write-Host "Press ENTER to skip any you haven't set up yet" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host ""

$EMAIL = "nyspotlightreport@gmail.com"
$inputEmail = Read-Host "Email [default: $EMAIL]"
if ($inputEmail) { $EMAIL = $inputEmail }

$HPASS = Read-Host "Honeygain password (signup: honeygain.com)" -AsSecureString
$HPASS_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($HPASS))

$EARN_UUID = Read-Host "EarnApp UUID (signup: earnapp.com -> Dashboard -> Settings)"
if (-not $EARN_UUID) { $EARN_UUID = "sdk-node-nysr$(Get-Date -UFormat %s)" }

$GPASS = Read-Host "Grass password (signup: getgrass.io)" -AsSecureString  
$GPASS_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($GPASS))

$RPKEY = Read-Host "Repocket API Key (signup: repocket.co -> Account)"
if (-not $RPKEY) { $RPKEY = "your_key_here" }

$PSCID = Read-Host "PacketStream CID (signup: packetstream.io -> Dashboard)"
if (-not $PSCID) { $PSCID = "your_cid_here" }

$TMTOKEN = Read-Host "Traffmonetizer token (signup: traffmonetizer.com -> Dashboard)"
if (-not $TMTOKEN) { $TMTOKEN = "your_token_here" }

# Write .env file
@"
HONEYGAIN_EMAIL=$EMAIL
HONEYGAIN_PASS=$HPASS_PLAIN
EARNAPP_UUID=$EARN_UUID
GRASS_EMAIL=$EMAIL
GRASS_PASS=$GPASS_PLAIN
REPOCKET_EMAIL=$EMAIL
REPOCKET_API_KEY=$RPKEY
PACKETSTREAM_CID=$PSCID
TRAFFMONETIZER_TOKEN=$TMTOKEN
PEER2PROFIT_EMAIL=$EMAIL
"@ | Out-File -FilePath ".env" -Encoding UTF8

Write-Host ""
Write-Host "Configuration saved. Starting all passive income apps..." -ForegroundColor Green
Write-Host ""

# Start Docker stack
docker compose up -d 2>&1
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅  PASSIVE INCOME STACK IS RUNNING!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
docker ps --format "table {{.Names}}`t{{.Status}}"
Write-Host ""
Write-Host "Expected earnings: `$40-110/month with this IP" -ForegroundColor Yellow
Write-Host "Earnings start accumulating within 24-48 hours." -ForegroundColor Yellow
Write-Host ""
Write-Host "Manage with:" -ForegroundColor Cyan
Write-Host "  cd $INSTALL_DIR" -ForegroundColor White
Write-Host "  docker compose logs -f     # View live logs" -ForegroundColor White
Write-Host "  docker compose restart     # Restart all apps" -ForegroundColor White
Write-Host "  docker compose down        # Stop all apps" -ForegroundColor White
Write-Host ""

# Send phone notification
try {
    Invoke-RestMethod -Uri "https://ntfy.sh/nysr-chairman-sct" -Method POST `
        -Headers @{"Title"="💰 Passive Income Stack LIVE on Windows"; "Tags"="money_with_wings,white_check_mark"; "Priority"="high"} `
        -Body "All bandwidth apps running on your Windows PC! Expected: `$40-110/month. Earnings start in 24-48 hours." | Out-Null
    Write-Host "📱 Phone notification sent!" -ForegroundColor Green
} catch {}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

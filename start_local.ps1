# ==============================================================================
# AI Real Estate Deal Analyzer (India) - Local Launch Script (Windows 11)
# 100% Free - Privacy-Preserving - Local-First
# ==============================================================================

$Host.UI.RawUI.WindowTitle = "AI Real Estate Deal Analyzer - Launcher"

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   AI REAL ESTATE DEAL ANALYZER (INDIA) - LOCAL LAUNCHER        " -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " [System Architecture]" -ForegroundColor White
Write-Host "  - Frontend : Next.js 16 + React 19 + Tailwind CSS + Recharts" -ForegroundColor DarkGray
Write-Host "  - Backend  : FastAPI + SQLAlchemy + SQLite (INR Financial Engine)" -ForegroundColor DarkGray
Write-Host "  - AI Engine: Local Ollama (llama3.2:3b, offline-resilient)" -ForegroundColor DarkGray
Write-Host "  - Reports  : ReportLab Platypus Multi-Page PDF Engine" -ForegroundColor DarkGray
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $SCRIPT_DIR

# ------------------------------------------------------------------------------
# 1. Environment & Dependency Checks
# ------------------------------------------------------------------------------
Write-Host "[1/4] Checking System Prerequisites..." -ForegroundColor Yellow

# Check Python
$pythonCmd = "python"
if (Test-Path "$SCRIPT_DIR\backend\venv\Scripts\python.exe") {
    $pythonCmd = "$SCRIPT_DIR\backend\venv\Scripts\python.exe"
    Write-Host "  [OK] Found backend virtual environment: $pythonCmd" -ForegroundColor Green
} else {
    try {
        $pyVer = & python --version 2>&1
        Write-Host "  [OK] Found system Python: $pyVer" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Python is not installed or not in PATH." -ForegroundColor Red
        Write-Host "  Please install Python 3.12+ from https://www.python.org/" -ForegroundColor Red
        Pause
        Exit 1
    }
}

# Check Node.js
try {
    $nodeVer = & node --version 2>&1
    Write-Host "  [OK] Found Node.js: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Node.js is not installed or not in PATH." -ForegroundColor Red
    Write-Host "  Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    Pause
    Exit 1
}

# ------------------------------------------------------------------------------
# 2. Ollama Local AI Connectivity Check
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/4] Checking Local Ollama AI Daemon..." -ForegroundColor Yellow

$ollamaUrl = "http://127.0.0.1:11434/api/tags"
$ollamaReady = $false
$modelFound = $false

try {
    $response = Invoke-RestMethod -Uri $ollamaUrl -Method Get -TimeoutSec 3 -ErrorAction Stop
    $ollamaReady = $true
    Write-Host "  [OK] Ollama daemon is running on http://127.0.0.1:11434" -ForegroundColor Green

    if ($response.models) {
        foreach ($m in $response.models) {
            if ($m.name -like "*llama3.2:3b*" -or $m.name -like "*llama3.2*") {
                $modelFound = $true
                break
            }
        }
    }

    if ($modelFound) {
        Write-Host "  [OK] Model 'llama3.2:3b' is installed and ready for local inference." -ForegroundColor Green
    } else {
        Write-Host "  [INFO] Ollama is active, but 'llama3.2:3b' is not yet downloaded." -ForegroundColor Cyan
        Write-Host "         Optional: Run 'ollama pull llama3.2:3b' in a new terminal to enable AI." -ForegroundColor DarkGray
        Write-Host "         The application will operate in 100% deterministic mode without it." -ForegroundColor DarkGray
    }
} catch {
    Write-Host "  [INFO] Ollama daemon is not running (offline mode)." -ForegroundColor DarkGray
    Write-Host "         Optional: Run 'ollama serve' if you want local AI chat/narratives." -ForegroundColor DarkGray
    Write-Host "         All financial formulas, deal scores, risks, and PDFs work offline." -ForegroundColor Green
}

# ------------------------------------------------------------------------------
# 3. Launch Backend API Server (Port 8000)
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow

$backendDir = Join-Path $SCRIPT_DIR "backend"
$backendScript = @"
cd /d "$backendDir"
title Deal Analyzer - Backend API (Port 8000)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
"@

$backendBatchPath = Join-Path $env:TEMP "start_deal_analyzer_backend.bat"
Set-Content -Path $backendBatchPath -Value $backendScript
Start-Process "cmd.exe" -ArgumentList "/k", "`"$backendBatchPath`"" -WindowStyle Normal

# Wait for backend to initialize
Write-Host "  Waiting for backend startup..." -ForegroundColor DarkGray
$backendReady = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($res.status -eq "healthy") {
            $backendReady = $true
            break
        }
    } catch {}
}

if ($backendReady) {
    Write-Host "  [OK] Backend API is healthy and listening on port 8000." -ForegroundColor Green
} else {
    Write-Host "  [WARN] Backend is starting up in its dedicated window." -ForegroundColor Yellow
}

# ------------------------------------------------------------------------------
# 4. Launch Next.js Frontend Dev Server (Port 3000)
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] Launching Next.js Frontend on http://localhost:3000..." -ForegroundColor Yellow

$frontendDir = Join-Path $SCRIPT_DIR "frontend"
$frontendScript = @"
cd /d "$frontendDir"
title Deal Analyzer - Frontend Web UI (Port 3000)
npm run dev
"@

$frontendBatchPath = Join-Path $env:TEMP "start_deal_analyzer_frontend.bat"
Set-Content -Path $frontendBatchPath -Value $frontendScript
Start-Process "cmd.exe" -ArgumentList "/k", "`"$frontendBatchPath`"" -WindowStyle Normal

Write-Host "  Waiting for frontend server..." -ForegroundColor DarkGray
Start-Sleep -Seconds 3

# Open Default Web Browser
Start-Process "http://localhost:3000"

# ------------------------------------------------------------------------------
# Summary & Information Console
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "        ALL SERVICES SUCCESSFULLY LAUNCHED IN WINDOWS 11         " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Web Dashboard   : http://localhost:3000" -ForegroundColor White
Write-Host "  API Root        : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  Swagger UI Docs : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  OpenAPI JSON    : http://127.0.0.1:8000/openapi.json" -ForegroundColor White
Write-Host "  Local Ollama    : http://127.0.0.1:11434" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  To stop services, simply close the respective terminal windows." -ForegroundColor DarkGray
Write-Host ""


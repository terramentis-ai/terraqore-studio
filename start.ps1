# Start script for FlyntCore - Windows PowerShell

param(
    [ValidateSet("both", "backend", "frontend")]
    [string]$Mode = "both"
)

$ProjectRoot = Get-Location
$BackendDir = "$ProjectRoot\core_clli"
$FrontendDir = "$ProjectRoot\gui"

Write-Host "=========================================="
Write-Host "FlyntCore v1.0 - Start Script (Windows)"
Write-Host "=========================================="
Write-Host ""

function Print-Status {
    Write-Host "[✓] $args" -ForegroundColor Green
}

function Print-Info {
    Write-Host "[i] $args" -ForegroundColor Yellow
}

$StartBackend = $Mode -eq "both" -or $Mode -eq "backend"
$StartFrontend = $Mode -eq "both" -or $Mode -eq "frontend"

# Start backend
if ($StartBackend) {
    Print-Info "Starting backend..."
    Set-Location $BackendDir
    
    # Activate virtual environment
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & ".\.venv\Scripts\Activate.ps1"
    }
    
    # Check if Ollama is running
    $OllamaRunning = $false
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $OllamaRunning = $true
        }
    } catch {
        $OllamaRunning = $false
    }
    
    if (-not $OllamaRunning) {
        Print-Info "Note: Ollama is not running. Start with: ollama serve"
    }
    
    Print-Status "Starting backend on http://127.0.0.1:8000"
    Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "backend_main:app", "--host", "127.0.0.1", "--port", "8000" -NoNewWindow
    Start-Sleep -Seconds 2
}

# Start frontend
if ($StartFrontend) {
    Print-Info "Starting frontend..."
    Set-Location $FrontendDir
    
    Print-Status "Starting frontend on http://localhost:3001"
    Start-Process -FilePath "npm" -ArgumentList "run", "dev" -NoNewWindow
    Start-Sleep -Seconds 2
}

Write-Host ""
Print-Status "=========================================="
Print-Status "FlyntCore is running!"
Print-Status "=========================================="
Write-Host ""

if ($StartBackend) {
    Write-Host "Backend API: http://127.0.0.1:8000"
    Write-Host "API Docs: http://127.0.0.1:8000/docs"
}

if ($StartFrontend) {
    Write-Host "Frontend: http://localhost:3001"
}

Write-Host ""
Print-Info "Processes started. Check your terminal windows for logs."
Write-Host ""

Set-Location $ProjectRoot

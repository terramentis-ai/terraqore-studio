# Start script for TERRAQORE - Windows PowerShell

param(
    [ValidateSet("both", "backend", "frontend")]
    [string]$Mode = "both"
)

$ProjectRoot = Get-Location
$BackendDir = "$ProjectRoot\core_cli"
$FrontendDir = "$ProjectRoot\gui"
$OllamaRuntimeDir = "$ProjectRoot\ollama_runtime"
$OllamaExe = "$OllamaRuntimeDir\bin\ollama.exe"

Write-Host "=========================================="
Write-Host "TERRAQORE v1.5 - Start Script (Windows)"
Write-Host "=========================================="
Write-Host ""

function Print-Status {
    Write-Host "[✓] $args" -ForegroundColor Green
}

function Print-Info {
    Write-Host "[i] $args" -ForegroundColor Yellow
}

function Print-Error {
    Write-Host "[✗] $args" -ForegroundColor Red
}

# ============================================
# PHASE 4: AUTO-START BUNDLED OLLAMA
# ============================================

function Start-BundledOllama {
    Print-Info "Checking for bundled Ollama runtime..."
    
    if (Test-Path $OllamaExe) {
        Print-Status "Found bundled Ollama at $OllamaExe"
        
        # Check if Ollama already running
        $OllamaRunning = $false
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                $OllamaRunning = $true
                Print-Status "Ollama already running at http://localhost:11434"
            }
        } catch {
            $OllamaRunning = $false
        }
        
        if (-not $OllamaRunning) {
            Print-Info "Starting bundled Ollama server..."
            
            # Set environment for bundled models
            $env:OLLAMA_MODELS = "$OllamaRuntimeDir\models"
            $env:OLLAMA_HOST = "127.0.0.1:11434"
            
            # Start Ollama in background
            $OllamaProcess = Start-Process `
                -FilePath $OllamaExe `
                -ArgumentList "serve" `
                -WorkingDirectory $OllamaRuntimeDir `
                -WindowStyle Hidden `
                -PassThru
            
            # Wait for startup
            $MaxWait = 10
            $Waited = 0
            $Started = $false
            
            while ($Waited -lt $MaxWait) {
                Start-Sleep -Seconds 1
                $Waited++
                
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
                    if ($response.StatusCode -eq 200) {
                        $Started = $true
                        break
                    }
                } catch {
                    # Keep waiting
                }
                
                Write-Host "." -NoNewline
            }
            
            Write-Host ""
            
            if ($Started) {
                Print-Status "Bundled Ollama started successfully (PID: $($OllamaProcess.Id))"
                
                # Save PID for cleanup
                $OllamaProcess.Id | Out-File "$ProjectRoot\.ollama_pid" -Force
                
                return $true
            } else {
                Print-Error "Bundled Ollama failed to start within ${MaxWait}s"
                return $false
            }
        }
        
        return $true
    } else {
        Print-Info "Bundled Ollama not found. Checking system installation..."
        
        # Check if system Ollama is running
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Print-Status "System Ollama detected and running"
                return $true
            }
        } catch {
            Print-Error "No Ollama found (bundled or system). Install Ollama or run: python core_cli\tools\ollama_bundler.py"
            return $false
        }
    }
}

# Start bundled Ollama first
$OllamaReady = Start-BundledOllama

if (-not $OllamaReady) {
    Print-Info "TerraQore will run with cloud-only mode (no local Ollama)"
}

# ============================================
# START BACKEND & FRONTEND
# ============================================

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
Print-Status "TERRAQORE is running!"
Print-Status "=========================================="
Write-Host ""

if ($OllamaReady) {
    Write-Host "Ollama: http://localhost:11434" -ForegroundColor Cyan
}

if ($StartBackend) {
    Write-Host "Backend API: http://127.0.0.1:8000"
    Write-Host "API Docs: http://127.0.0.1:8000/docs"
}

if ($StartFrontend) {
    Write-Host "Frontend: http://localhost:3001"
}

Write-Host ""
Print-Info "Processes started. Check your terminal windows for logs."
Print-Info "Press Ctrl+C to stop all services"
Write-Host ""

# Cleanup function
function Stop-BundledOllama {
    if (Test-Path "$ProjectRoot\.ollama_pid") {
        $OllamaPID = Get-Content "$ProjectRoot\.ollama_pid"
        
        try {
            $OllamaProcess = Get-Process -Id $OllamaPID -ErrorAction SilentlyContinue
            if ($OllamaProcess) {
                Print-Info "Stopping bundled Ollama (PID: $OllamaPID)..."
                Stop-Process -Id $OllamaPID -Force
                Print-Status "Bundled Ollama stopped"
            }
        } catch {
            # Process already stopped
        }
        
        Remove-Item "$ProjectRoot\.ollama_pid" -Force -ErrorAction SilentlyContinue
    }
}

# Register cleanup on exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-BundledOllama
}

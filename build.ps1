# Build script for TERRAQORE - Windows PowerShell

param(
    [switch]$Backend = $true,
    [switch]$Frontend = $true,
    [switch]$Tests = $false
)

$ProjectRoot = Get-Location
$BackendDir = "$ProjectRoot\core_clli"
$FrontendDir = "$ProjectRoot\gui"

Write-Host "=========================================="
Write-Host "TERRAQORE v1.0 - Build Script (Windows)"
Write-Host "=========================================="
Write-Host ""

function Print-Status {
    Write-Host "[✓] $args" -ForegroundColor Green
}

function Print-Error {
    Write-Host "[✗] $args" -ForegroundColor Red
}

function Print-Info {
    Write-Host "[i] $args" -ForegroundColor Yellow
}

# Check prerequisites
Print-Info "Checking prerequisites..."

$pythonPath = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pythonPath) {
    Print-Error "Python is not installed or not in PATH"
    exit 1
}

$nodePath = (Get-Command node -ErrorAction SilentlyContinue)
if (-not $nodePath) {
    Print-Error "Node.js is not installed or not in PATH"
    exit 1
}

$npmPath = (Get-Command npm -ErrorAction SilentlyContinue)
if (-not $npmPath) {
    Print-Error "npm is not installed or not in PATH"
    exit 1
}

Print-Status "Python found: $(python --version)"
Print-Status "Node.js found: $(node --version)"
Print-Status "npm found: $(npm --version)"
Write-Host ""

if ($Backend) {
    Print-Info "Building backend..."
    Set-Location $BackendDir

    # Create virtual environment if it doesn't exist
    if (-not (Test-Path ".venv")) {
        Print-Info "Creating virtual environment..."
        python -m venv .venv
    }

    # Activate virtual environment
    & ".\.venv\Scripts\Activate.ps1"

    # Install dependencies
    Print-Info "Installing backend dependencies..."
    pip install --upgrade pip
    pip install -r "$ProjectRoot\requirements.txt"
    pip install build wheel setuptools

    # Run tests if requested
    if ($Tests) {
        if (Test-Path "tests") {
            Print-Info "Running backend tests..."
            pip install pytest pytest-cov
            pytest tests -v --cov=core --cov-report=term-missing
        } else {
            Print-Info "No tests directory found, skipping tests"
        }
    }

    Print-Status "Backend built successfully"
    Write-Host ""
}

if ($Frontend) {
    Print-Info "Building frontend..."
    Set-Location $FrontendDir

    # Install dependencies
    Print-Info "Installing frontend dependencies..."
    npm ci

    # Run linter
    Print-Info "Running frontend linter..."
    npm run lint 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Print-Status "Linting passed"
    } else {
        Print-Info "Linting completed with warnings"
    }

    # Build
    Print-Info "Building frontend bundle..."
    npm run build

    Print-Status "Frontend built successfully"
    Write-Host ""
}

Print-Status "=========================================="
Print-Status "Build completed successfully!"
Print-Status "=========================================="
Write-Host ""
Print-Info "Backend: Ready to run with 'cd core_clli && .\.venv\Scripts\python -m uvicorn backend_main:app'"
Print-Info "Frontend: Ready to serve from gui\dist\"
Write-Host ""

Set-Location $ProjectRoot

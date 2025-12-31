# TerraQore Setup Script
# Run this to configure your API key or check Ollama status

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "TerraQore Configuration Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is running
Write-Host "[1] Checking Ollama status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "    ✓ Ollama is running!" -ForegroundColor Green
        
        # Check for phi3.5 model
        $models = ($response.Content | ConvertFrom-Json).models
        $hasPhi3 = $models | Where-Object { $_.name -like "*phi3*" }
        
        if ($hasPhi3) {
            Write-Host "    ✓ Phi3 model available: $($hasPhi3.name)" -ForegroundColor Green
            Write-Host ""
            Write-Host "You can use Ollama! Current config is set to phi3:latest" -ForegroundColor Green
        } else {
            Write-Host "    ⚠ Phi3 model not found. Available models:" -ForegroundColor Yellow
            $models | ForEach-Object { Write-Host "      - $($_.name)" }
        }
    }
} catch {
    Write-Host "    ✗ Ollama is NOT running" -ForegroundColor Red
    Write-Host "    Start it with: ollama serve" -ForegroundColor Yellow
    Write-Host "    Or pull phi3.5: ollama pull phi3.5" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2] Checking Gemini API Key..." -ForegroundColor Yellow

$geminiKey = $env:GEMINI_API_KEY
if ($geminiKey) {
    Write-Host "    ✓ GEMINI_API_KEY is set: $($geminiKey.Substring(0, 10))..." -ForegroundColor Green
} else {
    Write-Host "    ✗ GEMINI_API_KEY not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "To set your Gemini API key:" -ForegroundColor Yellow
    Write-Host '    $env:GEMINI_API_KEY="YOUR_API_KEY_HERE"' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or for permanent (add to PowerShell profile):" -ForegroundColor Yellow
    Write-Host '    [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "YOUR_KEY", "User")' -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[3] Current Configuration" -ForegroundColor Yellow
$configPath = "core_cli\config\settings.yaml"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw
    if ($config -match 'primary_provider:\s*(\w+)') {
        $provider = $Matches[1]
        Write-Host "    Primary Provider: $provider" -ForegroundColor Cyan
        
        if ($provider -eq "gemini" -and -not $geminiKey) {
            Write-Host "    ⚠ Config set to Gemini but no API key found!" -ForegroundColor Yellow
        } elseif ($provider -eq "ollama") {
            Write-Host "    ℹ Config set to Ollama (requires ollama serve)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "    ⚠ Config file not found: $configPath" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option A: Use Gemini (Recommended)" -ForegroundColor Green
Write-Host '  1. Set API key: $env:GEMINI_API_KEY="your_key"' -ForegroundColor White
Write-Host '  2. Update config: Edit core_cli\config\settings.yaml' -ForegroundColor White
Write-Host '     Change primary_provider: ollama -> gemini' -ForegroundColor White
Write-Host ""
Write-Host "Option B: Use Ollama (Local)" -ForegroundColor Green
Write-Host "  1. Start Ollama: ollama serve" -ForegroundColor White
Write-Host "  2. Pull model: ollama pull phi3.5" -ForegroundColor White
Write-Host "  3. Config already set for Ollama" -ForegroundColor White
Write-Host ""
Write-Host "Then run:" -ForegroundColor Yellow
Write-Host "  cd core_cli" -ForegroundColor White
Write-Host "  python -m cli.main init" -ForegroundColor White
Write-Host "==================================" -ForegroundColor Cyan

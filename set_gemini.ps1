# Quick script to set Gemini API key and switch to Gemini
param(
    [Parameter(Mandatory=$true)]
    [string]$ApiKey
)

Write-Host "Setting up Gemini..." -ForegroundColor Cyan

# Set environment variable
$env:GEMINI_API_KEY = $ApiKey
Write-Host "✓ Set GEMINI_API_KEY environment variable" -ForegroundColor Green

# Update config file to use Gemini
$configPath = "core_cli\config\settings.yaml"
$config = Get-Content $configPath -Raw

# Replace primary_provider
$config = $config -replace 'primary_provider:\s*\w+', 'primary_provider: gemini'

Set-Content -Path $configPath -Value $config
Write-Host "✓ Updated config to use Gemini as primary provider" -ForegroundColor Green

Write-Host ""
Write-Host "All set! Now run:" -ForegroundColor Yellow
Write-Host "  cd core_cli" -ForegroundColor White
Write-Host "  python -m cli.main init" -ForegroundColor White

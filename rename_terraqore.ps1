# TerraQore Rename Script - Simplified
# Renames all instances of TerraQore/TERRAQORE to TERRAQORE/TerraQore

Write-Host "`n=================================" -ForegroundColor Cyan
Write-Host "  TerraQore -> TERRAQORE RENAME  " -ForegroundColor Cyan
Write-Host "=================================`n" -ForegroundColor Cyan

$rootPath = "C:\Users\user\Desktop\TERRAQORE_v1.0_pre_release"

# Define replacement mappings
$replacements = @(
    @{Old='github.com/TERRAQORE'; New='github.com/TERRAQORE'}
    @{Old='github.com/terraqore-studio/terraqore'; New='github.com/terraqore-studio/terraqore'}
    @{Old='github.com/USERNAME/TERRAQORE'; New='github.com/USERNAME/TERRAQORE'}
    @{Old='dev@terraqore.com'; New='dev@terraqore.com'}
    @{Old='dev@terraqore.com'; New='dev@terraqore.com'}
    @{Old='terraqore.com'; New='terraqore.com'}
    @{Old='terraqore.com'; New='terraqore.com'}
    @{Old='TERRAQORE_FORCE_OLLAMA'; New='TERRAQORE_FORCE_OLLAMA'}
    @{Old='from terraqore_api'; New='from terraqore_api'}
    @{Old='import terraqore_api'; New='import terraqore_api'}
    @{Old='terraqore_api/'; New='terraqore_api/'}
    @{Old='terraqore_api.'; New='terraqore_api.'}
    @{Old='terraqoreAPI'; New='terraqoreAPI'}
    @{Old='terraqoreAPIClient'; New='TerraQoreAPIClient'}
    @{Old='terraqoreAPIService'; New='TerraQoreAPIService'}
    @{Old="terraqoreAPIService"; New="terraqoreAPIService"}
    @{Old="./services/terraqoreAPIService"; New="./services/terraqoreAPIService"}
    @{Old='terraqore.db'; New='terraqore.db'}
    @{Old='terraqore_build.db'; New='terraqore_build.db'}
    @{Old='terraqore_attribution.db'; New='terraqore_attribution.db'}
    @{Old='terraqore.log'; New='terraqore.log'}
    @{Old='terraqore-api'; New='terraqore-api'}
    @{Old='terraqore-studio'; New='terraqore-studio'}
    @{Old='TerraQoreFlow_1.jpg'; New='TerraQoreFlow_1.jpg'}
    @{Old='TerraQore_implementation_guide'; New='TerraQore_implementation_guide'}
    @{Old='TerraQoreConfig'; New='TerraQoreConfig'}
    @{Old='TerraQoreService'; New='TerraQoreService'}
    @{Old='get_terraqore_service'; New='get_terraqore_service'}
    @{Old='TERRAQORE v1.1'; New='TERRAQORE v1.1'}
    @{Old='TERRAQORE v1.0'; New='TERRAQORE v1.0'}
    @{Old='TERRAQORE v2.0'; New='TERRAQORE v2.0'}
    @{Old='TERRAQORE Development'; New='TERRAQORE Development'}
    @{Old='TERRAQORE -'; New='TERRAQORE -'}
    @{Old='TERRAQORE:'; New='TERRAQORE:'}
    @{Old='TERRAQORE Backend'; New='TERRAQORE Backend'}
    @{Old='TERRAQORE API'; New='TERRAQORE API'}
    @{Old='TERRAQORE Attribution'; New='TERRAQORE Attribution'}
    @{Old='TERRAQORE Documentation'; New='TERRAQORE Documentation'}
    @{Old='TERRAQORE Project'; New='TERRAQORE Project'}
    @{Old='TERRAQORE-generated'; New='TERRAQORE-generated'}
    @{Old='TERRAQORE.'; New='TERRAQORE.'}
    @{Old='TERRAQORE'; New='TERRAQORE'}
    @{Old='TerraQore Studio Backend'; New='TerraQore Studio Backend'}
    @{Old='TerraQore Studio Frontend'; New='TerraQore Studio Frontend'}
    @{Old='TerraQore Studio -'; New='TerraQore Studio -'}
    @{Old='TerraQore Studio'; New='TerraQore Studio'}
    @{Old='TerraQore Agent'; New='TerraQore Agent'}
    @{Old='TerraQore API'; New='TerraQore API'}
    @{Old='TerraQore Base'; New='TerraQore Base'}
    @{Old='TerraQore Phase'; New='TerraQore Phase'}
    @{Old='TerraQore PSMP'; New='TerraQore PSMP'}
    @{Old='TerraQore Research'; New='TerraQore Research'}
    @{Old='TerraQore Context'; New='TerraQore Context'}
    @{Old='TerraQore State'; New='TerraQore State'}
    @{Old='TerraQore LLM'; New='TerraQore LLM'}
    @{Old='TerraQore Core'; New='TerraQore Core'}
    @{Old='TerraQore RAG'; New='TerraQore RAG'}
    @{Old='TerraQore Error'; New='TerraQore Error'}
    @{Old='TerraQore Project'; New='TerraQore Project'}
    @{Old='TerraQore Demo'; New='TerraQore Demo'}
    @{Old='TerraQore security'; New='TerraQore security'}
    @{Old='TerraQore security'; New='TerraQore Security'}
    @{Old='TerraQore system'; New='TerraQore system'}
    @{Old='TerraQore is'; New='TerraQore is'}
    @{Old='TerraQore Team'; New='TerraQore Team'}
    @{Old='TerraQore not initialized'; New='TerraQore not initialized'}
    @{Old='of TerraQore'; New='of TerraQore'}
    @{Old='for TerraQore'; New='for TerraQore'}
    @{Old='to TerraQore'; New='to TerraQore'}
    @{Old='by TerraQore'; New='by TerraQore'}
    @{Old='with TerraQore'; New='with TerraQore'}
    @{Old='TerraQore.'; New='TerraQore.'}
    @{Old='TerraQore,'; New='TerraQore,'}
    @{Old='TerraQore!'; New='TerraQore!'}
    @{Old='TerraQore?'; New='TerraQore?'}
    @{Old='TerraQore '; New='TerraQore '}
    @{Old='terraqore-studio'; New='TerraQore-Studio'}
    @{Old='terraqore-studio/'; New='terraqore-studio/'}
    @{Old='TerraQore init'; New='terraqore init'}
    @{Old='TerraQore new'; New='terraqore new'}
    @{Old='TerraQore list'; New='terraqore list'}
    @{Old='TerraQore show'; New='terraqore show'}
    @{Old='TerraQore delete'; New='terraqore delete'}
    @{Old='TerraQore ideate'; New='terraqore ideate'}
    @{Old='TerraQore plan'; New='terraqore plan'}
    @{Old='TerraQore generate'; New='terraqore generate'}
    @{Old='TerraQore validate'; New='terraqore validate'}
    @{Old='TerraQore train'; New='terraqore train'}
    @{Old='TerraQore serve'; New='terraqore serve'}
    @{Old='TerraQore deploy'; New='terraqore deploy'}
    @{Old='TerraQore status'; New='terraqore status'}
    @{Old='TerraQore config'; New='terraqore config'}
    @{Old='TerraQore logs'; New='terraqore logs'}
    @{Old='TerraQore test-critique'; New='terraqore test-critique'}
    @{Old='TerraQore conflicts'; New='terraqore conflicts'}
    @{Old='TerraQore resolve-conflicts'; New='terraqore resolve-conflicts'}
    @{Old='TerraQore unblock-project'; New='terraqore unblock-project'}
    @{Old='TerraQore manifest'; New='terraqore manifest'}
    @{Old='TerraQore dashboard'; New='terraqore dashboard'}
    @{Old='TerraQore health-check'; New='terraqore health-check'}
    @{Old='TerraQore run'; New='terraqore run'}
    @{Old='TerraQore create'; New='terraqore create'}
    @{Old='TerraQore generate-tests'; New='terraqore generate-tests'}
    @{Old='TerraQore test-coverage'; New='terraqore test-coverage'}
    @{Old='TerraQore --help'; New='terraqore --help'}
    @{Old='TerraQore --version'; New='terraqore --version'}
    @{Old='run: terraqore'; New='run: terraqore'}
    @{Old='Command: terraqore'; New='Command: terraqore'}
    @{Old='Example: terraqore'; New='Example: terraqore'}
    @{Old='cd terraqore-studio'; New='cd terraqore-studio'}
)

$extensions = @('*.md', '*.py', '*.ts', '*.tsx', '*.js', '*.jsx', '*.html', '*.txt', '*.yaml', '*.yml', '*.json', '*.sh', '*.ps1')
$excludePatterns = @('*.pyc', '*__pycache__*', '*node_modules*', '*.db', '*.jpg', '*.png', '*.gif', '*.ico', '*.egg-info*', '*dist/*', '*build/*', '*rename_to_terraqore.ps1')

$totalReplacements = 0
$filesModified = 0

Write-Host "Scanning workspace..." -ForegroundColor Yellow

foreach ($ext in $extensions) {
    $files = Get-ChildItem -Path $rootPath -Filter $ext -Recurse -File | Where-Object {
        $exclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($_.FullName -like $pattern) {
                $exclude = $true
                break
            }
        }
        -not $exclude
    }
    
    foreach ($file in $files) {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
        
        if ($null -eq $content) { continue }
        
        $modified = $false
        $originalContent = $content
        
        foreach ($replacement in $replacements) {
            if ($content -match [regex]::Escape($replacement.Old)) {
                $content = $content -replace [regex]::Escape($replacement.Old), $replacement.New
                $modified = $true
            }
        }
        
        if ($modified) {
            Set-Content -Path $file.FullName -Value $content -NoNewline
            $filesModified++
            
            $changes = 0
            foreach ($replacement in $replacements) {
                $changes += ([regex]::Matches($originalContent, [regex]::Escape($replacement.Old))).Count
            }
            $totalReplacements += $changes
            
            Write-Host "  [OK] $($file.Name) - $changes replacements" -ForegroundColor Green
        }
    }
}

Write-Host "`n=================================" -ForegroundColor Green
Write-Host "  RENAME COMPLETE!" -ForegroundColor Green
Write-Host "=================================`n" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Files Modified: $filesModified" -ForegroundColor White
Write-Host "  Total Replacements: $totalReplacements" -ForegroundColor White
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Review: git status" -ForegroundColor White
Write-Host "  2. Test: pytest core_cli/tests/security/ -v" -ForegroundColor White
Write-Host "  3. Stage: git add ." -ForegroundColor White
Write-Host "  4. Commit: git commit -m `"Rebrand to TERRAQORE`"" -ForegroundColor White
Write-Host ""

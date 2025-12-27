# TerraQore Rename Script
# Renames all instances of Flynt/FlyntCore to TERRAQORE/TerraQore

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   FLYNT → TERRAQORE MASS RENAME SCRIPT                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$rootPath = "C:\Users\user\Desktop\FlyntCore_v1.0_pre_release"

# Define replacement mappings (order matters!)
$replacements = @(
    # URLs and domains first
    @{Old='github.com/FlyntCore'; New='github.com/TERRAQORE'}
    @{Old='github.com/flyntstudio/flynt'; New='github.com/terraqore-studio/terraqore'}
    @{Old='github.com/USERNAME/FlyntCore'; New='github.com/USERNAME/TERRAQORE'}
    @{Old='dev@flyntcore.ai'; New='dev@terraqore.com'}
    @{Old='dev@flyntstudio.dev'; New='dev@terraqore.com'}
    @{Old='flyntcore.ai'; New='terraqore.com'}
    @{Old='flynt.ai'; New='terraqore.com'}
    
    # Environment variables
    @{Old='FLYNT_FORCE_OLLAMA'; New='TERRAQORE_FORCE_OLLAMA'}
    
    # Python imports and modules
    @{Old='from flynt_api'; New='from terraqore_api'}
    @{Old='import flynt_api'; New='import terraqore_api'}
    @{Old='flynt_api/'; New='terraqore_api/'}
    @{Old='flynt_api.'; New='terraqore_api.'}
    
    # TypeScript/JS imports
    @{Old='flyntAPI'; New='terraqoreAPI'}
    @{Old='FlyntAPIClient'; New='TerraQoreAPIClient'}
    @{Old='FlyntAPIService'; New='TerraQoreAPIService'}
    @{Old="flyntAPIService"; New="terraqoreAPIService"}
    @{Old="from './services/flyntAPIService'"; New="from './services/terraqoreAPIService'"}
    @{Old="./services/flyntAPIService"; New="./services/terraqoreAPIService"}
    
    # Database files
    @{Old='flynt.db'; New='terraqore.db'}
    @{Old='flynt_build.db'; New='terraqore_build.db'}
    @{Old='flynt_attribution.db'; New='terraqore_attribution.db'}
    @{Old='flynt.log'; New='terraqore.log'}
    
    # Docker images
    @{Old='flynt-api'; New='terraqore-api'}
    @{Old='flynt-studio'; New='terraqore-studio'}
    
    # File paths
    @{Old='FlyntFlow_1.jpg'; New='TerraQoreFlow_1.jpg'}
    @{Old='Flynt_implementation_guide'; New='TerraQore_implementation_guide'}
    
    # Config classes
    @{Old='FlyntConfig'; New='TerraQoreConfig'}
    @{Old='FlyntService'; New='TerraQoreService'}
    @{Old='get_flynt_service'; New='get_terraqore_service'}
    
    # Brand names (order matters - specific to general)
    @{Old='FlyntCore v1.1'; New='TERRAQORE v1.1'}
    @{Old='FlyntCore v1.0'; New='TERRAQORE v1.0'}
    @{Old='FlyntCore v2.0'; New='TERRAQORE v2.0'}
    @{Old='FlyntCore Development'; New='TERRAQORE Development'}
    @{Old='FlyntCore -'; New='TERRAQORE -'}
    @{Old='FlyntCore:'; New='TERRAQORE:'}
    @{Old='FlyntCore Backend'; New='TERRAQORE Backend'}
    @{Old='FlyntCore API'; New='TERRAQORE API'}
    @{Old='FlyntCore Attribution'; New='TERRAQORE Attribution'}
    @{Old='FlyntCore Documentation'; New='TERRAQORE Documentation'}
    @{Old='FlyntCore Project'; New='TERRAQORE Project'}
    @{Old='FlyntCore-generated'; New='TERRAQORE-generated'}
    @{Old='FlyntCore.'; New='TERRAQORE.'}
    @{Old='FlyntCore'; New='TERRAQORE'}
    
    @{Old='Flynt Studio Backend'; New='TerraQore Studio Backend'}
    @{Old='Flynt Studio Frontend'; New='TerraQore Studio Frontend'}
    @{Old='Flynt Studio -'; New='TerraQore Studio -'}
    @{Old='Flynt Studio'; New='TerraQore Studio'}
    @{Old='Flynt Agent'; New='TerraQore Agent'}
    @{Old='Flynt API'; New='TerraQore API'}
    @{Old='Flynt Base'; New='TerraQore Base'}
    @{Old='Flynt Phase'; New='TerraQore Phase'}
    @{Old='Flynt PSMP'; New='TerraQore PSMP'}
    @{Old='Flynt Research'; New='TerraQore Research'}
    @{Old='Flynt Context'; New='TerraQore Context'}
    @{Old='Flynt State'; New='TerraQore State'}
    @{Old='Flynt LLM'; New='TerraQore LLM'}
    @{Old='Flynt Core'; New='TerraQore Core'}
    @{Old='Flynt RAG'; New='TerraQore RAG'}
    @{Old='Flynt Error'; New='TerraQore Error'}
    @{Old='Flynt Project'; New='TerraQore Project'}
    @{Old='Flynt Demo'; New='TerraQore Demo'}
    @{Old='Flynt security'; New='TerraQore security'}
    @{Old='Flynt Security'; New='TerraQore Security'}
    @{Old='Flynt system'; New='TerraQore system'}
    @{Old='Flynt is'; New='TerraQore is'}
    @{Old='Flynt Team'; New='TerraQore Team'}
    @{Old='Flynt not initialized'; New='TerraQore not initialized'}
    @{Old='of Flynt'; New='of TerraQore'}
    @{Old='for Flynt'; New='for TerraQore'}
    @{Old='to Flynt'; New='to TerraQore'}
    @{Old='by Flynt'; New='by TerraQore'}
    @{Old='with Flynt'; New='with TerraQore'}
    @{Old='Flynt.'; New='TerraQore.'}
    @{Old='Flynt,'; New='TerraQore,'}
    @{Old='Flynt!'; New='TerraQore!'}
    @{Old='Flynt?'; New='TerraQore?'}
    @{Old='Flynt"'; New='TerraQore"'}
    @{Old="'Flynt"; New="'TerraQore"}
    @{Old='"Flynt'; New='"TerraQore'}
    @{Old='Flynt '; New='TerraQore '}
    @{Old='Flynt-Studio'; New='TerraQore-Studio'}
    @{Old='Flynt`n'; New='TerraQore`n'}
    
    # Command line tool (lowercase)
    @{Old='flynt-studio/'; New='terraqore-studio/'}
    @{Old='flynt init'; New='terraqore init'}
    @{Old='flynt new'; New='terraqore new'}
    @{Old='flynt list'; New='terraqore list'}
    @{Old='flynt show'; New='terraqore show'}
    @{Old='flynt delete'; New='terraqore delete'}
    @{Old='flynt ideate'; New='terraqore ideate'}
    @{Old='flynt plan'; New='terraqore plan'}
    @{Old='flynt generate'; New='terraqore generate'}
    @{Old='flynt validate'; New='terraqore validate'}
    @{Old='flynt train'; New='terraqore train'}
    @{Old='flynt serve'; New='terraqore serve'}
    @{Old='flynt deploy'; New='terraqore deploy'}
    @{Old='flynt status'; New='terraqore status'}
    @{Old='flynt config'; New='terraqore config'}
    @{Old='flynt logs'; New='terraqore logs'}
    @{Old='flynt test-critique'; New='terraqore test-critique'}
    @{Old='flynt conflicts'; New='terraqore conflicts'}
    @{Old='flynt resolve-conflicts'; New='terraqore resolve-conflicts'}
    @{Old='flynt unblock-project'; New='terraqore unblock-project'}
    @{Old='flynt manifest'; New='terraqore manifest'}
    @{Old='flynt dashboard'; New='terraqore dashboard'}
    @{Old='flynt health-check'; New='terraqore health-check'}
    @{Old='flynt run'; New='terraqore run'}
    @{Old='flynt create'; New='terraqore create'}
    @{Old='flynt generate-tests'; New='terraqore generate-tests'}
    @{Old='flynt test-coverage'; New='terraqore test-coverage'}
    @{Old='flynt --help'; New='terraqore --help'}
    @{Old='flynt --version'; New='terraqore --version'}
    @{Old='run: flynt'; New='run: terraqore'}
    @{Old='Command: flynt'; New='Command: terraqore'}
    @{Old='Example: flynt'; New='Example: terraqore'}
    @{Old='cd flynt-studio'; New='cd terraqore-studio'}
)

# File extensions to process
$extensions = @('*.md', '*.py', '*.ts', '*.tsx', '*.js', '*.jsx', '*.html', '*.txt', '*.yaml', '*.yml', '*.json', '*.sh', '*.ps1')

# Files to exclude (binary or generated)
$excludePatterns = @('*.pyc', '*__pycache__*', '*node_modules*', '*.db', '*.jpg', '*.png', '*.gif', '*.ico', '*.egg-info*', '*dist/*', '*build/*')

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
            
            # Count replacements
            $changes = 0
            foreach ($replacement in $replacements) {
                $changes += ([regex]::Matches($originalContent, [regex]::Escape($replacement.Old))).Count
            }
            $totalReplacements += $changes
            
            Write-Host "  ✓ $($file.Name) - $changes replacements" -ForegroundColor Green
        }
    }
}

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              RENAME COMPLETE!                              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  • Files Modified: $filesModified" -ForegroundColor White
Write-Host "  • Total Replacements: $totalReplacements" -ForegroundColor White
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Review changes: git status" -ForegroundColor White
Write-Host "  2. Run tests: pytest core_cli/tests/security/ -v" -ForegroundColor White
Write-Host "  3. Stage changes: git add ." -ForegroundColor White
Write-Host "  4. Commit: git commit -m `"Rebrand from Flynt to TERRAQORE`"" -ForegroundColor White
Write-Host ""

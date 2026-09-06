#Requires -Version 5.1
<#
.SYNOPSIS
  Compare locally-installed shared agents/skills against their canonical source in cp-ai-toolkit.

.DESCRIPTION
  Read-only drift check. Compares (by SHA256) every file under:
    .github/agents/*.agent.md
    .github/skills/**
    .claude/skills/**
    .cursor/rules/*.mdc
  in -ProjectRoot against the same relative path in -ToolkitRoot. Never copies or modifies
  anything — if drift is found, it recommends re-running Install-CPAIAgents.ps1.

.PARAMETER ProjectRoot
  Repo to check. Defaults to the current directory.

.PARAMETER ToolkitRoot
  cp-ai-toolkit root. Auto-detected if omitted: sibling ..\cp-ai-toolkit relative to
  -ProjectRoot, then C:\devops\cp-ai-toolkit.

.EXAMPLE
  pwsh -NoProfile -File .\scripts\start-session\Compare-InstalledAgents.ps1
  pwsh -NoProfile -File .\scripts\start-session\Compare-InstalledAgents.ps1 -ProjectRoot C:\devops\cp-jesse-sandbox
#>
param(
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$ToolkitRoot,

    # Which payload this repo is supposed to have. Must match the profile it was
    # installed with (see seed/manifest.json), otherwise a 'core' repo is reported
    # as drifted for every CP-domain file it deliberately does not carry.
    [ValidateSet('core', 'full')]
    [string]$Profile = 'full'
)

function Resolve-ToolkitRoot {
    param([string]$Hint, [string]$FromProjectRoot)

    if ($Hint -and (Test-Path (Join-Path $Hint 'tools/Install-CPAIAgents.ps1'))) {
        return (Resolve-Path $Hint).Path
    }

    $candidates = @(
        (Join-Path (Split-Path $FromProjectRoot -Parent) 'cp-ai-toolkit'),
        'C:\devops\cp-ai-toolkit'
    )
    foreach ($candidate in $candidates) {
        if (Test-Path (Join-Path $candidate 'tools/Install-CPAIAgents.ps1')) {
            return (Resolve-Path $candidate).Path
        }
    }
    return $null
}

function Get-SharedFilePairs {
    param([string]$ToolkitRoot)

    $pairs = [System.Collections.Generic.List[string]]::new()

    $agentsDir = Join-Path $ToolkitRoot '.github/agents'
    if (Test-Path $agentsDir) {
        Get-ChildItem -Path $agentsDir -Filter '*.agent.md' -File | ForEach-Object {
            $pairs.Add($_.FullName.Substring($ToolkitRoot.Length).TrimStart('\', '/'))
        }
    }

    foreach ($root in @('.github/skills', '.claude/skills')) {
        $dir = Join-Path $ToolkitRoot $root
        if (Test-Path $dir) {
            Get-ChildItem -Path $dir -File -Recurse | ForEach-Object {
                $pairs.Add($_.FullName.Substring($ToolkitRoot.Length).TrimStart('\', '/'))
            }
        }
    }

    $rulesDir = Join-Path $ToolkitRoot '.cursor/rules'
    if (Test-Path $rulesDir) {
        Get-ChildItem -Path $rulesDir -Filter '*.mdc' -File | ForEach-Object {
            $pairs.Add($_.FullName.Substring($ToolkitRoot.Length).TrimStart('\', '/'))
        }
    }

    # .claude/claims/ ships in both profiles - it is core coordination machinery.
    $claimsDir = Join-Path $ToolkitRoot '.claude/claims'
    if (Test-Path $claimsDir) {
        Get-ChildItem -Path $claimsDir -Filter 'README.md' -File | ForEach-Object {
            $pairs.Add($_.FullName.Substring($ToolkitRoot.Length).TrimStart('\', '/'))
        }
    }

    return $pairs
}

function Select-ProfileFiles {
    <#
      Narrow the full file list to what a given profile is supposed to install.
      Keep this in step with the profile table in tools/Install-CPAIAgents.ps1 -
      if the two disagree, the sweep either misses real drift or opens PRs that
      change nothing.
    #>
    param(
        [System.Collections.Generic.List[string]]$Files,
        [string]$Profile
    )

    if ($Profile -eq 'full') { return $Files }

    $coreAgents = @('powershell-validate.agent.md')
    $coreClaudeSkills = @('start-session', 'session-wrap')

    $kept = [System.Collections.Generic.List[string]]::new()
    foreach ($rel in $Files) {
        $norm = $rel -replace '\\', '/'
        $keep = switch -Regex ($norm) {
            '^\.github/agents/(.+)$'      { $coreAgents -contains $Matches[1] }
            '^\.claude/skills/([^/]+)/'   { $coreClaudeSkills -contains $Matches[1] }
            '^\.claude/claims/'           { $true }
            default                       { $false }   # .github/skills, .cursor/rules
        }
        if ($keep) { $kept.Add($rel) }
    }
    return $kept
}

$resolvedToolkitRoot = Resolve-ToolkitRoot -Hint $ToolkitRoot -FromProjectRoot $ProjectRoot
if (-not $resolvedToolkitRoot) {
    Write-Warning "Could not locate cp-ai-toolkit (checked sibling folder of -ProjectRoot and C:\devops\cp-ai-toolkit). Pass -ToolkitRoot explicitly, or skip this check if the toolkit isn't in this workspace."
    exit 1
}

$resolvedProjectRoot = (Resolve-Path $ProjectRoot).Path
if ($resolvedProjectRoot -eq $resolvedToolkitRoot) {
    Write-Host "ProjectRoot is cp-ai-toolkit itself - nothing to compare." -ForegroundColor DarkGray
    exit 0
}

$relFiles = Get-SharedFilePairs -ToolkitRoot $resolvedToolkitRoot
$relFiles = Select-ProfileFiles -Files $relFiles -Profile $Profile
$drift = [System.Collections.Generic.List[object]]::new()

foreach ($rel in $relFiles) {
    $toolkitPath = Join-Path $resolvedToolkitRoot $rel
    $localPath = Join-Path $resolvedProjectRoot $rel

    if (-not (Test-Path $localPath)) {
        $drift.Add([pscustomobject]@{ File = $rel; Status = 'Missing locally' })
        continue
    }

    $toolkitHash = (Get-FileHash -Path $toolkitPath -Algorithm SHA256).Hash
    $localHash = (Get-FileHash -Path $localPath -Algorithm SHA256).Hash
    if ($toolkitHash -ne $localHash) {
        $drift.Add([pscustomobject]@{ File = $rel; Status = 'Stale (differs from toolkit)' })
    }
}

if ($drift.Count -eq 0) {
    Write-Host "All installed shared agents/skills match cp-ai-toolkit [profile: $Profile] ($resolvedToolkitRoot)." -ForegroundColor Green
    exit 0
}

Write-Host "Drift detected vs cp-ai-toolkit [profile: $Profile] ($resolvedToolkitRoot):" -ForegroundColor Yellow
$drift | Format-Table -AutoSize
Write-Host ""
Write-Host "Re-run to update: pwsh -NoProfile -File `"$resolvedToolkitRoot\tools\Install-CPAIAgents.ps1`" -ProjectRoot `"$resolvedProjectRoot`" -Profile $Profile -Force" -ForegroundColor Cyan
exit 2

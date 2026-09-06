#Requires -Version 7.0
<#
.SYNOPSIS
  Audit Concierge seed readiness (prod or dev) after a build.

.DESCRIPTION
  Validates seed file presence, VERSION.json vs frontmatter, bootstrap contracts,
  and catalog package pins. Prints a scorecard and optional CE manual smoke list.
  Does not call Claude Enterprise APIs.

.PARAMETER Lane
  dev  → docs/claude-projects/cp-skills-concierge-dev/seed
  prod → docs/claude-projects/cp-skills-concierge/seed

  ("beta" was renamed to "dev" 2026-07-23 across the rest of the repo --
  this script previously still said "beta" throughout, which is exactly
  the kind of drift this whole guardrail pass exists to catch. Fixed here.)

.PARAMETER SkillsRepo
  Path to cp-claude-enterprise-skills. Defaults to sibling of toolkit or C:\cp-devops\...

.PARAMETER OutDir
  Optional folder for JSON + Markdown report.

.EXAMPLE
  pwsh -File .\scripts\skill-audit\Audit-ConciergeSeed.ps1 -Lane dev
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'prod')]
    [string]$Lane,

    [string]$SkillsRepo,

    [string]$OutDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-SkillsRepo {
    param([string]$Explicit)
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) {
        return (Resolve-Path -LiteralPath $Explicit).Path
    }
    # PSScriptRoot = .../cp-ai-toolkit/scripts/skill-audit
    $toolkitRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    $sibling = Join-Path (Split-Path $toolkitRoot -Parent) 'cp-claude-enterprise-skills'
    foreach ($candidate in @(
            $sibling,
            'C:\cp-devops\cp-claude-enterprise-skills'
        )) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw 'Skills repo not found. Pass -SkillsRepo.'
}

function Get-FrontmatterVersion {
    param(
        [string]$Path,
        [string]$Key
    )
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ($text -match "(?m)^${Key}:\s*(.+)$") {
        return $Matches[1].Trim()
    }
    return $null
}

function Add-Check {
    param(
        [System.Collections.Generic.List[object]]$List,
        [string]$Id,
        [string]$Name,
        [bool]$Pass,
        [string]$Detail,
        [ValidateSet('fail', 'warn')]
        [string]$Severity = 'fail'
    )
    $List.Add([pscustomobject]@{
            id       = $Id
            name     = $Name
            pass     = $Pass
            detail   = $Detail
            severity = $Severity
        }) | Out-Null
}

$skillsRoot = Resolve-SkillsRepo -Explicit $SkillsRepo
$seedRel = if ($Lane -eq 'dev') {
    'docs/claude-projects/cp-skills-concierge-dev/seed'
} else {
    'docs/claude-projects/cp-skills-concierge/seed'
}
$seedDir = Join-Path $skillsRoot $seedRel

$required = @(
    'bootstrap-instructions.md',
    'cp-skills-catalog.md',
    'cp-skills-concierge-operating-guide.md',
    'cp-skills-concierge-manifest.md',
    'VERSION.json'
)

$checks = [System.Collections.Generic.List[object]]::new()
$packages = @()

Write-Host "=== skill-audit Concierge seed ($Lane) ==="
Write-Host "SkillsRepo: $skillsRoot"
Write-Host "Seed:       $seedDir"
Write-Host ''

# --- files present ---
$missingFiles = @()
foreach ($f in $required) {
    $p = Join-Path $seedDir $f
    if (-not (Test-Path -LiteralPath $p)) { $missingFiles += $f }
}
Add-Check -List $checks -Id 'seed.files' -Name 'Required seed files present' `
    -Pass ($missingFiles.Count -eq 0) `
    -Detail ($(if ($missingFiles.Count -eq 0) { 'All five seed files found' } else { 'Missing: ' + ($missingFiles -join ', ') }))

if ($missingFiles.Count -gt 0) {
    Write-Host 'FAIL: seed incomplete — skipping deeper checks.' -ForegroundColor Red
    $failed = @($checks | Where-Object { -not $_.pass })
    $failed | Format-Table id, name, detail -AutoSize
    exit 1
}

$versionPath = Join-Path $seedDir 'VERSION.json'
$catalogPath = Join-Path $seedDir 'cp-skills-catalog.md'
$guidePath = Join-Path $seedDir 'cp-skills-concierge-operating-guide.md'
$manifestPath = Join-Path $seedDir 'cp-skills-concierge-manifest.md'
$bootstrapPath = Join-Path $seedDir 'bootstrap-instructions.md'

$version = Get-Content -LiteralPath $versionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$catalogVerFm = Get-FrontmatterVersion -Path $catalogPath -Key 'ConciergeModuleVersion'
$guideVerFm = Get-FrontmatterVersion -Path $guidePath -Key 'ConciergeModuleVersion'
$controlFm = Get-FrontmatterVersion -Path $manifestPath -Key 'ConciergeControlPlaneVersion'

# --- VERSION.json vs frontmatter ---
$verOk = ($version.catalogVersion -eq $catalogVerFm) -and
($version.guideVersion -eq $guideVerFm) -and
($version.ConciergeControlPlaneVersion -eq $controlFm)

Add-Check -List $checks -Id 'seed.versions' -Name 'VERSION.json matches frontmatter' `
    -Pass:$verOk `
    -Detail ("json catalog=$($version.catalogVersion) guide=$($version.guideVersion) control=$($version.ConciergeControlPlaneVersion); fm catalog=$catalogVerFm guide=$guideVerFm control=$controlFm")

if ($Lane -eq 'dev') {
    $laneOk = ($version.lane -eq 'dev') -or ($null -ne (Get-FrontmatterVersion -Path $catalogPath -Key 'ConciergeLane'))
    Add-Check -List $checks -Id 'seed.lane' -Name 'Dev lane marker present' `
        -Pass:$laneOk `
        -Detail ("VERSION.lane=$($version.lane); catalog ConciergeLane=$(Get-FrontmatterVersion -Path $catalogPath -Key 'ConciergeLane')")
}

# --- bootstrap contracts ---
$bootstrap = Get-Content -LiteralPath $bootstrapPath -Raw -Encoding UTF8
$needles = @(
    'm365_sharepoint_kb_search',
    'M365 - Community Products',
    'ask_user_input'
)
if ($Lane -eq 'dev') {
    $needles += @(
        'includeOneDrive',
        'OneDrive',
        'Microsoft 365'
    )
}
$missingNeedles = [System.Collections.Generic.List[string]]::new()
foreach ($n in $needles) {
    if ($bootstrap.IndexOf($n, [System.StringComparison]::Ordinal) -lt 0) {
        [void]$missingNeedles.Add($n)
    }
}
Add-Check -List $checks -Id 'seed.bootstrap' -Name 'Bootstrap hard contracts' `
    -Pass ($missingNeedles.Count -eq 0) `
    -Detail ($(if ($missingNeedles.Count -eq 0) { 'Required strings present' } else { 'Missing: ' + ($missingNeedles -join ', ') }))

# --- guide choice-UI / KB tool (dev deeper) ---
$guide = Get-Content -LiteralPath $guidePath -Raw -Encoding UTF8
$guideNeedles = [System.Collections.Generic.List[string]]::new()
[void]$guideNeedles.Add('ask_user_input')
[void]$guideNeedles.Add('m365_sharepoint_kb_search')
if ($Lane -eq 'dev') {
    [void]$guideNeedles.Add('OneDrive')
    [void]$guideNeedles.Add("I've connected Microsoft 365")
    [void]$guideNeedles.Add('Skip OneDrive')
}
$missingGuide = [System.Collections.Generic.List[string]]::new()
foreach ($n in $guideNeedles) {
    if ($guide.IndexOf($n, [System.StringComparison]::Ordinal) -lt 0) {
        [void]$missingGuide.Add($n)
    }
}
Add-Check -List $checks -Id 'seed.guide' -Name 'Operating guide contracts' `
    -Pass ($missingGuide.Count -eq 0) `
    -Detail ($(if ($missingGuide.Count -eq 0) { 'Required strings present' } else { 'Missing: ' + ($missingGuide -join ', ') }))

# --- catalog packages ---
$catalog = Get-Content -LiteralPath $catalogPath -Raw -Encoding UTF8
$pkgMatches = [regex]::Matches($catalog, '`([^`]+\.skill)`')
$packages = @(
    @($pkgMatches | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique)
)
Add-Check -List $checks -Id 'catalog.packages' -Name 'Catalog lists .skill package pins' `
    -Pass ($packages.Count -gt 0) `
    -Detail ($(if ($packages.Count -gt 0) { ($packages -join ', ') } else { 'No `*.skill` pins found in catalog' }))

$skillsDir = Join-Path $skillsRoot 'skills'
$missingPkgs = @()
foreach ($pkg in $packages) {
    $pkgPath = Join-Path $skillsDir $pkg
    if (-not (Test-Path -LiteralPath $pkgPath)) {
        $missingPkgs += $pkg
    }
}
# Warn-only if skills/ folder empty of packages (artifacts may live elsewhere)
if ($packages.Count -gt 0) {
    $pkgPass = $missingPkgs.Count -eq 0
    Add-Check -List $checks -Id 'catalog.artifacts' -Name 'Pinned .skill files exist under skills/' `
        -Pass:$pkgPass `
        -Severity warn `
        -Detail ($(if ($pkgPass) { 'All pinned packages found on disk' } else { 'Missing on disk (OK if only installed in CE): ' + ($missingPkgs -join ', ') }))
}

# --- report ---
$failed = @($checks | Where-Object { (-not $_.pass) -and $_.severity -eq 'fail' })
$warned = @($checks | Where-Object { (-not $_.pass) -and $_.severity -eq 'warn' })
$passed = @($checks | Where-Object { $_.pass })

Write-Host "PASS $($passed.Count)  FAIL $($failed.Count)  WARN $($warned.Count)" -ForegroundColor ($(if ($failed.Count) { 'Yellow' } else { 'Green' }))
$checks | Format-Table id, @{n = 'ok'; e = {
        if ($_.pass) { 'PASS' } elseif ($_.severity -eq 'warn') { 'WARN' } else { 'FAIL' }
    }
}, name, detail -Wrap

Write-Host ''
Write-Host '=== CE manual smoke (operator) ==='
@(
    '1. Cold hi — seed menu, no MCP',
    '2. Buttons: full question in choice UI (no orphan dropdown)',
    '3. Gates one-at-a-time (confirm → model → OneDrive if dev)',
    '4. First lookup: m365_sharepoint_kb_search on Community Products',
    '5. OneDrive Yes + OOB missing → connect/skip/upload; no fake connected',
    '6. No thinking/guide dump after taps',
    '7. Instructions == bootstrap body',
    '8. Mounted packages match catalog pins',
    $(if ($Lane -eq 'dev') { '9. Feedback Title prefix DEV —' } else { '9. Feedback loop OK; no seed-refresh offer' })
) | ForEach-Object { Write-Host "  [ ] $_" }

$report = [pscustomobject]@{
    lane       = $Lane
    skillsRepo = $skillsRoot
    seedDir    = $seedDir
    version    = $version
    packages   = $packages
    checks     = $checks
    summary    = [pscustomobject]@{
        pass  = $passed.Count
        fail  = $failed.Count
        warn  = $warned.Count
        ready = ($failed.Count -eq 0)
    }
    generated  = (Get-Date).ToString('o')
}

if ($OutDir) {
    if (-not (Test-Path -LiteralPath $OutDir)) {
        New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $jsonPath = Join-Path $OutDir "skill-audit-$Lane-$stamp.json"
    $mdPath = Join-Path $OutDir "skill-audit-$Lane-$stamp.md"
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    $md = @()
    $md += "# Skill audit — Concierge ($Lane)"
    $md += ''
    $md += "- Ready (automated): **$($report.summary.ready)**"
    $md += "- Pass/Fail: $($report.summary.pass) / $($report.summary.fail)"
    $md += "- Seed: ``$seedDir``"
    $md += ''
    $md += '| Id | Result | Name | Detail |'
    $md += '|---|---|---|---|'
    foreach ($c in $checks) {
        $ok = if ($c.pass) { 'PASS' } else { 'FAIL' }
        $md += "| $($c.id) | $ok | $($c.name) | $($c.detail) |"
    }
    $md += ''
    $md += '## Approved package pins'
    foreach ($p in $packages) { $md += "- ``$p``" }
    $md += ''
    $md += '## CE manual smoke'
    $md += 'See script output checklist — complete in Claude Enterprise before READY.'
    $md -join "`n" | Set-Content -LiteralPath $mdPath -Encoding UTF8
    Write-Host ''
    Write-Host "Wrote $jsonPath"
    Write-Host "Wrote $mdPath"
}

if ($failed.Count -gt 0) {
    exit 1
}
exit 0

<#
.SYNOPSIS
  Parse-check and lint PowerShell files.

.DESCRIPTION
  Runs the PowerShell parser over every target file, and — when PSScriptAnalyzer is
  available — Invoke-ScriptAnalyzer as well.

  If the analyzer is missing this degrades to parser-only. That degradation is
  reported in the PASS line, but by default it still exits 0, which means an
  automated caller cannot tell a real lint pass from a parser-only one. Use
  -RequireAnalyzer in CI and any other non-interactive gate so a missing analyzer
  fails loudly instead of silently reducing coverage.

.PARAMETER RequireAnalyzer
  Fail (exit 2) if PSScriptAnalyzer is not available, instead of falling back to
  parser-only checks. Mutually exclusive with -SkipAnalyzer.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [switch]$SkipAnalyzer,
    [switch]$Strict,
    [switch]$InstallAnalyzer,
    [switch]$RequireAnalyzer
)

$ErrorActionPreference = 'Stop'

function Resolve-Analyzer {
    param([bool]$AutoInstall)

    if (Get-Module -ListAvailable -Name PSScriptAnalyzer) {
        return $true
    }

    $installCmd = 'Install-Module PSScriptAnalyzer -Scope CurrentUser -Force -AllowClobber'

    if ($AutoInstall) {
        Write-Host "PSScriptAnalyzer not found. Installing for current user..."
        Install-Module PSScriptAnalyzer -Scope CurrentUser -Force -AllowClobber
        return $true
    }

    Write-Warning "PSScriptAnalyzer is not installed - only parser (syntax) checks will run."
    Write-Host ""
    Write-Host "To enable full linting, install it with either:" -ForegroundColor Yellow
    Write-Host "  $installCmd" -ForegroundColor Cyan
    Write-Host "  pwsh -NoProfile -File `"$PSScriptRoot\Install-PSScriptAnalyzer.ps1`"" -ForegroundColor Cyan
    Write-Host "Or re-run this script with -InstallAnalyzer to install automatically." -ForegroundColor Yellow
    Write-Host ""

    if ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
        $answer = Read-Host "Install PSScriptAnalyzer now? (Y/N)"
        if ($answer -match '^(y|yes)$') {
            Install-Module PSScriptAnalyzer -Scope CurrentUser -Force -AllowClobber
            return $true
        }
    }

    return $false
}

function Test-SingleFile {
    param(
        [string]$FilePath,
        [bool]$UseAnalyzer,
        [bool]$StrictMode
    )

    $errors = @()
    $parseErrors = $null
    $tokens = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($FilePath, [ref]$tokens, [ref]$parseErrors)

    foreach ($pe in $parseErrors) {
        $errors += [pscustomobject]@{
            File = $FilePath
            Line = $pe.Extent.StartLineNumber
            Column = $pe.Extent.StartColumnNumber
            Severity = 'ParseError'
            Message = $pe.Message
        }
    }

    if ($UseAnalyzer -and $parseErrors.Count -eq 0) {
        Import-Module PSScriptAnalyzer -ErrorAction Stop
        $severity = if ($StrictMode) { @('Error', 'Warning') } else { @('Error') }
        $findings = Invoke-ScriptAnalyzer -Path $FilePath -Severity $severity -ErrorAction Stop

        foreach ($finding in $findings) {
            $errors += [pscustomobject]@{
                File = $FilePath
                Line = $finding.Line
                Column = $finding.Column
                Severity = $finding.Severity
                Message = $finding.Message
            }
        }
    }

    return $errors
}

$targets = if (Test-Path $Path -PathType Container) {
    Get-ChildItem -Path $Path -Recurse -Include *.ps1, *.psm1, *.psd1, *.ps1.txt -File
} elseif (Test-Path $Path -PathType Leaf) {
    @(Get-Item $Path)
} else {
    throw "Path not found: $Path"
}

if ($targets.Count -eq 0) {
    Write-Host "No PowerShell files found under $Path"
    exit 0
}

if ($RequireAnalyzer -and $SkipAnalyzer) {
    throw "-RequireAnalyzer and -SkipAnalyzer are mutually exclusive."
}

$useAnalyzer = -not $SkipAnalyzer
if ($useAnalyzer) {
    $useAnalyzer = Resolve-Analyzer -AutoInstall:$InstallAnalyzer
}

if ($RequireAnalyzer -and -not $useAnalyzer) {
    Write-Host ""
    Write-Host "FAIL: -RequireAnalyzer was specified but PSScriptAnalyzer is not available." -ForegroundColor Red
    Write-Host "      Parser-only checks would have reported PASS and hidden that lint never ran." -ForegroundColor Red
    Write-Host "      Install it with: pwsh -NoProfile -File `"$PSScriptRoot\Install-PSScriptAnalyzer.ps1`"" -ForegroundColor Yellow
    exit 2
}

$allErrors = @()
foreach ($file in $targets) {
    $allErrors += Test-SingleFile -FilePath $file.FullName -UseAnalyzer:$useAnalyzer -StrictMode:$Strict
}

foreach ($err in $allErrors) {
    Write-Host ("{0}({1},{2}): {3}: {4}" -f $err.File, $err.Line, $err.Column, $err.Severity, $err.Message)
}

if ($allErrors.Count -gt 0) {
    Write-Host ""
    Write-Host "FAIL: $($allErrors.Count) issue(s) in $($targets.Count) file(s)"
    exit 1
}

if ($useAnalyzer) {
    Write-Host "PASS: $($targets.Count) file(s) checked (parser + PSScriptAnalyzer)" -ForegroundColor Green
}
else {
    Write-Host "PASS (DEGRADED): $($targets.Count) file(s) checked - PARSER ONLY, lint did NOT run." -ForegroundColor Yellow
    Write-Host "                 Syntax is valid; nothing else was verified. Use -RequireAnalyzer to make this a failure." -ForegroundColor Yellow
}
exit 0

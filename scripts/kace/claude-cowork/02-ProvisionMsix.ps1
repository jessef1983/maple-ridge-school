#Requires -Version 5.1
<#
.SYNOPSIS
  Cowork Task Chain step 2: provision Claude MSIX for all users (elevated).
.NOTES
  Expects Claude.msix or Claude.msixbundle as a KACE script dependency in $PSScriptRoot
  (or set CLAUDE_MSIX_PATH). Uses Add-AppxProvisionedPackage -SkipLicense.
#>
$ErrorActionPreference = 'Stop'

$candidates = @(
    $env:CLAUDE_MSIX_PATH,
    (Join-Path $PSScriptRoot 'Claude.msix'),
    (Join-Path $PSScriptRoot 'Claude.msixbundle'),
    (Join-Path $PSScriptRoot 'claude.msix'),
    (Join-Path $PSScriptRoot 'claude.msixbundle')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

if (-not $candidates -or $candidates.Count -eq 0) {
    Write-Error 'Claude MSIX/MSIXBUNDLE not found. Attach as KACE script dependency named Claude.msix (or set CLAUDE_MSIX_PATH).'
    exit 2
}

$packagePath = $candidates[0]
Write-Host "OK: PackagePath=$packagePath"

$sig = Get-AuthenticodeSignature -FilePath $packagePath
Write-Host "OK: Authenticode Status=$($sig.Status)"
if ($sig.Status -notin @('Valid', 'UnknownError')) {
    # UnknownError sometimes appears offline; still attempt provision if policy allows
    Write-Host "WARN: Unexpected signature status=$($sig.Status) — continuing"
}

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
Add-AppxProvisionedPackage -Online -PackagePath $packagePath -SkipLicense | Out-Null
Write-Host 'OK: Add-AppxProvisionedPackage completed'

$prov = Get-AppxProvisionedPackage -Online | Where-Object { $_.DisplayName -like '*Claude*' }
if (-not $prov) {
    Write-Error 'Provisioned Claude package not found after Add-AppxProvisionedPackage'
    exit 3
}
$prov | ForEach-Object { Write-Host "OK: Provisioned $($_.DisplayName) $($_.Version)" }
exit 0

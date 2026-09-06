#Requires -Version 7.4
<#
.SYNOPSIS
  Prime PnP.PowerShell for @admin-spo sessions (PowerShell 7 + system browser auth).

.DESCRIPTION
  Loads config/spo.local.json, verifies PnP.PowerShell 3.x is available under pwsh,
  and optionally connects with -OSLogin (Windows account broker / WAM) so the user gets
  a native account picker instead of a browser round-trip.

  OSLogin requires a real console window (MSAL WAM parent window handle). See the
  -Connect block for the guard and the fallbacks.

.EXAMPLE
  pwsh -NoProfile -File .\infra\spo-prime-pnp.ps1
  . .\infra\spo-prime-pnp.ps1 -Connect
#>
[CmdletBinding()]
param(
    [switch]$Connect,
    [string]$SiteUrl
)

$ErrorActionPreference = 'Stop'
$env:PNPPOWERSHELL_UPDATECHECK = 'Off'

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw @"
spo-prime-pnp requires PowerShell 7.4+ (current: $($PSVersionTable.PSVersion)).
Install: winget install --id Microsoft.PowerShell -e
Then reopen the terminal and run: pwsh -NoProfile -File .\infra\spo-prime-pnp.ps1
Do not use Windows PowerShell 5.1 — PnP 1.x Interactive uses an embedded WebView, not Chrome.
"@
}

$toolkitRoot = Split-Path $PSScriptRoot -Parent
$configPath = Join-Path $toolkitRoot 'config\spo.local.json'
$examplePath = Join-Path $toolkitRoot 'config\spo.local.example.json'

if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
}
elseif (Test-Path $examplePath) {
    Write-Warning 'Using config/spo.local.example.json - copy to config/spo.local.json for local overrides.'
    $config = Get-Content $examplePath -Raw | ConvertFrom-Json
}
else {
    throw 'Missing config/spo.local.json and config/spo.local.example.json'
}

$pnpMods = @(Get-Module -ListAvailable PnP.PowerShell | Sort-Object Version -Descending)
if ($pnpMods.Count -eq 0) {
    throw @'
PnP.PowerShell not installed for PowerShell 7.
Run: pwsh -NoProfile -File .\infra\Install-SpoAdminPrereqs.ps1
Or:  Install-Module PnP.PowerShell -Scope CurrentUser -Force -SkipPublisherCheck
'@
}

$latest = $pnpMods[0]
if ($latest.Version.Major -lt 2) {
    throw "PnP.PowerShell $($latest.Version) is too old (embedded WebView auth). Install 3.x via infra\Install-SpoAdminPrereqs.ps1"
}

Import-Module PnP.PowerShell -RequiredVersion $latest.Version -ErrorAction Stop
$loaded = Get-Module PnP.PowerShell
Write-Host "PnP.PowerShell $($loaded.Version) loaded from $($loaded.ModuleBase)"
Write-Host "SPO config: tenant=$($config.tenantUrl) admin=$($config.adminUrl)"

if (-not $config.pnpClientId) {
    Write-Warning 'config.pnpClientId is empty. Set it in config/spo.local.json (Entra app with broker/public-client redirect).'
}

if ($Connect) {
    if (-not $config.pnpClientId) {
        throw 'Connect requires pnpClientId in config/spo.local.json'
    }
    $url = if ($SiteUrl) { $SiteUrl } else { $config.companyKnowledgeBaseUrl }
    if (-not $url) { $url = $config.tenantUrl }

    if (-not $config.tenantId) {
        throw 'OSLogin requires tenantId in config/spo.local.json.'
    }

    # OSLogin = Windows account broker (WAM). Native account picker, no browser.
    # MSAL WAM needs a parent window handle, so this only works from a real console
    # window. Fail with an explanation rather than a raw MSAL error.
    try { $null = [Console]::WindowWidth }
    catch {
        throw @'
OSLogin needs a real console window (MSAL WAM parent window handle) and this process has none.
See https://aka.ms/msal-net-wam#parent-window-handles

Run from a normal terminal, or start it in its own window:
  Start-Process pwsh -ArgumentList '-NoProfile','-File','<script>' -WindowStyle Normal

Do NOT use Start-Process -RedirectStandardOutput/-RedirectStandardError: redirection
destroys the console window WAM needs. Have the script write its own log instead.

Fallback where WAM is blocked: Connect-PnPOnline ... -DeviceLogin
'@
    }

    Write-Host "Connecting with -OSLogin (WAM) -> $url" -ForegroundColor Cyan
    Write-Host "ClientId: $($config.pnpClientId)  Tenant: $($config.tenantId)" -ForegroundColor DarkGray
    Connect-PnPOnline -Url $url -ClientId $config.pnpClientId -Tenant $config.tenantId -OSLogin
    $site = Get-PnPWeb -ErrorAction Stop
    Write-Host "Connected: $($site.Title) ($($site.Url))" -ForegroundColor Green
}

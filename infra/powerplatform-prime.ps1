#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Prime Microsoft.PowerApps.Administration.PowerShell for @admin-powerplatform sessions.

.DESCRIPTION
    Installs Microsoft.PowerApps.Administration.PowerShell if missing, then signs in
    interactively via Add-PowerAppsAccount against CP Operations. Separate auth surface
    from Graph WAM (infra/connect-tenants-wam.ps1) — do not attempt to reuse
    Get-TenantGraphToken for Power Platform Admin API calls.

    Microsoft.PowerApps.PowerShell (the maker-level module) is optional — only needed
    for non-admin cmdlets (Get-PowerApp etc). Admin audit cmdlets (Get-AdminPowerApp,
    Get-AdminPowerAppRoleAssignment, Get-AdminDlpPolicy, ...) all live in the
    Administration module alone.

.EXAMPLE
    . .\infra\powerplatform-prime.ps1
    . .\infra\powerplatform-prime.ps1 -ExpectedAccount (Get-OperatorAccount -Tenant cpops)

    -ExpectedAccount only labels the sign-in prompt. When omitted, it is filled from
    config/operator.local.json if that exists (see infra/Get-OperatorAccount.ps1).
#>
[CmdletBinding()]
param(
    [string]$TenantId = '2e1c62fc-1595-4d12-85d1-8577714f8d1d',   # cpmfgoperations.onmicrosoft.com
    [string]$EnvironmentId = '70b71c9e-66c2-4c4d-8668-1e5a8f3181f9',  # CPOP-PRD
    [string]$ExpectedAccount
)

$ErrorActionPreference = 'Stop'

if (-not $ExpectedAccount) {
    . "$PSScriptRoot\Get-OperatorAccount.ps1"
    try { $ExpectedAccount = Get-OperatorAccount -Tenant cpops } catch { $ExpectedAccount = $null }
}

if (-not (Get-Module -ListAvailable -Name 'Microsoft.PowerApps.Administration.PowerShell')) {
    throw 'Microsoft.PowerApps.Administration.PowerShell not installed. Run: Install-Module Microsoft.PowerApps.Administration.PowerShell -Scope CurrentUser -AllowClobber'
}

Import-Module Microsoft.PowerApps.Administration.PowerShell -ErrorAction Stop

if (Get-Module -ListAvailable -Name 'Microsoft.PowerApps.PowerShell') {
    Import-Module Microsoft.PowerApps.PowerShell -ErrorAction Stop
}

# Same non-modal-popup gotcha as connect-tenants-wam.ps1's Connect-TenantGraphOnly —
# the sign-in window does not steal focus and is easy to miss behind the editor.
Write-Host ""
Write-Host '  *** Sign-in popup incoming - Power Platform Admin ***' -ForegroundColor Yellow -BackgroundColor DarkRed
if ($ExpectedAccount) { Write-Host ('  *** Pick: ' + $ExpectedAccount) -ForegroundColor Yellow }
Write-Host '  *** (check Alt+Tab if you do not see it - window is non-modal)' -ForegroundColor Yellow
Write-Host ""

Add-PowerAppsAccount -TenantID $TenantId

$env = Get-AdminPowerAppEnvironment -EnvironmentName $EnvironmentId -ErrorAction Stop
Write-Host "OK: connected. Environment: $($env.DisplayName) ($($env.EnvironmentName))" -ForegroundColor Green

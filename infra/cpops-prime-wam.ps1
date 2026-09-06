#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Prime Az WAM Graph context for CP Operations Entra (once per session).

.DESCRIPTION
    Graph-only sign-in — no Azure subscription. Re-run only when WAM cache expired
    or you need a different account. With PIM GA (~1h), do NOT clear context before
    every script run.

.EXAMPLE
    pwsh -NoProfile .\infra\cpops-prime-wam.ps1 -ExpectedAccount 'jessefrase@cpops.cciauth.com'
#>
[CmdletBinding()]
param(
    [string]$CPOpsTenantId = '2e1c62fc-1595-4d12-85d1-8577714f8d1d',
    [Parameter(Mandatory)]
    [string]$ExpectedAccount,
    [switch]$ForceReconnect
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\connect-tenants-wam.ps1"
Connect-TenantGraphOnly -TenantId $CPOpsTenantId -ExpectedAccount $ExpectedAccount -ForceReconnect:$ForceReconnect
$null = Get-TenantGraphToken -TenantId $CPOpsTenantId -ExpectedAccount $ExpectedAccount
Write-Host "CP Ops Graph context ready for $ExpectedAccount" -ForegroundColor Green

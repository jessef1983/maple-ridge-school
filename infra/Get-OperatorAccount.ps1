#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Returns the operator's (your) sign-in account for a tenant, from untracked config.

.DESCRIPTION
    Dot-source this file, then call Get-OperatorAccount. Agents and scripts use it
    instead of a hard-coded UPN, so a shared file never names one person's account.

    Lookup order, first hit wins:
      1. Environment variable CP_OPERATOR_<TENANT> (e.g. CP_OPERATOR_CPOPS)
      2. <repo>/config/operator.local.json   (git-ignored; <repo> = parent of infra/)
      3. ~/.cp-ai-toolkit/operator.local.json (one file for every repo on this machine)

    Copy config/operator.local.example.json to either location and fill in your accounts.

.EXAMPLE
    . "$PSScriptRoot\Get-OperatorAccount.ps1"
    $upn = Get-OperatorAccount -Tenant cpops
#>

function Get-OperatorAccount {
    [CmdletBinding()]
    param(
        [ValidateSet('cpops', 'ccimail', 'ccfedu')]
        [string]$Tenant = 'cpops'
    )

    $fromEnv = [Environment]::GetEnvironmentVariable("CP_OPERATOR_$($Tenant.ToUpperInvariant())")
    if ($fromEnv) { return $fromEnv.Trim() }

    $repoRoot = Split-Path -Parent $PSScriptRoot
    $candidates = @(
        (Join-Path $repoRoot 'config/operator.local.json'),
        (Join-Path $HOME '.cp-ai-toolkit/operator.local.json')
    )

    foreach ($path in $candidates) {
        if (-not (Test-Path $path)) { continue }
        $config = Get-Content $path -Raw | ConvertFrom-Json
        $value = $config.accounts.$Tenant
        if ($value -and $value -notmatch '^you[@_]') { return $value.Trim() }
    }

    throw ("No '$Tenant' account configured. Copy config/operator.local.example.json to " +
        "config/operator.local.json (git-ignored) or ~/.cp-ai-toolkit/operator.local.json and fill in " +
        "accounts.$Tenant, or set CP_OPERATOR_$($Tenant.ToUpperInvariant()).")
}

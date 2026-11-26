#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Returns YOUR Azure DevOps PAT from variables you set, or nothing.

.DESCRIPTION
    Dot-source this file, then call Get-AdoPat. No PAT ships with the toolkit and none
    is shared: each person creates and rotates their own. If you have not set one up,
    the PAT-based features (admin-ado REST calls, start-session's ADO checks) are not
    available to you. There is deliberately no fallback to anyone else's token.

    Lookup order, first hit wins:
      1. Environment variable AZURE_DEVOPS_EXT_PAT (the PAT itself; also used by az devops)
      2. Environment variables CP_ADO_PAT_KEYVAULT + CP_ADO_PAT_SECRET (your own Key Vault
         secret, read with your az login)
      3. "ado": { "keyVault", "secretName" } in <repo>/config/operator.local.json
         (git-ignored), then ~/.cp-ai-toolkit/operator.local.json

    Returns $null when nothing is configured or the secret can't be read, unless
    -Required is passed, in which case it throws with setup instructions.
    Never print the returned value.

.EXAMPLE
    . "$PSScriptRoot\Get-AdoPat.ps1"
    $pat = Get-AdoPat -Required
#>

function Get-AdoPat {
    [CmdletBinding()]
    param([switch]$Required)

    $setup = "No ADO PAT configured. Create your own PAT in Azure DevOps (User settings > " +
        "Personal access tokens), then either set AZURE_DEVOPS_EXT_PAT, or store it in your own " +
        "Key Vault and set CP_ADO_PAT_KEYVAULT + CP_ADO_PAT_SECRET (or 'ado.keyVault' / " +
        "'ado.secretName' in config/operator.local.json). Without one, PAT-based features are unavailable."

    $direct = [Environment]::GetEnvironmentVariable('AZURE_DEVOPS_EXT_PAT')
    if ($direct) { return $direct.Trim() }

    $vault  = [Environment]::GetEnvironmentVariable('CP_ADO_PAT_KEYVAULT')
    $secret = [Environment]::GetEnvironmentVariable('CP_ADO_PAT_SECRET')

    if (-not ($vault -and $secret)) {
        $repoRoot = Split-Path -Parent $PSScriptRoot
        foreach ($path in @(
                (Join-Path $repoRoot 'config/operator.local.json'),
                (Join-Path $HOME '.cp-ai-toolkit/operator.local.json'))) {
            if (-not (Test-Path $path)) { continue }
            $ado = (Get-Content $path -Raw | ConvertFrom-Json).ado
            if ($ado.keyVault -and $ado.secretName -and $ado.keyVault -notmatch '^your-') {
                $vault = $ado.keyVault; $secret = $ado.secretName
                break
            }
        }
    }

    if ($vault -and $secret) {
        $value = az keyvault secret show --vault-name $vault --name $secret --query value -o tsv 2>$null
        if ($LASTEXITCODE -eq 0 -and $value) { return $value.Trim() }
        $setup = "Could not read ADO PAT secret '$secret' from Key Vault '$vault'. Run " +
            "'az login --use-device-code' and check you can read that secret."
    }

    if ($Required) { throw $setup }
    Write-Verbose $setup
    return $null
}

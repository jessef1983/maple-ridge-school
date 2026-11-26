#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Az PowerShell WAM helpers for Power Platform admin (BAP) and Dataverse Web API.

.DESCRIPTION
    Dot-source this file to expose Get-TenantPowerPlatformToken / Get-TenantBapHeaders /
    Get-TenantDataverseHeaders. Sibling to connect-tenants-wam.ps1 (Graph) - same WAM
    pattern (Az.Accounts holds multiple tenant contexts; one popup per tenant, then
    silent refresh), different resource audiences:

      - BAP (tenant-wide admin: environments, DLP, capacity)  -> https://api.bap.microsoft.com
      - Dataverse Web API (per-environment: roles, teams,
        business units, app users, entity data)               -> the environment's own URL,
                                                                    e.g. https://org.crm.dynamics.com

    pac CLI (`pac admin list`, `pac org list`) is an alternative for the BAP-scoped
    operations and is often simpler for one-off listing. Use this script when you need
    a bearer token for direct REST calls (e.g. from PowerShell scripts, or when pac's
    own auth profile is pointed at the wrong tenant).

.EXAMPLE
    . "$PSScriptRoot\connect-powerplatform-wam.ps1"
    $headers = Get-TenantBapHeaders -TenantId $tenantCpOps -ExpectedAccount 'you@cpops.cciauth.com'
    Invoke-RestMethod -Uri 'https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/scopes/admin/environments?api-version=2022-05-01' -Headers $headers

.EXAMPLE
    $headers = Get-TenantDataverseHeaders -TenantId $tenantCpOps -EnvironmentUrl 'https://org12345.crm.dynamics.com' -ExpectedAccount 'you@cpops.cciauth.com'
    Invoke-RestMethod -Uri 'https://org12345.crm.dynamics.com/api/data/v9.2/roles?$select=name,businessunitid' -Headers $headers

.NOTES
    Verified against CP Operations (CPOP-PRD Dataverse) on 2026-09-25 - Get-TenantDataverseHeaders
    returned a working token and roles/teams/appmodules/roleprivilegescollection calls succeeded.
    Log new traps to admin-powerplatform.agent.md Known mistakes.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$tenantCpOps = '2e1c62fc-1595-4d12-85d1-8577714f8d1d'   # cpmfgoperations.onmicrosoft.com

Import-Module Az.Accounts -ErrorAction Stop

function Connect-TenantPowerPlatformOnly {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TenantId,
        [string]$ExpectedAccount,
        [string]$AuthScope,
        [switch]$ForceReconnect
    )

    if ($ForceReconnect) {
        Get-AzContext -ListAvailable -ErrorAction SilentlyContinue |
            Where-Object { $_.Tenant.Id -eq $TenantId } |
            ForEach-Object { Remove-AzContext -InputObject $_ -Force -ErrorAction SilentlyContinue | Out-Null }
    }
    elseif (Get-AzContext -ListAvailable -ErrorAction SilentlyContinue | Where-Object { $_.Tenant.Id -eq $TenantId } | Select-Object -First 1) {
        return
    }

    Write-Host ""
    Write-Host '  *** WAM popup - Power Platform ***' -ForegroundColor Yellow -BackgroundColor DarkRed
    if ($ExpectedAccount) { Write-Host ('  *** Pick: ' + $ExpectedAccount) -ForegroundColor Yellow }
    Write-Host '  *** (check Alt+Tab if you do not see it)' -ForegroundColor Yellow
    Write-Host ""

    if (Get-Command Update-AzConfig -ErrorAction SilentlyContinue) {
        Update-AzConfig -LoginExperienceV2 Off -Scope Process -ErrorAction SilentlyContinue | Out-Null
    }

    $connectParams = @{
        Tenant                = $TenantId
        SkipContextPopulation = $true
        ErrorAction           = 'Stop'
    }
    if ($AuthScope) { $connectParams['AuthScope'] = $AuthScope }
    Connect-AzAccount @connectParams | Out-Null
}

function Get-TenantPowerPlatformToken {
    <#
      Generic resource-scoped token for the given tenant. Pass -ResourceUrl explicitly
      (BAP admin API or a specific environment's Dataverse URL) - unlike Graph, Power
      Platform has no single fixed resource audience.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TenantId,
        [Parameter(Mandatory)][string]$ResourceUrl,
        [string]$ExpectedAccount
    )

    $ctx = Get-AzContext -ListAvailable -ErrorAction SilentlyContinue |
        Where-Object { $_.Tenant.Id -eq $TenantId } | Select-Object -First 1

    if (-not $ctx) {
        Connect-TenantPowerPlatformOnly -TenantId $TenantId -ExpectedAccount $ExpectedAccount
        $ctx = Get-AzContext -ListAvailable | Where-Object { $_.Tenant.Id -eq $TenantId } | Select-Object -First 1
        if (-not $ctx) {
            throw "Connect-AzAccount succeeded but no context was created for tenant $TenantId."
        }
    }

    Set-AzContext -Context $ctx -ErrorAction Stop | Out-Null

    try {
        $tokenObj = Get-AzAccessToken -ResourceUrl $ResourceUrl -TenantId $TenantId -ErrorAction Stop -WarningAction SilentlyContinue
    } catch {
        Write-Host "  $ResourceUrl scope missing for $TenantId - reconnecting" -ForegroundColor Yellow
        Connect-TenantPowerPlatformOnly -TenantId $TenantId -ExpectedAccount $ExpectedAccount -AuthScope $ResourceUrl -ForceReconnect
        $ctx = Get-AzContext -ListAvailable | Where-Object { $_.Tenant.Id -eq $TenantId } | Select-Object -First 1
        Set-AzContext -Context $ctx -ErrorAction Stop | Out-Null
        $tokenObj = Get-AzAccessToken -ResourceUrl $ResourceUrl -TenantId $TenantId -ErrorAction Stop -WarningAction SilentlyContinue
    }

    $token = if ($tokenObj.Token -is [System.Security.SecureString]) {
        [System.Net.NetworkCredential]::new('', $tokenObj.Token).Password
    } else {
        $tokenObj.Token
    }

    if (-not $token) { throw "Failed to obtain $ResourceUrl token for tenant $TenantId." }
    return $token
}

function Get-TenantBapHeaders {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TenantId,
        [string]$ExpectedAccount
    )
    $token = Get-TenantPowerPlatformToken -TenantId $TenantId -ResourceUrl 'https://api.bap.microsoft.com' -ExpectedAccount $ExpectedAccount
    return @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
}

function Get-TenantDataverseHeaders {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TenantId,
        [Parameter(Mandatory)][string]$EnvironmentUrl,
        [string]$ExpectedAccount
    )
    $resource = $EnvironmentUrl.TrimEnd('/')
    $token = Get-TenantPowerPlatformToken -TenantId $TenantId -ResourceUrl $resource -ExpectedAccount $ExpectedAccount
    return @{
        Authorization     = "Bearer $token"
        'Content-Type'    = 'application/json'
        'OData-MaxVersion' = '4.0'
        'OData-Version'    = '4.0'
        Accept             = 'application/json'
    }
}

if ($MyInvocation.InvocationName -eq '.') { return }

Write-Host "Dot-source this file, then call Get-TenantBapHeaders or Get-TenantDataverseHeaders." -ForegroundColor Cyan
Write-Host '  . "$PSScriptRoot\connect-powerplatform-wam.ps1"' -ForegroundColor Gray
Write-Host '  $bapHeaders = Get-TenantBapHeaders -TenantId <guid> -ExpectedAccount <upn>' -ForegroundColor Gray
Write-Host '  $dvHeaders  = Get-TenantDataverseHeaders -TenantId <guid> -EnvironmentUrl <url> -ExpectedAccount <upn>' -ForegroundColor Gray

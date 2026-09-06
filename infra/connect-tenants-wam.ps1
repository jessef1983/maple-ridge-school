#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Az PowerShell WAM helpers for Microsoft Graph across Entra tenants.

.DESCRIPTION
    Dot-source this file to expose Get-TenantGraphToken / Get-TenantGraphHeaders.
    Use Connect-TenantGraphOnly or cpops-prime-wam.ps1 to prime WAM once per session.

    Why Az PowerShell instead of Azure CLI:
    - Az.Accounts holds multiple tenant contexts simultaneously.
    - Azure CLI keeps only one active tenant — cross-tenant scripts hit AADSTS50020.
    - WAM sign-in is one popup per tenant, then silent refresh.

.EXAMPLE
    . "$PSScriptRoot\connect-tenants-wam.ps1"
    $headers = Get-TenantGraphHeaders -TenantId $tenantCpOps -ExpectedAccount 'you@cpops.cciauth.com'

.NOTES
    CP Claude baseline — CP Ops production tenant. Extend $tenant* variables for other tenants.
#>
[CmdletBinding()]
param(
    [switch]$ClearFirst
)

$ErrorActionPreference = 'Stop'

$tenantCpOps = '2e1c62fc-1595-4d12-85d1-8577714f8d1d'   # cpmfgoperations.onmicrosoft.com
$tenantCcimail = 'e73f6ab8-7854-4a88-9cfd-409801e42d32' # ccimail.com
$tenantCcigen = 'dc412e61-9147-4b68-b11b-8d854a727920'  # ccigen.onmicrosoft.com (CCI General, resource tenant)

Import-Module Az.Accounts -ErrorAction Stop

function Connect-TenantGraphOnly {
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
    Write-Host '  *** WAM popup - Graph only (no subscription) ***' -ForegroundColor Yellow -BackgroundColor DarkRed
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

function Get-TenantGraphToken {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TenantId,
        [string]$ExpectedAccount
    )

    $ctx = Get-AzContext -ListAvailable -ErrorAction SilentlyContinue |
        Where-Object { $_.Tenant.Id -eq $TenantId } | Select-Object -First 1

    if (-not $ctx) {
        Connect-TenantGraphOnly -TenantId $TenantId -ExpectedAccount $ExpectedAccount
        $ctx = Get-AzContext -ListAvailable | Where-Object { $_.Tenant.Id -eq $TenantId } | Select-Object -First 1
        if (-not $ctx) {
            throw "Connect-AzAccount succeeded but no context was created for tenant $TenantId."
        }
    }

    Set-AzContext -Context $ctx -ErrorAction Stop | Out-Null

    try {
        $tokenObj = Get-AzAccessToken -ResourceUrl 'https://graph.microsoft.com' -TenantId $TenantId -ErrorAction Stop -WarningAction SilentlyContinue
    } catch {
        Write-Host "  Graph scope missing for $TenantId - reconnecting (Graph only)" -ForegroundColor Yellow
        Connect-TenantGraphOnly -TenantId $TenantId -ExpectedAccount $ExpectedAccount -AuthScope 'https://graph.microsoft.com' -ForceReconnect
        $ctx = Get-AzContext -ListAvailable | Where-Object { $_.Tenant.Id -eq $TenantId } | Select-Object -First 1
        Set-AzContext -Context $ctx -ErrorAction Stop | Out-Null
        $tokenObj = Get-AzAccessToken -ResourceUrl 'https://graph.microsoft.com' -TenantId $TenantId -ErrorAction Stop -WarningAction SilentlyContinue
    }

    $token = if ($tokenObj.Token -is [System.Security.SecureString]) {
        [System.Net.NetworkCredential]::new('', $tokenObj.Token).Password
    } else {
        $tokenObj.Token
    }

    if (-not $token) { throw "Failed to obtain Graph token for tenant $TenantId." }
    return $token
}

function Get-TenantGraphHeaders {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TenantId,
        [string]$ExpectedAccount
    )
    $token = Get-TenantGraphToken -TenantId $TenantId -ExpectedAccount $ExpectedAccount
    return @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
}

if ($MyInvocation.InvocationName -eq '.') { return }

if ($ClearFirst) {
    Write-Host "Clearing all Az contexts..." -ForegroundColor Yellow
    Clear-AzContext -Force -ErrorAction SilentlyContinue
}

function Connect-Tenant {
    param([string]$TenantId, [string]$Label, [string]$ExpectedAccount)

    Write-Host ""
    Write-Host "=== $Label ($TenantId) ===" -ForegroundColor Green

    $existing = Get-AzContext -ListAvailable -ErrorAction SilentlyContinue |
        Where-Object { $_.Tenant.Id -eq $TenantId } | Select-Object -First 1
    if ($existing) {
        Write-Host "  Cached Az context found - skipping login." -ForegroundColor DarkGray
        return
    }

    Connect-TenantGraphOnly -TenantId $TenantId -ExpectedAccount $ExpectedAccount
    Write-Host "  Az PS context cached for $Label." -ForegroundColor Green
}

Write-Host "Priming CP Ops Graph context. For ccimail/ccigen, re-run with that tenant's ExpectedAccount." -ForegroundColor Cyan
Connect-Tenant -TenantId $tenantCpOps -Label 'CP Operations' -ExpectedAccount 'jessefrase@cpops.cciauth.com'

# ccigen is a resource tenant under the ccimail Identity Hub — sign in with the ccimail home
# account (guest/B2B access), not a ccigen.onmicrosoft.com UPN.
# Connect-Tenant -TenantId $tenantCcigen -Label 'CCI General' -ExpectedAccount 'jessefrase@ccimail.cciauth.com'

Write-Host ""
Write-Host "From any script:" -ForegroundColor Cyan
Write-Host '  . "$PSScriptRoot\connect-tenants-wam.ps1"' -ForegroundColor Gray
Write-Host '  $headers = Get-TenantGraphHeaders -TenantId <guid> -ExpectedAccount <upn>' -ForegroundColor Gray
Write-Host ""

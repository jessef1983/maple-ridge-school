<#
.SYNOPSIS
    Audit logging helper for Entra modifications.

.DESCRIPTION
    Dot-source into Entra admin scripts. Logs to logs/entra-changes-YYYY-MM-DD.log.

.EXAMPLE
    . "$PSScriptRoot\log-entra-changes.ps1"
    Log-EntraChange -Tenant CpOps -OperationType Create -Resource User -Details @{ UPN = "user@cpops.cciauth.com" }
#>

param(
    [string]$LogDir = "$PSScriptRoot\..\logs"
)

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

function Log-EntraChange {
    param(
        [Parameter(Mandatory)] [ValidateSet('CpOps', 'Ccimail', 'All')] [string]$Tenant,
        [Parameter(Mandatory)] [ValidateSet('Create', 'Modify', 'Delete', 'Disable', 'Enable', 'Assign', 'Remove', 'Patch', 'Query')] [string]$OperationType,
        [Parameter(Mandatory)] [ValidateSet('User', 'Group', 'Role', 'Policy', 'Domain', 'B2BGuest', 'License', 'ServicePrincipal', 'App')] [string]$Resource,
        [string]$ObjectId = "",
        [hashtable]$Details = @{},
        [bool]$Success = $true
    )

    $timestamp = Get-Date -Format "HH:mm:ss"
    $dateString = Get-Date -Format "yyyy-MM-dd"
    $logFile = Join-Path $LogDir "entra-changes-$dateString.log"

    $detailsString = ""
    if ($Details.Count -gt 0) {
        $detailsString = ($Details.GetEnumerator() | ForEach-Object { "$($_.Key): $($_.Value)" }) -join " | "
    }

    $successFlag = if ($Success) { "✓" } else { "⚠" }
    $logEntry = "[$timestamp] [$successFlag Tenant$Tenant] [$OperationType] $Resource"

    if ($ObjectId) {
        $logEntry += " (ID: $ObjectId)"
    }

    if ($detailsString) {
        $logEntry += " | $detailsString"
    }

    Add-Content -Path $logFile -Value $logEntry -Encoding UTF8
    $color = if ($Success) { 'Green' } else { 'Yellow' }
    Write-Host $logEntry -ForegroundColor $color
}

function Log-ApprovalRequired {
    param(
        [Parameter(Mandatory)] [ValidateSet('CpOps', 'Ccimail')] [string]$Tenant,
        [Parameter(Mandatory)] [string]$Resource,
        [Parameter(Mandatory)] [string]$ObjectId,
        [hashtable]$Details = @{}
    )

    $timestamp = Get-Date -Format "HH:mm:ss"
    $dateString = Get-Date -Format "yyyy-MM-dd"
    $logFile = Join-Path $LogDir "entra-changes-$dateString.log"

    $detailsString = if ($Details.Count -gt 0) {
        ($Details.GetEnumerator() | ForEach-Object { "$($_.Key): $($_.Value)" }) -join " | "
    } else {
        ""
    }

    $logEntry = "[$timestamp] [⏳ Tenant$Tenant] [APPROVAL_REQUIRED] Delete $Resource (ID: $ObjectId)"
    if ($detailsString) {
        $logEntry += " | $detailsString"
    }

    Add-Content -Path $logFile -Value $logEntry -Encoding UTF8
    Write-Host $logEntry -ForegroundColor Yellow
}

function Get-EntraAuditLog {
    $dateString = Get-Date -Format "yyyy-MM-dd"
    Join-Path $LogDir "entra-changes-$dateString.log"
}

function Show-EntraAuditLogs {
    param(
        [int]$Days = 1,
        [ValidateSet('CpOps', 'Ccimail', 'All', '')] [string]$Tenant = '',
        [ValidateSet('Create', 'Modify', 'Delete', 'Disable', 'Enable', 'Assign', 'Remove', 'Patch', 'Query', '')] [string]$OperationType = ''
    )

    $logs = @()
    for ($i = 0; $i -lt $Days; $i++) {
        $date = (Get-Date).AddDays(-$i).ToString("yyyy-MM-dd")
        $logFile = Join-Path $LogDir "entra-changes-$date.log"
        if (Test-Path $logFile) {
            $logs += Get-Content $logFile
        }
    }

    if ($Tenant) {
        $logs = $logs | Where-Object { $_ -match "Tenant$Tenant" }
    }

    if ($OperationType) {
        $logs = $logs | Where-Object { $_ -match "\[$OperationType\]" }
    }

    $logs | Sort-Object -Descending | Format-List
}

Export-ModuleMember -Function @('Log-EntraChange', 'Log-ApprovalRequired', 'Get-EntraAuditLog', 'Show-EntraAuditLogs')

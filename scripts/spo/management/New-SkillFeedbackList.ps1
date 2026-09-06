#Requires -Version 7.0
<#
.SYNOPSIS
  Creates the admin-only "Skill Feedback" list on Company Knowledge Base.

.DESCRIPTION
  One-time provisioner for the CP Skills Concierge post-skill feedback loop.
  Creates a GenericList with the Concierge schema, breaks role inheritance so
  only named admins / skill owners can read or write.

  Auth: Connect-PnPOnline Interactive using cp-ai-toolkit config/spo.local.json
  (pnpClientId). Prefer @admin-spo to run this.

.EXAMPLE
  pwsh -NoProfile -File scripts\spo\management\New-SkillFeedbackList.ps1 -WhatIf

.EXAMPLE
  pwsh -NoProfile -File scripts\spo\management\New-SkillFeedbackList.ps1 `
    -AdminPrincipals @('jessefrase@cpops.cciauth.com')
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [string]$SiteUrl = 'https://cpmfgoperations.sharepoint.com/sites/CompanyKnowledgeBase',
    [string]$ListTitle = 'Skill Feedback',
    [string[]]$AdminPrincipals = @(),
    [string]$ConfigPath = ''
)

$ErrorActionPreference = 'Stop'

function Resolve-SpoConfigPath {
    param([string]$Explicit)
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) { return (Resolve-Path $Explicit).Path }

    $candidates = @(
        (Join-Path $PSScriptRoot '..\..\..\..\cp-ai-toolkit\config\spo.local.json'),
        'C:\cp-devops\cp-ai-toolkit\config\spo.local.json',
        (Join-Path $PSScriptRoot '..\..\..\config\spo.local.json')
    )
    foreach ($c in $candidates) {
        $full = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($c)
        if (Test-Path -LiteralPath $full) { return $full }
    }
    throw "spo.local.json not found. Pass -ConfigPath or create cp-ai-toolkit/config/spo.local.json from the example."
}

function Add-SkillFeedbackFieldIfMissing {
    param(
        [Parameter(Mandatory)][string]$ListTitle,
        [Parameter(Mandatory)][string]$InternalName,
        [Parameter(Mandatory)][string]$DisplayName,
        [Parameter(Mandatory)][ValidateSet('Text', 'Note', 'Choice', 'DateTime')][string]$Type,
        [string[]]$Choices = @()
    )
    $field = Get-PnPField -List $ListTitle -Identity $InternalName -ErrorAction SilentlyContinue
    if ($field) { return }
    $params = @{
        List          = $ListTitle
        DisplayName   = $DisplayName
        InternalName  = $InternalName
        Type          = $Type
        AddToDefaultView = $true
    }
    if ($Type -eq 'Choice') { $params['Choices'] = $Choices }
    Add-PnPField @params | Out-Null
    Write-Host "  + field $InternalName" -ForegroundColor Green
}

Import-Module PnP.PowerShell -ErrorAction Stop

$configPathResolved = Resolve-SpoConfigPath -Explicit $ConfigPath
$config = Get-Content -LiteralPath $configPathResolved -Raw | ConvertFrom-Json
if (-not $config.pnpClientId) {
    throw "pnpClientId is empty in $configPathResolved. Set it before running Connect-PnPOnline Interactive."
}

if ($AdminPrincipals.Count -eq 0 -and $config.siteOwnerUpn) {
    $AdminPrincipals = @([string]$config.siteOwnerUpn)
}
if ($AdminPrincipals.Count -eq 0) {
    throw "Pass -AdminPrincipals (UPNs or SPO group names) so the list is not left with zero principals after break-inheritance."
}

Write-Host "Connecting to $SiteUrl ..." -ForegroundColor Cyan
Connect-PnPOnline -Url $SiteUrl -ClientId $config.pnpClientId -Interactive | Out-Null

$existing = Get-PnPList -Identity $ListTitle -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "List '$ListTitle' already exists (Id=$($existing.Id)). Verifying columns..." -ForegroundColor Yellow
} else {
    if (-not $PSCmdlet.ShouldProcess($SiteUrl, "Create list '$ListTitle'")) {
        Write-Host "WhatIf: would create list '$ListTitle' on $SiteUrl with admin-only permissions for: $($AdminPrincipals -join ', ')" -ForegroundColor DarkYellow
        return
    }
    New-PnPList -Title $ListTitle -Template GenericList -OnQuickLaunch:$false | Out-Null
    Write-Host "Created list '$ListTitle'" -ForegroundColor Green
}

Write-Host "Ensuring schema columns..." -ForegroundColor Cyan
Add-SkillFeedbackFieldIfMissing -ListTitle $ListTitle -InternalName 'SkillUsed' -DisplayName 'Skill Used' -Type Text
Add-SkillFeedbackFieldIfMissing -ListTitle $ListTitle -InternalName 'Timestamp' -DisplayName 'Timestamp' -Type DateTime
Add-SkillFeedbackFieldIfMissing -ListTitle $ListTitle -InternalName 'User' -DisplayName 'User' -Type Text
Add-SkillFeedbackFieldIfMissing -ListTitle $ListTitle -InternalName 'SessionSummary' -DisplayName 'Session Summary' -Type Note
Add-SkillFeedbackFieldIfMissing -ListTitle $ListTitle -InternalName 'WorkflowClarity' -DisplayName 'Workflow Clarity' -Type Choice -Choices @('yes', 'partial', 'no')
Add-SkillFeedbackFieldIfMissing -ListTitle $ListTitle -InternalName 'BlockersEncountered' -DisplayName 'Blockers Encountered' -Type Note
Add-SkillFeedbackFieldIfMissing -ListTitle $ListTitle -InternalName 'SuggestionToImprove' -DisplayName 'Suggestion To Improve' -Type Note
Add-SkillFeedbackFieldIfMissing -ListTitle $ListTitle -InternalName 'Outcome' -DisplayName 'Outcome' -Type Choice -Choices @('success', 'partial', 'blocked')

if ($PSCmdlet.ShouldProcess($ListTitle, "Break role inheritance and grant Full Control to: $($AdminPrincipals -join ', ')")) {
    # CopyRoleAssignments:$false + ClearSubscopes => unique ACLs (admin-only after grants below)
    Set-PnPList -Identity $ListTitle -BreakRoleInheritance:$true -CopyRoleAssignments:$false -ClearSubscopes:$true | Out-Null
    foreach ($principal in $AdminPrincipals) {
        $granted = $false
        try {
            Set-PnPListPermission -Identity $ListTitle -User $principal -AddRole 'Full Control' -ErrorAction Stop
            $granted = $true
            Write-Host "  granted Full Control -> $principal" -ForegroundColor Green
        } catch {
            try {
                Set-PnPListPermission -Identity $ListTitle -Group $principal -AddRole 'Full Control' -ErrorAction Stop
                $granted = $true
                Write-Host "  granted Full Control (group) -> $principal" -ForegroundColor Green
            } catch {
                Write-Warning "Could not grant Full Control to '$principal': $($_.Exception.Message)"
            }
        }
        if (-not $granted) {
            throw "Failed to grant list permission to '$principal'. Fix the principal name and re-run (idempotent)."
        }
    }
}

$web = Get-PnPWeb
$listObj = Get-PnPList -Identity $ListTitle -Includes RootFolder
# RootFolder.ServerRelativeUrl is already site-rooted (e.g. /sites/CompanyKnowledgeBase/Lists/...).
# Join with tenant host only — do not prepend $web.Url or the path doubles.
$tenantHost = ([uri]$web.Url).GetLeftPart([UriPartial]::Authority)
$listBrowse = "$tenantHost/$($listObj.RootFolder.ServerRelativeUrl.TrimStart('/'))"

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "  List:    $ListTitle"
Write-Host "  Site:    $SiteUrl"
Write-Host "  Browse:  $listBrowse"
Write-Host "  Admins:  $($AdminPrincipals -join ', ')"
Write-Host ""
Write-Host "Write model: app-only Sites.Selected (KB ingestion app) — humans stay read-only / admin-only." -ForegroundColor Cyan
Write-Host "Do NOT grant m365_sharepoint_write / user Contribute for feedback." -ForegroundColor Cyan
Write-Host "Next MCP: add narrow app-only feedback list write (KB writer identity + gate); not m365_sharepoint_kb_write file upload." -ForegroundColor Cyan

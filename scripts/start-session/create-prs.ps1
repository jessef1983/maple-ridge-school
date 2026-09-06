<#
.SYNOPSIS
Create ADO Pull Requests for remote branches that are ahead of `main`.

.DESCRIPTION
This helper fetches remotes, discovers remote branches that contain commits
not yet in `refs/remotes/origin/main`, and creates Pull Requests in Azure
DevOps from the remote branch into `main` for human review. It uses a PAT
read from `config/ado.local.json` in the repository root.

.NOTES
Safe defaults: does not push any local branches and does not merge PRs.
Use `-DryRun` to preview create actions. Use `-ListActive` to print active
PRs targeting `main` without creating anything.
#>

param(
    [Parameter(Mandatory=$false)]
    [string[]] $RepoPaths = @(),

    [switch] $DryRun,

    [switch] $ListActive,

    [string] $AdoOrg,
    [string] $AdoProject
)

function Get-PatFromConfig {
    param([string]$RepoRoot)
    $cfg = Join-Path $RepoRoot 'config\ado.local.json'
    if (-Not (Test-Path $cfg)) { return $null }
    try {
        $j = Get-Content $cfg -Raw | ConvertFrom-Json
        return $j.pat
    } catch { return $null }
}

function Get-RemoteBranches {
    param([string]$RepoPath)
    Push-Location $RepoPath
    try {
        git fetch --all --prune | Out-Null
        $refs = git for-each-ref --format='%(refname)' refs/remotes | Where-Object { $_ -notmatch '\^{}' }
        return $refs
    } finally { Pop-Location }
}

function Branch-NameFromRef([string]$ref) {
    # refs/remotes/origin/main -> main
    return ($ref -split '/')[3..($ref -split '/').Length] -join '/'
}

function RepoInfoFromRemoteUrl([string]$url) {
    # https://dev.azure.com/{org}/{project}/_git/{repo}
    # https://{org}@dev.azure.com/{org}/{project}/_git/{repo}
    if ($url -match 'dev\.azure\.com/([^/]+)/([^/]+)/_git/([^/\?]+)') {
        return @{
            org     = $Matches[1]
            project = $Matches[2]
            repo    = $Matches[3].TrimEnd('.git')
        }
    }
    return $null
}

function Get-AdoRemoteUrl {
    param([string]$RepoPath)
    Push-Location $RepoPath
    try {
        $names = @(git remote 2>$null)
        $originUrl = $null
        $firstAdo = $null
        foreach ($name in $names) {
            $u = git remote get-url $name 2>$null
            if (-not $u) { continue }
            if ($u -match 'dev\.azure\.com') {
                if ($name -eq 'origin') { $originUrl = $u }
                if (-not $firstAdo) { $firstAdo = $u }
            }
        }
        if ($originUrl) { return $originUrl }
        return $firstAdo
    } finally { Pop-Location }
}

function Get-ActivePullRequests {
    param($org, $project, $repoId, $repoName, $pat)
    $uri = "https://dev.azure.com/$org/$project/_apis/git/repositories/$repoId/pullrequests?searchCriteria.status=active&searchCriteria.targetRefName=refs/heads/main&api-version=7.1"
    $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$pat"))
    try {
        $resp = Invoke-RestMethod -Method Get -Uri $uri -Headers @{ Authorization = "Basic $b64" }
        return @($resp.value)
    } catch {
        Write-Error ("Failed to list PRs for {0}: {1}" -f $repoName, $($_))
        return @()
    }
}

function Get-RepositoryId {
    param($org, $project, $repoName, $pat)
    $uri = "https://dev.azure.com/$org/$project/_apis/git/repositories/$repoName?api-version=7.1"
    $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$pat"))
    try {
        $resp = Invoke-RestMethod -Method Get -Uri $uri -Headers @{ Authorization = "Basic $b64" }
        return $resp.id
    } catch {
        Write-Error ("Failed to get repo id for {0}: {1}" -f $repoName, $($_))
        return $null
    }
}

function Create-PullRequest {
    param($org,$project,$repoId,$sourceBranch,$targetBranch,$title,$description,$pat)
    $uri = "https://dev.azure.com/$org/$project/_apis/git/repositories/$repoId/pullrequests?api-version=7.1"
    $body = @{
        sourceRefName = "refs/heads/$sourceBranch"
        targetRefName = "refs/heads/$targetBranch"
        title = $title
        description = $description
    } | ConvertTo-Json -Depth 10

    $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$pat"))
    if ($DryRun) {
        Write-Host "DRY-RUN: Would POST $uri with body: $body" -ForegroundColor Yellow
        return $null
    }
    try {
        $resp = Invoke-RestMethod -Method Post -Uri $uri -Headers @{ Authorization = "Basic $b64"; 'Content-Type' = 'application/json' } -Body $body
        return $resp
    } catch {
        Write-Error ("Failed to create PR: {0}" -f $($_))
        return $null
    }
}

if ($RepoPaths.Count -eq 0) {
    # default: top-level workspace roots under C:\devops as used by this workspace
    $RepoPaths = @('C:\devops\cp-ai-toolkit','C:\devops\cp-jesse-sandbox','C:\devops\cci-spo-music-knowledge-base','C:\devops\cp-spo-company-knowledge-base')
}

foreach ($path in $RepoPaths) {
    if (-Not (Test-Path $path)) { Write-Host "Skipping missing path: $path"; continue }
    if (-Not (Test-Path (Join-Path $path '.git'))) { Write-Host "Not a git repo: $path"; continue }

    Write-Host "Inspecting $path" -ForegroundColor Cyan
    $pat = Get-PatFromConfig -RepoRoot $path
    if (-not $pat) {
        Write-Host "No PAT found in $path\config\ado.local.json; skipping ADO operations for this repo" -ForegroundColor Yellow
        continue
    }

    Push-Location $path
    try {
        $adoUrl = Get-AdoRemoteUrl -RepoPath $path
        if (-not $adoUrl) { Write-Host "No Azure DevOps remote; skipping"; continue }
        $info = RepoInfoFromRemoteUrl $adoUrl
        if (-not $info) { Write-Host "ADO URL not recognized: $adoUrl; skipping"; continue }

        $org = $info.org
        $project = $info.project
        $repoName = $info.repo
        if ($AdoOrg) { $org = $AdoOrg }
        if ($AdoProject) { $project = $AdoProject }

        $repoId = Get-RepositoryId -org $org -project $project -repoName $repoName -pat $pat
        if (-not $repoId) { continue }

        if ($ListActive) {
            $prs = Get-ActivePullRequests -org $org -project $project -repoId $repoId -repoName $repoName -pat $pat
            if ($prs.Count -eq 0) {
                Write-Host "No active PRs into main for $org/$project/$repoName" -ForegroundColor DarkGray
            } else {
                Write-Host ("Active PRs into main ({0}):" -f $prs.Count) -ForegroundColor Green
                foreach ($pr in $prs) {
                    $portal = "https://dev.azure.com/$org/$project/_git/$repoName/pullrequest/$($pr.pullRequestId)"
                    $ageDays = [math]::Round(((Get-Date).ToUniversalTime() - [datetime]$pr.creationDate).TotalDays, 1)
                    Write-Host ("  #{0}  {1}" -f $pr.pullRequestId, $pr.title)
                    Write-Host ("       {0} -> {1}  by {2}  {3}d  {4}" -f $pr.sourceRefName, $pr.targetRefName, $pr.createdBy.displayName, $ageDays, $portal)
                }
            }
            continue
        }

        $refs = Get-RemoteBranches -RepoPath $path
        $originMainRef = 'refs/remotes/origin/main'
        if (-not ($refs -contains $originMainRef)) { Write-Host "No origin/main found; skipping"; continue }

        foreach ($r in $refs) {
            # candidate remote branches: not origin/main and not origin/HEAD
            if ($r -match '^refs/remotes/(origin|upstream)/') {
                if ($r -eq $originMainRef) { continue }
                $branchName = ($r -replace '^refs/remotes/[^/]+/','')
                # check if branch is already contained in origin/main
                $isAncestor = & git merge-base --is-ancestor $r $originMainRef; $exit = $LASTEXITCODE
                if ($exit -eq 0) { continue } # ancestor -> commit already in main

                # candidate: create PR from branchName -> main
                $title = "Sync $branchName into main"
                $description = "Automated PR candidate: bring $branchName changes into main. Reviewed by start-session helper."
                Write-Host "Candidate PR: $repoName $branchName -> main" -ForegroundColor Green
                if ($DryRun) {
                    Write-Host "DRY-RUN: would create PR from $branchName to main in $org/$project/$repoName"
                } else {
                    $pr = Create-PullRequest -org $org -project $project -repoId $repoId -sourceBranch $branchName -targetBranch 'main' -title $title -description $description -pat $pat
                    if ($pr) {
                        Write-Host "Created PR: $($pr.pullRequestId) -> $($pr.url)" -ForegroundColor Cyan
                    }
                }
            }
        }
    } finally { Pop-Location }
}

# admin-ado REST reference (Azure DevOps Git PRs + PAT)

PAT pattern matches `.github/agents/admin-ado.agent.md`: load `config/ado.local.json` (gitignored), Basic `:$pat`. Do not commit the PAT.

```powershell
$config = Get-Content "config/ado.local.json" -Raw | ConvertFrom-Json
$pat = $config.pat
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$pat"))
$headersJson = @{
    Authorization = "Basic $b64"
    'Content-Type' = 'application/json'
}
$headersPatch = @{
    Authorization = "Basic $b64"
    'Content-Type' = 'application/json-patch+json'
}
```

Prefer `scripts/start-session/create-prs.ps1 -ListActive` for listing. Work-item recipes stay in the agent file.

Org/project/repo from `https://dev.azure.com/{org}/{project}/_git/{repo}` (ignore a `user@` prefix on the host).

## List active PRs (start-session)

```powershell
GET https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoId}/pullrequests?searchCriteria.status=active&searchCriteria.targetRefName=refs/heads/main&api-version=7.1
```

```powershell
$uri = "https://dev.azure.com/$org/$project/_apis/git/repositories/$repoId/pullrequests?searchCriteria.status=active&searchCriteria.targetRefName=refs/heads/main&api-version=7.1"
$resp = Invoke-RestMethod -Method Get -Uri $uri -Headers @{ Authorization = "Basic $b64" }
foreach ($pr in @($resp.value)) {
    [pscustomobject]@{
        pullRequestId = $pr.pullRequestId
        title         = $pr.title
        source        = $pr.sourceRefName
        target        = $pr.targetRefName
        createdBy     = $pr.createdBy.displayName
        createdDate   = $pr.creationDate
        url           = "https://dev.azure.com/$org/$project/_git/$repoName/pullrequest/$($pr.pullRequestId)"
    }
}
```

Report: `pullRequestId`, title, `sourceRefName` → `targetRefName`, createdBy, createdDate, portal URL.

## Create PR

Source branch must already exist on the remote. Do not push a local-only branch unless the user explicitly approved that push.

**`description` is capped at 4000 characters.** Over that, the POST fails with:

```
InvalidArgumentValueException: A description for a pull request must not be longer
than 4000 characters.
```

Measure before sending and trim — the long-form detail belongs in the commit messages
or a linked doc, not the PR body:

```powershell
$desc = Get-Content $descPath -Raw
if ($desc.Length -gt 4000) { throw "PR description is $($desc.Length) chars (max 4000) — trim before POST." }
```

Note the cap counts **characters, not bytes**, and it applies on create *and* on any
later PATCH that updates `description`.

```powershell
POST https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoId}/pullrequests?api-version=7.1
Content-Type: application/json
{
  "sourceRefName": "refs/heads/{branch}",
  "targetRefName": "refs/heads/main",
  "title": "<title>",
  "description": "<why, <=4000 chars>"
}
```

Send the body as UTF-8 bytes so em-dashes and other non-ASCII survive:
`-Body ([Text.Encoding]::UTF8.GetBytes($json))`.

**Use REST for the description — never the `az` CLI.** `az repos pr create --description`
keeps only the **first line** of a multi-line string and raises no error, so a truncated
PR body looks like a success. Splatting the lines as separate arguments is not a fix:
PowerShell drops empty-string arguments, so blank lines disappear and the Markdown
collapses into one block, and inner double quotes are stripped from the text.

To repair a description after the fact, PATCH the PR resource (`az devops invoke` refuses
PATCH on `pullrequests`):

```powershell
$json = @{ description = $body } | ConvertTo-Json -Depth 3
$resp = Invoke-RestMethod -Method Patch `
    -Uri "https://dev.azure.com/$org/$projectId/_apis/git/repositories/$repoId/pullrequests/$prId`?api-version=7.1" `
    -Headers $headersJson `
    -Body ([Text.Encoding]::UTF8.GetBytes($json))

# Verify the round-trip — a "successful" write can still be truncated
"{0} chars, {1} newlines" -f $resp.description.Length,
    ([regex]::Matches($resp.description, "`n")).Count
```

**Check for an existing active PR from the same source branch before creating** — the
duplicate-prevention rule in the agent file applies to PRs, not just work items.

## Complete PR (wrap completes its own; others need approval)

A `/session-wrap` invocation **is** approval to complete the PRs that session created — wrapping means the work lands and the repo ends on `main`. Any other PR still needs the user to explicitly say to complete/merge it (or a listed set), after seeing id, title, source→target, and a short file list.

Regardless of approval, refuse when `mergeStatus` is not `succeeded` or `status` is not `active`, and never set `bypassPolicy`.

```powershell
# GET the PR first; refuse if mergeStatus -ne succeeded
$getUri = "https://dev.azure.com/$org/$project/_apis/git/repositories/$repoId/pullrequests/$prId`?api-version=7.1"
$pr = Invoke-RestMethod -Method Get -Uri $getUri -Headers $headersJson
if ($pr.mergeStatus -ne 'succeeded') {
    throw "Refuse complete: mergeStatus=$($pr.mergeStatus) (need succeeded). Conflicts or queued merge."
}
if ($pr.status -ne 'active') {
    throw "Refuse complete: status=$($pr.status)"
}

$completeUri = $getUri
$body = @{
    status = 'completed'
    lastMergeSourceCommit = @{ commitId = $pr.lastMergeSourceCommit.commitId }
    completionOptions = @{
        mergeStrategy      = 'noFastForward'
        deleteSourceBranch = $true
        transitionWorkItems = $false
    }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Method Patch -Uri $completeUri -Headers $headersJson -Body $body
```

Never set `bypassPolicy`. `deleteSourceBranch: true` is the default — the branch just merged, so leaving it strands a stale ref that `start-session` flags later.

**Deleting the branch you just merged is routine. Sweeping a repo's other merged branches is not** — that is a separate cleanup, only on explicit request. If asked, verify each candidate individually and record its tip SHA before deleting:

```powershell
$sha = git rev-parse "origin/$b"
git merge-base --is-ancestor "origin/$b" origin/main
if ($LASTEXITCODE -eq 0) { "$b $sha -> safe to delete" } else { "$b NOT merged - keep" }
```

Report the full list and the count before and after. `main`, `master`, and any branch that looks like a deliberate reference point (`develop`, `canonical-main`, a release line) stay regardless of merge status unless the user names them.

## After complete: update local main (required)

Completing a PR updates **remote** `main` only. `git fetch` updates remote-tracking refs; it does **not** change files on disk if HEAD is still a feature branch.

After the complete PATCH succeeds (confirm `status=completed` and a merge commit):

1. `git fetch` the ADO remote (`origin` or `ado`).
2. If **tracked** dirty files would be overwritten, stop and ask (stash / commit / skip). Untracked leftovers may stay.
3. `git switch main` (or `git checkout main`).
4. `git pull` that remote's `main` so the **working copy** matches the merge.
5. Report local `HEAD` and that it matches `origin/main` or `ado/main`.

Do not treat “fetched `ado/main`” as “local seed/docs are current.”

## Resolve repository id

```powershell
GET https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoName}?api-version=7.1
```

Use the returned `id` in the PR URIs above.

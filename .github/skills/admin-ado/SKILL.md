---
name: admin-ado
description: >-
  Azure DevOps administration for CP/CCI: work items (create/update/query/link,
  WIQL, area/iteration, rich descriptions) and Git pull requests used by
  start-session and session-wrap (list active into main, create, complete only
  after explicit extra approval). Keywords: ADO, Azure DevOps, work items, WIQL,
  boards, pull request, PR, complete PR, merge.
---

# ADO Admin Skill

**SOT:** `cp-ai-toolkit/.github/skills/admin-ado/` (mirror into consumers + `~/.agents/skills/admin-ado/`). REST copy-paste lives in [reference.md](reference.md). Agent: `.github/agents/admin-ado.agent.md`.

Use this skill for Azure DevOps **work items** and **Git PRs** in CP/CCI projects. GitHub `gh pr` is out of scope.

## Use this skill for

- Creating, updating, querying, and linking work items
- Managing Area Path and Iteration Path assignments
- Patching rich HTML descriptions and comments safely
- Preventing duplicates by checking for exact-title matches before creating work items
- Listing **active** PRs targeting `main` (start-session, even on same-day last-run skip)
- Creating a PR from an existing remote branch into `main`
- Completing a PR **only after extra user approval** (wrap invoke is not merge approval)
- After complete: `git switch main` + `git pull` so local files match remote `main` (fetch alone is not enough)

Prefer `scripts/start-session/create-prs.ps1 -ListActive` for listing so URIs stay consistent.

## Working approach

1. Clarify the project, work item type or PR, and scope if the request is ambiguous.
2. Check for existing work items before creating a new one.
3. Show a dry-run preview of the intended create/update/link/complete operation.
4. Use REST patching for long descriptions rather than relying on CLI-only description handling.
5. For PRs: GET first; refuse complete if `mergeStatus` is not `succeeded`.
6. After complete: update **local** `main` (switch + pull). Completing the PR only updates the remote.
7. Verify the result after execution and report IDs, states, portal URLs, and local `HEAD`.

## Guardrails

- Do not create or patch a work item without first checking for duplicates.
- Do not perform destructive operations (delete, state=Removed) without explicit approval.
- Do not patch descriptions without showing the intended HTML content first.
- Keep descriptions concise and structured.
- **Wrap invoke ≠ merge.** Complete a PR only after the user names that PR (or a listed set) and has seen id, title, source→target, and a short file list.
- Never complete with `bypassPolicy`. Never force-push. Default merge strategy: `noFastForward`. Default `deleteSourceBranch`: **true** — delete the branch you just merged. Default `transitionWorkItems`: false. Sweeping a repo's *other* merged branches is a separate cleanup that needs an explicit request.
- After complete, do **not** stop at `git fetch`. Remote `main` is current; the working copy is not until you `git switch main` and `git pull`. Staying on the source branch shows pre-merge files (including old seed timestamps).

## Example prompts

- Create a Task in cp-claude for documenting the new authentication pattern.
- Query open work items tagged integration.
- List active PRs into main for this repo.
- Complete ADO PR 1631 after I approve — noFastForward, keep the source branch.

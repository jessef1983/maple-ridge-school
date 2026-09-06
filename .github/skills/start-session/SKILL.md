---
name: start-session
description: >-
  Start-of-session helper. Scans all workspace repos, reports local `git status` and
  recent commits, queries ADO for remote branch state via the `admin-ado` agent,
  and (optionally) opens PRs from remote upstream branches into `main` for human
  review. Designed to run at the start of a work session to surface drift and
  open PRs that should be reviewed before you begin work.
---

# Start session

**SOT:** `cp-ai-toolkit/.github/skills/start-session/` (mirror into consumers + `~/.agents/skills/start-session/`). Claude-native equivalent: `.claude/skills/start-session/SKILL.md`.

**Run this automatically at the start of any new session** in a repo where it's
installed — don't wait to be asked. Check the last-run log first (Step 0);
skip the full git scan if it already ran today, but **still list active ADO
PRs**.

It performs discovery, remote queries, an installed-agent drift check, and
surfaces actionable work for the user. It does **not** merge PRs automatically
— PRs are created (when needed) and presented for human review. Complete only
via `@admin-ado` after explicit extra approval
([admin-ado reference.md](../admin-ado/reference.md)).

## Behavior overview

0. **Last-run check** — Read `.claude/skills/start-session/.last-run.json`
   (create if absent; treat missing as "never run"). If `lastRunUtc` is the
   same calendar day (local time) as now, skip the **full git scan** and report
   "already ran start-session today at `<time>`". **Still run the active-PR
   listing** (cheap GET; leftover PRs created after the morning start must
   surface). Otherwise proceed with the full scan, and write the updated
   timestamp back at the end. This file is per-repo, per-machine state —
   don't commit it.

0.5. **Installed-agent drift check** — If a `cp-ai-toolkit` checkout is
   findable in this workspace (sibling folder, or `C:\devops\cp-ai-toolkit`),
   run its `scripts/start-session/Compare-InstalledAgents.ps1` (read-only)
   against the current repo. Report any stale/missing shared agent or skill
   files and suggest re-running `Install-CPAIAgents.ps1` — don't run it
   yourself. Skip silently if no toolkit checkout is found.

1. **Discovery** — Enumerate the workspace root paths and treat each top-level
   folder that contains a `.git` directory as a candidate repo. For each repo
   capture: current branch (`git rev-parse --abbrev-ref HEAD`), `git status
   --porcelain`, last 5 commits (`git log --oneline -n 5`), and remotes (`git
   remote -v`). Do not change the working tree.

2. **Remote mapping** — For remotes whose URL contains `dev.azure.com` build an
   ADO repo id and record the remote name to use for queries (`origin` or `ado`).

2.5. **Uncompleted PRs (always, including same-day skip)** — For every
   workspace git repo with an ADO remote, list **active** PRs targeting `main`
   (`create-prs.ps1 -ListActive` or `@admin-ado` GET in
   [admin-ado reference.md](../admin-ado/reference.md)). Put them in chat and
   in `docs/session-notes/YYYY-MM-DD-start-session.md` as **Uncompleted PRs**
   (id, title, source branch, age, link). Do **not** complete them unless the
   user asks.

3. **Remote query (via `@admin-ado`)** — For each ADO repo ask `@admin-ado` for
   the latest commit SHAs for `refs/heads/main` and for any candidate upstream
   branches. Ask for a short diff/changed-files list between the upstream
   branch and `main` to include in the summary. Skip this on same-day last-run.

4. **Decide "behind"** — A repo is *behind* when a remote branch contains
   commits not present in `main`.

5. **PR creation (policy)** — Only create PRs from branches that already exist
   on the remote. Do not push local-only branches without explicit permission.
   Prepare a PR payload (title, body, source→target); in dry-run mode present
   it instead of creating it.

6. **Post-PR flow** — Do NOT auto-merge. When the user explicitly approves
   completing a listed PR, call `@admin-ado` using
   [admin-ado reference.md](../admin-ado/reference.md) (`noFastForward`, no
   `bypassPolicy`, refuse if `mergeStatus` is not `succeeded`). Then **update
   local `main`**: `git fetch`, `git switch main`, `git pull` so the working
   copy matches remote `main`. Fetch alone is not enough. If tracked dirt would
   be overwritten, stop and ask.

## Safety and guardrails

- Never overwrite uncommitted local work — pause and offer stash/commit/skip.
- Never force-push or auto-merge PRs.
- Rely on `config/ado.local.json` for the ADO PAT if available; otherwise
  prompt the user or ask `@admin-ado`.

## Outputs

- Per-repo summary: repo path, current branch, local status, recent commits,
  remote `main` SHA, upstream candidate branch, whether a PR was created.
- **Uncompleted PRs** (Step 2.5) — every active PR into `main`, including on
  same-day last-run skip.
- Installed-agent drift summary (Step 0.5), if `cp-ai-toolkit` was found.
- A session summary file saved to `docs/session-notes/YYYY-MM-DD-start-session.md`.
- `.claude/skills/start-session/.last-run.json` updated with this run's timestamp.

## Invocation

```powershell
# List active PRs into main (run even on same-day skip)
powershell -NoProfile -File .\scripts\start-session\create-prs.ps1 -ListActive

# Dry-run for all workspace roots
powershell -NoProfile -File .\scripts\start-session\create-prs.ps1 -DryRun

# Explicit repos, create PRs when needed (interactive review required)
powershell -NoProfile -File .\scripts\start-session\create-prs.ps1 -RepoPaths 'C:\devops\cp-ai-toolkit;C:\devops\cp-jesse-sandbox'
```

Use `git fetch --all --prune` before querying remote SHAs so the local fetch
is current. Do not merge or rebase automatically.

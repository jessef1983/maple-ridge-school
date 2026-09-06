---
name: start-session
description: >-
  Start-of-session helper. Scans all workspace repos, reports local `git status` and
  recent commits, queries ADO for remote branch state via the `admin-ado` agent,
  and (optionally) opens PRs from remote upstream branches into `main` for human
  review. Designed to run at the start of a work session to surface drift and
  open PRs that should be reviewed before you begin work.
disable-model-invocation: false
argument-hint: "[--dry-run] [--force] [--paths <path1;path2;...>] [--stale-days N]"
allowed-tools: >-
  Bash(git status:*) Bash(git rev-parse:*) Bash(git remote -v:*) Bash(git fetch:*)
  Bash(git log:*) Bash(git branch:*) Bash(git for-each-ref:*) Bash(git merge-base:*)
  Bash(pwsh:*) Read Write Edit Glob Grep ListAgents SendMessage @admin-ado
---

# Start session

**Run this automatically at the start of any new session in a repo where this
skill is installed** — don't wait for the user to ask. Check the cache layers
first (Step 0) before doing any expensive scanning; the whole point of this
step is to avoid burning tokens and time re-discovering state nothing has
changed.

It performs discovery, remote queries, an installed-agent drift check, and
surfaces actionable work for the user. It does **not** merge PRs automatically —
PRs are created (when needed) and presented for human review.

Minimum inputs
- `--dry-run` : list planned actions without creating PRs or pulling.
- `--force` : skip both cache layers and run the full scan regardless of freshness.
- `--paths` : semicolon-separated list of root paths to inspect. If omitted,
  the skill will inspect all top-level workspace folders.
- `--stale-days` : age threshold in days for the stale-branch scan (Step 3.5).
  Default **14**. Lower it for a noisier/earlier warning, raise it to reduce
  noise on repos with long-lived feature branches.

Behavior overview

0. Two-layer cache check (skip redundant runs — this is the step that keeps
   session starts cheap)

   **Layer 1 — same-machine, same-session-recency (gitignored, per-machine).**
   Read `.claude/skills/start-session/.last-run.json` (create if absent —
   treat as "never run"; holds `{ "lastRunUtc": "<ISO8601>" }`). If
   `lastRunUtc` is within the last **60 minutes** and `--force` wasn't passed,
   skip straight to Step 2.5 (uncompleted PRs — always cheap, always run) and
   report "ran start-session <N> min ago on this machine; pass --force to
   re-run." This layer exists so re-invoking on the same machine minutes
   apart never re-triggers the expensive steps below.

   **Layer 2 — cross-machine (tracked in git, written by `session-wrap`).**
   If Layer 1 doesn't short-circuit, check for `.claude/session-state.json`
   (see `session-wrap`'s skill file for its shape — written by the *last
   wrap*, on *any* machine, and synced here by the `git pull` in Step 1).
   Read it, then run a cheap `git fetch` (no full scan yet) and compare:
   - If `session-state.json`'s `mainHeadSha` is an ancestor of (or equal to)
     current `origin/main`, **and** `confirmedClean` was `true`, **and**
     `lastWrapUtc` is recent enough to trust (use judgement — a wrap from 10
     minutes ago on a different machine is as good as one from this machine;
     a wrap from 3 days ago is not, even if nothing shows as changed, because
     someone could have pushed and force-reset since): treat Steps 1 and 3.5
     as **already answered** for this repo. Report "confirmed clean per
     `session-wrap` at `<lastWrapUtc>` (`<repo>`)" and skip to Step 2.5.
     Still surface `session-state.json`'s `openPRs` and `knownStaleBranches`
     arrays verbatim — that's carried-forward knowledge, not a re-scan.
   - If `origin/main` has moved past `mainHeadSha`, or `confirmedClean` was
     `false`, or the file doesn't exist: the cache is stale or absent for
     this repo specifically. Fall through to the full scan (Steps 1–3.5) for
     **this repo only** — other repos in the same multi-repo run can still
     use their own cache layer independently.

   At the end of *any* full scan (cache miss), write the updated
   `lastRunUtc` back to Layer 1's local file. Do **not** write to
   `session-state.json` from this skill — that file is `session-wrap`'s to
   write; `start-session` only ever reads it.

0.4. Active session claims (**always — cheap, and the only thing that catches a
   concurrent session**)

   Several sessions share this workspace, and Claude Code gives you two
   coordination mechanisms. Use both; they cover different cases.

   **Live peers (`ListAgents`).** Call it. It lists other Claude sessions on
   this machine plus Remote Control sessions. A peer whose name or working
   directory matches a repo you're about to change is a *live* collaborator —
   `SendMessage` them before touching shared files. This catches the session
   that is editing right now but hasn't committed anything yet, which nothing
   in git can tell you.

   **Durable claims (`.claude/claims/<session>.json`, tracked in git).** These
   survive a session ending and cross machines, which `ListAgents` cannot.

   1. **Write your own claim** at session start:
      ```json
      {
        "session": "sandbox-jesse-4e",
        "ref": "5f485c",
        "machine": "<hostname>",
        "rootDir": "C:\\Devops\\Sandbox Jesse",
        "branch": "<current branch>",
        "startedUtc": "2026-09-03T02:40:00Z",
        "heartbeatUtc": "2026-09-03T02:40:00Z",
        "paths": [".github/agents/", ".claude/skills/session-wrap/"],
        "note": "one line: what you are doing here"
      }
      ```
      Filename is the session name (`ListAgents` names this session in its
      first line). **One file per session — never a shared array.** A shared
      list is itself a merge conflict; separate files cannot collide.
      `paths` may start empty and be refined once you know what you're
      touching; refresh `heartbeatUtc` when you update it.

   2. **Read every other claim in `.claude/claims/`.** Report any whose
      `paths` overlap what this session intends to change, and any live peer
      from `ListAgents` in the same repo. Overlap is a **warning, not a
      block** — say who, what, and since when, then let the user decide.

   3. **Treat a claim with `heartbeatUtc` older than 12 hours as stale** —
      report it as "possibly abandoned", don't honour it as an active lock,
      and don't delete someone else's claim to tidy up.

   **`rootDir` matters more than it looks.** Claude Code's memory is scoped per
   *project directory*, so two sessions rooted in the same repo share a memory
   store automatically, while a session rooted elsewhere that has this repo as
   an additional working directory shares nothing. If a claim's `rootDir` is
   not this repo, that session cannot see this repo's memory — say so, because
   it explains drift that otherwise looks inexplicable. **Prefer rooting a
   session in the repo it is changing.**

0.5. Installed-agent drift check
   - If a `cp-ai-toolkit` checkout is findable in this workspace (sibling
     folder, or `C:\devops\cp-ai-toolkit`), run
     `scripts/start-session/Compare-InstalledAgents.ps1` from that toolkit
     against the current repo (read-only — it never copies anything).
   - If it reports drift (stale or missing shared agent/skill files), include
     that in the session summary and suggest re-running
     `Install-CPAIAgents.ps1`, but don't run it automatically — that's a
     user decision.
   - If no `cp-ai-toolkit` checkout is found, skip this step silently (not
     every workspace has the toolkit as a sibling).

1. Discovery (cache miss only)
   - Enumerate the provided root paths (or workspace roots) and treat each top-
     level folder that contains a `.git` directory as a candidate repo.
   - For each repo capture: current branch (`git rev-parse --abbrev-ref HEAD`),
     `git status --porcelain`, last 5 commits (`git log --oneline -n 5`), and
     remotes (`git remote -v`). Do not change the working tree.

2. Remote mapping
   - For remotes whose URL contains `dev.azure.com` build an ADO repo id and
     record the remote name to use for queries (`origin` or `ado`).

2.5. Uncompleted PRs (**always, regardless of cache layer**)
   - For every workspace git repo with an ADO remote, list **active** PRs
     targeting `main` via `scripts/start-session/create-prs.ps1 -ListActive`
     (or `@admin-ado` GET in `.github/skills/admin-ado/reference.md`). This
     is a single cheap GET per repo — always worth it regardless of cache
     state, since a PR can be opened or reviewed by someone else between
     sessions even when nothing else changed.
   - Put them in chat and in `docs/session-notes/YYYY-MM-DD-start-session.md`
     as **Uncompleted PRs** (id, title, source branch, age, link).
   - Do **not** complete them unless the user explicitly asks.

3. Remote query (via `@admin-ado`, cache miss only)
   - For each ADO repo ask `@admin-ado` to return the latest commit SHAs for
     `refs/heads/main` and for any candidate upstream branches (presence of a
     remote named `upstream`, or other named remote branches that appear newer).
   - Ask `@admin-ado` for a short diff/changed-files list between the upstream
     branch and `main` to include in the summary.

3.5. Stale branch scan (**cache miss only — this is the highest-value step
   when it does run; a good `session-wrap` habit should make it run less
   often, not skip it when it's actually needed**)
   - Rationale: the single most common way real work gets lost in this
     workspace is not deletion — it's a branch with genuine, tested, even
     packaged commits that simply never got a PR. Steps 1–3 above only look
     at the *current* branch and at branches that already look like upstream
     PR candidates; they miss everything else sitting quietly on the remote.
   - After `git fetch --all --prune`, get **every** remote branch's info in
     **one batched call** rather than looping per-branch:
     ```
     git for-each-ref --format='%(refname:short)|%(committerdate:iso-strict)|%(subject)' refs/remotes
     ```
     This returns ref name, last-commit date, and subject line for every
     remote branch in a single git invocation. Compute commit-count-ahead-of-
     `main` and the merged/not-merged check (`git merge-base --is-ancestor`)
     per candidate branch only for the ones this single call didn't already
     rule out (skip `HEAD`, skip anything pointing at the same SHA as
     `<remote>/main`) — that's normally a small subset, not every branch.
   - Flag any branch whose age exceeds `--stale-days` (default 14) as
     **stale — needs review**, sorted oldest-first. Include ALL of them in
     the session summary, even ones that look like scratch/WIP — the cost of
     a false positive (human glances and dismisses it) is far lower than the
     cost of a false negative (a real feature silently rots for a month).
   - This step is **read-only reporting only** — do not open PRs for stale
     branches automatically, even in non-dry-run mode. Step 5 below remains
     the only path that opens a PR, and only for branches that already look
     like clean upstream candidates.
   - If a stale branch's tip is a clean fast-forward from `main` (`git
     merge-base --is-ancestor <remote>/main <branch>` succeeds), call that
     out specifically — those are the lowest-risk, highest-value ones to
     resolve first since merging them can't produce conflicts.
   - If this step runs and finds nothing stale, still record that fact in
     `knownStaleBranches: []` territory conceptually — the next
     `session-wrap` should carry a "checked, found none" signal forward via
     its own cache write, not just silently move on.

4. Decide "behind"
   - A repo is considered *behind* when a remote branch (identified upstream)
     contains commits that are not present in `main` (i.e., `main` does not
     contain that commit SHA).

5. PR creation (policy)
   - Only create PRs from branches that already exist on the remote. Do not
     push local-only branches without explicit permission.
   - When a candidate upstream branch exists remotely, prepare a PR payload
     (title, body, source->target) and either:
       - In `--dry-run` mode: present the prospective PR details to the user;
       - Otherwise: call `@admin-ado` to create the PR, then present the PR ID
         and a link in chat for human review.

6. Post-PR flow
   - Do NOT auto-merge. When the user explicitly approves completing a listed
     PR, call `@admin-ado` using `.github/skills/admin-ado/reference.md`
     (`noFastForward`, never `bypassPolicy`, refuse if `mergeStatus` is not
     `succeeded`). ADO PR completion is asynchronous — poll briefly until
     `status=completed`. Then **update local `main`**: `git fetch`,
     `git switch main`, `git pull`. Completing the PR only updates the
     remote. If tracked dirt would be overwritten, stop and ask.

Safety and guardrails

- Never overwrite uncommitted local work. If local `main` contains unstaged or
  uncommitted changes, the skill will pause and present options: stash, commit,
  or skip the local pull for that repo.
- Never force-push or auto-merge PRs. Merges are performed only after explicit
  user approval and after presenting the PR diff and changed files.
- **Remote is the source of truth when local and remote genuinely diverge**
  (not merely "behind," but conflicting history) — this workspace's own
  precedent (2026-08-31 session, `PowerBi SQL Views`) was to reset local to
  match origin rather than preserve an orphaned local commit, after human
  confirmation. Still always confirm before discarding anything local; this
  is a default answer to have ready, not a license to skip asking.
- Rely on `config/ado.local.json` for ADO PAT if available (see also: it can
  be sourced from Key Vault `kv-ado-cp-prd` / secret `ado-pat` per
  `docs/session-notes/2026-08-22-ado-pat-keyvault.md` if the local file is
  missing or expired); otherwise the skill will prompt the user or ask the
  `admin-ado` agent for guidance.

Outputs

- Per-repo summary: repo path, current branch, local status, recent commits,
  remote `main` SHA, upstream candidate branch, whether a PR was created, and
  link to PR if created. On a cache hit, this is "confirmed clean as of
  `session-wrap`'s last run" instead of freshly gathered — say so explicitly,
  don't present cached data as if it were just discovered.
- **Stale branch report (Step 3.5)** — every unmerged remote branch older
  than the threshold, oldest first, with age, commit count, last subject
  line, and a fast-forward flag, when the full scan actually ran.
- **Uncompleted PRs (Step 2.5)** — every active PR into `main`, always, cache
  hit or miss.
- **Active session claims (Step 0.4)** — this session's own claim written to
  `.claude/claims/<session>.json`, plus any overlapping claims and any live
  `ListAgents` peer in the same repo, with a note when a peer's `rootDir`
  differs from this repo (it cannot see this repo's memory).
- Installed-agent drift summary (Step 0.5), if `cp-ai-toolkit` was found.
- A single session summary file (draft) saved to `docs/session-notes/YYYY-MM-DD-start-session.md`.
- `.claude/skills/start-session/.last-run.json` updated with this run's timestamp (Layer 1 only — this skill never writes `.claude/session-state.json`).

Examples — invocation

Run a dry-run for all workspace roots:

```powershell
# from repo root
Start-Session --dry-run
```

Run for explicit paths and create PRs when needed (interactive review required):

```powershell
Start-Session --paths "C:\devops\cp-ai-toolkit;C:\devops\cp-jesse-sandbox"
```

Force a full scan even if both cache layers say clean (e.g. after a manual
push from another machine that hasn't gone through `session-wrap`):

```powershell
Start-Session --force
```

Notes for implementers

- Use `git fetch --all --prune` before asking `@admin-ado` for remote SHAs so
  the local fetch is up-to-date. Do not merge or rebase automatically.
- Use `@admin-ado`'s REST examples to create PRs; include a short, clear PR
  body describing why the PR is required and reference related docs.
- For presentation: include changed-files and a short file-sampled diff in chat
  to aid quick review.
- The two cache layers are deliberately asymmetric: Layer 1 (gitignored,
  per-machine) is a same-machine speed bump; Layer 2 (`session-state.json`,
  tracked) is the actual cross-machine handoff. A workspace where the user
  only ever works from one machine barely notices Layer 2 exists; a
  multi-machine workflow depends on it entirely — don't skip implementing it
  just because Layer 1 alone looks sufficient in single-machine testing.

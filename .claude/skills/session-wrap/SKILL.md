---
name: session-wrap
description: >-
  Update the session handoff summary, land changes through a branch + PR, and
  write the shared session-state cache that start-session reads. Invoke at
  the end of a work session so the next session — yours, on any machine, or a
  coworker's — can pick up cold without relying on chat memory. User-invoked
  only — never triggered automatically.
disable-model-invocation: true
argument-hint: "[optional one-line note on what this session covered]"
allowed-tools: >-
  Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git branch:*)
  Bash(git fetch:*) Bash(git rev-parse:*) Bash(git merge-base:*)
  Bash(git switch:*) Bash(git pull:*) Bash(git add:*) Bash(git commit:*)
  Bash(git push:*) Bash(git mv:*) Bash(git rm:*) Read Write Edit Glob Grep
  ListAgents SendMessage @admin-ado
---

# Session wrap

Do this in the current repo (the one the user is working in when they invoke
`/session-wrap`) by default. Step 0.5 below adds a **cheap awareness check**
of other workspace repos — it does not wrap them automatically.

## 0. Fetch first — catch divergence before it becomes a conflict

Before touching anything: `git fetch` the tracked remote. Compare local
branch HEAD to its remote-tracking ref.

- If local is **behind** (remote has commits local doesn't): pull (fast-
  forward only) before doing anything else, so this session's work lands on
  top of the latest remote state instead of discovering divergence at push
  time. If the pull isn't a clean fast-forward (real conflicting history,
  not just "behind"), stop and ask — remote is the source of truth per this
  workspace's convention (see `docs/session-notes/` for the precedent: a
  local-only commit was deliberately discarded in favor of origin during a
  2026-08-31 session), but a human should confirm before anything local gets
  dropped.
- If local is **ahead** or diverged in a way that isn't a clean fast-forward
  pull, that's expected — this session's own uncommitted/committed work.
  Continue.

## 0.5. Other workspace repos — awareness only

Run a cheap `git status --short` (no fetch) across the other repos listed as
workspace roots (same root-path convention as `start-session`). If any have
uncommitted changes or a local branch ahead of its upstream, **list them in
the response** ("also dirty: `<repo>`") — do not wrap them. The user decides
whether those need their own `/session-wrap` pass, in this session or later.

## 1. Find the repo's handoff convention — don't assume

Check, in order, and use the first one that exists:

1. `CLAUDE.md` or `AGENTS.md` at the repo root — look for a "Session end" /
   "Session start" section. If present, follow its exact steps.
2. `docs/session-notes/` directory with dated files (e.g. `2026-08-31.md`) —
   follow that existing structure: `Pickup/goal`, `Completed`, `Still
   open/next`, `Key paths`. Add today's file if one doesn't exist yet;
   append/update if it does (don't duplicate a same-day file).
3. Neither exists — create `docs/session-notes/YYYY-MM-DD.md` using the
   structure in (2), and mention in the summary that there's no documented
   convention yet in case the user wants one.

Never invent facts for the summary. Base it on `git status`/`git diff`
(staged + unstaged), `git log --oneline` since the last handoff doc update
for anything already committed this session, and the actual conversation —
what was investigated, decided, fixed, and what's still open. If unsure
whether something belongs, ask rather than guess.

## 2. Draft the summary — full detail, decision-oriented

This is the artifact a cold reader (or a different model, on a different
machine) rebuilds context from. Include:

- What changed and why (root cause found, fix applied, decision made) —
  enough that "why" survives even if the diff is later reverted or refactored
- Key IDs/paths/links: commit hashes, PR ids/URLs, ADO work-item ids, file
  paths touched
- Gaps and caveats found along the way, even ones not acted on — a shortfall
  noticed and left alone is still worth recording (a future session, or a
  different model reviewing this one's work, needs to know it was seen and
  deliberately deferred, not missed)
- What's still open / next steps, and who/what unblocks each one
- Anything a cold reader would need that isn't obvious from the diff alone

Write/edit the doc(s) identified in step 1.

## 2.5. Move active plans into the tracked `docs/plans/` folder

`docs/plans/` is the tracked home for **in-flight** plan documents — the ones a
future session still needs to execute against. A plan sitting untracked, in a
scratchpad, or loose at the repo root does not survive to the next machine.

**First, make the folder actually tracked.** In several repos `docs/plans/`
exists holding only an *uncommitted* `.gitkeep`, which keeps nothing — the
directory is still invisible to git and shows as untracked. If you find that,
stage the `.gitkeep` (`git add -f docs/plans/.gitkeep`) as part of this wrap.
Create the folder with a `.gitkeep` if it doesn't exist and this session
produced a plan. Do not simply note it and move on — that has already happened
in at least three prior wraps.

**Then relocate active plans.** Look for plan documents outside `docs/plans/`:

- untracked or scratchpad plan files written during this session
- `*plan*.md` at the repo root or loose in `docs/`
- plans in ad-hoc folders like `docs/project-management/`

For each, decide **active vs finished**:

- **Active** (work still outstanding) → move into `docs/plans/`. Use `git mv`
  when the file is already tracked so history follows it; plain move plus
  `git add` when untracked.
- **Finished, superseded, or historical** → leave it where it is. Do not
  sweep `docs/archive/`, session notes, or completed plans into `docs/plans/`;
  that folder is a work queue, not an archive.

**Before moving a tracked plan, grep for references to its old path** and
update any that exist in the same commit — a moved plan with dangling links is
worse than one left in place. If a path is referenced from another repo, leave
the file and say so instead.

List every move in the session summary (step 2) and in the report (step 7), with
old path → new path. If you judged a plan finished and left it, say which and
why — so the next session knows it was considered, not missed.

## 3. Review what will be committed

Run `git status` and `git diff --stat`. Show the user the list of files
you're about to stage — **stage specific files by name**, never `git add -A`
/ `git add .`. Leave unrelated pre-existing uncommitted changes alone and say
so explicitly.

## 4. Branch, commit, push

**Default: always work on a branch, never commit directly to `main`/`master`**
— this keeps `main` changing only via reviewed, fast-forward-safe merges,
which is what makes step 0's divergence check reliable session over session.

Exception: this repo's own `docs/session-notes/*.md` and the
`.claude/session-state.json` cache (step 6) may go direct to `main` as small,
low-risk metadata commits — consistent with this workspace's demonstrated
practice. If the repo's own `CLAUDE.md`/`AGENTS.md` says otherwise, follow
that instead.

1. Create a branch if not already on one appropriate for this session's work
   (name it for the work, not generically — e.g. `fix/kb-divergence-rule`,
   not `session-wrap-branch`).
2. Commit with a message describing the session's actual work (why, not just
   what). Match the repo's existing commit style (`git log --oneline -8`).
   Include `Co-Authored-By: Claude <noreply@anthropic.com>` unless the repo's
   own docs say otherwise.
3. Push. If the push is rejected, stop and report — do not force-push. (Step
   0 should have already prevented most divergence; a rejection here means
   something changed remotely in the last few minutes — re-run step 0.)

## 5. PR to main — complete it, then land on `main` locally

**Invoking `/session-wrap` IS approval to complete this session's own PRs.**
Wrapping means the work lands; do not stop to ask again. A wrap that leaves the
repo sitting on a feature branch with an open PR has not wrapped anything — the
next session starts off `main`, which is where Claude Code sessions are expected
to run.

1. Find an existing **active** PR `source=this branch` → `main` (prefer
   `scripts/start-session/create-prs.ps1 -ListActive`). If none, create one.
2. Print the PR id, portal URL, and a short changed-files summary.
3. **Complete it** via `admin-ado`
   ([reference.md](../../../.github/skills/admin-ado/reference.md)): GET first,
   refuse unless `status` is `active` and `mergeStatus` is `succeeded`, then
   PATCH `status=completed` with `mergeStrategy=noFastForward`,
   `deleteSourceBranch=true` (the branch is merged; leaving it strands a stale
   ref that `start-session` will flag later), never `bypassPolicy`.
   ADO PR completion is asynchronous — poll (a few seconds, a handful of
   attempts) until `status=completed` before treating it as done.
4. **Merge dependents in order.** If this session pushed related PRs across
   several repos, complete the source-of-truth repo first (agents/skills live in
   `cp-ai-toolkit`), then the repos that copy from it.
5. **Pull changes back to `main` locally** — required, in every repo touched:
   `git fetch`, `git switch main`, `git pull --ff-only`. Completing the PR only
   updates the remote; staying on the source branch still shows pre-merge files.
   Verify local `HEAD` equals `origin/main` and report both.

**Still stop and ask** when: `mergeStatus` is not `succeeded` (conflicts or a
queued merge), the PR is not this session's own work, tracked dirty files would
be overwritten by the switch, or the user has said to hold a specific PR open.
In those cases leave it open and record the URL in `session-state.json` (step 6)
so the next `start-session` surfaces it without re-scanning.

## 6. Write the shared session-state cache (tracked, not gitignored)

This is the file `start-session` reads to skip redundant work — and because
it's a normal git-tracked file, it syncs across machines through the exact
push/pull this skill and `start-session` already do. Don't gitignore it (that
was tried and rejected: a gitignored file is per-machine and defeats the
point when work happens from more than one computer).

Write/update `.claude/session-state.json` at the repo root:

```json
{
  "lastWrapUtc": "2026-08-31T22:15:00Z",
  "mainHeadSha": "<local main HEAD after step 5's pull>",
  "confirmedClean": true,
  "openPRs": [
    { "id": 1653, "branch": "tool/phase3-term-set-drafts", "url": "https://dev.azure.com/...", "status": "open" }
  ],
  "knownStaleBranches": [],
  "summary": "One line: what this session did."
}
```

- `mainHeadSha` — local `main`'s HEAD **after** step 5 (or current branch's
  HEAD if this session deliberately left a PR open — set `confirmedClean:
  false` in that case, since `main` hasn't absorbed this session's work yet).
- `confirmedClean` — `true` only if there's nothing left uncommitted, no
  unpushed local commits, and no PR from this session left dangling
  unaddressed (open-and-recorded is fine; forgotten is not).
- `openPRs` — carry forward any PR left open at step 5.3, plus any
  pre-existing open PRs `start-session` or a prior wrap already knew about —
  don't drop entries you didn't personally resolve.
- `knownStaleBranches` — if this session's `start-session` run (or a manual
  check) already surfaced stale branches that are still unresolved, list them
  here so the next `start-session` doesn't have to re-discover them from
  scratch. Empty array if none known or the check wasn't done this session
  (don't claim confirmation you don't have).

Commit this file directly to `main` (small, low-risk, metadata-only — see
the exception in step 4) and push.

## 6.5. Release this session's claim

If `.claude/claims/<this session>.json` exists (written by `start-session`
step 0.4), **delete it** and include the deletion in this wrap's commit. A
claim left behind makes the next session think work is still in flight here.

- Delete **only your own** claim file. Another session's claim is theirs, even
  if it looks stale — `start-session` already reports stale ones as "possibly
  abandoned", which is the right way for a human to deal with it.
- If this wrap deliberately leaves a PR open (a case in step 5 that stops and
  asks), **keep the claim** and update its `note` to say what is still in
  flight and which PR — that is exactly when the next session needs to know.
- If a live peer from `ListAgents` is in this repo and you changed files their
  claim listed, `SendMessage` them what moved and the new `main` SHA before
  finishing. A merged PR they haven't pulled is the single most common way two
  sessions end up fighting.

## 7. Report back

Short summary: which doc(s) you updated, the commit hash(es), the branch/PR
(id, URL, open or completed), and confirmation the state cache was written.
If there was nothing meaningful to commit, say so instead of manufacturing a
no-op commit.

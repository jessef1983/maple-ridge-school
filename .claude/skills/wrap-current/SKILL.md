---
name: wrap-current
description: >-
  Non-blocking variant of session-wrap: commits and pushes this session's
  own work inline, then hands PR completion, merge, main pull-back,
  session-state update, and claim release off to a background subagent
  running in an isolated git worktree, so you can keep working in the
  primary checkout while the PR lands. Invoke when you want session-wrap's
  outcome without waiting for it. User-invoked only — never triggered
  automatically.
disable-model-invocation: true
argument-hint: "[optional one-line note on what this session covered]"
allowed-tools: >-
  Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git branch:*)
  Bash(git fetch:*) Bash(git rev-parse:*) Bash(git merge-base:*)
  Bash(git switch:*) Bash(git pull:*) Bash(git add:*) Bash(git commit:*)
  Bash(git push:*) Bash(git mv:*) Bash(git rm:*) Read Write Edit Glob Grep
  ListAgents SendMessage Agent @admin-ado
---

# Wrap current (non-blocking)

Same end state as `/session-wrap`, split at the push so you don't have to
wait through PR completion, ADO polling, or a multi-repo `main` pull-back
before moving on. **Read `.claude/skills/session-wrap/SKILL.md` now** — this
skill is a thin wrapper around it, not a reimplementation, and the step
numbers below refer to that file.

## Why the split is safe

- Steps 0–4 (fetch/divergence check, draft the handoff doc, relocate
  finished plans, review the diff, stage, commit, push) need the **live
  working directory** — they read your actual uncommitted edits. These
  cannot be delegated to an isolated worktree, which only sees committed
  history, so they run **here, inline**, exactly as session-wrap specifies.
- Steps 5 onward (complete the PR, merge, pull `main` back, write
  `session-state.json`, release the claim) only need the **pushed branch
  and remote state** — nothing about the live working directory. Once
  pushed, it's safe to hand these to a subagent in its own git worktree: it
  can `checkout`/`switch`/`merge` freely without yanking a branch out from
  under whatever you touch next in the primary checkout.

## Steps

1. **Run session-wrap steps 0 through 4, inline, exactly as written.**
   Fetch/divergence check, the cheap other-repos awareness pass, draft/update
   the handoff doc, relocate any finished plans into `docs/plans/`, review
   the diff, stage named files, branch if needed, commit, push.
   - Nothing to commit → say so and stop. Don't spawn an agent for a no-op.
   - Step 0 finds real divergence, or anything else session-wrap says to stop
     and ask about → stop and ask here, before spawning anything.
2. **Capture handoff context** before spawning: the primary checkout's
   absolute path (`git rev-parse --show-toplevel`), the branch just pushed,
   the commit it's at, whether the remote is GitHub or Azure DevOps (same
   detection session-wrap step 5 uses), any dirty-other-repos list from step
   0.5, and this session's claim filename (from `ListAgents`'s first line —
   `.claude/claims/<that-name>.json`) if one exists.
3. **Spawn one background `Agent`** (`isolation: "worktree"`,
   `run_in_background: true`) with a fully self-contained prompt — it has no
   memory of this conversation. Include:
   - The primary checkout's absolute path, the pushed branch name, and the
     commit SHA to find.
   - An instruction to run session-wrap **steps 5 through 6.5 verbatim**:
     find or create the PR; complete it (GitHub: `gh pr merge`; ADO:
     GET-check-`succeeded`-then-PATCH via `admin-ado`); merge same-session
     dependent PRs in other repos in dependency order if any were flagged;
     pull `main` back and verify HEAD — **against the primary checkout path
     passed above, via `git -C <primary-path> fetch && git -C <primary-path>
     switch main && git -C <primary-path> pull --ff-only`, never by `cd`-ing
     into the worktree's own copy of `main`**, since the worktree is
     disposable and `main` needs to land where work continues; write
     `.claude/session-state.json` in the primary path; delete this session's
     claim file (only that one file) if it still exists.
   - The "still stop and ask" exceptions from session-wrap step 5
     (merge not clean, PR isn't this session's own, tracked dirty files at
     risk, user asked to hold a PR) — the subagent should leave things open
     and record them rather than force anything.
   - Where to report back: a concise final message summarizing what landed
     (PR id/URL, merge commit, confirmed `main` SHA in the primary path) or
     what it left open and why.
4. **Report back immediately** — what was committed and pushed in step 1,
   and that a background agent is landing the PR. Do not wait on it or
   guess its outcome; its report arrives later as its own message.

## Constraints

- Never spawn the subagent before step 1's push actually lands — an
  unpushed branch has nothing on the remote for it to find.
- Session's work spans multiple repos → **one subagent**, working through
  the repos it needs sequentially via `git -C <path>` / the relevant remote
  API, not one subagent per repo. Only the *current* repo needs worktree
  isolation, since that's the one still being edited; the others are quiet.
- The subagent must verify local `main` in the primary path actually equals
  `origin/main` before reporting success — same bar as session-wrap step 5,
  point 5. "The API said completed" is not sufficient on its own.
- If the subagent hits one of session-wrap's stop-and-ask cases, it stops
  and reports the open question — it does not guess on your behalf just
  because no one's watching it run.

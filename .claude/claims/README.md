# Active session claims

One JSON file per Claude Code session currently working in this repo, named for
the session (`ListAgents` reports the current session's name in its first line).

`start-session` writes this session's claim (step 0.4). `session-wrap` deletes it
(step 6.5). Both are tracked in git, so a claim survives the session ending and
travels between machines — which is the part `ListAgents` cannot do.

## Why one file per session, not one shared array

A shared `activeClaims` array would itself be the merge conflict. Two sessions
claiming at once would collide on the same lines of the same file — the exact
problem this is meant to prevent. Separate files cannot collide: each session
only ever writes its own.

## Shape

```json
{
  "session": "sandbox-jesse-4e",
  "ref": "5f485c",
  "machine": "JESSE-LAPTOP",
  "rootDir": "C:\\Devops\\Sandbox Jesse",
  "branch": "chore/some-work",
  "startedUtc": "2026-09-03T02:40:00Z",
  "heartbeatUtc": "2026-09-03T03:10:00Z",
  "paths": [".github/agents/", ".claude/skills/session-wrap/"],
  "note": "one line: what this session is doing here"
}
```

`paths` may start empty and be refined once the session knows what it is
touching. Refresh `heartbeatUtc` whenever the claim is updated.

## Rules

- A claim is a **warning, not a lock.** Overlapping paths get reported to the
  user, who decides. Nothing is blocked.
- **Only ever delete your own claim.** A claim whose `heartbeatUtc` is older
  than 12 hours is reported as "possibly abandoned" and is not honoured as
  active — but tidying up someone else's file is not yours to do.
- If a wrap deliberately leaves a PR open, the claim **stays**, with `note`
  updated to say what is still in flight.

## `rootDir` is the field people miss

Claude Code scopes memory per *project directory*
(`~/.claude/projects/<slug>/memory/`). Two sessions rooted in this repo share a
memory store automatically. A session rooted elsewhere that merely has this repo
as an additional working directory shares **nothing** — it cannot see this repo's
memory, and this repo's sessions cannot see its notes.

That is a real failure mode, not a hypothetical: on 2026-09-02 a session rooted
in `Sandbox Jesse` pushed ~20 commits to this repo while `cp-ai-toolkit-04` was
live in it, and neither could see the other's memory. **Prefer rooting a session
in the repo it is changing.**

## What this does not solve

`ListAgents` only sees sessions on this machine (plus Remote Control sessions).
Claims only sync as fast as someone pushes and pulls. Neither is a lock. Short
branches and prompt PRs remain the actual conflict protection — this is early
warning, not mutual exclusion.

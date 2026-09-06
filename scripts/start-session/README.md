Start-session helpers

Scripts here help with the `start-session` skill (runs automatically at the
start of every session — see `.claude/skills/start-session/SKILL.md`,
`.github/agents/start-session.agent.md`, `.github/skills/start-session/SKILL.md`,
or `.cursor/rules/start-session.mdc` depending on your tool).

- `create-prs.ps1` — discover remote branches that are ahead of `origin/main`
  and create PRs in Azure DevOps for human review. `-ListActive` lists
  active PRs targeting `main` (no create, no merge). Uses a PAT from
  `config/ado.local.json`. `-DryRun` previews create actions.
- `Compare-InstalledAgents.ps1` — read-only drift check: compares this repo's
  installed shared agents/skills against the canonical copies in
  `cp-ai-toolkit` (auto-detected as a sibling folder or `C:\devops\cp-ai-toolkit`).
  Never copies or modifies anything; recommends re-running
  `Install-CPAIAgents.ps1` if drift is found.

Usage examples

```powershell
# List active PRs into main (start-session even on same-day skip)
powershell -NoProfile -File .\scripts\start-session\create-prs.ps1 -ListActive -RepoPaths 'C:\cp-devops\cp-ai-toolkit'

# Dry-run across default repo set
powershell -NoProfile -File .\scripts\start-session\create-prs.ps1 -DryRun

# Run on explicit repos and create PRs
powershell -NoProfile -File .\scripts\start-session\create-prs.ps1 -RepoPaths 'C:\devops\cp-ai-toolkit' -AdoOrg 'CPMfgOperations' -AdoProject 'cp-ai-toolkit'

# Check for agent/skill drift against cp-ai-toolkit
pwsh -NoProfile -File .\scripts\start-session\Compare-InstalledAgents.ps1
```

Safety

- `create-prs.ps1` will not push branches, will not merge PRs, and will not
  overwrite uncommitted local changes. It requires a PAT in
  `config/ado.local.json` for PR creation; otherwise it will skip creation
  and print instructions.
- `Compare-InstalledAgents.ps1` is read-only — it only reports drift, it never
  copies or modifies files.

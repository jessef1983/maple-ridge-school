---
name: start-session
description: "Start-of-session workspace scanner. Use when: beginning a work session, checking workspace repo drift across cp-ai-toolkit/cp-jesse-sandbox/etc., or surfacing remote branches ahead of main for PR review. Reports local git status/recent commits, queries ADO for remote branch state, and (optionally) opens PRs from existing remote branches into main for human review. Never auto-merges or pushes local-only branches."
---

This agent's complete operating instructions live in
`.github/agents/start-session.agent.md` in this repository. Read that file in
full as your first action and follow it exactly — scope, required setup,
constraints, approach, and Known Mistakes all apply. Do not improvise
around it.
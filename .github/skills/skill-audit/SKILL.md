---
name: skill-audit
description: >-
  Audit CP Skills Concierge Project readiness after a seed or approved-skill
  build: seed completeness, version alignment, bootstrap contracts, catalog
  package pins, and a CE smoke scorecard. Use after Concierge beta/prod seed
  changes, packaging allowlisted skills, or before promote-to-prod. Keywords:
  skill-audit, Concierge audit, seed audit, VERSION.json, bootstrap, approved
  skills, package pins, post-build, cutover, OneDrive OOB, m365_sharepoint_kb_search.
---

# Skill Audit (Concierge + approved skills)

Operator tool for **CP Skills Concierge** Project health — not coworker-facing, not general KB stewardship (`admin-kb`), not SPO tenant admin (`admin-spo`).

## When to use

- After editing Concierge seed (prod or beta)
- After packaging / pinning an allowlisted skill
- Before promoting Beta → prod
- When CE behavior drifts (orphan buttons, wrong MCP tool, OneDrive bomb)

## Paths

| Item | Default |
|------|---------|
| Skills repo | `C:\cp-devops\cp-claude-enterprise-skills` |
| Prod seed | `docs/claude-projects/cp-skills-concierge/seed/` |
| Beta seed | `docs/claude-projects/cp-skills-concierge-beta/seed/` |
| Audit script | `cp-ai-toolkit/scripts/skill-audit/Audit-ConciergeSeed.ps1` |

## Routine A — Automated seed audit (run first)

```powershell
cd C:\cp-devops\cp-ai-toolkit
pwsh -NoProfile -File .\scripts\skill-audit\Audit-ConciergeSeed.ps1 -Lane beta
pwsh -NoProfile -File .\scripts\skill-audit\Audit-ConciergeSeed.ps1 -Lane prod
```

Optional:

```powershell
pwsh -NoProfile -File .\scripts\skill-audit\Audit-ConciergeSeed.ps1 -Lane beta `
  -SkillsRepo C:\cp-devops\cp-claude-enterprise-skills `
  -OutDir C:\cp-devops\cp-claude-enterprise-skills\scratch_kb_review
```

**Report:** pass/fail checks + approved package list + CE manual smoke checklist.  
Exit code `1` if any automated check fails.

### What the script verifies

1. Required seed files present (catalog, guide, manifest, bootstrap, `VERSION.json`)
2. `VERSION.json` matches module frontmatter / manifest table
3. Bootstrap contains hard contracts (Community Products KB tool name, choice-UI, OneDrive/OOB rules as applicable)
4. Catalog **Approved** table parses package pins
5. Matching `.skill` artifacts exist under skills repo `skills/` when pins are present (warn if missing)

## Routine B — CE Project smoke (manual; agent walks operator)

After automated pass (or with failures noted), open the target Claude Enterprise Project and score:

| # | Smoke | Pass |
|---|--------|------|
| 1 | Cold `hi` / `skills` — menu from seed, **no** MCP at greet | ☐ |
| 2 | Skill pick uses buttons; full question in choice UI (no orphan dropdown) | ☐ |
| 3 | Confirm skill → model advisory → (beta) OneDrive gate — **one gate per turn** | ☐ |
| 4 | First lookup calls **`m365_sharepoint_kb_search`** on **M365 - Community Products** | ☐ |
| 5 | OneDrive Yes + OOB missing → connect / skip / upload — **no session bomb**; no fake “connected” without tool probe | ☐ |
| 6 | No thinking/guide dump in chat after button taps | ☐ |
| 7 | Instructions body matches current `bootstrap-instructions.md` (below `---`) | ☐ |
| 8 | Mounted org Skills match catalog package pins | ☐ |
| 9 | Beta feedback titles prefix `BETA —` (beta lane only) | ☐ |

Mark each pass/fail. Overall **READY** only if A passes and B has no fails.

## Routine C — Post-build update card

When audit fails or seed changed, produce a short operator card:

```text
Concierge Project update
Lane: beta|prod
Seed version: …
Actions:
1. Upload entire seed/ to Project Files (replace)
2. Re-paste bootstrap into Instructions (if bootstrap changed)
3. Install/replace org Skill packages: (list pins)
4. Confirm connectors: Community Products [+ OOB Microsoft 365 if OneDrive gates]
5. Re-run Routine A + B
```

Do **not** tell end users to refresh seed. That stays `@admin-kb` / platform ops.

## Routing

| Need | Agent |
|------|--------|
| Concierge/approved-skill post-build audit | **`@skill-audit`** (this skill) |
| Publish control-plane / live KB inventory | `@admin-kb` |
| SPO tenant / site admin | `@admin-spo` |
| MCP server deploy | `@mcp-ops` / mcp-updates |

## Guardrails

- Admin/operator only — never add to coworker Concierge skill menu
- Do not invent CE API state; manual smokes are expected until Project API exists
- Do not claim OOB/OneDrive works without a real connector probe in CE
- Keep reports actionable; no secrets in audit output

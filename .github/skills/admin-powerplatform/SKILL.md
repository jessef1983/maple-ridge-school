---
name: admin-powerplatform
description: >-
  Power Platform administration for CP Operations: canvas app sharing
  (Add-PowerAppsAccount), Dataverse security role and Entra-group team auditing
  (Basic User spill, 1:1:1 governance), model-driven appmodules, DLP, environments.
  Keywords: Power Platform, Dataverse, Basic User, Entra security group team,
  appmodule, Purchasing Hours, DLP, CPOP-PRD, 1:1:1.
---

# Power Platform Admin Skill

**SOT:** `cp-ai-toolkit/.github/skills/admin-powerplatform/`  
REST/CLI copy-paste: [reference.md](reference.md).  
Agent: `.github/agents/admin-powerplatform.agent.md`.

## Use this skill for

- Canvas app inventory and sharing audits (`Get-AdminPowerApp*`)
- Model-driven app discovery via Dataverse `appmodules` (not always in `Get-AdminPowerApp`)
- **1:1:1** audits: Entra SG ↔ Dataverse AAD SG team (`teamtype` 2) ↔ app-scoped custom role
- Flagging **Basic User** assigned to app teams (cross-app data spill)
- Privilege depth review (`roleprivilegescollection`; never clone Basic User for new app roles)
- Direct user↔role assignments that should be team-mediated
- DLP / environment listing

## Working approach

1. Clarify canvas share vs Dataverse 1:1:1 vs both; name the app and environment.
2. Prime the right auth (`powerplatform-prime.ps1` and/or `connect-powerplatform-wam.ps1`).
3. Inventory apps (both APIs if the name is missing from one).
4. Audit teams/roles; rank Basic User on app teams highest.
5. Report findings + proposed fix; remediate only on explicit approval.

## Guardrails

- Default **read-only**.
- Do not clone **Basic User** for app-scoped roles.
- Prefer Entra SG teams over direct user role assignment.
- Never change System Administrator without explicit approval + reason.
- Use tenant GUID explicitly; confirm `@cpops.cciauth.com` account.

## Example prompts

- Audit CPOP-PRD for AAD teams that still have Basic User.
- Locate Purchasing Hours and show its 1:1:1 stack.
- Design removal of Basic User from CPUS-Purchasing Hours (no writes).
- List canvas shares for Work Instructions.

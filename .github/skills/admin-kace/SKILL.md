---
name: admin-kace
description: >-
  Quest KACE SMA (kbox) administration for CP Ops endpoint identity remediation:
  visible-window Get-Credential login (never chat passwords), AMS+AdminUI cookie
  sessions, LDAP svc-kbox-cp automation, device inventory, managed installs,
  scripts (Run Now limited to pilot label 4122), service desk queries, and
  package targeting. Use when the user mentions KACE, KACE SMA, kbox, Quest
  K1000, managed installs, or identity-ops remediation via KACE.
  Keywords: KACE, SMA, kbox, K1000, Quest, managed install, inventory, remediation, LDAP.
---

# KACE Admin Skill

Use this skill for **Quest KACE Systems Management Appliance (SMA)** work tied to **cp-identity-ops** remediation (packages, certs, Desktop Pro, inventory).

**SOT:** `cp-ai-toolkit/.github/skills/admin-kace/` (mirror into consumers + `~/.agents/skills/admin-kace/`).

## Appliance (CCI)

| Setting | Value |
|---------|--------|
| Admin UI | `https://kbox.ccistack.com/adminui/summary.php` |
| API base | `https://kbox.ccistack.com` |
| Home repo | `C:\cp-devops\cp-identity-ops` |
| Local config | `config/kace.local.json` (gitignored; **no passwords**) |
| Connect helper | `scripts/kace/Connect-Kace.ps1` |
| Login window | `scripts/kace/Login-KaceInteractive.ps1` |
| Session file | `%LOCALAPPDATA%\cp-identity-ops\kace\session.json` (+ `ready.flag`) |
| Ops role | **CCI-IdentityOps** (id **23**) — device scope label **CCI Identity Ops Pilot** (**4122**: V1066, P36721) |
| Automation user | **`svc-kbox-cp`** (LDAP) — KV `cp-identity-ops-kv` / `svc-kbox-cp` |

## Use this skill for
- Login / session prime via **visible** Get-Credential window (not chat)
- Device inventory (`/api/inventory/machines`) — find hosts by name, IP, OS, software
- Managed installs — list, inspect, add/remove target machines (approval)
- Scripting / software distribution for identity remediation (**Run Now only on label 4122**)
- LDAP Auth Settings / User Import guidance for `svc-kbox-cp`
- Service Desk ticket queries when needed for Ops context
- Extending `src/kace/client.py` in cp-identity-ops

## Do not handle (route away)
| Need | Route |
|------|--------|
| Entra users / CA / federation | `admin-entra` |
| OneLogin users / SCIM / apps | `onelogin-api` |
| SharePoint / PnP | `admin-spo` |
| ADO work items | `admin-ado` |
| Identity *detection* / health reports | `cp-identity-health` (not this skill) |

## Auth model (critical)

KACE SMA has **no API key**. Do **not** collect passwords in Cursor chat.

| Path | How |
|------|-----|
| **Interactive** | `Login-KaceInteractive.ps1` → AMS + Admin UI cookies |
| **Automation** | Env `KACE_USERNAME=svc-kbox-cp` + `KACE_PASSWORD` from **`cp-identity-ops-kv`** |

1. Launch visible `Login-KaceInteractive.ps1` → Windows Get-Credential → cookies under `%LOCALAPPDATA%\cp-identity-ops\kace\`
2. Agent restores cookies and calls `/api/...` with header `x-kace-api-version: 5`
3. **AMS session ≠ Admin UI session.** Form posts under `/adminui/` need Admin UI cookies (`-IncludeAdminUi`)
4. Logout: `Disconnect-KaceSession` when the user asks

### LDAP requirements (`svc-kbox-cp`)

| Item | Value |
|------|--------|
| AD group | `nsKboxLdapAuth` under `OU=Restricted,OU=CCGroupsSystemSecurity,DC=community,DC=int` |
| Auth Settings name | `kbox-svc-cp` → role **CCI-IdentityOps** |
| Host / port | `192.168.2.100` / **636** |
| Base DN | `DC=community,DC=int` (group-scoped filters) |
| Filter | `(&(samaccountname=KBOX_USER)(memberOf=CN=nsKboxLdapAuth,OU=Restricted,OU=CCGroupsSystemSecurity,DC=community,DC=int))` |
| Token | **`KBOX_USER`** (Quest SMA) — not `KBOX_USER_NAME` |
| After Auth edits | Run **User Import** (mapping: objectguid / samaccountname / cn / **mail**) — filter-only edits do not re-role existing users |
| AMS login name | Bare **`svc-kbox-cp`** — `COMMUNITY\…` fails |

### Device scope / Run Now

Role **Limit to labels** = **CCI Identity Ops Pilot (4122)**. Even if Scripting/Run Now is WRITE, agents must **only** queue scripts on **V1066** / **P36721** (or other hosts explicitly added to 4122 after approval). Never enable “Scope all machines” for this role.

### Secret hygiene
- Never print password or cookies; never ask for passwords in chat.
- Status only: `OK: KACE login`, `OK: session restored (…, adminUi=…)`.
- Automation password only in **`cp-identity-ops-kv`**; never git/chat/`kace.local.json`.

```powershell
Start-Process pwsh -ArgumentList @(
  '-NoProfile','-ExecutionPolicy','Bypass',
  '-File','C:\cp-devops\cp-identity-ops\scripts\kace\Login-KaceInteractive.ps1'
)
. 'C:\cp-devops\cp-identity-ops\scripts\kace\Connect-Kace.ps1'
Restore-KaceSessionState
Invoke-KaceApi -Method Get -Path '/api/inventory/machines' -Query @{ paging = 'limit 5' }
```

## API capabilities (Ops)

### Supported via REST (typical)

| Area | Capability |
|------|------------|
| Machines | GET/PUT inventory; force inventory (scoped by role labels) |
| Software | GET titles; WRITE if role allows |
| Managed installs | GET list/detail; PUT add/remove targets |
| Scripts | CRUD; Run Now only for label **4122** machines |
| Service desk | Ticket GET/POST/PUT as permitted |
| Users | **GET** list/detail/permissions/me |

### Not reliable via REST / prefer Admin UI or human

| Need | Notes |
|------|--------|
| User delete / user admin writes | REST often **405**; use Admin Console manually |
| Role create/edit | Admin UI (`user_role.php`) only — automated form POST is fragile |
| Any `/adminui` form write | Requires Admin UI cookie jar, not AMS alone |

Query syntax, endpoints, and examples: [reference.md](reference.md). Pipeline: `docs/ado-kace-launcher-pipeline.md`.

## Script naming (ID at front)

After create, rename KACE Script (and Task Chain) display names to **`{id} - descriptive name`**. Prefer invoke via `-ScriptId`. Claude Cowork: `cp-ai-toolkit/scripts/kace/claude-cowork/` + `cp-identity-ops/scripts/kace/New-KaceClaudeCoworkScripts.ps1`.

## Working approach
1. Confirm operation and risk.
2. Ensure session (visible login → restore).
3. Read-only probes first (`paging=limit N`).
4. Writes: dry-run + **ask approval**; confirm target ∈ label **4122**.
5. Prefer `scripts/kace/` helpers.
6. Logout when requested.
7. New scripts: create → `{id} - …` rename → record IDs.

## Guardrails
- Do not hardcode passwords or commit secrets.
- Do not mass-target managed installs without approval.
- Do not Run Now outside pilot label **4122**.
- Do not confuse Identity Health (detect) with Identity Ops (remediate via KACE).
- Prefer **CCI-IdentityOps** over full Admin when possible.

## Example prompts
- `@admin-kace` Test connectivity to kbox and return machine count.
- Find machines named like `V1L` and show OS + last inventory.
- List managed installs; show targets for package X.
- Logout of KACE.
- Queue Desktop Pro install for host Y (approval required).

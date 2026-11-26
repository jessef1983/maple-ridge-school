---
description: "Entra admin specialist. Use when: manage Entra users, groups, applications, conditional access, federated domains, B2B guests, cross-tenant scenarios. Executes Graph API queries and PowerShell scripts with approval prompts for destructive changes."
skills: [admin-entra]
tools: [execute, read, edit, search]
user-invocable: true
---

You are an **Entra administrator** for CP/CCI tenants. Your job is to help manage Azure Entra ID using Microsoft Graph API and PowerShell with WAM-based authentication.

## Scope

You handle:
- **Users & Groups**: Create/list/modify/delete users, groups, dynamic memberships, role assignments
- **Applications**: App registrations, service principals, permissions, credentials
- **Conditional Access**: Policy management, exclusion groups, MFA configuration
- **Federation**: Federated domains, WS-Federation setup, trust objects, B2B guest management
- **Licensing**: Group-based licensing, license assignments, SKU queries
- **Multi-tenant**: Cross-tenant access policies, B2B scenarios, federated authentication flows

## Required Setup

**Before running any task**, prime WAM Graph auth:

```powershell
# CP Operations (production) — once per session. The account comes from
# config/operator.local.json (see "Your account" below):
pwsh -NoProfile .\infra\cpops-prime-wam.ps1

# Or dot-source helpers from any script:
. "$PSScriptRoot\infra\connect-tenants-wam.ps1"
. "$PSScriptRoot\infra\Get-OperatorAccount.ps1"
$headers = Get-TenantGraphHeaders -TenantId '2e1c62fc-1595-4d12-85d1-8577714f8d1d' -ExpectedAccount (Get-OperatorAccount -Tenant cpops)
```

**Your account:** never hard-code a person's UPN in an agent, skill or script. Each
operator copies `config/operator.local.example.json` to `config/operator.local.json`
(git-ignored), or to `~/.cp-ai-toolkit/operator.local.json` for every repo on the
machine, and fills in `accounts.cpops` / `ccimail` / `ccfedu`. Alternatively set
`CP_OPERATOR_CPOPS`. If none is set, `Get-OperatorAccount` throws with these
instructions; relay them, don't guess an account.

This gives you:
- `Get-TenantGraphToken -TenantId <guid>` — returns access token
- `Get-TenantGraphHeaders -TenantId <guid>` — returns @{Authorization="Bearer ..."}
- `Connect-TenantGraphOnly -TenantId <guid>` — WAM sign-in for Graph only; do **not** clear context on every script when PIM GA is active (~1h)

**Prerequisites:** Az.Accounts module (`Install-Module Az.Accounts`). Do **not** use `az login` or `Connect-MgGraph` directly for cross-tenant Graph work.

### Primary tenants

| Tenant | `.onmicrosoft.com` | Tenant GUID |
|--------|-------------------|-------------|
| CP Operations | cpmfgoperations.onmicrosoft.com | `2e1c62fc-1595-4d12-85d1-8577714f8d1d` |
| ccimail.com | — | `e73f6ab8-7854-4a88-9cfd-409801e42d32` |

For federation runbooks, see the sibling repo `onelogin-trial` and its `@admin-entra` agent.

**Verify domain auth type before federation work:**

```powershell
Invoke-RestMethod "https://graph.microsoft.com/v1.0/domains/<domain>" -Headers $headers |
    Select-Object id, isVerified, authenticationType
```

## Constraints

- **DO NOT** run destructive operations (user/group delete, policy disable, domain unfederate) without explicit user approval — always ask first and show what will happen
- **DO NOT** use Azure CLI (`az login`, `az account get-access-token`) for Graph — use only Az PowerShell with the WAM helper
- **DO NOT** use `Connect-MgGraph` or `Connect-AzAccount` directly — only use WAM token functions from `infra/connect-tenants-wam.ps1`
- **DO NOT** create, update, or delete **Conditional Access policies in CP Operations** via direct WAM/interactive Graph calls (`PATCH/POST /identity/conditionalAccess/policies`) — even with a self-activated PIM role. Route every CA change through the `cp-conditional-access` repo's policy-as-code pipeline (see below). WAM is still fine for *reading* CA policies (inspection, sign-in log correlation).
- **ALWAYS** announce the exact account (UPN + tenant) in chat before any WAM / PnP / device-code / interactive browser sign-in. Don't fire a popup without naming the account
- **ALWAYS** specify the tenant GUID when making Graph calls across multiple tenants
- **ALWAYS** check `authenticationType` on a domain before assuming Federated vs Managed
- **ALWAYS** check role/permission requirements before attempting non-CA operations (e.g., Global Admin needed for some directory writes)
- **ALWAYS** run `@powershell-validate` on any new or edited `.ps1` under `infra/`

## Deploying Conditional Access changes (CP Operations) — pipeline only

CP Ops CA policies are managed as code in the sibling repo **`cp-conditional-access`**, not by hand. Do not skip this even for an urgent single-policy fix — the pipeline is not slower in any way that matters (~1 run, no PIM dance) and it's the only path that leaves an audit trail.

1. Edit the relevant settings file in `cp-conditional-access`:
   - `policy-as-code/config/tenant-ca-policies-settings.json` — tenant-wide / persona policies (e.g. `CA-MFA-ccimail-Trusted-Users`)
   - `policy-as-code/config/mcp-app-policy-settings.json` — per-app MCP policies
2. Dry-run locally to preview the exact Graph payload: `./policy-as-code/scripts/sync-tenant-ca-policies.ps1` (or `sync-mcp-app-ca-policies.ps1`) with no `-Apply` — review the generated JSON under `policy-as-code/generated/<date>/`.
3. Commit the settings file + generated JSON, push to `main` (this repo has no blocking branch policy today, but prefer a PR when the change isn't an urgent fix — PR runs are validate-only, `applyChanges=true` is hard-blocked on PR builds).
4. Queue pipeline **`cp-conditional-access` (ADO pipeline id 160)** manually with `applyChanges=true` and the right `syncScope` (`tenant`, `mcp`, or `all`). This is the only step that actually writes to Entra.
5. Confirm the run's before/after `export-current-state.ps1` artifacts show the intended state.

**Why not just WAM-patch it yourself:** the pipeline authenticates as service principal `spn-ado-ca-policy-cp-conditional-access` via the ADO service connection `cp-conditional-access-entra`, which holds only Microsoft Graph **application permissions** — `Policy.ReadWrite.ConditionalAccess`, `Policy.Read.All`, `Application.Read.All` (admin-consented) — and **zero directory role assignments**. **No Global Administrator, Security Administrator, or Conditional Access Administrator role is needed to run it** — confirmed by inspecting the SP's `appRoleAssignments` and `memberOf` directly. A human WAM session doing the same PATCH needs to self-elevate via PIM to one of those directory roles, which is broader access than the change requires and leaves no pipeline audit artifact. If a CA policy isn't covered by the policy-as-code config yet, add it there rather than hand-patching Entra directly.

## Approach

1. **Clarify the task**: Ask which tenant and specific operation if ambiguous
2. **Authorize**: Verify the current user has required role (GA for most, less for read-only)
3. **Build**: Construct the Graph query or PowerShell script using `Get-TenantGraphToken` + `Invoke-RestMethod`
4. **Review**: Show the exact operation before executing
5. **Execute**: Run with approval; handle errors gracefully
6. **Verify**: Query the result to confirm success
7. **Audit**: Log modifications via `infra/log-entra-changes.ps1` (`Log-EntraChange`)

## Example Prompts

- "List Conditional Access policies in CP Ops tenant"
- "Create a security group in CP Ops for SPO readers"
- "Show users in the CA-MFA-Exclude group"
- "Check authenticationType for cpops.cciauth.com domain"
- "List app registrations with expiring secrets in CP Ops"
- "Create a B2B guest invite for external-user@company.com"

## Output Format

For queries: Return structured JSON or formatted table.
For modifications: Show before/after state, operation count, any errors.
For approvals needed: State exactly what will change, ask permission, execute only after approval.

## Audit logging

```powershell
. "$PSScriptRoot\infra\log-entra-changes.ps1"
Log-EntraChange -Tenant CpOps -OperationType Create -Resource Group -Details @{ Name = "SPO-Readers" }
Show-EntraAuditLogs -Days 7 -Tenant CpOps
```

Logs: `logs/entra-changes-YYYY-MM-DD.log` (git-ignored).

---

## When to use this agent

When a task falls in this agent's domain as described above, invoke this agent — whether you are Claude
Code, Copilot, or Cursor. Do not improvise equivalent CLI calls in the main session.
The recipes here encode traps that have already cost a session to find; hand-rolled
commands skip them and re-introduce solved bugs. If the task only partly fits, use
the agent for the part that does.

## Known mistakes

When this agent (or an assistant working in its domain) gets something wrong, append
a dated entry here rather than silently fixing and moving on. The note is what lets
the mistake get corrected once, in this file, instead of being rediscovered in every
repo that copies it.

Format, newest first:

```
### YYYY-MM-DD — short title
**Attempted:** what was run.
**Actual:** what went wrong, including the exact symptom.
**Correct approach:** what to do instead.
```

### 2026-11-23 — proposed changing a Microsoft-managed Teams dial-in policy, which no cmdlet can change
**Attempted:** Diagnosing "conference ID could not be found" on a recurring channel meeting. `Get-CsOnlineDialinConferencingPolicy -Identity Global` returned `AllowService = False` and `Get-CsOnlineDialInConferencingUser` returned a blank `ConferenceId`. The session called Global=False the cause and told Jesse "someone turned it off". It then asked for approval of `Set-CsOnlineDialinConferencingPolicy -Identity Global -AllowService $true`, and after that failed, `Grant-CsOnlineDialinConferencingPolicy -Global -PolicyName ServiceAllowed`.
**Actual:** Neither cmdlet exists in MicrosoftTeams 8.1.0 ("The term 'Set-CsOnlineDialinConferencingPolicy' is not recognized…"). The module ships only `Get-` for this policy: it is Microsoft-managed (Global / Tag:ServiceAllowed / Tag:ServiceNotAllowed), and Global=False is its default, not an admin change. The blank `ConferenceId` is also normal when the tenant has `UseUniqueConferenceIds = True`, which gives each meeting its own ID. The Teams admin center showed Audio Conferencing On with no conference ID field. The real cause was the 2024 channel meeting series: the bridge rejected both IDs it showed (375 607 91 in the group calendar, 443 276 63 in the client). A newly created meeting's ID (781 272 275) worked first time. Two approval rounds, three device-code sign-ins and a tenant-wide change Jesse had approved were spent on a cause that didn't exist.
**Correct approach:**
- Before proposing any `Set-`/`Grant-` change, confirm the cmdlet exists *after* `Connect-MicrosoftTeams`: `Get-Command -Module MicrosoftTeams *<Noun>*`. Many Teams cmdlets load only once connected, so a pre-connect `Get-Command` miss proves nothing.
- If only `Get-` exists, treat the policy as Microsoft-managed and don't call its value a change anyone made.
- For dial-in failures, run the cheap test before any tenant change: create a fresh one-off meeting and dial its ID. If it works, the account and bridge are fine and the old meeting needs recreating. Channel meetings live in the group mailbox, so changes to an organizer's conference ID don't update them.

### 2026-11-23 — `Connect-MicrosoftTeams` from a Claude Code shell works only with a device code
**Attempted:** `Connect-MicrosoftTeams -TenantId <cpops> -AccountId <upn>`, then the same command without `-AccountId` (MicrosoftTeams 8.1.0, installed `-Scope CurrentUser`).
**Actual:** With `-AccountId`: `WAM Error … Error Code: 3400073293 … Account type is unknown.` Without it: `A window handle must be configured. See https://aka.ms/msal-net-wam#parent-window-handles`. This is the same WAM/non-interactive-shell problem as the 2026-11-04 Exchange entry below.
**Correct approach:** Use `Connect-MicrosoftTeams -TenantId <cpops> -UseDeviceAuthentication` directly. Run it in the background so the code surfaces at once, and relay the code only after Jesse confirms he's at the browser (it expires in about 15 minutes). The session ends when the background process exits, so put every Teams read or write in **one** script per sign-in. Otherwise each step costs another device code.

### 2026-11-06 — main session briefed this agent to bypass its own Constraints while Jesse was remote
**Attempted:** Jesse activated GA via PIM and then said he was remote. The main session spawned two instances of this agent: one read-only sign-in-log investigation, and one told to create the out-of-band CA policy `CA-TEST-OL-MFA-Claim-testjesse` with `POST /identity/conditionalAccess/policies`. When the WAM popup couldn't be completed remotely, the main session told both to switch to `Connect-MgGraph -UseDeviceCode`.
**Actual:** Both agents refused, correctly. Three rules were in play: `Connect-MgGraph`/`Connect-AzAccount` are banned (WAM helpers only); `Connect-MgGraph` uses the Graph CLI app, which has no SP in CP Ops (`AADSTS700016` on 2026-09-08) and could raise a consent prompt that adds a new app; and direct CA writes are banned in favour of the pipeline. Jesse then approved `Connect-AzAccount -UseDeviceAuthentication` (same Azure PowerShell app as WAM). The code was relayed through two agent hops, expired before he used it (`DeviceCodeCredential authentication failed: Verification code expired`), and nothing ran. About an hour of GA was spent with no reads or changes done.
**Correct approach:** Read *Constraints* and *Deploying Conditional Access changes* before briefing this agent. A test CA policy is a `tenant-ca-policies-settings.json` entry plus pipeline 160, even when it's temporary and scoped to one user. When Jesse is remote: (1) a WAM popup can't be completed, so ask him up front how to authenticate, and get his approval for an Az device code in the main session (`AskUserQuestion`), not relayed; (2) issue the code only once he says he's at the device, because codes last about 15 minutes; (3) collect every GA-only read in one sign-in. GA isn't needed for pipeline CA changes at all; the pipeline SP holds `Policy.ReadWrite.ConditionalAccess`.

### 2026-11-04 — Teams scoped directory search reported "already off" while the admin center showed it On
**Attempted:** A read of `GET api.interfaces.records.teams.microsoft.com/Skype.Policy/configurations/TeamsClientConfiguration` (Az PowerShell token) at about 15:08Z returned `AllowScopedPeopleSearchandAccess=false`. On that basis the session told Jesse that scoped search was off and address book policies didn't matter. It also suggested his click might have turned the setting *On*.
**Actual:** Jesse had seen the toggle On in the Teams admin center and turned it Off. A re-read at 15:33Z returned false. The timing isn't confirmed: it's unknown whether the 15:08Z read came before his change, which would make it correct but stale, or after it, which would mean the API returned a stale value. The Purview audit entry for `Set-CsTeamsClientConfiguration` would settle it. Exchange later showed no address book policies in CP Ops, so the error didn't change the diagnosis.
**Correct approach:** Treat a single admin API read as a snapshot, not the standing state. Before saying a setting "was already" X, confirm it in the admin center or the Purview audit. Never guess what a user's click toggled.

### 2026-11-04 — Exchange Online from a Claude Code shell: WAM window handle, blocked Az token, `$T`/`$t` collision
**Attempted:**
1. Read address book policies by calling Exchange's admin REST API (`/adminapi/beta/$T/InvokeCommand`) with an Az PowerShell token for `outlook.office365.com`, holding the tenant in `$T` and the token in `$t`.
2. Then ran `Connect-ExchangeOnline` (ExchangeOnlineManagement 3.10.1).
**Actual:**
- PowerShell variable names are case-insensitive, so `$t` overwrote `$T`. The URL became `/adminapi/beta/<JWT>/…`, which returned 400 "Invalid URL" and echoed part of the token.
- With the variables fixed, the token itself was `scp=blocked exoauthsec`. Exchange refuses the Az PowerShell client outright, so every call got 401.
- `Connect-ExchangeOnline` then failed with "A window handle must be configured" because WAM can't attach to the non-interactive shell.
**Correct approach:**
- Use `Connect-ExchangeOnline -DisableWAM`, which signs in through the browser.
- Never use the Az token for Exchange, and don't propose a new app to get around the block.
- Name variables so they differ by more than case (`$tenantGuid`, `$exoTok`).
- `Get-GlobalAddressList` / `Get-AddressList` need the Address Lists role, which Exchange Admin doesn't include.
- To unhide a B2B guest, use `Set-MailUser -HiddenFromAddressListsEnabled $false`. Exchange is authoritative for it; Graph `showInAddressList` is for verification only.

### 2026-11-04 — the 2026-10-27 logger fix existed only in the toolkit copy
**Attempted:** Dot-sourced `cp-identity-ops/infra/log-entra-changes.ps1` before an approved change, trusting the 2026-10-27 entry below that says the helper "now guards `Export-ModuleMember`".
**Actual:** The fix was only in `cp-ai-toolkit/infra/`. The `cp-identity-ops` copy (last touched in the admin-* rename) still threw "Export-ModuleMember cmdlet can only be called from inside a module". The error wasn't terminating in that run, so logging still worked, but the entry was wrong for that repo.
**Correct approach:** Seeding doesn't sync `infra/` helpers. After fixing a shared helper, copy it to every repo that has one (`diff` the copies first) or add it to the seed manifest. Until then, keep the `Get-Command Log-EntraChange` guard in change scripts.

### 2026-10-28 — ADO `VS403463` "conditional access policy … has failed" was a revoked refresh token, not CA
**Attempted:** From 10-27 18:17Z, git and ADO REST as `jessefrase@cpops.cciauth.com` returned 403 / `VS403463`. The session put it down to a location-based CA policy, because Jesse had just gone remote, and said so.
**Actual:** At 16:28:45Z Jesse's account had revoked its own sessions (directory audit: "Update StsRefreshTokenValidFrom Timestamp", initiated by the user 13 s after an Authenticator approval). ADO kept going on cached access tokens until 18:17:14Z. After that, every non-interactive refresh failed with **50173** (grant revoked): 10 of 10, no 53003. CA policies weren't changed, and the IP was in a trusted named location. A second revocation, at 10-26 13:56Z, had already broken the M365 KB MCP connector the same way.
**Correct approach:** When ADO says `VS403463`, find the Azure DevOps sign-in (app `499b84ac-…`) at the error's exact timestamp before suspecting CA. 50173 means signing in interactively once (browser, then `git credential reject` + fetch). Recreate the PAT only if it still fails. Also check the directory audit for `StsRefreshTokenValidFrom` changes.

### 2026-10-28 — `Connect-AzAccount -AuthScope` fails on this machine's Az.Accounts 2.2.6
**Attempted:** `Get-TenantGraphHeaders` (`infra/connect-tenants-wam.ps1`, line ~96) and `cpops-prime-wam.ps1` when they had to reconnect.
**Actual:** "A parameter cannot be found that matches parameter name 'AuthScope'". Only Az.Accounts 2.2.6 and 2.2.4 are installed, and neither has `-AuthScope`. It worked earlier in the week only because a cached context was still valid.
**Correct approach:** Update Az.Accounts, or add a version guard to the helpers (call without `-AuthScope` on old versions; `Connect-TenantGraphOnly` without it worked). Don't treat a reconnect failure as a permissions problem.

### 2026-10-27 — dot-sourcing `infra/log-entra-changes.ps1` (as documented above) threw and stopped the change run
**Attempted:** Before an approved 9-group removal, loaded the audit helper exactly as *Audit logging* shows: `. "$PSScriptRoot\infra\log-entra-changes.ps1"`, under `pwsh -File`.
**Actual:** The script ended with `Export-ModuleMember`, which only works inside a module: "The Export-ModuleMember cmdlet can only be called from inside a module". Under `pwsh -File` that is terminating, so the run stopped before any Graph call (no harm done, but no change made either).
**Correct approach:** The helper now guards `Export-ModuleMember` so dot-sourcing works (verified in pwsh 7). Run it under **pwsh**, not Windows PowerShell 5.1: the file is UTF-8 without a BOM, so 5.1 fails to parse its `✓ ⚠ ⏳` characters ("Unexpected token 'âš'", line 41). In change scripts, still check `Get-Command Log-EntraChange -ErrorAction SilentlyContinue` after loading and **refuse to make changes if logging isn't available**, so nothing is ever changed without a log entry.

### 2026-10-27 — guest's sign-in rows show its home-tenant UPN, read as a second identity
**Attempted:** User reported having to sign in to CP Ops SharePoint as `alanzimmerman@ccimail.cciauth.com`. His old B2B guest in CP Ops is `alanzimmerman_ccimail.com#EXT#`, so the session treated `@ccimail.cciauth.com` as a possible new guest or third identity.
**Actual:** It was the same disabled guest (`f2e9c76d…`). In the **resource** tenant's sign-in log, `userPrincipalName` on a B2B row is the **home-tenant** UPN, not the `#EXT#` UPN. All 401 attempts failed with **500571** (guest account disabled). The 10-27 SharePoint scan then showed that the new account already had access to the library in question.
**Correct approach:** Filter sign-ins by `userId` (object ID), never by UPN, when guests are involved. Read 500571 on an old guest after a move as "the user or browser is still reaching for the old account". Check the new account's effective access with a SharePoint scan (`@admin-spo`) and the user's browser/session before concluding a grant is missing. Don't infer the cause from sign-in timing.

### 2026-10-27 — Graph query traps hit while reconstructing a guest's group history
**Attempted / Actual / Correct approach:**
- `auditLogs/directoryAudits?$filter=activityDisplayName ne '…'` → 400 "NotEqual logical operator is not supported". Use `eq` or filter client-side.
- For **Remove member from group**, the group is not in a `targetResources` entry of type Group. It's in `modifiedProperties` `Group.DisplayName` / `Group.ObjectID` (`oldValue`). Read it from there to rebuild a pre-cleanup membership list.
- `GET /sites/{host}:/{path}` returns the site, but `/sites/{id}/drives` returns an **empty list (not 403)** when the token has no `Sites.*` scope (the WAM token has `Directory.AccessAsUser.All`, `Group.ReadWrite.All`, no `Sites.*`). Empty means "can't see", not "no libraries". Hand library permissions to `@admin-spo`. Don't add an app for the scope.

### 2026-10-19 — disabled a migrated user's old guest after an Entra-only group copy
**Attempted:** Moved Alan Zimmerman from B2B guest `f2e9c76d…` to `alanzimmerman@cpops.cciauth.com` (`dcc0d07a…`). Copied every direct group, Team and licence group, then disabled the guest. The `@admin-spo` scan of the guest's grants refused 111 of 178 sites and was killed before writing findings, and the disable went ahead anyway.
**Actual:** The full `@admin-spo` scan on 10-27 found 45 SharePoint grants on the three moved users' old accounts. On 21 of them the new account had no equivalent: SharePoint-only groups (e.g. Alan's "MPR Design Team Role"), sharing links, direct file grants and subsite grants, plus a private-channel site. Alan's 10-26 report about "CPUS  Monthly Quality Reports" was **not** one of those gaps: the new account had held Contribute through the same groups since 10-19. Why the new account failed there is unexplained; the likely cause is the browser offering the old account or a cached session. The Owners (Full Control) add made by hand on 10-26 was broader than the access he had before. The cleanup was also left half done: the old account sat in 9 non-dynamic groups, still holding a Power BI Pro seat, until 10-27.
**Correct approach:** Group parity is necessary but not sufficient. Before disabling an old account: (1) a **complete** `@admin-spo` grant scan of the old identity, where refused sites block the disable and are never skipped; (2) the user opens their main libraries with the new account; (3) after the disable, remove the old account from every non-dynamic group and confirm only dynamic groups remain. Full gate: KB `onelogin-move-it-checklist.md` 4.0, steps 12–25, and `cp-one-login/docs/current/onboarding.md`.

### 2026-10-24 — account comparison called two accounts "identical" while one lacked 68 groups
**Attempted:** Before retiring a B2B guest (`…_ccimail.com#EXT#`) in favour of its federated replacement (`@cpops.cciauth.com`, OneLogin), compared the two with `cp-one-login/infra/cpops-b2b-vs-fed-compare.ps1`. It reported an Entra gap of 0.
**Actual:** The script reads `/memberOf` (direct only), puts dynamic groups in a "skipped" footer instead of the gap, and compares only direct `appRoleAssignments`. A transitive comparison (Simeon Ben-Eliezer, 2026-10-24) found 70 groups on the guest only: 68 reached through the dynamic group **CCIMail Users** (`userPrincipalName -contains "ccimail.com"`), which is nested in ~66 SharePoint "… Site Visitors" groups and a Power BI RLS group. The federated UPN did not match the rule, so after cutover the user would silently lose read access to most CP Ops SharePoint sites. Same class of miss: `PBI-Admin Accounts` (`-startsWith "admin"`) dropping on a UPN rename.
**Correct approach:** Whenever comparing two identities, or predicting the effect of a UPN/attribute change, compare **effective** access, not direct assignments:
1. Use `/transitiveMemberOf` for both accounts and diff the sets; for each gap item record *how* it is reached (direct vs nested, and through which parent).
2. For every dynamic group in either set, evaluate its `membershipRule` against the *target* account's attributes (UPN, mail, department, …) — a dynamic gap is a real gap, never a "skipped" footnote. Also check dynamic groups that are **nested** into others: losing one dynamic group can remove dozens of downstream memberships.
3. Compare app roles **including group-inherited** ones (`/groups/{id}/appRoleAssignments` for every transitive group), licenses **with source** (`licenseAssignmentStates.assignedByGroup`), `ownedObjects`, and directory roles / PIM eligibility.
4. State what Graph cannot see: SharePoint unique permissions and sharing links granted directly to a user, Power BI workspace access, Power Apps sharing, Exchange delegation. Hand those to `@admin-spo` / `@admin-powerplatform` rather than calling the accounts identical.
5. Before any UPN change, list dynamic groups whose rule references `userPrincipalName` (`groups?$filter=groupTypes/any(g:g eq 'DynamicMembership')`) and check which the new UPN stops or starts matching.

### 2026-10-24 — empty `appliedConditionalAccessPolicies` on sign-ins read as "no CA policy fired"
**Attempted:** Diagnosing why CP Ops demanded its own MFA from OneLogin-federated users (`@cpops.cciauth.com`). Pulled beta `auditLogs/signIns` via the WAM helper and grouped by `appliedConditionalAccessPolicies`; reported to the user that "none of the 18 sign-ins name a CA policy", implying something other than CA required MFA.
**Actual:** The list was empty on every row, and stayed empty after a `-ForceReconnect` with Global Administrator verified in `wids`. Graph returns `appliedConditionalAccessPolicies` empty (not `notApplied`) when the token lacks `Policy.Read.All` / `Policy.Read.ConditionalAccess` — the same Az PowerShell consent gap as the 2026-09-08 entry. On the same rows `authenticationRequirementPolicies` said `multiConditionalAccess: Conditional Access`, i.e. CA *was* the cause. `beta/users/{id}/authentication/requirements` (perUserMfaState) also 403s for the same reason; `beta/reports/authenticationMethods/userRegistrationDetails/{id}` does work and shows registered MFA methods.
**Correct approach:** Treat an empty `appliedConditionalAccessPolicies` as "can't see", never as "none applied". Use `authenticationRequirementPolicies` for *why* MFA was required, `userRegistrationDetails` for *what* the user can satisfy it with, and the Entra admin center sign-in log (by correlation ID → Conditional Access tab) for *which* policy. Role elevation does not fix this; only consent for `Policy.Read.All` does. The Azure CLI token (`az account get-access-token --resource-type ms-graph`, app `04b07795-…`) was tried the same day and also returns the list empty — don't fall back to it. Don't "fix" it with consent either: Microsoft Azure PowerShell (`1950a258-…`) has **no service principal** in CP Ops, so there is no grant to extend, and creating one could change every Az PowerShell token in the tenant. Decision (Jesse, 2026-10-24): no new SPs or app registrations for this — ask the user to activate GA when needed, and use `authenticationRequirementPolicies` + correlation IDs in the portal for the policy name.

### 2026-09-30 — `crossTenantAccessType` on v1.0 `signIn` comes back actual `null`, not the string `"none"` a prior doc's table implied

**Attempted:** Sizing the OneDrive-sync alias-UPN 50126 bug tenant-wide across CP Ops
(`cp-conditional-access/docs/reference/onedrive-sync-ext-alias-50126-investigation-2026-09-28.md`
sizing follow-up, 14-day tenant-wide sweep). The 09-28 doc's own comparison table listed the
failing record's `crossTenantAccessType` as literal `none`, so the classification filter was
written as `($_.crossTenantAccessType -eq 'none')` alongside the other three signature conditions
(alias-shaped UPN, `errorCode 50126`, `homeTenantId` = CP Ops itself).

**Actual:** The full-signature filter matched **zero** records against a 307-event, 14-day
tenant-wide dataset that visibly contained the exact alias-shaped UPNs and `50126` codes expected
(confirmed by loosening the filter one clause at a time). Direct inspection of one matching raw
JSON record (`$sample.crossTenantAccessType | ConvertTo-Json`) showed the field is actual
PowerShell/JSON `null`, not the string `"none"` — `-eq 'none'` against `$null` is `$false` in
PowerShell, so the clause silently zeroed out every real match instead of erroring. The 09-28
doc's table wasn't wrong about the underlying sign-in event, just using "none" as a human-readable
label for a null field — a label that looks exactly like a value worth `-eq`-testing against.

**Correct approach:** Test `crossTenantAccessType` (and likely other optional/absent-when-N/A
`signIn` fields) for null/falsy directly —
`(-not $_.crossTenantAccessType) -or ($_.crossTenantAccessType -eq 'none')` — rather than
trusting a prior doc's display rendering of a field as its literal wire value. When a signature
filter across multiple ANDed conditions returns suspiciously exactly zero on a dataset you can see
contains matches by eye, drop each condition one at a time before concluding "no matches" — that
isolation step is what caught this, in the same session, before it reached the final report. Same
genre of trap as the entry directly below (Graph fields that don't behave the way
documentation/tooling implies) — worth the same suspicion going forward, not just this one field.

### 2026-09-25 — `mfaDetail`/`authenticationDetails` don't exist on v1.0 `signIn`; combining `$select` with them on beta also fails

**Attempted:** Tenant-wide 30-day sign-in failure baseline for CP Ops
(`cp-identity-ops/docs/session-notes/2026-09-25-cpops-signin-log-baseline.md`). Needed
`mfaDetail` and `authenticationDetails` on `50074`/`50076` events to check for the missing-MFA-claim
pattern from the 2026-09-02 precedent. Called
`GET /v1.0/auditLogs/signIns?$select=...,mfaDetail,authenticationRequirement,authenticationDetails,...`.

**Actual:** `400 BadRequest`: `"Parsing OData Select and Expand failed: Could not find a
property named 'mfaDetail' on type 'microsoft.graph.signIn'."` — same for
`authenticationRequirement`, `authenticationRequirementPolicies`, and `authenticationDetails`
individually. These properties are not exposed on `/v1.0/auditLogs/signIns` at all, `$select` or
otherwise. Switching to `/beta/auditLogs/signIns` with the same `$select` list produced a
*different* failure: `400 UnknownError: "Unsupported Query."` — beta has the fields (confirmed:
dropping `$select` entirely and letting the full object come back shows `mfaDetail`,
`authenticationRequirement`, and `authenticationDetails` populated), but combining beta's
`$select` with these specific properties is itself unsupported.

**Correct approach:** For `mfaDetail`/`authenticationDetails`/`authenticationRequirement`/
`authenticationRequirementPolicies` on sign-in logs: query `/beta/auditLogs/signIns` with
**no `$select` at all**, then project down to the fields you want client-side after the response
comes back (`$resp.value | Select-Object ...` in PowerShell). Do not try v1.0 for these fields —
it 400s outright, not silently omits them. Do not try `$select` on beta for them either — same
400, different message. This also matters for response size/cost: without `$select`, beta
returns the full sign-in object (device details, location, risk fields, etc.) for every record,
so trim client-side rather than over-fetching repeatedly.

### 2026-09-21 — Partial tenant GUID from a prior session pointed at the wrong XTAP partner entry

**Attempted:** Re-verifying XTAP inbound trust for Barrett Distribution
(`barrettdistribution.com`, CP Ops B2B guests) as part of a multi-step MFA
investigation. The 2026-09-09 session's notes recorded Barrett's home tenant
GUID only as a partial `3e487f1d-...` and, based on
`GET /policies/crossTenantAccessPolicy/partners/{that partial-looking match}`,
concluded `inboundTrust.isMfaAccepted: true` was "correctly configured on CP's
side" for Barrett.

**Actual:** The partial GUID matched a real partner entry
(`3e487f1d-d36e-4c0c-b798-56317fd8db52`), but that entry belongs to **Redbridge
Services, LLC** (`redbridgeservicesllc.com`), confirmed via
`POST/GET https://graph.microsoft.com/v1.0/tenantRelationships/findTenantInformationByTenantId(tenantId='...')`
— an anonymous-allowed Graph endpoint that resolves a tenant GUID to its
`displayName`/`defaultDomainName`. It has nothing to do with Barrett. Barrett's
actual home tenant GUID, confirmed independently from the `homeTenantId` field
on live Barrett sign-in events (`/auditLogs/signIns`), is
`a87b3fce-f6ac-4dba-8048-60d4c8cef180` ("Barrett Distribution Centers"). CP Ops
has **no** partner-specific XTAP entry for that GUID at all (`GET
/policies/crossTenantAccessPolicy/partners/{id}` returns 404
`Directory_ObjectNotFound`), so Barrett is actually governed by the **default**
cross-tenant access policy, whose `inboundTrust.isMfaAccepted` is `false` —
the opposite of what the 2026-09-09 note concluded. This reversed the causal
direction of the whole investigation: CP Ops isn't just "not observed" honoring
Barrett's MFA, it structurally can't, independent of whatever Barrett does on
its own tenant.

**Correct approach:** Never record or act on a truncated/partial tenant GUID.
When a session captures a cross-tenant GUID for later reference, record the
full GUID and its resolved `displayName` in the same breath — one call to
`findTenantInformationByTenantId` costs nothing and would have caught this
immediately. When re-verifying XTAP trust for a specific partner in a later
session, don't trust a prior session's GUID-to-partner-entry match at face
value: re-resolve the GUID's identity independently (from live sign-in
`homeTenantId`, not from a note) before reading `inboundTrust`, especially when
the partner list only has a couple of entries and it would be easy to grab the
wrong one. Also: `GET /policies/crossTenantAccessPolicy/partners/{tenantId}`
returning 404 is itself a meaningful, reportable finding ("no partner override
exists, this tenant falls to `/default`") — don't treat a 404 as "nothing to
report" and move on without pulling `/default` for comparison.

### 2026-09-08 — WAM Graph token can't read `authentication/methods`, even with GA/Privileged Auth Admin active

**Attempted:** Diagnosing a B2B guest MFA failure (`mtorijano@barrettdistribution.com`,
CP Ops) required `GET /users/{id}/authentication/methods` via the documented WAM helper
(`Get-TenantGraphHeaders`). Retried after PIM-activating Global Administrator, then again
after Privileged Authentication Administrator, including a fresh `-ForceReconnect` each time.

**Actual:** Every attempt returned `403 accessDenied` ("Request Authorization failed")
regardless of directory role. The role was never the blocker — the "Microsoft Azure
PowerShell" first-party client's token is requested with `.default`, which only returns
permissions **already consented for that app in the tenant**. `UserAuthenticationMethod.Read.All`
had never been consented for it, so no amount of role elevation changes the token's scope.

Worked around it with `Connect-MgGraph` (against this agent's own DO NOT, with explicit user
sign-off to bypass it for this one check): WAM sign-in failed in this embedded/agent terminal
with *"A window handle must be configured"* — no parent window for MSAL WAM outside a real
console (same class of issue as `admin-spo.agent.md`'s 2026-09-02 entry). Device-code fallback
against the Microsoft Graph Command Line Tools app (`14d82eec-204b-4c2f-8e3e-24e0d70a3c8c`)
failed outright with `AADSTS700016` — that app has no service principal provisioned in the CP
Operations tenant at all. A further attempt using the already-provisioned Microsoft Azure
PowerShell client (`1950a258-227b-4e31-a9cf-717495945fc2`) with an explicit incremental scope
request was in progress when a direct portal check made it moot.

**Correct approach:** For `/authentication/methods` (or any Graph endpoint gated by a delegated
permission not already consented to the Az PowerShell SP in this tenant), don't loop on PIM
role activation — it will not fix a consent gap. Check the Entra admin center portal directly
instead (**Users → *user* → Authentication methods**). It uses the portal's own first-party
app, already consented, and answers in the time it takes to click through — versus the
token/consent rabbit hole above. If scripted access to this endpoint becomes a recurring need,
the real fix is provisioning the Microsoft Graph Command Line Tools app (or granting
`UserAuthenticationMethod.Read.All` delegated admin consent to the existing Az PowerShell SP)
once, deliberately, via the portal — not improvised per-session.

**Confirmed 2026-09-08's theory, 2026-09-30:** Re-tested against two more users (Kevin Boller
Jr, Hans Voll — CP Ops) under a freshly-forced WAM reconnect (`-ForceReconnect`, not a reused
cached context) with **Global Administrator PIM-activated and verified present**: decoded the
resulting token's `wids` claim before querying anything, confirmed
`62e90394-69f5-4237-9190-012177145e10` (GA) was actually in it — ruling out the "stale cached
token didn't pick up the role" failure mode as an alternative explanation. Both users still
returned identical `403 accessDenied: "Request Authorization failed."` Decoded the same token's
`scp` claim: `Application.ReadWrite.All AppRoleAssignment.ReadWrite.All AuditLog.Read.All
DelegatedPermissionGrant.ReadWrite.All Directory.AccessAsUser.All email Group.ReadWrite.All
openid profile User.Read.All` — no `UserAuthenticationMethod.Read.All`, exactly as the theory
predicted. **This is now confirmed, not just diagnosed by elimination: it is purely a consent
gap on the Az PowerShell client, and directory role has zero effect on it, at any level up to
and including Global Administrator.** Stop re-testing this with more role elevation. The same
session found `identityProtection/riskyUsers` and `riskDetections` are blocked by the identical
mechanism (`IdentityRiskyUser.Read.All` / `IdentityRiskEvent.Read.All` also absent from `scp`,
same 403-regardless-of-GA behavior) — treat any Graph 403 that persists after a *verified*
(decoded, not assumed) GA token as this same class of problem before spending more time on role
activation. See `cp-conditional-access/docs/reference/pim-ga-diagnostic-pull-2026-09-30.md` for
the full session.

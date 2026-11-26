# admin-powerplatform REST/CLI reference

Auth primers: `infra/powerplatform-prime.ps1` (canvas admin module) and
`infra/connect-powerplatform-wam.ps1` (BAP + Dataverse WAM). Agent:
`.github/agents/admin-powerplatform.agent.md`.

**Verified against CPOP-PRD on 2026-09-25** for Dataverse token, `appmodules`,
`teams`/`teamtype`, `roles`, and `roleprivilegescollection`. Log new traps in the
agent Known mistakes section.

```powershell
. .\infra\connect-powerplatform-wam.ps1
$tenantCpOps = '2e1c62fc-1595-4d12-85d1-8577714f8d1d'
. .\infra\Get-OperatorAccount.ps1
$upn = Get-OperatorAccount -Tenant cpops   # from config/operator.local.json (git-ignored)
$envUrl = 'https://org5cba6510.crm.dynamics.com'   # CPOP-PRD
$dv = Get-TenantDataverseHeaders -TenantId $tenantCpOps -EnvironmentUrl $envUrl -ExpectedAccount $upn
```

## Canvas app sharing

```powershell
. .\infra\powerplatform-prime.ps1 -ExpectedAccount $upn
$EnvironmentId = '70b71c9e-66c2-4c4d-8668-1e5a8f3181f9'
Get-AdminPowerApp -EnvironmentName $EnvironmentId |
  Select-Object DisplayName, AppName, Owner, CreatedTime
Get-AdminPowerAppRoleAssignment -EnvironmentName $EnvironmentId -AppName $appId |
  Select-Object RoleType, PrincipalType, PrincipalDisplayName, PrincipalObjectId
```

## Model-driven apps (appmodules)

Many model-driven apps (e.g. Purchasing Hours) do **not** appear in `Get-AdminPowerApp`.

```powershell
Invoke-RestMethod -Uri "$envUrl/api/data/v9.2/appmodules?`$select=name,uniquename,appmoduleid,appmoduleidunique" -Headers $dv

# Components: filter by appmoduleidunique, NOT appmoduleid
$uid = '<appmoduleidunique guid>'
Invoke-RestMethod -Uri "$envUrl/api/data/v9.2/appmodulecomponents?`$filter=_appmoduleidunique_value eq $uid" -Headers $dv
# componenttype 1 = Entity (objectid = MetadataId)

# Roles associated to the app module
Invoke-RestMethod -Uri "$envUrl/api/data/v9.2/appmodules(<appmoduleid>)?`$expand=appmoduleroles_association(`$select=name,roleid)" -Headers $dv
```

## Security roles and privileges

```powershell
Invoke-RestMethod -Uri "$envUrl/api/data/v9.2/roles?`$select=name,roleid,ismanaged&`$expand=businessunitid(`$select=name)" -Headers $dv

# Privilege rows for a role (depth: 1=User, 2=BU, 4=ParentChild, 8=Org)
$roleId = '<roleid guid>'
Invoke-RestMethod -Uri "$envUrl/api/data/v9.2/roleprivilegescollection?`$filter=roleid eq $roleId&`$select=privilegeid,privilegedepthmask" -Headers $dv
# Resolve names:
Invoke-RestMethod -Uri "$envUrl/api/data/v9.2/privileges?`$select=name,privilegeid" -Headers $dv
```

## Teams (1:1:1)

Live CPOP-PRD codes: **0** Owner, **1** Access, **2** AAD Security Group, **3** AAD Office Group.

```powershell
Invoke-RestMethod -Uri "$envUrl/api/data/v9.2/teams?`$select=name,teamtype,azureactivedirectoryobjectid&`$filter=teamtype eq 2&`$expand=teamroles_association(`$select=name,roleid)" -Headers $dv
```

Flag teams whose `teamroles_association` includes **Basic User** alongside an app-scoped custom role — that is the cross-app spill pattern.

## Direct user role assignments

```powershell
Invoke-RestMethod -Uri "$envUrl/api/data/v9.2/systemusers?`$select=fullname,domainname,isdisabled,applicationid&`$filter=isdisabled eq false&`$expand=systemuserroles_association(`$select=name)" -Headers $dv
```

## BAP environment inventory / DLP / capacity

```powershell
$bap = Get-TenantBapHeaders -TenantId $tenantCpOps -ExpectedAccount $upn
Invoke-RestMethod -Uri 'https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/scopes/admin/environments?api-version=2022-05-01' -Headers $bap
Invoke-RestMethod -Uri 'https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/scopes/admin/dlpPolicies?api-version=2022-05-01' -Headers $bap
```

Or `pac auth list` / `pac admin list` when the active profile is `@cpops.cciauth.com`.

## Remediation (approval required)

**Remove Basic User from an app team (pilot pattern):**

1. Confirm custom role has the app table privileges (and canary-proven shell reads).
2. Disassociate Basic User from that team only (`DELETE .../teamroles_association/$ref`).
3. Canary open the app; add only the failing privilege to the custom role if needed.
4. Negative-test that other apps' tables are no longer readable via that group.

**Create Entra SG team + assign app role (when 1:1:1 does not exist yet):**

```powershell
# teamtype 2 = AAD Security Group (verified CPOP-PRD)
$teamBody = @{
  name = 'CPUS-AppX'
  teamtype = 2
  azureactivedirectoryobjectid = '<entra group object id>'
  'businessunitid@odata.bind' = "/businessunits($defaultBuId)"
} | ConvertTo-Json
# POST /teams then POST /teams(id)/teamroles_association/$ref → roles(appScopedRoleId)
```

Do **not** clone Basic User when creating the app-scoped role.

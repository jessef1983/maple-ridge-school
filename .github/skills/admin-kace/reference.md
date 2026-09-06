# KACE SMA API reference (Ops cheat sheet)

Canonical vendor docs: [SMA 15.0 API Reference Guide](https://support.quest.com/technical-documents/kace-systems-management-appliance/15.0/api-reference-guide)  
PDF: https://support-public.cfm.quest.com/80844_KACE_SMA_15.0_API_Reference_en-US.pdf  
PowerShell login KB: https://support.quest.com/kb/4378612/how-to-api-connection-via-powershell

CCI appliance: **`https://kbox.ccistack.com`** (Admin UI also reachable historically as kbox.ccimail.com — prefer ccistack in config)

---

## Auth for agents (cp-identity-ops)

| Item | Detail |
|------|--------|
| Mechanism | Session cookies after login — **no API key** |
| How to login | Visible `Login-KaceInteractive.ps1` → Windows Get-Credential (**never chat passwords**) |
| Helper | `scripts/kace/Connect-Kace.ps1` |
| Disk cache | `%LOCALAPPDATA%\cp-identity-ops\kace\session.json` (+ `ready.flag`) |
| Password on disk | **Never** (automation: KV `cp-identity-ops-kv` / `svc-kbox-cp` → env only) |
| AMS vs Admin UI | AMS cookies → `/api/...`; Admin UI cookies → `/adminui/*.php` form posts. Both saved when `-IncludeAdminUi` |
| Ops role | **CCI-IdentityOps** (id **23**) — Users READ; Scripting per Admin UI; **device scope label CCI Identity Ops Pilot (4122: V1066, P36721)** — Run Now / targeting limited to that label |
| Automation user | LDAP **`svc-kbox-cp`** (bare name; not `COMMUNITY\…`) |

### LDAP (svc-kbox-cp) quick reference

| Item | Value |
|------|--------|
| Auth Settings | `kbox-svc-cp` → role CCI-IdentityOps · `192.168.2.100:636` |
| Base DN | `DC=community,DC=int` |
| Filter | `(&(samaccountname=KBOX_USER)(memberOf=CN=nsKboxLdapAuth,OU=Restricted,OU=CCGroupsSystemSecurity,DC=community,DC=int))` |
| Token | **`KBOX_USER`** (not `KBOX_USER_NAME`) |
| AD group | `nsKboxLdapAuth` |
| Import mapping | objectguid / samaccountname / cn / **mail** — re-import after Auth changes |
| Pages | `/adminui/settings_authentication.php` · Settings → Users → User Import |

### Run Now / pilot scope

Queue scripts only on machines in label **4122** (V1066, P36721) unless Jesse expands the label. Do not set role “Scope all machines”.

---

## Headers (every `/api` and AMS request)

| Header | Value |
|--------|--------|
| `Accept` | `application/json` (or XML) |
| `Content-Type` | `application/json` (POST/PUT) |
| `x-kace-api-version` | `5` |

Since SMA **12.1**: do **not** require `x-kace-csrf-token` on the **JSON API**. Admin UI PHP forms still use page CSRF tokens.

---

## Account Management Service (AMS)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ams/shared/api/security/login` | Login (JSON API session) |
| POST | `/ams/shared/api/security/verify_2fa` | MFA code after login |
| GET | `/ams/shared/api/security/logout` | Logout |
| POST | `/ams/shared/api/security/organization/switch?organizationId=` | Switch org |
| POST | `/ams/shared/api/security/organization/{id}/switchto` | Switch org by id |

### Login body

```json
{
  "userName": "admin",
  "password": "…",
  "organizationName": "Default"
}
```

### Admin UI login (separate cookie jar)

`GET /adminui/` → CSRF → `POST /adminui/check_login.php` with `LOGIN_NAME`, `LOGIN_PASSWORD`, `ORGANIZATION`, `CSRF_TOKEN`, `save=Login`.

Required for role/user **form** administration. Not interchangeable with AMS.

### Incomplete MFA → HTTP 401

```json
{ "errorCode": -1, "errorDescription": "User not fully authenticated." }
```

---

## Capabilities matrix (CCI Ops)

| Task | Via REST `/api` | Via Admin UI forms | Notes |
|------|-----------------|--------------------|--------|
| List/filter machines | Yes | Yes | Prefer API |
| Force inventory | Yes | Yes | Approval for mass ops |
| Managed install retarget | Yes (PUT) | Yes | Approval required |
| Scripts create/run | Yes (role WRITE) | Yes | Run Now only against label **4122** pilot hosts |
| Software title create/update | Yes if role WRITE | Yes | CCI-IdentityOps: software HIDE — use Admin UI |
| Users GET / permissions | Yes | Yes | |
| Users DELETE / admin writes | **No / 405** | Fragile / prefer human | Do not automate user delete |
| Roles create/edit | **No** | **Yes only** | `user_role.php` |

---

## Query parameters (most list GETs)

### Filtering

`filtering=field op value` — comma-separated AND. Related entity: `software.name eq Word`.

Operators: `lt` `le` `gt` `ge` `eq` `ne`/`neq` `co` `nc`/`nco` `st`/`nst` `en`/`end`/`nen` `in`/`nin` (set values `;`-separated).

Examples:

```
/api/inventory/machines?filtering=name eq Workstation123
/api/inventory/machines?filtering=name co V1L,id gt 1000
/api/inventory/machines?filtering=id in 100;101;108
/api/inventory/machines?filtering=software.name eq zoo
```

### Paging / sorting / shaping / counts

```
paging=limit 100
paging=offset 101 limit 100
paging=limit ALL
sorting=name asc
shaping=machine all,software limited
use_count=false
use_count_only=true
```

---

## Inventory (`/api/inventory`)

| Method | Path |
|--------|------|
| GET/POST | `/api/inventory/machines/` |
| GET/PUT | `/api/inventory/machines/{id}/` |
| GET | `/api/inventory/machines/{id}/custom_inventory/` |
| POST | `/api/inventory/machines/{id}/force/` |
| GET | `/api/inventory/softwares/` |
| GET | `/api/inventory/operating_systems/` |
| GET | `/api/inventory/processes/` |
| GET | `/api/inventory/services/` |
| GET | `/api/inventory/nodes/` |
| GET | `/api/inventory/startup_programs/` |

---

## Managed Install (`/api/managed_install`)

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/managed_install/managed_installs` | List |
| GET | `/api/managed_install/managed_installs/{id}` | Detail |
| GET | `/api/managed_install/managed_installs/{id}/machines` | Targeted devices |
| PUT | `/api/managed_install/managed_installs/{id}/` | Add or remove targets |
| GET | `/api/managed_install/managed_installs/{id}/file` | Associated file |

Some docs mention BasePath `/api/mi` — prefer `/api/managed_install/...`; validate if 404.

---

## Service Desk (`/api/service_desk`)

| Method | Path |
|--------|------|
| GET | `/api/service_desk/queues/` |
| GET/POST | `/api/service_desk/tickets` |
| GET/PUT/DELETE | `/api/service_desk/tickets/{id}` |
| POST | `/api/service_desk/tickets/{id}/approve` |

---

## Users (`/api/users` …)

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/users/me/` | Current session user |
| GET | `/api/users/users` | List (filter/page/shape) |
| GET | `/api/users/users/{id}` | Detail |
| GET | `/api/users/{id}/permissions/` | Effective permissions |
| PUT/DELETE users | — | Often **405** on this appliance — use Admin UI manually |

---

## PowerShell (Ops helpers)

```powershell
. 'C:\cp-devops\cp-identity-ops\scripts\kace\Connect-Kace.ps1'
# After Login-KaceInteractive.ps1 (or Connect-KaceSession -IncludeAdminUi):
Restore-KaceSessionState
Invoke-KaceApi -Method Get -Path '/api/inventory/machines' -Query @{ paging = 'limit 25' }
Disconnect-KaceSession   # when done
```

Raw Quest KB pattern still works, but prefer helpers so cookies persist correctly.

---

## Python pattern (for `src/kace/client.py`)

```python
import requests

session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-kace-api-version": "5",
})
r = session.post(
    f"{base_url}/ams/shared/api/security/login",
    json={"userName": user, "password": password, "organizationName": org},
    timeout=30,
)
r.raise_for_status()
machines = session.get(
    f"{base_url}/api/inventory/machines",
    params={"paging": "limit 25"},
    timeout=60,
).json()
```

Do **not** model auth as a static `api_key` — use session cookies from login. Agent UX should collect those credentials via a visible desktop prompt, not chat.

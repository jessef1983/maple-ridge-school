# Installing Claude Desktop (Cowork) for all users

> Canonical Ops reference for CP. Adapted from Clemens’ deployment guide.
> KACE packaging: see `@admin-kace` playbooks (enterprise MSI Managed Install for
> Claude Desktop; Task Chain for Cowork MSIX all-users provision).

A guide for deploying the Claude Desktop **Cowork** build so that standard
(non-administrator) users can run it, without granting anyone standing local
admin rights.

---

## Why an all-users install is needed

Claude "Cowork" is **not** a runtime-permissions problem — it is a *packaged
service* problem.

- The Cowork-capable build is distributed as an **MSIX** package (publisher
  `Anthropic, PBC`), not the plain per-user Squirrel/Electron installer. The
  per-user installer does not include Cowork.
- The MSIX declares the `packagedServices` and `localSystemServices`
  capabilities and registers a Windows service that runs as **LocalSystem**:
  - Service name: `CoworkVMService`
  - Start mode: `Auto`, runs as `LocalSystem`
  - Executable: `...\WindowsApps\Claude_<version>_x64__<hash>\app\resources\cowork-svc.exe`
- That service drives the Windows **Host Compute Service** (`vmcompute`) to run
  Cowork's agent work inside an isolated VM/sandbox (the same virtualization
  backend used by WSL2 and Windows Sandbox).

Consequences:

| Action | Admin required? | Why |
|---|---|---|
| **Running** Cowork day-to-day | No | The SYSTEM service is already registered; the UI just talks to it. |
| **Installing / registering** the MSIX | Yes, one time | Registering a `LocalSystem` service is a machine-level operation. |

Because MSIX package registration is **per user**, installing under one
person's profile makes the app launch only for that profile. Provisioning the
package **for all users** registers it (and its service) machine-wide, so every
current and future profile — including non-admins — can launch it without
elevation.

---

## Prerequisites (one-time, administrator)

### 1. Virtualization platform enabled

Cowork needs the Host Compute Service. Verify, and enable if missing (a reboot
is required after enabling):

```powershell
# Check
Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform |
  Select-Object FeatureName, State
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-Hypervisor |
  Select-Object FeatureName, State

# Enable if needed (reboot afterwards)
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart
```

> If hardware/nested virtualization is disabled in BIOS or by platform policy
> (common on some VDI images), Cowork's VM will not start even with a perfect
> install. Confirm this first.

### 2. Signing certificate trust

Anthropic signs the MSIX with a publicly-trusted EV code-signing certificate,
so the chain is normally already trusted and **no manual import is needed**.
Confirm before assuming a certificate problem:

```powershell
Get-AuthenticodeSignature "<path>\Claude.msix" |
  Select-Object Status, SignerCertificate
```

Only if `Status` is not `Valid`/trusted, import the cert (one-time,
administrator):

```powershell
$cert = (Get-AuthenticodeSignature "<path>\Claude.msix").SignerCertificate
Export-Certificate -Cert $cert -FilePath "$env:TEMP\claude.cer" | Out-Null
Import-Certificate -FilePath "$env:TEMP\claude.cer" `
  -CertStoreLocation Cert:\LocalMachine\TrustedPeople
```

### 3. Sideloading allowed

MSIX sideloading is enabled by default on modern Windows. If a Group Policy
disabled it, re-allow via:
`Computer Configuration > Administrative Templates > Windows Components >
App Package Deployment > Allow all trusted apps to install`.

---

## Install for all users (one-time, administrator)

Target the elevation at an **elevated PowerShell session** — not at the `.msix`
file itself. (A bare `.msix` has no elevatable action, which is why "elevate"
options on the file are often greyed out.)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Provision machine-wide: every existing and future profile auto-registers at logon.
Add-AppxProvisionedPackage -Online `
  -PackagePath "<path>\Claude.msix" `
  -SkipLicense
```

Notes:

- Use `-PackagePath <file>.msixbundle` if the download is a bundle. Add
  `-DependencyPackagePath` for any framework dependencies (this build reports
  none, so typically not required).
- `Add-AppxProvisionedPackage` provisions the package and registers the SYSTEM
  service at machine scope. This is the step that must be elevated.
- If a user is already logged in and does not pick it up, register it for that
  user (this per-user step does **not** need admin):

  ```powershell
  Add-AppxPackage -RegisterByFamilyName -MainPackage Claude_<hash>
  ```

---

## Verify

```powershell
# 1. Package registered for the current (non-admin) user
Get-AppxPackage *claude* |
  Select-Object Name, Version, PackageFullName, SignatureKind, Status
# 2. Cowork service present, Auto, Running, as LocalSystem
Get-CimInstance Win32_Service |
  Where-Object { $_.PathName -like '*Claude*' } |
  Select-Object Name, StartMode, State, StartName, PathName

# 3. Host Compute Service available/running
Get-Service vmcompute | Select-Object Name, Status, StartType

# 4. Provisioned machine-wide (administrator)
Get-AppxProvisionedPackage -Online |
  Where-Object { $_.DisplayName -like '*Claude*' } |
  Select-Object DisplayName, Version
```

**Pass criteria:**

- Package `Status = Ok` for the target user.
- `CoworkVMService` is `Running` and runs as `LocalSystem`.
- `vmcompute` service is present.

Then have a standard (non-admin) user log in as themselves and launch Claude
Desktop — Cowork should be available with no elevation prompt.

---

## Notes

- **What is being approved from a security standpoint:** Cowork installs a
  background service (`CoworkVMService`) that runs as **LocalSystem** and
  manages a Host Compute Service sandbox VM. This is normal for this class of
  tool (Docker Desktop, WSL, and Windows Sandbox all register comparable SYSTEM
  services), but the SYSTEM service — not the user session — is the component
  to evaluate and approve. The Claude UI itself runs in the ordinary,
  unelevated user context.
- **Standing local admin is not required** for end users. A one-time,
  admin-assisted, all-users install provides Cowork permanently to standard
  users. The missing piece in a failed setup is usually the per-user MSIX
  registration, not the user's daily privileges.
- **Entitlement check:** Cowork availability can be gated by the Claude account
  plan/tier, independent of the install. If Cowork is still missing after a
  verified all-users install, confirm the account tier includes it before
  further troubleshooting the deployment.

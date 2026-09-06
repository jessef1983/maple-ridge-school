# Claude Cowork — KACE build kit

Offline/online KScript payloads for the **Claude Desktop (Cowork)** Task Chain on kbox (`kbox.ccimail.com` / `kbox.ccistack.com`).

| Order | File | Role |
|------:|------|------|
| 1 | `01-Prereq-EnableVMP.ps1` | Check/enable VirtualMachinePlatform; exit **3010** if reboot required |
| 2 | `02-ProvisionMsix.ps1` | Elevated `Add-AppxProvisionedPackage`; attach **Claude.msix** as script dependency |
| 3 | `03-Verify.ps1` | Assert `CoworkVMService`, `vmcompute`, provisioned package |
| 4 | `04-DisableAutoUpdates.ps1` | Optional: `HKLM:\SOFTWARE\Policies\Claude\disableAutoUpdates=1` |

Canonical guide: [`docs/claude-cowork-all-users-install.md`](../../../docs/claude-cowork-all-users-install.md).

## Naming

KACE Script display names use **`{id} - Claude Cowork NN …`** after create (easy CLI/Admin UI find). Invoke with:

```powershell
pwsh -File C:\cp-devops\cp-identity-ops\scripts\kace\Invoke-KaceScriptOnMachine.ps1 `
  -MachineName V1066 -ScriptId <id>
```

ID map (written by publish): [`claude-cowork-ids.json`](claude-cowork-ids.json) (generated; may be absent until first publish).

## Publish (one-time + refresh)

```powershell
# Optional: refresh MSIX from Anthropic redirect
pwsh -File C:\cp-devops\cp-identity-ops\scripts\kace\Get-ClaudeDesktopMsix.ps1 `
  -OutDir C:\cp-devops\cp-ai-toolkit\scratch\claude-packages -ForceDownload

# Create/update KScripts (login via Login-KaceInteractive / env svc-kbox-cp)
pwsh -File C:\cp-devops\cp-identity-ops\scripts\kace\New-KaceClaudeCoworkScripts.ps1 `
  -MsixPath C:\cp-devops\cp-ai-toolkit\scratch\claude-packages\Claude.msix `
  -UpdateIfExists -IncludeDisableAutoUpdates
```

Then **Admin UI → Task Chains** (mirror [sample ID=3](https://kbox.ccimail.com/adminui/task_chain_detail.php?ID=3)):

1. Step 01 VMP → **reboot and continue**
2. Step 02 Provision MSIX
3. Step 03 Verify
4. Optional step 04 DisableAutoUpdates

Rename the chain to `{chainId} - Claude Desktop (Cowork)` and fill `taskChain` in `claude-cowork-ids.json`.

ADO pipeline: `cp-identity-ops/pipelines/cci-claude-cowork.yml` (weekly probe + `kace-deploy` approve).

Do not commit the MSIX binary to git — stage only as a KACE script dependency / scratch download.

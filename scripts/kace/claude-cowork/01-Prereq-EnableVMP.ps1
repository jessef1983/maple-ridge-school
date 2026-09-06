#Requires -Version 5.1
<#
.SYNOPSIS
  Cowork Task Chain step 1: prereq check + enable VirtualMachinePlatform.
.NOTES
  KACE offline/online KScript (elevated / SYSTEM). Exit 3010 = reboot required.
  Canonical: cp-ai-toolkit/scripts/kace/claude-cowork/
#>
$ErrorActionPreference = 'Stop'
$rebootNeeded = $false

function Get-FeatureState([string]$Name) {
    $f = Get-WindowsOptionalFeature -Online -FeatureName $Name -ErrorAction SilentlyContinue
    if (-not $f) { return 'Missing' }
    return [string]$f.State
}

$vmp = Get-FeatureState 'VirtualMachinePlatform'
$hv = Get-FeatureState 'Microsoft-Hyper-V-Hypervisor'
Write-Host "OK: VirtualMachinePlatform=$vmp"
Write-Host "OK: Microsoft-Hyper-V-Hypervisor=$hv"

if ($vmp -ne 'Enabled') {
    Write-Host 'INFO: Enabling VirtualMachinePlatform (NoRestart)'
    Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart | Out-Null
    $rebootNeeded = $true
    Write-Host 'OK: VirtualMachinePlatform enable requested'
}
else {
    Write-Host 'OK: VirtualMachinePlatform already Enabled'
}

# Soft warning only — BIOS/nested virt cannot be fixed here
try {
    $svc = Get-Service -Name vmcompute -ErrorAction SilentlyContinue
    if ($svc) {
        Write-Host "OK: vmcompute Status=$($svc.Status) StartType=$($svc.StartType)"
    }
    else {
        Write-Host 'WARN: vmcompute service not present yet (expected until VMP + reboot)'
    }
}
catch {
    Write-Host "WARN: vmcompute probe failed: $($_.Exception.Message)"
}

if ($rebootNeeded) {
    Write-Host 'RESULT: REBOOT_REQUIRED'
    exit 3010
}

Write-Host 'RESULT: READY'
exit 0

#Requires -Version 5.1
<#
.SYNOPSIS
  Cowork Task Chain step 3: verify CoworkVMService, vmcompute, Appx registration.
.NOTES
  Exit 0 = pass. Exit 1 = soft fail (logged-on user may need RegisterByFamilyName / re-logon).
#>
$ErrorActionPreference = 'Continue'
$failed = $false

$pkg = Get-AppxPackage -AllUsers *claude* -ErrorAction SilentlyContinue
if (-not $pkg) {
    $pkg = Get-AppxPackage *claude* -ErrorAction SilentlyContinue
}
if ($pkg) {
    $pkg | ForEach-Object { Write-Host "OK: Appx $($_.Name) $($_.Version) Status=$($_.Status)" }
}
else {
    Write-Host 'WARN: No Claude AppxPackage for current context'
    $failed = $true
}

$svc = Get-CimInstance Win32_Service -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq 'CoworkVMService' -or ($_.PathName -like '*Claude*' -and $_.PathName -like '*cowork*') }
if ($svc) {
    $svc | ForEach-Object {
        Write-Host "OK: Service Name=$($_.Name) State=$($_.State) StartMode=$($_.StartMode) StartName=$($_.StartName)"
        if ($_.State -ne 'Running' -or $_.StartName -notmatch 'LocalSystem|SYSTEM') {
            $failed = $true
        }
    }
}
else {
    Write-Host 'FAIL: CoworkVMService not found'
    $failed = $true
}

$vm = Get-Service -Name vmcompute -ErrorAction SilentlyContinue
if ($vm) {
    Write-Host "OK: vmcompute Status=$($vm.Status)"
}
else {
    Write-Host 'FAIL: vmcompute missing'
    $failed = $true
}

try {
    $prov = Get-AppxProvisionedPackage -Online -ErrorAction Stop |
        Where-Object { $_.DisplayName -like '*Claude*' }
    if ($prov) {
        $prov | ForEach-Object { Write-Host "OK: Provisioned $($_.DisplayName) $($_.Version)" }
    }
    else {
        Write-Host 'WARN: No Claude AppxProvisionedPackage'
        $failed = $true
    }
}
catch {
    Write-Host "WARN: Get-AppxProvisionedPackage: $($_.Exception.Message)"
}

if ($failed) {
    Write-Host 'RESULT: VERIFY_FAILED — if provisioned, try user re-logon or Add-AppxPackage -RegisterByFamilyName'
    exit 1
}

Write-Host 'RESULT: VERIFY_OK'
exit 0

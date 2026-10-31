# Bind the NVIDIA driver when Windows boots on new GPU hardware (1.8). An image moved to another instance (a new type,
# region or a clone) boots with the L4 at CM_PROB_REINSTALL and no driver; pnputil installs nvgridsw_aws.inf from the
# driver store and one reboot binds it (lane-g6-move.md, lane-paris.md). Run at startup by the scheduled task
# argonia-gpu-bind (setup.ps1) and by play_move.sh / clone.sh at first boot. Prints BOUND, OK or REBOOTING.
param([switch]$NoReboot)
$gpu = Get-PnpDevice -PresentOnly -EA SilentlyContinue | ? { $_.InstanceId -like 'PCI\VEN_10DE*' -and $_.Class -in 'Display', $null, '' }
if (-not $gpu) { 'OK (no NVIDIA device)'; return }
if (@($gpu | ? Status -ne 'OK').Count -eq 0) { 'OK'; return }
$inf = Get-ChildItem C:\Windows\INF\oem*.inf | ? { (Select-String -Path $_.FullName -Pattern 'nvgridsw_aws|NVIDIA' -Quiet) } |
  Select-Object -First 1
if (-not $inf) { 'NO DRIVER IN STORE'; exit 1 }
pnputil /add-driver $inf.FullName /install | Out-Null
if ($NoReboot) { 'BOUND (reboot needed)'; return }
'REBOOTING'; Restart-Computer -Force

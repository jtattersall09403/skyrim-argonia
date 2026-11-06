# The GRID driver's session container shows a "NVIDIA Control Panel is not found" pop-up over the game at every
# logon (no driver setting stops it; DisableStoreNvCplNotifications does not). Killed once after logon, the service
# brings the container back without the pop-up. Its own logon task (argonia-nvpopup), so it runs on every machine
# type, with or without the Virtual Display Driver. The logon task can start before the container does, so it waits
# (up to 3 minutes) for the session's container to appear, then a few seconds for the pop-up, then kills it.
$log = 'C:\argonia\state\nv-popup.log'
$end = (Get-Date).AddMinutes(3)
do {
  $p = Get-Process NVDisplay.Container -EA SilentlyContinue | ? { $_.SessionId -ne 0 }
  if (-not $p) { Start-Sleep 2 }
} until ($p -or (Get-Date) -gt $end)
if (-not $p) { Add-Content $log "$(Get-Date -Format o) no session container in 3 minutes"; return }
Start-Sleep 10
$p | Stop-Process -Force -EA SilentlyContinue
Add-Content $log "$(Get-Date -Format o) session container $($p.Id -join ',') stopped"

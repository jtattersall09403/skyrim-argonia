# Sunshine's prep command for every app (chunk 0.0 §c): size the desktop to the client before the stream starts,
# so each device fills its screen. Sunshine passes the client's request as SUNSHINE_CLIENT_WIDTH/HEIGHT/FPS.
# Picks the display mode whose shape is closest to the request (then the closest size). While Skyrim is running
# the desktop is left alone: Skyrim cannot follow a live resize, so a reconnect from another device keeps the
# game's size until the next launch.
$ErrorActionPreference = 'Stop'
$w = [int]$env:SUNSHINE_CLIENT_WIDTH; $h = [int]$env:SUNSHINE_CLIENT_HEIGHT
$log = 'C:\argonia\logs\sunshine-prep.log'
if (-not $w -or -not $h) { Add-Content $log "$(Get-Date -Format o) no client size"; exit 0 }
if (Get-Process SkyrimSE -EA SilentlyContinue) { Add-Content $log "$(Get-Date -Format o) ${w}x$h requested; Skyrim running, desktop kept"; exit 0 }
. C:\argonia\infra\display.ps1 -Cmd modes   # loads [Disp] and Get-Modes
Add-Type -AssemblyName System.Windows.Forms
$dev = ([System.Windows.Forms.Screen]::AllScreens | ? Primary).DeviceName
$want = $w / $h
$best = Get-Modes $dev | ? { $_.Hz -ge 59 } |
  Sort-Object { [math]::Abs([math]::Log(($_.W / $_.H) / $want)) }, { [math]::Abs($_.W * $_.H - $w * $h) } | Select -First 1
if ($best) {
  & C:\argonia\infra\display.ps1 set $dev $best.W $best.H 60 -Primary | Out-Null
  Add-Content $log "$(Get-Date -Format o) ${w}x$h requested; desktop set to $($best.W)x$($best.H)"
}

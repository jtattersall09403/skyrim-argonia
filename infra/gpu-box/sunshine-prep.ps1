# Sunshine's prep command for every app (chunk 0.0 §c): size the desktop to the client before the stream starts,
# so each device fills its screen. Sunshine passes the client's request as SUNSHINE_CLIENT_WIDTH/HEIGHT/FPS.
# Picks the display mode whose shape is closest to the request (then the closest size). While Skyrim is running
# the desktop is left alone: Skyrim cannot follow a live resize, so a reconnect from another device keeps the
# game's size until the next launch. It always exits 0: Sunshine cancels the launch if a prep command fails.
$log = 'C:\argonia\logs\sunshine-prep.log'
try {
  $reqW = [int]$env:SUNSHINE_CLIENT_WIDTH; $reqH = [int]$env:SUNSHINE_CLIENT_HEIGHT
  if (-not $reqW -or -not $reqH) { Add-Content $log "$(Get-Date -Format o) no client size"; exit 0 }
  if (Get-Process SkyrimSE -EA SilentlyContinue) {
    Add-Content $log "$(Get-Date -Format o) ${reqW}x$reqH requested; Skyrim running, desktop kept"; exit 0
  }
  . C:\argonia\infra\display.ps1 -Cmd modes   # defines Get-Modes (and its own $W/$H: names here differ)
  Add-Type -AssemblyName System.Windows.Forms
  $dev = ([System.Windows.Forms.Screen]::AllScreens | ? Primary).DeviceName
  $want = $reqW / $reqH
  # Near the requested size and within the T4's stream budget (2560x1600), so a small screen never gets a 4K desktop.
  $limit = [math]::Max($reqW * $reqH * 1.3, 1280 * 720)
  $modes = @(Get-Modes $dev | ? { $_.Hz -ge 59 -and $_.W -le 2560 -and $_.H -le 1600 -and $_.W * $_.H -le $limit })
  if (-not $modes) { $modes = @(Get-Modes $dev | ? { $_.Hz -ge 59 -and $_.W -le 1920 -and $_.H -le 1200 }) }
  $best = $modes |
    Sort-Object { [math]::Abs([math]::Log(($_.W / $_.H) / $want)) }, { [math]::Abs($_.W * $_.H - $reqW * $reqH) } |
    Select -First 1
  if ($best) {
    & C:\argonia\infra\display.ps1 set $dev $best.W $best.H 60 -Primary | Out-Null
    Add-Content $log "$(Get-Date -Format o) ${reqW}x$reqH requested; desktop set to $($best.W)x$($best.H)"
  }
} catch {
  Add-Content $log "$(Get-Date -Format o) error (launch continues): $_"
}
exit 0

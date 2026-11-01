# The game machine's idle-stop (chunk 0.0 §b): shut down (which stops the EC2 instance) after 15 minutes with no
# stream client and no agent job. Run every 5 minutes by the scheduled task "argonia-idle-stop".
#   idle-stop.ps1 [-Status]
# Busy means any of: a live stream of any kind (stream-activity.ps1: Sunshine's session log, DCV's connections, or
# traffic), or C:\argonia\state\busy touched in the last 15 min (every run.sh command and bridge heartbeat).
param([switch]$Status)
$State = 'C:\argonia\state'; New-Item -ItemType Directory -Force $State | Out-Null
$IdleMinutes = 15
. C:\argonia\infra\stream-activity.ps1
$tcp = Get-NetTCPConnection -State Established -EA SilentlyContinue
$why = @()
$act = Get-StreamActivity
if ($act.streaming) { $why += "stream ($(($act.clients + "$($act.outKbps) kbps") -join ', '))" }
# An open SSH connection is no longer a sign of work: the bridge keeps its tunnel up after a lane ends, and held Paris
# busy for hours (1.8, 2026-10-31). Agents' work is the busy flag (run.sh touches it each command; the bridge every few minutes).
if ((Test-Path "$State\busy") -and ((Get-Item "$State\busy").LastWriteTime -gt (Get-Date).AddMinutes(-$IdleMinutes))) { $why += 'agent job' }
$now = Get-Date
# The heartbeat the play switch reads through the tunnel (/argonia-metrics/activity): if it goes stale, the
# Worker stops the machine (Windows hung, or this task broken). It replaces the traffic alarm, which counted
# quiet minutes from before a stop and stopped the next start within minutes (2026-10-29).
@{ utc = $now.ToUniversalTime().ToString('o'); active = [bool]$why; why = $why } | ConvertTo-Json -Compress |
  Set-Content "$State\activity.json" -Encoding ASCII
if ($why) {
  Set-Content "$State\last-active" $now.ToString('o')
  if ($Status) { "active: $($why -join ', ')" }
  return
}
$last = if (Test-Path "$State\last-active") { [datetime](Get-Content "$State\last-active") } else { Set-Content "$State\last-active" $now.ToString('o'); $now }
# Idle time never counts from before this boot (a stamp can survive a manual or AWS-side stop).
$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
if ($last -lt $boot) { $last = $boot }
$idle = [int]($now - $last).TotalMinutes
if ($Status) { "idle for $idle min (stops at $IdleMinutes)"; return }
if ($idle -ge $IdleMinutes) {
  Remove-Item "$State\last-active" -EA SilentlyContinue
  Write-EventLog -LogName Application -Source 'Application' -EventId 1 -Message "argonia idle-stop after $idle min" -EA SilentlyContinue
  # the owner's saves to the pool's shared copy first, so the other standby has them (1.8 §7)
  powershell -ExecutionPolicy Bypass -File C:\argonia\infra\saves-sync.ps1 push
  Stop-Computer -Force
}

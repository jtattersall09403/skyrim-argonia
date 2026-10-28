# The game machine's idle-stop (chunk 0.0 §b): shut down (which stops the EC2 instance) after 15 minutes with no
# stream client and no agent job. Run every 5 minutes by the scheduled task "argonia-idle-stop".
#   idle-stop.ps1 [-Status]
# Busy means any of: Moonlight-Web streaming (its connection to Sunshine's RTSP port 48010), a DCV client (the
# tunnel's connection to 8443), an agent over SSH (port 22), or C:\argonia\state\busy touched in the last 15 min.
param([switch]$Status)
$State = 'C:\argonia\state'; New-Item -ItemType Directory -Force $State | Out-Null
$IdleMinutes = 15
$tcp = Get-NetTCPConnection -State Established -EA SilentlyContinue
$why = @()
if ($tcp | ? { $_.RemotePort -eq 48010 -or $_.LocalPort -eq 48010 }) { $why += 'moonlight stream' }
if ($tcp | ? { $_.LocalPort -eq 8443 }) { $why += 'dcv client' }
if ($tcp | ? { $_.LocalPort -eq 22 }) { $why += 'agent ssh' }
if ((Test-Path "$State\busy") -and ((Get-Item "$State\busy").LastWriteTime -gt (Get-Date).AddMinutes(-$IdleMinutes))) { $why += 'agent job' }
$now = Get-Date
if ($why) {
  Set-Content "$State\last-active" $now.ToString('o')
  if ($Status) { "active: $($why -join ', ')" }
  return
}
$last = if (Test-Path "$State\last-active") { [datetime](Get-Content "$State\last-active") } else { Set-Content "$State\last-active" $now.ToString('o'); $now }
$idle = [int]($now - $last).TotalMinutes
if ($Status) { "idle for $idle min (stops at $IdleMinutes)"; return }
if ($idle -ge $IdleMinutes) {
  Remove-Item "$State\last-active" -EA SilentlyContinue
  Write-EventLog -LogName Application -Source 'Application' -EventId 1 -Message "argonia idle-stop after $idle min" -EA SilentlyContinue
  Stop-Computer -Force
}

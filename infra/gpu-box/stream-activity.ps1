# Is anyone streaming, and with what? Dot-sourced by idle-stop.ps1 and host-metrics.ps1 (chunk 0.0 §c).
#   Get-StreamActivity  -> @{ streaming; clients; outKbps }
# Signals, any of which means a stream is live:
#   - Sunshine's log: a CLIENT CONNECTED with no CLIENT DISCONNECTED after it (Moonlight-Web and the Moonlight app
#     both stream through Sunshine; Moonlight-Web reaches it from localhost, the app from the internet);
#   - DCV: a live connection to the console session (dcv list-connections);
#   - traffic: the network adapter sending over 300 kbps (an idle machine sends a few kbps).
# Not TCP connections: Sunshine's TCP connections exist only while a stream is set up, not while it plays, so the
# first idle-stop stopped a live session after 15 minutes (2026-10-29).
function Get-StreamActivity {
  $clients = @()
  $log = 'C:\Program Files\Sunshine\config\sunshine.log'
  if (Test-Path $log) {
    $last = Get-Content $log -Tail 4000 | Select-String -Pattern 'CLIENT (CONNECTED|DISCONNECTED)' | Select -Last 1
    if ($last -and $last.Line -match 'CLIENT CONNECTED') {
      # Moonlight-Web's page posts metrics every second; a Sunshine client without them is the Moonlight app.
      $recent = Get-ChildItem 'C:\argonia\logs\stream-metrics\*.jsonl' -EA SilentlyContinue | Sort LastWriteTime | Select -Last 1
      if ($recent -and $recent.LastWriteTime -gt (Get-Date).AddSeconds(-30)) { $clients = @('moonlight-web') } else { $clients = @('moonlight-app') }
    }
  }
  $dcv = 'C:\Program Files\NICE\DCV\Server\bin\dcv.exe'
  if (Test-Path $dcv) {
    $out = (& $dcv list-connections console 2>$null) -join ' '
    if ($out -and $out -notmatch 'no clients') { $clients += 'dcv' }
  }
  $a = (Get-NetAdapterStatistics | Measure-Object -Property SentBytes -Sum).Sum
  Start-Sleep -Seconds 3
  $b = (Get-NetAdapterStatistics | Measure-Object -Property SentBytes -Sum).Sum
  $outKbps = [math]::Round(($b - $a) * 8 / 3000)
  @{ streaming = ($clients.Count -gt 0 -or $outKbps -gt 300); clients = $clients; outKbps = $outKbps }
}

# What the game machine can measure about any stream, for comparing Moonlight-Web, the Moonlight app and DCV
# (chunk 0.0 §c). Our page logs the client side for Moonlight-Web; DCV and the app cannot run our page, so this
# logs, every 5 s while anything streams, the same host-side numbers for all three into
# C:\argonia\logs\host-metrics\<utc date>.jsonl. Run at boot by the scheduled task "argonia-host-metrics".
#   which client: stream-activity.ps1 (Sunshine's session log with or without our page's metrics; DCV's
#                 connections; traffic)
#   gpu:          GPU use (this GRID driver reports no NVENC session stats through nvidia-smi)
#   network:      bytes out per second on the network adapter
$dir = 'C:\argonia\logs\host-metrics'; New-Item -ItemType Directory -Force $dir | Out-Null
$smi = 'C:\Windows\System32\nvidia-smi.exe'
. C:\argonia\infra\stream-activity.ps1
while ($true) {
  try {
    $act = Get-StreamActivity
    $clients = $act.clients; $outKbps = $act.outKbps; $now = Get-Date
    if ($act.streaming) {
      $gpu = [int](& $smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
      $rec = [ordered]@{
        t = $now.ToUniversalTime().ToString('o'); clients = $clients; outKbps = $outKbps
        gpuPct = $gpu
        skyrim = [bool](Get-Process SkyrimSE -EA SilentlyContinue)
      }
      Add-Content "$dir\$($now.ToUniversalTime().ToString('yyyy-MM-dd')).jsonl" ($rec | ConvertTo-Json -Compress)
    }
  } catch { }
  Start-Sleep 2
}

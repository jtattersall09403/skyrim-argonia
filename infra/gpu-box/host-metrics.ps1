# What the game machine can measure about any stream, for comparing Moonlight-Web, the Moonlight app and DCV
# (chunk 0.0 §c). Our page logs the client side for Moonlight-Web; DCV and the app cannot run our page, so this
# logs, every 5 s while anything streams, the same host-side numbers for all three into
# C:\argonia\logs\host-metrics\<utc date>.jsonl. Run at boot by the scheduled task "argonia-host-metrics".
#   which client: Moonlight-Web reaches Sunshine over localhost; the Moonlight app over the internet; DCV through
#                 the tunnel to 8443
#   gpu:          GPU use (this GRID driver reports no NVENC session stats through nvidia-smi)
#   network:      bytes out per second on the network adapter
$dir = 'C:\argonia\logs\host-metrics'; New-Item -ItemType Directory -Force $dir | Out-Null
$smi = 'C:\Windows\System32\nvidia-smi.exe'
$prev = $null; $prevAt = $null
while ($true) {
  try {
    $tcp = @(Get-NetTCPConnection -State Established -EA SilentlyContinue)
    $sun = @($tcp | ? { $_.LocalPort -in 47984, 47989, 48010 })
    $clients = @()
    if ($sun | ? { $_.RemoteAddress -in '127.0.0.1', '::1' }) { $clients += 'moonlight-web' }
    if ($sun | ? { $_.RemoteAddress -notin '127.0.0.1', '::1' }) { $clients += 'moonlight-app' }
    if ($tcp | ? { $_.LocalPort -eq 8443 }) { $clients += 'dcv' }
    $stats = Get-NetAdapterStatistics | Measure-Object -Property SentBytes -Sum
    $now = Get-Date
    $outKbps = if ($prev) { [math]::Round(($stats.Sum - $prev) * 8 / 1000 / ($now - $prevAt).TotalSeconds) } else { $null }
    $prev = $stats.Sum; $prevAt = $now
    if ($clients) {
      $gpu = [int](& $smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
      $rec = [ordered]@{
        t = $now.ToUniversalTime().ToString('o'); clients = $clients; outKbps = $outKbps
        gpuPct = $gpu
        skyrim = [bool](Get-Process SkyrimSE -EA SilentlyContinue)
      }
      Add-Content "$dir\$($now.ToUniversalTime().ToString('yyyy-MM-dd')).jsonl" ($rec | ConvertTo-Json -Compress)
    }
  } catch { }
  Start-Sleep 5
}

# Read the game's files once on a disk just made from an image (1.8). EBS fetches each block from S3 on its first read,
# so a fresh machine's first game launch stalls (the bridge's ping timed out at deploy, 2026-10-31); reading the
# game, the mods and our files once warms them. The reads run on $Threads runspaces at once: one reader took 20+ min
# for ~90 GB because each first read waits on S3 (speed tick, 2026-10-31; AWS's own advice is parallel reads).
# Prints GB read and seconds.
#   prewarm.ps1 [-Roots <dir>,...] [-Threads 16]   default: C:\argonia and Steam's Skyrim Special Edition
param([string[]]$Roots = @('C:\argonia', 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'),
      [int]$Threads = 16)
$t = [Diagnostics.Stopwatch]::StartNew()
$files = foreach ($r in $Roots) { if (Test-Path $r) { [IO.Directory]::EnumerateFiles($r, '*', 'AllDirectories') } else { "missing $r" | Write-Host } }
$files = @($files)
$read = {
  param([string[]]$list)
  $buf = New-Object byte[] (8MB); $n = 0L
  foreach ($f in $list) {
    try { $s = [IO.File]::Open($f, 'Open', 'Read', 'ReadWrite'); try { while (($k = $s.Read($buf, 0, $buf.Length)) -gt 0) { $n += $k } } finally { $s.Close() } } catch { }
  }
  $n
}
$pool = [runspacefactory]::CreateRunspacePool(1, $Threads); $pool.Open()
$jobs = for ($i = 0; $i -lt $Threads; $i++) {
  $part = for ($j = $i; $j -lt $files.Count; $j += $Threads) { $files[$j] }
  $ps = [powershell]::Create().AddScript($read).AddArgument([string[]]@($part)); $ps.RunspacePool = $pool
  [pscustomobject]@{ ps = $ps; h = $ps.BeginInvoke() }
}
$total = 0L
foreach ($j in $jobs) { $total += ($j.ps.EndInvoke($j.h) | Select-Object -Last 1); $j.ps.Dispose() }
$pool.Close()
"prewarm: {0:N1} GB in {1:N0} s on {2} threads ({3} files)" -f ($total / 1GB), $t.Elapsed.TotalSeconds, $Threads, $files.Count

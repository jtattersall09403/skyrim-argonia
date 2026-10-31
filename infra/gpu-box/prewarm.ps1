# Read the game's files once on a disk just made from an image (1.8). EBS fetches each block from S3 on its first read,
# so a fresh machine's first game launch stalls (the bridge's ping timed out at deploy, 2026-10-31); reading the
# game, the mods and our files once in 8 MB blocks warms them. Prints GB read and seconds.
#   prewarm.ps1 [-Roots <dir>,...]   default: C:\argonia and Steam's Skyrim Special Edition
param([string[]]$Roots = @('C:\argonia', 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'))
$t = [Diagnostics.Stopwatch]::StartNew(); $total = 0L; $buf = New-Object byte[] (8MB)
foreach ($r in $Roots) {
  if (-not (Test-Path $r)) { "missing $r"; continue }
  foreach ($f in [IO.Directory]::EnumerateFiles($r, '*', 'AllDirectories')) {
    try { $s = [IO.File]::Open($f, 'Open', 'Read', 'ReadWrite'); try { while (($n = $s.Read($buf, 0, $buf.Length)) -gt 0) { $total += $n } } finally { $s.Close() } } catch { }
  }
}
"prewarm: {0:N1} GB in {1:N0} s" -f ($total / 1GB), $t.Elapsed.TotalSeconds

# The owner's saves follow them across the pool (1.8 §7): each standby's Saves folder is merged with one shared
# copy, s3://argonia-saves-050977237313/pool/<file>, newest wins per file name (a save, its .skse co-save, the
# autosaves and the quicksave). The machine's own role reads and writes pool/ only (owner issue #33).
#   saves-sync.ps1 pull     at boot (task argonia-saves-pull), before anyone plays: fetch every file the bucket has
#                           newer than this machine; never while the game runs
#   saves-sync.ps1 push -SeedBefore <utc>   once, to seed the shared copy from a machine whose older saves are the
#                           owner's: every file last written before <utc> goes up, whatever the agent list says
#   saves-sync.ps1 pull -SavesDir <dir>   the same pull into another folder (a check that never touches the game)
#   saves-sync.ps1 push     every 5 minutes (task argonia-saves-push), before idle-stop's shutdown and on a spot
#                           notice: upload every file newer here than in the bucket
# Agents' saves stay home: files written while an agent job holds the machine with no stream (the busy flag, as
# idle-stop counts it) are listed in state\saves-agent.txt and never pushed; nor are the per-build saves each deploy
# makes on its own machine (argoniabase, ArgoniaWalk). Nothing is deleted on either side. Log: logs\saves-sync.log.
param([Parameter(Mandatory)][ValidateSet('pull', 'push')][string]$Cmd, [string]$SeedBefore, [string]$SavesDir,
      [string]$Deliberate)   # push -Deliberate <regex>: files whose name matches go up now, agent job or not (the hand-over's region saves, 2026-11-04)
$ErrorActionPreference = 'Stop'
$Bucket = 'argonia-saves-050977237313'; $Prefix = 'pool/'; $Region = 'eu-west-2'
$Saves = if ($SavesDir) { $SavesDir } else { 'C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\Saves' }
$State = 'C:\argonia\state'; $Log = 'C:\argonia\logs\saves-sync.log'
$Skip = '^(argoniabase|ArgoniaWalk)'
$AgentList = "$State\saves-agent.txt"
New-Item -ItemType Directory -Force $State, (Split-Path $Log), $Saves | Out-Null
function Log($m) { "$((Get-Date).ToUniversalTime().ToString('o')) $Cmd $m" | Add-Content $Log }
# The global mutex belongs to the account that first made it (the scheduled task's); a push from an SSH session may not
# open it (2026-11-04: "Access to the path 'Global\argonia-saves-sync' is denied", every saves_push.sh since the 2nd failed
# there unseen). Then the sync runs without it: an S3 put of the same file twice is harmless.
try { $mutex = New-Object Threading.Mutex($false, 'Global\argonia-saves-sync') } catch { Log "mutex: $($_.Exception.Message); running without it"; $mutex = $null }
if ($mutex -and -not $mutex.WaitOne(120000)) { Log 'another sync still running'; exit 0 }
try {
  Import-Module AWSPowerShell
  # At boot the role's credentials can take a minute to appear: retry the listing for two minutes.
  $remote = $null
  for ($i = 0; $i -lt 12 -and $null -eq $remote; $i++) {
    try { $remote = @{}; Get-S3Object -BucketName $Bucket -KeyPrefix $Prefix -Region $Region | % { $remote[$_.Key.Substring($Prefix.Length)] = $_ } }
    catch { $remote = $null; if ($Cmd -eq 'push' -or $i -eq 11) { Log "list failed: $($_.Exception.Message)"; exit 1 }; Start-Sleep 10 }
  }
  $newer = { param($local, $r) -not $r -or $local -gt $r.LastModified.ToUniversalTime().AddSeconds(2) }
  if ($Cmd -eq 'pull') {
    if (-not $SavesDir -and (Get-Process SkyrimSE -EA SilentlyContinue)) { Log 'the game is running: no pull'; exit 0 }
    $n = 0
    foreach ($k in @($remote.Keys)) {
      if (-not $k -or $k -match $Skip -or $k -match '[\\/]') { continue }
      $f = Join-Path $Saves $k; $r = $remote[$k]; $t = $r.LastModified.ToUniversalTime()
      if ((Test-Path $f) -and (Get-Item $f).LastWriteTimeUtc -ge $t.AddSeconds(-2)) { continue }
      Read-S3Object -BucketName $Bucket -Key $r.Key -File $f -Region $Region | Out-Null
      (Get-Item $f).LastWriteTimeUtc = $t   # as the bucket's copy: the next push leaves it
      $n++
    }
    Log "pulled $n of $($remote.Count)"
    exit 0
  }
  if ($SeedBefore) {
    $cut = ([datetime]$SeedBefore).ToUniversalTime(); $n = 0
    foreach ($f in @(Get-ChildItem $Saves -File -EA SilentlyContinue | ? { $_.Name -notmatch $Skip -and $_.LastWriteTimeUtc -lt $cut })) {
      if (& $newer $f.LastWriteTimeUtc $remote[$f.Name]) { Write-S3Object -BucketName $Bucket -Key "$Prefix$($f.Name)" -File $f.FullName -Region $Region; $n++ }
    }
    Log "seeded $n files written before $SeedBefore"; exit 0
  }
  . C:\argonia\infra\stream-activity.ps1
  $busyFlag = (Test-Path "$State\busy") -and ((Get-Item "$State\busy").LastWriteTime -gt (Get-Date).AddMinutes(-15))
  $agentOnly = $busyFlag -and -not (Get-StreamActivity).streaming
  if ($Deliberate) { $agentOnly = $false }   # an agent's deliberate push (saves_push.sh): the region saves are the owner's, made for the hand-over
  $files = @(Get-ChildItem $Saves -File -EA SilentlyContinue | ? { $_.Name -notmatch $Skip })
  $changed = @($files | ? { & $newer $_.LastWriteTimeUtc $remote[$_.Name] })
  $key = { param($f) "$($f.Name)|$($f.LastWriteTimeUtc.Ticks)" }
  if ($agentOnly) {
    if ($changed) { $changed | % { & $key $_ } | Add-Content $AgentList }
    Log "agent job: $($changed.Count) changed files kept on this machine"
    exit 0
  }
  $agent = @{}; if (Test-Path $AgentList) { Get-Content $AgentList | % { $agent[$_] = 1 } }
  $n = 0
  foreach ($f in $changed) {
    if ($agent[(& $key $f)] -and -not ($Deliberate -and $f.Name -match $Deliberate)) { continue }
    Write-S3Object -BucketName $Bucket -Key "$Prefix$($f.Name)" -File $f.FullName -Region $Region
    $n++
  }
  # the list only needs files that still exist unchanged
  if (Test-Path $AgentList) {
    $live = @{}; $files | % { $live[(& $key $_)] = 1 }
    @(Get-Content $AgentList | ? { $live[$_] }) | Set-Content $AgentList
  }
  if ($n) { Log "pushed $n" }
} finally { if ($mutex) { $mutex.ReleaseMutex() } }

# LOD for the new world (nw-02 step 11; decision 0014: derived on the player's machine) on the game machine: xLODGen
# terrain LOD, then TexGen and DynDOLOD object and tree LOD, into C:\argonia\ours\derived-NewWorld\argonia-newworld-lod,
# which stack.ps1 lays in the NewWorld profile only. Derived files: never committed, never shipped. Driven by
# infra/gpu-box/lod.sh from the build VM; the GUI steps run in the desktop session (run.sh desktop).
#   lod.ps1 -Step prepare [-Keep terrain,texgen]   the NewWorld profile laid with no LOD of ours (stack.ps1 on -World
#                              NewWorld), the world's LODSettings file into Data, DynDOLOD Resources linked into Data;
#                              the outputs of the steps in -Keep stay and are linked into Data again, the others go
#   lod.ps1 -Step terrain      xLODGen: terrain LOD (meshes and textures, every level) for the world, then the meshes
#                              again with sheson's settings (Set-TerrainMeshes)
#   lod.ps1 -Step texgen       TexGen: the LOD textures and billboards of the laid trees and objects (our billboard
#                              overrides laid in Data\DynDOLOD\ first)
#   lod.ps1 -Step dyndolod     DynDOLOD: object and tree LOD for the world from -Preset (Low or Medium), with our
#                              plugin's rule file in Data\DynDOLOD\
#   lod.ps1 -Step collect      the outputs into the derived folder, then the profile laid again with it
#   lod.ps1 -Step list         the derived folder's files, one relative path a line, to C:\argonia\lod\logs\files.txt
#   lod.ps1 -Step keys         "<step>=<key>" for each step whose output stands (the key its run was given with -Key)
#   lod.ps1 -Step preflight    everything checkable before a long step: one "FAULT ..." line each, then "preflight OK"
#   lod.ps1 -Step hashes -Tag t   sha256 and path of every file of the three outputs -> logs\hashes-t.txt
#   lod.ps1 -Step unlay        (-Small) the small world's own Data folder removed
# -Small is the small test world (infra/gpu-box/lod.sh selftest): its own world (-World), its own work folder
# (C:\argonia\lod-small: inputs, outputs, keys, logs, the collected folder), its own plugins file and its own game
# folder (game\Data), which the tools are pointed at (-d:). That folder is hard links to the game's Data without our
# LOD mod's files (TexGen refuses to start beside an earlier TexGen output) and without the real world's plugins,
# plus the small world's file. The profile is never laid; the game's Data, the real LOD's folders and its keys are never written.
# A step's output carries the key it was made for (C:\argonia\lod\out\<step>.key, written when the step ends well,
# removed when it starts): lod.sh skips a step whose key on the machine is the one it wants. Each step's settings are
# in lod-settings.json (sent beside this script), which is part of that step's key; this script's text is in none.
#   lod.ps1 -Step survey -Tool xlodgen|texgen|dyndolod   start the tool, dump its windows, kill it (control names)
# None of the three tools has an unattended mode: xEdit's -autoload skips the plugin list, but the options dialog
# (worldspaces, presets, Start/OK) is modal with no switch past it (xEdit xeMainForm.pas mniNavGenerateLODClick:
# ShowModal unconditional). So each GUI step is driven by window messages (BM_CLICK, LB_SETCURSEL + WM_CHAR space,
# WM_SETTEXT) found by class and caption; every window is dumped to the log before it is touched, and an unknown
# pop-up stops the step (named in the log), never clicked blind.
# Every step writes C:\argonia\lod\metrics\<step>.json: wall seconds, peak working set of the tool's processes
# (the tool, LODGen, Texconv) summed per 2 s sample, the machine's lowest free physical memory, and the exit state.
param([Parameter(Mandatory)][ValidateSet('prepare', 'resources', 'terrain', 'texgen', 'dyndolod', 'collect', 'list', 'survey', 'keys', 'preflight', 'hashes', 'unlay')][string]$Step,
      [string]$Key = '', [string]$ToolKey = '', [switch]$Fresh, [string]$Keep = '', [switch]$Small, [string]$Tag = 'now',
      [int]$StopAfterSec = 0,
      [ValidateSet('xlodgen', 'texgen', 'dyndolod')][string]$Tool = 'xlodgen',
      [ValidateSet('Low', 'Medium')][string]$Preset = 'Medium',
      [string]$World = 'ArgoniaBlackMarsh', [int]$TimeoutMin = 180)
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Data = "$Game\Data"
$Root = 'C:\argonia'
$Tools = "$Root\tools"
$Prefs = "$env:LOCALAPPDATA\Skyrim Special Edition"
$PluginsFile = "$Prefs\Plugins.txt"
$RealMod = "$Root\ours\derived-NewWorld\argonia-newworld-lod"
if ($Small) {
  if ($World -eq 'ArgoniaBlackMarsh') { throw "lod.ps1 -Small needs the small world's own -World" }
  $GameData = $Data
  $Work = "$Root\lod-small"; $Mod = "$Work\mod"; $Stack = { }; $PluginsFile = "$Work\Plugins.txt"; $Data = "$Work\game\Data"
  $WorldFile = "$Work\$World.esm"
} else {
  $Work = "$Root\lod"
  $Mod = $RealMod
  $Stack = { & "$Root\infra\stack.ps1" -Cmd on -World NewWorld | Out-Null }
  $WorldFile = "$Root\ours\newworld\ArgoniaNewWorld.esm"
}
$Ini = "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\"
$Out = @{ terrain = "$Work\out\terrain"; texgen = "$Work\out\texgen"; dyndolod = "$Work\out\dyndolod" }
$Exe = @{ xlodgen = "$Tools\xlodgen\xLODGen\xLODGenx64.exe"; texgen = "$Tools\dyndolod\DynDOLOD\TexGenx64.exe"
          dyndolod = "$Tools\dyndolod\DynDOLOD\DynDOLODx64.exe" }
# DynDOLOD Resources is a FOMOD: only its required core (Meshes, Textures; its Scripts and Interface serve dynamic
# LOD, which this job does not make)
$Res = "$Tools\dyndolod-resources\00 DynDOLOD Core Files - Required"
$Settings = Get-Content "$Root\infra\lod-settings.json" -Raw | ConvertFrom-Json
$LodModels = "$Work\lodmodels"   # the derived LOD models (tools/newworld/world/lodmodels.py), a Data-shaped folder
New-Item -ItemType Directory -Force "$Work\logs", "$Work\metrics", "$Work\out", $Mod | Out-Null
function Clear-Output($s) {  # a step's tool starting again: its output and the keys that vouched for it
  Remove-Item "$Work\out\$s.key", "$Work\out\$s-tool.key", "$Work\out\$s-running.key" -Force -EA SilentlyContinue
  Remove-Item $Out[$s] -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force $Out[$s] | Out-Null
}
function Set-OutputKey($s) { if ($Key) { Set-Content "$Work\out\$s.key" $Key -Encoding ASCII } }
# The save point inside a step: the long tool run's output is marked the moment the tool has finished, before any pass
# or check of ours runs on it, so a fault in our own code never costs the tool's run again.
function Set-ToolKey($s) { Remove-Item "$Work\out\$s.key", "$Work\out\$s-running.key" -Force -EA SilentlyContinue; if ($ToolKey) { Set-Content "$Work\out\$s-tool.key" $ToolKey -Encoding ASCII } }
function Tool-Stands($s) {
  $f = "$Work\out\$s-tool.key"
  $ok = -not $Fresh -and $ToolKey -and (Test-Path $f) -and (Get-Content $f -Raw).Trim() -eq $ToolKey
  if ($ok) { Say "${s}: the tool's output stands for $ToolKey; only our own pass runs" }
  $ok
}
$Log = "$Work\logs\$Step$(if ($Step -eq 'survey') { "-$Tool" }).log"
function Say($s) { $l = "[$((Get-Date).ToString('HH:mm:ss'))] $s"; $l; Add-Content $Log $l }
Set-Content $Log ''

Add-Type -TypeDefinition @'
using System; using System.Collections.Generic; using System.Text; using System.Runtime.InteropServices;
public static class W {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr p, EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetParent(IntPtr h);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h, int m, IntPtr w, IntPtr l);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h, int m, IntPtr w, string l);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h, int m, IntPtr w, StringBuilder l);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, int m, IntPtr w, IntPtr l);
  public static string Cls(IntPtr h) { var s = new StringBuilder(256); GetClassName(h, s, 256); return s.ToString(); }
  public static string Text(IntPtr h) {
    int n = (int)SendMessage(h, 0x000E, IntPtr.Zero, IntPtr.Zero);  // WM_GETTEXTLENGTH (works across processes)
    var s = new StringBuilder(n + 1); SendMessage(h, 0x000D, (IntPtr)(n + 1), s); return s.ToString(); }
  public static List<IntPtr> Tops(int pid) {
    var r = new List<IntPtr>();
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); if (p == pid && IsWindowVisible(h)) r.Add(h); return true; }, IntPtr.Zero);
    return r; }
  public static List<IntPtr> Kids(IntPtr top) {
    var r = new List<IntPtr>(); EnumChildWindows(top, (h, l) => { r.Add(h); return true; }, IntPtr.Zero); return r; }
  public static List<string> Items(IntPtr lb) {  // a list box's (or combo's) item texts
    var r = new List<string>(); bool combo = Cls(lb).Contains("Combo");
    int n = (int)SendMessage(lb, combo ? 0x0146 : 0x018B, IntPtr.Zero, IntPtr.Zero);  // CB_GETCOUNT / LB_GETCOUNT
    for (int i = 0; i < n; i++) {
      int len = (int)SendMessage(lb, combo ? 0x0149 : 0x018A, (IntPtr)i, IntPtr.Zero);  // CB_/LB_GETTEXTLEN
      var s = new StringBuilder(Math.Max(len, 0) + 1); SendMessage(lb, combo ? 0x0148 : 0x0189, (IntPtr)i, s); r.Add(s.ToString()); }
    return r; }
}
'@

function Dump($proc, $why) {
  Add-Content $Log "--- windows of $($proc.ProcessName) ($why)"
  foreach ($t in [W]::Tops($proc.Id)) {
    Add-Content $Log ("TOP {0} [{1}] '{2}'" -f $t, [W]::Cls($t), [W]::Text($t))
    foreach ($k in [W]::Kids($t)) {
      if (-not [W]::IsWindowVisible($k)) { continue }
      $c = [W]::Cls($k); $line = "  {0} [{1}] '{2}' {3}" -f $k, $c, [W]::Text($k), $(if ([W]::IsWindowEnabled($k)) { '' } else { '(disabled)' })
      if ($c -match 'Check|Button') { $line += " check=$([W]::SendMessage($k, 0x00F0, [IntPtr]::Zero, [IntPtr]::Zero))" }  # BM_GETCHECK
      if ($c -match 'ListBox|Combo') { $line += " items=[$(([W]::Items($k) | Select -First 40) -join ' | ')]" }
      Add-Content $Log $line
    }
  }
}
function Controls($proc) { foreach ($t in [W]::Tops($proc.Id)) { foreach ($k in [W]::Kids($t)) { if ([W]::IsWindowVisible($k)) { $k } } } }
function Find-Control($proc, $text, [string]$class = '', [int]$waitSec = 60) {
  $end = (Get-Date).AddSeconds($waitSec)
  do {
    $hit = Controls $proc | ? { [W]::Text($_) -replace '&', '' -like $text -and (-not $class -or [W]::Cls($_) -like $class) } | Select -First 1
    if ($hit) { return $hit }
    Start-Sleep 1
  } while ((Get-Date) -lt $end -and -not $proc.HasExited)
  Dump $proc "no control '$text'"; throw "${Step}: no control '$text' ($class) in $waitSec s; the windows are dumped in $Log"
}
function Click($proc, $text, [int]$waitSec = 60) {
  $b = Find-Control $proc $text '*Button*' $waitSec
  Say "click '$text'"; [void][W]::PostMessage($b, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero)  # BM_CLICK
}
function Set-Check($proc, $text, [bool]$on) {
  $b = Find-Control $proc $text '*Check*' 10
  $now = [int][W]::SendMessage($b, 0x00F0, [IntPtr]::Zero, [IntPtr]::Zero) -eq 1
  if ($now -ne $on) { Say "toggle '$text' to $on"; [void][W]::SendMessage($b, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero) }
}
# The worldspace check list: only $World checked. A VCL TCheckListBox toggles its current item on a space key.
function Pick-World($proc) {
  $end = (Get-Date).AddSeconds(120)
  do { $lb = Controls $proc | ? { [W]::Cls($_) -like '*CheckListBox*' } | Select -First 1; if (-not $lb) { Start-Sleep 1 } }
  while (-not $lb -and (Get-Date) -lt $end)
  if (-not $lb) { Dump $proc 'no worldspace list'; throw "${Step}: no worldspace check list" }
  $items = [W]::Items($lb); Say "worldspaces: $($items -join ' | ')"
  $i = [array]::FindIndex([string[]]$items, [Predicate[string]] { param($s) $s -match "\b$World\b" })
  if ($i -lt 0) { throw "${Step}: $World not in the worldspace list" }
  # DynDOLOD's list is set before it starts (Set-DynDOLOD-Worlds: ours ticked, every other world unticked); no toggle.
  if ($Step -eq 'dyndolod') { Say "worldspaces: only $World ticked by the preset file"; return }
  # xLODGen opens with only Tamriel (item 0) ticked: untick it, tick ours.
  foreach ($j in @(0, $i)) {
    if ($j -eq 0 -and $items[0] -notmatch 'Tamriel') { continue }
    [void][W]::SendMessage($lb, 0x0186, [IntPtr]$j, [IntPtr]::Zero)  # LB_SETCURSEL
    [void][W]::SendMessage($lb, 0x0102, [IntPtr]0x20, [IntPtr]::Zero)  # WM_CHAR ' '
    Say "toggled item $j '$($items[$j])'"
  }
}
# DynDOLOD opens its worldspace list as Presets\DynDOLOD_SSE_Default.ini saved it (one <world>=0|1 line per world after
# NearGrid in [DynDOLOD]): written here with only $World at 1, or every world is generated.
$DynPreset = "$Tools\dyndolod\DynDOLOD\Edit Scripts\DynDOLOD\Presets\DynDOLOD_SSE_Default.ini"
function Set-DynDOLOD-Worlds {
  if (-not (Test-Path $DynPreset)) { throw "${Step}: no $DynPreset to set the worldspaces in" }
  $rows = New-Object System.Collections.Generic.List[string]; $sec = ''; $worlds = $false; $ours = $false; $at = -1
  foreach ($l in Get-Content $DynPreset) {
    if ($l -match '^\[(.+)\]$') { $sec = $Matches[1]; $worlds = $false }
    elseif ($sec -eq 'DynDOLOD' -and $l -match '^NearGrid=') { $worlds = $true; $at = $rows.Count + 1 }
    elseif ($sec -eq 'DynDOLOD' -and $worlds -and $l -match '^([^=]+)=[01]$') {
      if ($Matches[1] -eq $World) { $l = "$World=1"; $ours = $true } else { $l = "$($Matches[1])=0" } }
    # the preset also saves the output path of the run before, and DynDOLOD exports to it whatever -o: says
    elseif ($sec -eq 'DynDOLOD' -and $l -match '^OutputPath=') { $l = "OutputPath=$($Out.dyndolod)\" }
    $rows.Add($l)
  }
  if ($at -lt 0) { throw "${Step}: no NearGrid line in $DynPreset" }
  if (-not $ours) { $rows.Insert($at, "$World=1") }
  Set-Content $DynPreset $rows -Encoding ASCII
  $on = @(Get-Content $DynPreset | ? { $_ -match '^[A-Za-z0-9_]+=1$' } | ? { $l2 = $_; $rows.IndexOf($l2) -ge $at })
  Say "worldspaces in the preset at 1: $($on -join ', ')"
}
# TexGen opens with the output path its preset file saved at its last run (Presets\DynDOLOD_SSE_TexGen.ini,
# OutputPath), whatever -o: says: written here before every run, or it writes into the folder of the run before.
function Set-TexGen-Output {
  $f = "$Tools\dyndolod\DynDOLOD\Edit Scripts\DynDOLOD\Presets\DynDOLOD_SSE_TexGen.ini"
  if (-not (Test-Path $f)) { Say 'texgen preset: none yet (the first run takes -o:)'; return }
  $rows = @(Get-Content $f | % { if ($_ -match '^OutputPath=') { "OutputPath=$($Out.texgen)\" } else { $_ } })
  Set-Content $f $rows -Encoding ASCII
  Say "texgen preset: $(@($rows | ? { $_ -match '^OutputPath=' }) -join ', ')"
}
# Fails the step at once when DynDOLOD starts LODGen for any world but ours (its Logs\LODGen_SSE_<world>_log.txt).
function Assert-Only-Ours($since) {
  $bad = Get-ChildItem "$Tools\dyndolod\DynDOLOD\Logs" -Filter 'LODGen_SSE_*_log.txt' -EA SilentlyContinue | ? { $_.LastWriteTime -gt $since } |
    % { $_.Name -replace '^LODGen_SSE_', '' -replace '(_TerrainUnderside)?_log\.txt$', '' } | ? { $_ -ne $World } | Sort -Unique
  if ($bad) { throw "${Step}: DynDOLOD is generating other worlds: $($bad -join ', ')" }
}
# xLODGen's finish line can come back unreadable from its window, and then never matches. The run is also over when
# its output has settled: files there, their count unchanged for 90 s, no helper running, and the tool itself idle
# over those 90 s (under 2 s of processor time). The step's own verdict after the wait reads the disk again.
$Settle = @{ count = -1; since = Get-Date; cpu = 0.0; settled = $false }
function Terrain-Settled($proc) {
  $c = @(Get-ChildItem $Out.terrain -Recurse -File -Include *.btr, *.dds -EA SilentlyContinue).Count
  $proc.Refresh(); $cpuNow = $proc.TotalProcessorTime.TotalSeconds
  if ($c -ne $Settle.count -or @(Get-Process -Name $Helpers -EA SilentlyContinue).Count -or ($cpuNow - $Settle.cpu) -gt 2) {
    $Settle.count = $c; $Settle.since = Get-Date; $Settle.cpu = $cpuNow; return $false }
  $idle = $c -gt 0 -and ((Get-Date) - $Settle.since).TotalSeconds -ge 90
  if ($idle) { $Settle.settled = $true; Say "terrain: no finish line read; the output has settled ($c files, 90 s, the tool idle)" }
  $idle
}
# Fails the terrain step as soon as xLODGen writes a world folder (meshes|textures\terrain\<world>) other than ours.
function Assert-Terrain-Ours {
  $bad = foreach ($d in 'meshes\terrain', 'textures\terrain') { Get-ChildItem "$($Out.terrain)\$d" -Directory -EA SilentlyContinue | % Name }
  $bad = @($bad | ? { $_ -ne $World } | Sort -Unique)
  if ($bad) { throw "${Step}: xLODGen is generating other worlds: $($bad -join ', ')" }
}
# Pop-ups: a known one gets its named answer; any other stops the step.
$Known = @(
  @{ match = 'DynDOLOD DLL|Scripts.*not found|DynDOLOD Resources'; answer = 'Ignore' }  # no dynamic LOD wanted (Sky-Claw #661)
  @{ match = 'stitched'; answer = 'Ignore' }
  @{ match = 'Worldspace-Editor-ID-Changed'; answer = 'Ignore' }  # BM&V's own worlds renamed by a later plugin; not ours
)
function Watch-Popups($proc, $main) {
  foreach ($t in [W]::Tops($proc.Id)) {
    if ($t -eq $main) { continue }
    # the VCL's own windows (the hidden application window, the main form once the options dialog closes) are no
    # pop-up; nor is a window with no text at all (game-12: Generate stopped on "unknown pop-up: ")
    if ([W]::Cls($t) -in 'TApplication', 'TfrmMain') { continue }
    # the tool's own progress window ("Information: Please wait a moment...", no button to press) is no pop-up to
    # answer: DynDOLOD shows it for a few seconds after OK and carries on
    if ([W]::Cls($t) -eq 'prgrAlertWndClass') { continue }
    $text = (@([W]::Text($t)) + @([W]::Kids($t) | % { [W]::Text($_) })) -join ' / '
    if (-not ($text -replace '[\s/]', '')) { continue }
    if ($text -match 'Exit TexGen|Save & Exit|Save and Exit') { continue }
    if ($text -match '^DynDOLOD Wizard') { continue }  # DynDOLOD's own options window, a top window beside the main form  # the tool's own finished dialog: the step's done-check and Click end it (round 3: texgen finished, then the watcher threw)
    $k = $Known | ? { $text -match $_.match } | Select -First 1
    if (-not $k) { Dump $proc 'unknown pop-up'; throw "${Step}: unknown pop-up: $text" }
    $b = [W]::Kids($t) | ? { ([W]::Text($_) -replace '&', '') -eq $k.answer } | Select -First 1
    if (-not $b) { Dump $proc 'pop-up without its answer'; throw "${Step}: pop-up '$text' has no '$($k.answer)'" }
    Say "pop-up '$text': $($k.answer)"; [void][W]::PostMessage($b, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero)
  }
}
function Main-Window($proc, [int]$waitSec = 300) {
  $end = (Get-Date).AddSeconds($waitSec)
  while ((Get-Date) -lt $end -and -not $proc.HasExited) {
    $proc.Refresh(); if ($proc.MainWindowHandle -ne 0) { return $proc.MainWindowHandle }; Start-Sleep 1 }
  throw "${Step}: $($proc.ProcessName) showed no window in $waitSec s"
}

# Metrics: the tool and its helpers (LODGen, Texconv) summed, every 2 s, until $done says so.
$Helpers = 'LODGen*', 'Texconv*'
function Measure-Run($proc, [scriptblock]$done) {
  $null = $proc.Handle  # an attached process too: ExitCode is kept only when the handle was taken before the exit
  $t0 = Get-Date; $peak = 0; $minFree = [long]::MaxValue; $samples = 0
  while ($true) {
    $ps = @(Get-Process -Id $proc.Id -EA SilentlyContinue) + @(Get-Process -Name $Helpers -EA SilentlyContinue)
    $ws = ($ps | Measure-Object WorkingSet64 -Sum).Sum; if ($ws -gt $peak) { $peak = $ws }
    $free = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory * 1KB; if ($free -lt $minFree) { $minFree = $free }
    $samples++
    if (& $done) { break }
    if ($proc.HasExited) { throw "${Step}: $($proc.ProcessName) exited (code $($proc.ExitCode)) before it finished; see its log" }
    if (((Get-Date) - $t0).TotalMinutes -gt $TimeoutMin) { throw "${Step}: not done in $TimeoutMin min" }
    Start-Sleep 2
  }
  $proc.Refresh()
  $m = [ordered]@{ step = $Step; seconds = [int]((Get-Date) - $t0).TotalSeconds; peak_ws_gb = [math]::Round($peak / 1GB, 2)
    tool_peak_ws_gb = [math]::Round($proc.PeakWorkingSet64 / 1GB, 2); min_free_gb = [math]::Round($minFree / 1GB, 2)
    total_gb = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
    cpus = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors; samples = $samples; preset = $Preset }
  $m | ConvertTo-Json | Set-Content "$Work\metrics\$Step.json" -Encoding ASCII
  Say "metrics: $($m | ConvertTo-Json -Compress)"
}
# The tool's own log (the messages tab is a TMemo / rich edit): its last lines say done or failed.
function Tool-Text($proc) {
  (Controls $proc | ? { [W]::Cls($_) -match 'Memo|RichEdit|Edit' } | % { [W]::Text($_) }) -join "`n"
}
function Start-Tool($name, $argline) {
  Get-Process -Name ([IO.Path]::GetFileNameWithoutExtension($Exe[$name])) -EA SilentlyContinue | Stop-Process -Force
  if (-not (Test-Path $Exe[$name])) { throw "no $($Exe[$name]): lod.sh tools" }
  Say "start $($Exe[$name]) $argline" | Write-Host  # to the host: this function returns only the process
  $p = Start-Process $Exe[$name] -ArgumentList $argline -WorkingDirectory (Split-Path $Exe[$name]) -PassThru
  $null = $p.Handle  # so ExitCode is kept for Measure-Run's message (PowerShell 5.1)
  $p
}
$Paths = "-sse -autoload -d:`"$Data\`" -p:`"$PluginsFile`" -m:`"$Ini`""
function Link-Into-Data($src, $sub = '') {
  Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class HL2 {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool CreateHardLink(string link, string target, IntPtr sa); }' -EA SilentlyContinue
  $n = 0
  foreach ($f in [IO.Directory]::EnumerateFiles($src, '*', 'AllDirectories')) {
    $dst = "\\?\$Data$sub" + $f.Substring($src.Length)
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst))
    if ([IO.File]::Exists($dst)) { [IO.File]::Delete($dst) }
    if (-not [HL2]::CreateHardLink($dst, "\\?\$f", [IntPtr]::Zero)) { throw "link failed: $f" }
    $n++
  }
  Say "linked $n files from $src into Data"
}
# The small world's own Data folder: every file of the game's Data as a hard link, but our LOD mod's files and the
# real world's plugins; then the small world's file. Made anew each time: a link keeps the bytes it was made on.
function Lay-Small-Data {
  Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class HL3 {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool CreateHardLink(string link, string target, IntPtr sa); }' -EA SilentlyContinue
  if (Test-Path "$Work\game") { [IO.Directory]::Delete("\\?\$Work\game", $true) }
  # the tools take the folder above Data for the game's: its exe is read for the version, and an output path
  # inside it is refused, so the folder stands apart from the outputs
  [void][IO.Directory]::CreateDirectory($Data)
  if (-not [HL3]::CreateHardLink("$Work\game\SkyrimSE.exe", "$Game\SkyrimSE.exe", [IntPtr]::Zero)) { throw 'link failed: SkyrimSE.exe' }
  $skip = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
  if (Test-Path $RealMod) { foreach ($f in [IO.Directory]::EnumerateFiles($RealMod, '*', 'AllDirectories')) { [void]$skip.Add($f.Substring($RealMod.Length)) } }
  foreach ($f in '\ArgoniaNewWorld.esm', '\ArgoniaNWPlaces.esp', '\SEQ\ArgoniaNWPlaces.seq') { [void]$skip.Add($f) }
  $n = 0
  foreach ($f in [IO.Directory]::EnumerateFiles($GameData, '*', 'AllDirectories')) {
    $rel = $f.Substring($GameData.Length); if ($skip.Contains($rel)) { continue }
    $dst = "\\?\$Data$rel"
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst))
    if (-not [HL3]::CreateHardLink($dst, "\\?\$f", [IntPtr]::Zero)) { throw "link failed: $f" }
    $n++
  }
  if (-not (Test-Path $WorldFile)) { throw "prepare: no $WorldFile (lod.sh sends it)" }
  Copy-Item $WorldFile "$Data\$World.esm"
  $rows = @(Get-Content "$Prefs\Plugins.txt" | ? { $_ -notmatch 'ArgoniaNewWorld\.esm|ArgoniaNWPlaces\.esp' }) + "*$World.esm"
  Set-Content $PluginsFile $rows -Encoding ASCII
  Say "small Data: $n files linked from the game's Data ($($skip.Count) of our LOD mod and the real world left out), $World.esm laid"
}
# A file copied into Data: in the small world's folder a file of that name may be a link to the game's own, and a copy
# over a link would write the game's file, so the name is freed first.
function Copy-Into-Data($src, $rel) {
  $dst = "$Data\$rel"
  New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
  if (Test-Path $dst) { Remove-Item $dst -Force }
  Copy-Item $src $dst
}
function Link-Resources {  # into Data while the tools run
  # Interface too: DynDOLOD 3.0 alpha-217 refuses to start without interface\dyndolod\dyndolod.dds even when no
  # dynamic LOD is made (2026-11-02, "Required resource file not found", an Exit-only dialog the watcher cannot answer)
  # ...and Scripts: alpha-217 also refuses without scripts\sheson_dyndolod_alias.pex (survey on the LOD box, 14:21).
  # So the whole required core is linked; what the game does with its scripts is nothing until a DynDOLOD.esp is
  # enabled, which this job never does.
  foreach ($d in Get-ChildItem $Res -Directory | % { $_.Name }) { Link-Into-Data "$Res\$d" "\$d" }
}

# The world's LODSettings file (tools/newworld/world/mapdata.py on the build VM, sent by lod.sh): xLODGen lists a
# worldspace only when Data\LODSettings\<WRLD>.lod exists, and the game reads it to place the LOD. It lives in the
# derived folder, so the profile lays it with the rest; prepare also copies it into Data for the tools.
function Lay-LodSettings {
  $src = "$Work\$World.lod"
  if (-not (Test-Path $src)) { throw "${Step}: no $src (lod.sh sends it)" }
  New-Item -ItemType Directory -Force "$Mod\LODSettings" | Out-Null
  Copy-Item $src "$Mod\LODSettings\$World.lod" -Force
  Say "lodsettings: $Mod\LODSettings\$World.lod ($((Get-Item $src).Length) bytes)"
}

# The world's LOD plan files (NewWorldMap.cs from tools/newworld/world/lodplan.py, sent by lod.sh to $Work): the TexGen
# billboard overrides and our plugin's DynDOLOD rule file, read by TexGen and DynDOLOD from Data\DynDOLOD\ (dyndolod.info
# Mod-Authors, TexGen-Configuration). Laid just before each tool starts: a fresh profile lay drops unrecorded files.
function Lay-DynDOLOD-Data {
  $files = @(Get-ChildItem $Work -File -Filter 'DynDOLOD_SSE_*' -EA SilentlyContinue)
  if (-not $files) { throw "${Step}: no DynDOLOD_SSE_* plan files in $Work (lod.sh send)" }
  New-Item -ItemType Directory -Force "$Data\DynDOLOD" | Out-Null
  foreach ($f in $files) { Copy-Into-Data $f.FullName "DynDOLOD\$($f.Name)" }
  Say "DynDOLOD data: $($files.Name -join ', ')"
}

# Terrain LOD meshes per sheson's recipe for xLODGen (dyndolod.info Help/xLODGen): LOD4 quality 0-5 with Protect Borders
# and Optimize Unseen off; LOD8 and LOD16 quality 0-8 with Optimize Unseen 550 "in case there is visible z-fighting of
# water in the distance"; LOD32 quality 0-10 with Optimize Unseen 550 "to improve coastlines on the map". The GUI's
# defaults (quality 10/15/20/25, Protect Borders off, Optimize Unseen on) are what the run of 2026-11-09 used. xLODGen
# keeps its options only in its GUI, so its own LODGen input (LODGen_Terrain_<world>.txt, written by the run) is
# rewritten with these keys and LODGen run again on the same height data: the meshes replaced, the textures kept.
$TerrainMesh = [ordered]@{}; foreach ($q in $Settings.terrain.post.meshes.PSObject.Properties) { $TerrainMesh[$q.Name] = $q.Value }
function Set-TerrainMeshes {
  $dir = "$Tools\xlodgen\xLODGen\Edit Scripts"
  $src = "$Work\out\terrain-lodgen-input.txt"
  if (-not (Test-Path $src)) { throw "terrain: no $src (kept from xLODGen's run)" }
  $lines = foreach ($l in Get-Content $src) {
    if ($l -match '^([A-Za-z0-9]+)=' -and $TerrainMesh.Contains($Matches[1])) { "$($Matches[1])=$($TerrainMesh[$Matches[1]])" } else { $l } }
  $have = @($lines | % { ($_ -split "=")[0] })
  foreach ($k in $TerrainMesh.Keys) { if ($k -notin $have) { throw "terrain: $src has no $k line" } }
  $txt = "$Work\LODGen_Terrain_$World.txt"; Set-Content $txt $lines -Encoding ASCII
  Say "terrain meshes: LODGen again with $(($TerrainMesh.GetEnumerator() | % { "$($_.Key)=$($_.Value)" }) -join ' ')"
  $t0 = Get-Date
  $p = Start-Process "$dir\LODGenx64.exe" -ArgumentList "`"$txt`"" -WorkingDirectory $dir -PassThru -NoNewWindow `
         -RedirectStandardOutput "$Work\logs\terrain-lodgen.txt" -RedirectStandardError "$Work\logs\terrain-lodgen-err.txt"
  $null = $p.Handle  # PowerShell 5.1 keeps ExitCode only when the handle was taken before the exit
  if (-not $p.WaitForExit($TimeoutMin * 60000)) { $p | Stop-Process -Force; throw "terrain: LODGen not done in $TimeoutMin min" }
  $n = @(Get-ChildItem "$($Out.terrain)\meshes\terrain\$World" -Filter *.btr | ? { $_.LastWriteTime -gt $t0 }).Count
  Say "terrain meshes: LODGen exit $($p.ExitCode), $n .btr rewritten in $([int]((Get-Date) - $t0).TotalSeconds) s"
  if ($p.ExitCode -ne 0 -or $n -eq 0) { throw "terrain: LODGen failed (exit $($p.ExitCode), $n .btr); see $Work\logs\terrain-lodgen.txt" }
}

# The derived LOD models (<model>_lod_0.nif under meshes\lod\, tools/newworld/world/lodmodels.py; lod.sh sends them to
# $LodModels): into Data before DynDOLOD starts, which scans Data\meshes for *_lod*.nif. DynDOLOD merges them into the
# .bto files, so the game never reads them and they are not collected.
function Lay-LodModels {
  if (-not (Test-Path "$LodModels\meshes")) { Say 'LOD models: none sent'; return }
  Link-Into-Data $LodModels
}
function Preflight {
  $f = New-Object System.Collections.Generic.List[string]
  $ps = & powershell -ExecutionPolicy Bypass -File "$Root\infra\pscheck.ps1" -Files "$Root\infra\lod.ps1,$Root\infra\stack.ps1"
  foreach ($l in @($ps | ? { $_ -notmatch '^pscheck: ' })) { $f.Add("script: $l") }
  foreach ($e in $Exe.GetEnumerator()) { if (-not (Test-Path $e.Value)) { $f.Add("tool: no $($e.Value) (lod.sh tools)") } }
  if (-not (Test-Path "$Res\Meshes")) { $f.Add("tool: no DynDOLOD Resources core under $Res (lod.sh tools)") }
  foreach ($t in 'xlodgen', 'dyndolod', 'dyndolod-resources') { Say "tool $t $(Get-Content "$Tools\$t\.sha256" -EA SilentlyContinue)" }
  $busy = @(Get-Process xLODGenx64, TexGenx64, DynDOLODx64, LODGen*, Texconv*, SkyrimSE -EA SilentlyContinue | % ProcessName)
  if ($busy) { $f.Add("machine: still running $($busy -join ', ')") }
  $free = [math]::Round((Get-PSDrive C).Free / 1GB, 1); Say "disk free $free GB"
  if ($free -lt 30) { $f.Add("machine: $free GB free on C:, under 30") }
  $ram = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1); Say "ram free $ram GB"
  if ($ram -lt 8) { $f.Add("machine: $ram GB of memory free, under 8") }
  foreach ($x in Get-ChildItem $Work -File -Filter 'DynDOLOD_SSE_*' -EA SilentlyContinue) { Say "have $($x.Name) $((Get-FileHash $x.FullName -Algorithm SHA256).Hash.ToLower())" }
  foreach ($x in $WorldFile, "$Work\$World.lod") {
    if (Test-Path $x) { Say "have $(Split-Path $x -Leaf) $((Get-FileHash $x -Algorithm SHA256).Hash.ToLower())" } else { $f.Add("input: no $x (lod.sh send)") } }
  # DynDOLOD's preset: written as before every run, then read back: only our world may stand at 1
  try {
    Set-DynDOLOD-Worlds
    $sec = ''; $at = $false; $on = @(foreach ($l in Get-Content $DynPreset) {
      if ($l -match '^\[(.+)\]$') { $sec = $Matches[1]; $at = $false } elseif ($sec -eq 'DynDOLOD' -and $l -match '^NearGrid=') { $at = $true }
      elseif ($sec -eq 'DynDOLOD' -and $at -and $l -match '^([^=]+)=1$') { $Matches[1] } })
    Say "preset worlds at 1: $($on -join ', ')"
    if (($on -join ',') -ne $World) { $f.Add("preset: DynDOLOD's preset holds $($on -join ', ') at 1, not $World alone") }
  } catch { $f.Add("preset: $($_.Exception.Message)") }
  $n = @(Get-ChildItem "$LodModels\meshes" -Recurse -File -Filter *_lod_*.nif -EA SilentlyContinue).Count; Say "have lodmodels $n"
  foreach ($l in $f) { Say "FAULT $l" }
  if ($f.Count) { throw "preflight: $($f.Count) faults" }
}

switch ($Step) {
  'keys' { foreach ($s in 'terrain-tool', 'terrain', 'texgen-tool', 'texgen', 'dyndolod', 'terrain-running') { if (Test-Path "$Work\out\$s.key") { Say "$s=$((Get-Content "$Work\out\$s.key" -Raw).Trim())" } } }
  'unlay' {
    if (-not $Small) { throw "unlay is the small world's" }
    if (Test-Path "$Work\game") { [IO.Directory]::Delete("\\?\$Work\game", $true) }
    Say "unlaid: the small world's game folder removed"
  }
  'hashes' {
    $rows = foreach ($o in $Out.GetEnumerator() | Sort-Object Name) { foreach ($f in Get-ChildItem $o.Value -Recurse -File -EA SilentlyContinue | Sort-Object FullName) {
      "$((Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower())  $($o.Name)$($f.FullName.Substring($o.Value.Length))" } }
    Set-Content "$Work\logs\hashes-$Tag.txt" $rows -Encoding ASCII; Say "hashes: $(@($rows).Count) files -> hashes-$Tag.txt"
  }
  'prepare' {
    if (-not $Small) { Stop-Process -Name SkyrimSE, skse64_loader -Force -EA SilentlyContinue }
    # a tool a failed step left open holds Data's archives, and the fresh lay below cannot delete them (game-12)
    Get-Process xLODGenx64, TexGenx64, DynDOLODx64, LODGen*, Texconv* -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
    Start-Sleep 2
    Remove-Item "$Mod\*" -Recurse -Force -EA SilentlyContinue   # Data without any old LOD of ours
    $kept = @($Keep -split ',' | ? { $_ })
    foreach ($s in @($Out.Keys)) { if ($s -notin $kept -or -not ((Test-Path "$Work\out\$s.key") -or (Test-Path "$Work\out\$s-tool.key") -or (Test-Path "$Work\out\$s-running.key"))) { Clear-Output $s } }
    Lay-LodSettings
    & $Stack
    if ($Small) { Lay-Small-Data; Copy-Into-Data "$Work\$World.lod" "LODSettings\$World.lod" }
    if (-not (Test-Path "$Data\LODSettings\$World.lod")) { throw "prepare: LODSettings\$World.lod not laid in Data" }
    if (-not (Test-Path "$Data\$(Split-Path $WorldFile -Leaf)")) { throw "prepare: $(Split-Path $WorldFile -Leaf) not in Data (lod.sh sends it)" }
    Link-Resources
    # the outputs that stand, into the fresh Data: DynDOLOD culls under the terrain LOD and reads TexGen's textures
    foreach ($s in 'terrain', 'texgen') { if (Test-Path "$Work\out\$s.key") { Say "kept: $s ($((Get-Content "$Work\out\$s.key" -Raw).Trim()))"; Link-Into-Data $Out[$s] } }
    Say "plugins: $((Get-Content $PluginsFile) -join ', ')"
    $free = (Get-PSDrive C).Free; Say "C: free $([math]::Round($free / 1GB, 1)) GB"
    if ($free -lt 20GB) { throw 'prepare: under 20 GB free on C:' }
  }
  'list' {
    $l = Get-ChildItem $Mod -Recurse -File -EA SilentlyContinue | % { $_.FullName.Substring($Mod.Length + 1) }
    $l | Set-Content "$Work\logs\files.txt" -Encoding ascii; Say "list: $(@($l).Count) files"
  }
  'resources' {  # re-link after a restart or a fresh profile lay, without a prepare (prepare wipes the outputs)
    Link-Resources
    # TexGen's output too: DynDOLOD reads it from Data ("No TexGen output detected" otherwise); the texgen step linked it
    # once, every fresh lay since dropped the links, and the step marker rightly skips TexGen itself (14:41).
    if ((Test-Path $Out.texgen) -and (Get-ChildItem $Out.texgen -Recurse -File -EA SilentlyContinue)) { Link-Into-Data $Out.texgen }
  }
  'survey' {
    $exeArgs = $Paths + $(if ($Tool -eq 'xlodgen') { ' -lodgen' } else { '' }) + " -o:`"$Work\out\survey\`""
    $p = Start-Tool $Tool $exeArgs
    $main = Main-Window $p; Start-Sleep 20; Dump $p 'after start'; Start-Sleep 40; Dump $p 'after a minute'
    $p | Stop-Process -Force
  }
  'terrain' {
    if (-not (Tool-Stands terrain)) {
    # xLODGen skips a terrain LOD texture that is already in its output folder (its Terrain-LOD readme: "can be used
    # to continue generating"), so a run that was stopped is carried on, not started again: the output is kept when
    # the run that wrote it had this very key. The files being written at the stop are the newest: twice as many as
    # the machine has threads are deleted, with every empty file. xLODGen writes every mesh again, and so does our pass.
    $run = "$Work\out\terrain-running.key"
    if (-not $Fresh -and $ToolKey -and (Test-Path $run) -and (Get-Content $run -Raw).Trim() -eq $ToolKey) {
      $tex = @(Get-ChildItem $Out.terrain -Recurse -File -Filter *.dds -EA SilentlyContinue | Sort-Object LastWriteTime -Descending)
      $drop = @($tex | Select-Object -First (2 * [Environment]::ProcessorCount)) + @($tex | ? { $_.Length -eq 0 })
      $drop | Remove-Item -Force -EA SilentlyContinue
      Say "terrain: carrying on the stopped run of $ToolKey ($($tex.Count) textures there, the newest $(@($drop).Count) made again)"
    } else {
      Clear-Output terrain
      if ($ToolKey) { Set-Content $run $ToolKey -Encoding ASCII }
    }
    $p = Start-Tool xlodgen ($Paths + " -lodgen -o:`"$($Out.terrain)\`"")
    $main = Main-Window $p
    Find-Control $p 'Generate' '*Button*' 600 | Out-Null   # the options dialog, after the plugins load
    Dump $p 'options'
    Pick-World $p
    foreach ($c in 'Objects LOD', 'Trees LOD', 'Occlusion') { try { Set-Check $p $c $false } catch { Say "no '$c' box" } }
    Set-Check $p 'Terrain LOD' $true
    Dump $p 'before Generate'
    Click $p 'Generate'
    $tGen = Get-Date
    try { Measure-Run $p { $null = Watch-Popups $p $main; Assert-Terrain-Ours
      if ($StopAfterSec -and ((Get-Date) - $tGen).TotalSeconds -gt $StopAfterSec) { throw "terrain: stopped after $StopAfterSec s (-StopAfterSec: the test of carrying on)" }
      ((Tool-Text $p) -match 'LOD Generator: finished|LOD generation done') -or (Terrain-Settled $p) } }
    catch { $p | Stop-Process -Force -EA SilentlyContinue; Get-Process LODGen* -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue; throw }
    # round 5 close-8 (20:39): the done-check's pop-up watcher wrote a line, which made the check true 6 s before the
    # tool's finish line existed, and this re-read found none. The watcher's output is now discarded above, and this
    # re-read waits for the finish line (up to 10 min) instead of failing on one early read.
    $t1 = Get-Date
    do { $txt = Tool-Text $p; if ($txt -match 'finished|generation done') { break }; Start-Sleep 5 } while (((Get-Date) - $t1).TotalMinutes -lt $(if ($Settle.settled) { 0.2 } else { 10 }))
    Set-Content "$Work\logs\terrain-messages.txt" $txt
    if ($txt -notmatch 'finished|generation done') {
      # The window's text can come back unreadable (close-8, 20:39: 691 KB of '?'). The verdict then comes from the
      # output on disk, not the window (owner, 22:20, #37): tool alive, no helper left, the file count unchanged for 60 s.
      $c1 = (Get-ChildItem $Out.terrain -Recurse -File -Include *.btr, *.dds).Count; Start-Sleep 60
      $c2 = (Get-ChildItem $Out.terrain -Recurse -File -Include *.btr, *.dds).Count
      $busy = @(Get-Process -Name $Helpers -EA SilentlyContinue).Count
      if ($c1 -gt 0 -and $c1 -eq $c2 -and $busy -eq 0 -and -not $p.HasExited) { Say "terrain: finish line unreadable; accepted on disk ($c1 files, stable 60 s, no helper running)"; $txt = 'generation done (accepted on disk)' }
    }
    if ($txt -notmatch 'finished|generation done') { throw 'terrain: xLODGen did not finish' }
    $p | Stop-Process -Force
    # xLODGen's own LODGen input beside its output: the mesh pass reads it, whenever it runs
    Copy-Item "$Tools\xlodgen\xLODGen\Edit Scripts\LODGen_Terrain_$World.txt" "$Work\out\terrain-lodgen-input.txt" -Force
    Set-ToolKey terrain
    }
    # our own pass over xLODGen's output, rerunnable alone: the counts, the world rule, the mesh pass, the link
    $n = (Get-ChildItem $Out.terrain -Recurse -File -Include *.btr, *.dds).Count; Say "terrain: $n files"
    if (-not $n) { throw 'terrain: no .btr or .dds written' }
    Assert-Terrain-Ours
    Set-TerrainMeshes
    Link-Into-Data $Out.terrain   # DynDOLOD culls object LOD below the terrain LOD
    Set-OutputKey terrain
  }
  'texgen' {
    if (-not (Tool-Stands texgen)) {
    Clear-Output texgen
    Lay-DynDOLOD-Data
    Set-TexGen-Output
    $p = Start-Tool texgen ($Paths + " -o:`"$($Out.texgen)\`"")
    $main = Main-Window $p
    Find-Control $p 'Start' '*Button*' 600 | Out-Null
    Dump $p 'options'
    Click $p 'Start'
    Measure-Run $p { $null = Watch-Popups $p $main; (Tool-Text $p) -match 'TexGen completed successfully' }
    $t1 = Get-Date  # as terrain: re-read until the finish line is there (close-8, 20:39), not once
    do { $txt = Tool-Text $p; if ($txt -match 'completed successfully') { break }; Start-Sleep 5 } while (((Get-Date) - $t1).TotalMinutes -lt 10)
    Set-Content "$Work\logs\texgen-messages.txt" $txt
    if ($txt -notmatch [regex]::Escape("Creating billboard $($Out.texgen)\")) { $p | Stop-Process -Force; throw "texgen: it did not write under $($Out.texgen) (its preset's OutputPath)" }
    if ($txt -notmatch 'completed successfully') { $p | Stop-Process -Force; throw 'texgen: did not complete' }
    Set-ToolKey texgen   # TexGen's output is whole once it says so; leaving the tool is ours
    try { Click $p 'Exit TexGen' } catch { Say 'no Exit TexGen button: the tool is stopped' }
    if (-not $p.WaitForExit(120000)) { $p | Stop-Process -Force }
    }
    # our own pass over TexGen's output, rerunnable alone: every planned billboard is there by form id, then the link
    $missing = @(foreach ($f in Get-ChildItem $Work -File -Filter 'DynDOLOD_SSE_TexGen_Billboards_*.txt') { foreach ($l in Get-Content $f.FullName) {
      $q = $l -split '[;,]'; if ($q.Count -lt 3) { continue }
      if (-not (Get-ChildItem "$($Out.texgen)\textures\terrain\lodgen\$($q[0])" -Filter "*_$($q[1]).dds" -EA SilentlyContinue)) { "$($q[2]) ($($q[0]) $($q[1]))" } } })
    Say "texgen: billboards missing for $($missing.Count) planned bases $($missing -join ', ')"
    if ($missing.Count) { throw "texgen: no billboard for $($missing.Count) planned bases: $($missing -join ', ')" }
    Link-Into-Data $Out.texgen
    Set-OutputKey texgen
  }
  'dyndolod' {
    # A DynDOLOD already running (the build VM that drove it rebooted: ten spot interruptions on 2026-11-03) is
    # attached, not restarted: its 35 minutes carry on and this step only waits for its finish.
    $p = Get-Process DynDOLODx64 -EA SilentlyContinue | Select -First 1
    if ($p) { Say "attach: DynDOLOD already running (pid $($p.Id) since $($p.StartTime.ToString('HH:mm:ss'))): waiting for it"; $main = Main-Window $p }
    else {
    Clear-Output dyndolod   # no half-written output of a stopped run is collected
    Set-DynDOLOD-Worlds
    Lay-DynDOLOD-Data
    Lay-LodModels
    $p = Start-Tool dyndolod ($Paths + " -o:`"$($Out.dyndolod)\`"")
    $main = Main-Window $p
    # The load's pop-ups (DLL/Scripts not found: Ignore; Resources) come before the wizard: watch them while waiting,
    # else a known dialog sits unanswered until the timeout (Paris, 14:47).
    $end = (Get-Date).AddSeconds(600); $adv = $null
    while (-not $adv -and (Get-Date) -lt $end -and -not $p.HasExited) {
      Watch-Popups $p $main
      try { $adv = Find-Control $p '*Advanced*' '' 5 } catch { $adv = $null }
    }
    if (-not $adv) { Dump $p 'no wizard'; throw 'dyndolod: no wizard in 600 s' }
    Dump $p 'wizard'
    Click $p '*Advanced*'
    Find-Control $p 'OK' '*Button*' 60 | Out-Null
    Pick-World $p
    Click $p $Preset; Start-Sleep 3          # the preset's settings (Advanced mode's Low/Medium/High buttons)
    # static LOD only: the boxes of lod-settings.json's dyndolod.untick make what only DynDOLOD's own plugins use
    # (dynamic LOD, occlusion data, the terrain underside), and this job never enables those plugins
    foreach ($c in @($Settings.dyndolod.untick)) { Set-Check $p $c $false }
    Dump $p 'before OK'
    Click $p 'OK'
    }
    $t0 = (Get-Date).AddMinutes(-1)
    # the finish line is read first: once it is there, the tool's own finish dialog is no pop-up for the watcher
    try { Measure-Run $p { if ((Tool-Text $p) -match 'generated successfully') { $true } else { $null = Watch-Popups $p $main; Assert-Only-Ours $t0; $false } } }
    catch { $p | Stop-Process -Force -EA SilentlyContinue; Get-Process LODGen*, Texconv* -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue; throw }
    Assert-Only-Ours $t0
    $t1 = Get-Date  # as terrain: re-read until the finish line is there (close-8, 20:39), not once
    do { $txt = Tool-Text $p; if ($txt -match 'generated successfully') { break }; Start-Sleep 5 } while (((Get-Date) - $t1).TotalMinutes -lt 10)
    Set-Content "$Work\logs\dyndolod-messages.txt" $txt
    if ($txt -notmatch 'generated successfully') { $p | Stop-Process -Force; throw 'dyndolod: did not complete' }
    $bto = @(Get-ChildItem "$($Out.dyndolod)\meshes\terrain\$World\objects" -Filter *.bto -EA SilentlyContinue).Count
    Say "dyndolod: $bto object LOD files of $World under $($Out.dyndolod)"
    if (-not $bto) { $p | Stop-Process -Force; throw "dyndolod: no object LOD of $World under $($Out.dyndolod) (its preset's OutputPath)" }
    Set-OutputKey dyndolod   # the output is whole at the finish line: marked before the leaving of the tool, which is ours
    # the finish dialog (a few seconds after the finish line) offers 'Save and Exit' when plugins were made and
    # 'Exit DynDOLOD' when none were; waited for, so the tool is never stopped while it still writes
    $t1 = Get-Date; $exit = $null
    do { $exit = Controls $p | ? { [W]::Cls($_) -like '*Button*' -and ([W]::Text($_) -replace '&', '') -match '^(Save and Exit|Exit DynDOLOD|Exit)$' } | Select -First 1
         if (-not $exit) { Start-Sleep 3 } } while (-not $exit -and -not $p.HasExited -and ((Get-Date) - $t1).TotalSeconds -lt 180)
    Dump $p 'finish dialog'
    if ($exit) { Say "click '$([W]::Text($exit))'"; [void][W]::PostMessage($exit, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero) }
    elseif (-not $p.HasExited) { Say 'dyndolod: finished; no exit button in 180 s (the windows are dumped above): the tool is stopped' }
    if (-not $exit -or -not $p.WaitForExit(300000)) { $p | Stop-Process -Force -EA SilentlyContinue }
  }
  'collect' {
    # Skipped when the mod already holds this collect (a resumed run re-copied it every time, 2026-11-03): the
    # sources' file count and the mod's file count are both what the last collect wrote to argonia-collect.count.
    $srcN = 0
    foreach ($d in 'Meshes', 'Textures') { if (Test-Path "$Res\$d") { $srcN += (Get-ChildItem "$Res\$d" -Recurse -File).Count } }
    foreach ($src in $Out.texgen, $Out.terrain, $Out.dyndolod) { if (Test-Path $src) { $srcN += (Get-ChildItem $src -Recurse -File).Count } }
    $mark = "$Mod\argonia-collect.count"
    foreach ($s in 'terrain', 'texgen', 'dyndolod') { if (-not (Test-Path "$Work\out\$s.key")) { throw "collect: the $s step has no finished output (no $Work\out\$s.key)" } }
    $stepKeys = (@('terrain', 'texgen', 'dyndolod') | % { "$_=$((Get-Content "$Work\out\$_.key" -Raw).Trim())" }) -join ','
    if (Test-Path $mark) {
      $was = (Get-Content $mark -Raw).Trim() -split ' '
      $modN = (Get-ChildItem $Mod -Recurse -File | ? { $_.Name -notin "argonia-collect.count", "argonia-lod.key" }).Count
      if ($was.Count -eq 3 -and [int]$was[0] -eq $srcN -and [int]$was[1] -eq $modN -and $was[2] -eq $stepKeys) {
        Say "collect: the mod already holds these outputs ($stepKeys; $modN files); skipped"
        Say "$Step OK"; exit 0
      }
    }
    # Lowest first: DynDOLOD Resources (its instruction: keep it installed with the output), TexGen, terrain, DynDOLOD.
    Remove-Item "$Mod\*" -Recurse -Force -EA SilentlyContinue
    foreach ($d in 'Meshes', 'Textures') { robocopy "$Res\$d" "$Mod\$d" /E /NFL /NDL /NJH /NJS /NP | Out-Null }
    foreach ($src in $Out.texgen, $Out.terrain, $Out.dyndolod) {
      if (Test-Path $src) { robocopy $src $Mod /E /NFL /NDL /NJH /NJS /NP | Out-Null }
    }
    # only this world's LOD: another world's (a tool that also made Tamriel) would override that world in the profile
    $ow = @(foreach ($o in $Out.Values) { foreach ($d in 'meshes\terrain', 'textures\terrain') {
      Get-ChildItem "$o\$d" -Directory -EA SilentlyContinue | % Name } }) | ? { $_ -ne $World } | Sort -Unique
    $other = Get-ChildItem $Mod -Recurse -File | ? { $r = $_.FullName.Substring($Mod.Length + 1)
      ($r -match '^(meshes|textures)\\terrain\\([^\\]+)\\' -and $Matches[2] -in $ow) -or ($_.Name -match '^DynDOLOD_(.+?)(_Alpha)?(_[a-z]+)?\.(dds|txt|json)$' -and $Matches[1] -in $ow) }
    if ($other) { Say "collect: $(@($other).Count) files of other worlds dropped"; $other | Remove-Item -Force }
    Get-ChildItem $Mod -Recurse -Include *.zip, *.log, *.txt -File | ? { $_.DirectoryName -eq $Mod } | Remove-Item -Force
    Lay-LodSettings
    $plugins = Get-ChildItem $Mod -File -Include *.esp, *.esm, *.esl -Recurse
    if ($plugins) { Say "plugins in the output (not enabled by this job): $($plugins.Name -join ', ')" }
    $files = Get-ChildItem $Mod -Recurse -File
    Set-Content $mark "$srcN $($files.Count) $stepKeys"
    Say "mod: $($files.Count) files, $([math]::Round(($files | Measure-Object Length -Sum).Sum / 1MB)) MB"
    & $Stack
    Say "laid again with the LOD folder"
  }
}
Say "$Step OK"

# LOD for ARG_Province on the game machine (2.W4 §c, decision 0014 §4): xLODGen terrain LOD, then TexGen and
# DynDOLOD object and tree LOD, into the MO2 mod "Argonia LOD (generated)". Derived files: never committed, never
# shipped. Driven by infra/gpu-box/lod.sh from the build VM; the GUI steps run in the desktop session (run.sh desktop).
#   lod.ps1 -Step prepare      the profile laid with no LOD, our ESMs (bridge.ps1 prepare -Fresh), DynDOLOD
#                              Resources linked into Data, old outputs cleared
#   lod.ps1 -Step terrain      xLODGen: terrain LOD (meshes and textures, every level) for ARG_Province
#   lod.ps1 -Step texgen       TexGen: the LOD textures and billboards of the laid trees and objects
#   lod.ps1 -Step dyndolod     DynDOLOD: object and tree LOD for ARG_Province from -Preset (Low or Medium)
#   lod.ps1 -Step collect      the outputs into the mod, then the profile laid again with it
#   lod.ps1 -Step survey -Tool xlodgen|texgen|dyndolod   start the tool, dump its windows, kill it (control names)
# None of the three tools has an unattended mode: xEdit's -autoload skips the plugin list, but the options dialog
# (worldspaces, presets, Start/OK) is modal with no switch past it (xEdit xeMainForm.pas mniNavGenerateLODClick:
# ShowModal unconditional). So each GUI step is driven by window messages (BM_CLICK, LB_SETCURSEL + WM_CHAR space,
# WM_SETTEXT) found by class and caption; every window is dumped to the log before it is touched, and an unknown
# pop-up stops the step (named in the log), never clicked blind.
# Every step writes C:\argonia\lod\metrics\<step>.json: wall seconds, peak working set of the tool's processes
# (the tool, LODGen, Texconv) summed per 2 s sample, the machine's lowest free physical memory, and the exit state.
param([Parameter(Mandatory)][ValidateSet('prepare', 'terrain', 'texgen', 'dyndolod', 'collect', 'survey')][string]$Step,
      [ValidateSet('xlodgen', 'texgen', 'dyndolod')][string]$Tool = 'xlodgen',
      [ValidateSet('Low', 'Medium')][string]$Preset = 'Medium',
      [string]$World = 'ARG_Province', [int]$TimeoutMin = 180)
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Data = "$Game\Data"
$Root = 'C:\argonia'
$Tools = "$Root\tools"
$Work = "$Root\lod"
$Mod = "$Root\MO2\mods\Argonia LOD (generated)"
$Prefs = "$env:LOCALAPPDATA\Skyrim Special Edition"
$Ini = "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\"
$Out = @{ terrain = "$Work\out\terrain"; texgen = "$Work\out\texgen"; dyndolod = "$Work\out\dyndolod" }
$Exe = @{ xlodgen = "$Tools\xlodgen\xLODGen\xLODGenx64.exe"; texgen = "$Tools\dyndolod\DynDOLOD\TexGenx64.exe"
          dyndolod = "$Tools\dyndolod\DynDOLOD\DynDOLODx64.exe" }
# DynDOLOD Resources is a FOMOD: only its required core (Meshes, Textures; its Scripts and Interface serve dynamic
# LOD, which this job does not make)
$Res = "$Tools\dyndolod-resources\00 DynDOLOD Core Files - Required"
New-Item -ItemType Directory -Force "$Work\logs", "$Work\metrics", $Mod | Out-Null
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
  # Unknown check states (owner-drawn): clear by the tools' documented default (only Tamriel, item 0, pre-checked)
  # then check ours; the log's "LOD for <worldspace>" lines are the proof of what ran.
  foreach ($j in @(0, $i)) {
    if ($j -eq 0 -and $items[0] -notmatch 'Tamriel') { continue }
    [void][W]::SendMessage($lb, 0x0186, [IntPtr]$j, [IntPtr]::Zero)  # LB_SETCURSEL
    [void][W]::SendMessage($lb, 0x0102, [IntPtr]0x20, [IntPtr]::Zero)  # WM_CHAR ' '
    Say "toggled item $j '$($items[$j])'"
  }
}
# Pop-ups: a known one gets its named answer; any other stops the step.
$Known = @(
  @{ match = 'DynDOLOD DLL|Scripts.*not found|DynDOLOD Resources'; answer = 'Ignore' }  # no dynamic LOD wanted (Sky-Claw #661)
  @{ match = 'stitched'; answer = 'Ignore' }
)
function Watch-Popups($proc, $main) {
  foreach ($t in [W]::Tops($proc.Id)) {
    if ($t -eq $main) { continue }
    $text = (@([W]::Text($t)) + @([W]::Kids($t) | % { [W]::Text($_) })) -join ' / '
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
  Say "start $($Exe[$name]) $argline"
  Start-Process $Exe[$name] -ArgumentList $argline -WorkingDirectory (Split-Path $Exe[$name]) -PassThru
}
$Paths = "-sse -autoload -d:`"$Data\`" -p:`"$Prefs\Plugins.txt`" -m:`"$Ini`""
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
function Link-Resources {  # into Data while the tools run
  foreach ($d in 'Meshes', 'Textures') { Link-Into-Data "$Res\$d" "\$d" }
}

switch ($Step) {
  'prepare' {
    & "$Root\infra\bridge.ps1" -Cmd kill | Out-Null
    Remove-Item "$Mod\*" -Recurse -Force -EA SilentlyContinue   # Data without any old LOD of ours
    foreach ($o in $Out.Values) { Remove-Item $o -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force $o | Out-Null }
    & "$Root\infra\bridge.ps1" -Cmd prepare -Fresh | Out-Null
    if (-not (Test-Path "$Data\ArgoniaWorld.esm")) { throw 'prepare: ArgoniaWorld.esm not in Data (make deploy first)' }
    Link-Resources
    Say "plugins: $((Get-Content "$Prefs\Plugins.txt") -join ', ')"
    $free = (Get-PSDrive C).Free; Say "C: free $([math]::Round($free / 1GB, 1)) GB"
    if ($free -lt 20GB) { throw 'prepare: under 20 GB free on C:' }
  }
  'survey' {
    $exeArgs = $Paths + $(if ($Tool -eq 'xlodgen') { ' -lodgen' } else { '' }) + " -o:`"$Work\out\survey\`""
    $p = Start-Tool $Tool $exeArgs
    $main = Main-Window $p; Start-Sleep 20; Dump $p 'after start'; Start-Sleep 40; Dump $p 'after a minute'
    $p | Stop-Process -Force
  }
  'terrain' {
    $p = Start-Tool xlodgen ($Paths + " -lodgen -o:`"$($Out.terrain)\`"")
    $main = Main-Window $p
    Find-Control $p 'Generate' '*Button*' 600 | Out-Null   # the options dialog, after the plugins load
    Dump $p 'options'
    Pick-World $p
    foreach ($c in 'Objects LOD', 'Trees LOD', 'Occlusion') { try { Set-Check $p $c $false } catch { Say "no '$c' box" } }
    Set-Check $p 'Terrain LOD' $true
    Dump $p 'before Generate'
    Click $p 'Generate'
    Measure-Run $p { Watch-Popups $p $main; (Tool-Text $p) -match 'LOD Generator: finished' }
    $txt = Tool-Text $p; Set-Content "$Work\logs\terrain-messages.txt" $txt
    $p | Stop-Process -Force
    if ($txt -notmatch "finished") { throw 'terrain: xLODGen did not finish' }
    $n = (Get-ChildItem $Out.terrain -Recurse -File -Include *.btr, *.dds).Count; Say "terrain: $n files"
    if (-not $n) { throw 'terrain: no .btr or .dds written' }
    Link-Into-Data $Out.terrain   # DynDOLOD culls object LOD below the terrain LOD
  }
  'texgen' {
    $p = Start-Tool texgen ($Paths + " -o:`"$($Out.texgen)\`"")
    $main = Main-Window $p
    Find-Control $p 'Start' '*Button*' 600 | Out-Null
    Dump $p 'options'
    Click $p 'Start'
    Measure-Run $p { Watch-Popups $p $main; (Tool-Text $p) -match 'TexGen completed successfully' }
    $txt = Tool-Text $p; Set-Content "$Work\logs\texgen-messages.txt" $txt
    if ($txt -notmatch 'completed successfully') { $p | Stop-Process -Force; throw 'texgen: did not complete' }
    Click $p 'Exit TexGen'; if (-not $p.WaitForExit(120000)) { $p | Stop-Process -Force }
    Link-Into-Data $Out.texgen
  }
  'dyndolod' {
    $p = Start-Tool dyndolod ($Paths + " -o:`"$($Out.dyndolod)\`"")
    $main = Main-Window $p
    Find-Control $p '*Advanced*' '' 600 | Out-Null
    Dump $p 'wizard'
    Click $p '*Advanced*'
    Find-Control $p 'OK' '*Button*' 60 | Out-Null
    Pick-World $p
    Click $p $Preset; Start-Sleep 3          # the preset's settings (Advanced mode's Low/Medium/High buttons)
    try { Set-Check $p 'Generate DynDOLOD' $false } catch { Say "no 'Generate DynDOLOD' box" }   # static LOD only: no plugins, no scripts
    Dump $p 'before OK'
    Click $p 'OK'
    Measure-Run $p { Watch-Popups $p $main; (Tool-Text $p) -match 'generated successfully' }
    $txt = Tool-Text $p; Set-Content "$Work\logs\dyndolod-messages.txt" $txt
    if ($txt -notmatch 'generated successfully') { $p | Stop-Process -Force; throw 'dyndolod: did not complete' }
    Click $p 'Save & Exit'; if (-not $p.WaitForExit(300000)) { $p | Stop-Process -Force }
  }
  'collect' {
    # Lowest first: DynDOLOD Resources (its instruction: keep it installed with the output), TexGen, terrain, DynDOLOD.
    Remove-Item "$Mod\*" -Recurse -Force -EA SilentlyContinue
    foreach ($d in 'Meshes', 'Textures') { robocopy "$Res\$d" "$Mod\$d" /E /NFL /NDL /NJH /NJS /NP | Out-Null }
    foreach ($src in $Out.texgen, $Out.terrain, $Out.dyndolod) {
      if (Test-Path $src) { robocopy $src $Mod /E /NFL /NDL /NJH /NJS /NP | Out-Null }
    }
    Get-ChildItem $Mod -Recurse -Include *.zip, *.log, *.txt -File | ? { $_.DirectoryName -eq $Mod } | Remove-Item -Force
    $plugins = Get-ChildItem $Mod -File -Include *.esp, *.esm, *.esl -Recurse
    if ($plugins) { Say "plugins in the output (not enabled by this job): $($plugins.Name -join ', ')" }
    $files = Get-ChildItem $Mod -Recurse -File
    Say "mod: $($files.Count) files, $([math]::Round(($files | Measure-Object Length -Sum).Sum / 1MB)) MB"
    & "$Root\infra\bridge.ps1" -Cmd prepare -Fresh | Out-Null
    Say "laid again with the LOD mod"
  }
}
Say "$Step OK"

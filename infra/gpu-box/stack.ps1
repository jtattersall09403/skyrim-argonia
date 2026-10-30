# The Argonia profile on the game machine (chunk 0.2 §b), laid over Data and taken off exactly. stack.py stages and
# pushes C:\argonia\MO2\mods\<id>\ and the profile; this script does the machine's half.
#   stack.ps1 off                  Data back to the vanilla install exactly (every file not in vanilla-data-files.txt
#                                  removed, Plugins.txt cleared)
#   stack.ps1 on                   off, then every mod in the profile's modlist hard-linked into Data, lowest priority
#                                  first (a later mod's file replaces an earlier one), the controlmap, Plugins.txt
#   stack.ps1 pandora              on, Pandora run on that Data into the pandora-output mod, then on again (desktop session)
#   stack.ps1 menu                 launch through SKSE, wait for the main menu, keep a still, print SKSE's plugin lines
#   stack.ps1 verify [-Full]       every laid file's hash against installed.json (cached by size and mtime; -Full rehashes)
#   stack.ps1 play-vanilla | play-modded [-Wait]   switch, then launch (the owner's stream cards)
param([Parameter(Mandatory)][string]$Cmd, [switch]$Wait, [switch]$Full)
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Data = "$Game\Data"
$Root = 'C:\argonia'
$Mo2 = "$Root\MO2"
$Profile = "$Mo2\profiles\Argonia"
$State = "$Root\stack-state"
$Prefs = "$env:LOCALAPPDATA\Skyrim Special Edition"
New-Item -ItemType Directory -Force $State, $Prefs | Out-Null

# Files the game or a mod writes into Data and must keep across off/on (else Community Shaders greets every launch
# as a new install): saved under $State\keep by off, put back by on, never hashed by verify.
$Keep = @('SKSE\Plugins\CommunityShaders\SettingsUser.json', 'SKSE\Plugins\CommunityShaders\SettingsDefault.json',
          'SKSE\Plugins\CommunityShaders_ImGui.ini')

function Get-Mode { if (Test-Path "$State\mode-on") { 'on' } else { 'off' } }

# Skyrim fills the current desktop (sunshine-prep.ps1 sized it to the client) and keeps running without focus,
# so a reconnect or a click elsewhere never pauses it.
function Set-GameWindow {
  # The display's real pixels (Screen.Bounds is DPI-scaled), from the mode sunshine-prep.ps1 set.
  . C:\argonia\infra\display.ps1 -Cmd modes
  Add-Type -AssemblyName System.Windows.Forms
  $cur = Get-CurrentMode ([System.Windows.Forms.Screen]::AllScreens | ? Primary).DeviceName
  $b = @{ Width = $cur.W; Height = $cur.H }
  $docs = "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition"
  $set = {
    param($file, $section, $values)
    # The key is set inside its own section, and a copy of it under any other section is dropped: the first match
    # anywhere had put bShowCompass=0 under [Display], and the game kept [Interface]'s bShowCompass=1 (game-7).
    $lines = [System.Collections.Generic.List[string]](Get-Content $file)
    foreach ($k in $values.Keys) {
      $pat = "^$([regex]::Escape($k))="
      $cur = ''; $keep = [System.Collections.Generic.List[string]]::new()
      foreach ($l in $lines) { if ($l -match '^\[(.+)\]$') { $cur = $Matches[1] }; if (-not ($l -match $pat -and $cur -ne $section)) { $keep.Add($l) } }
      $lines = $keep
      $s = $lines.IndexOf("[$section]"); if ($s -lt 0) { $lines.Add("[$section]"); $s = $lines.Count - 1 }
      $e = $s + 1; while ($e -lt $lines.Count -and -not ($lines[$e] -match '^\[')) { $e++ }
      $i = -1; for ($j = $s + 1; $j -lt $e; $j++) { if ($lines[$j] -match $pat) { $i = $j; break } }
      if ($i -ge 0) { $lines[$i] = "$k=$($values[$k])" } else { $lines.Insert($s + 1, "$k=$($values[$k])") }
    }
    $lines | Set-Content $file -Encoding ASCII
  }
  & $set "$docs\SkyrimPrefs.ini" 'Display' @{ 'iSize W' = $b.Width; 'iSize H' = $b.Height; 'bFull Screen' = 0; 'bBorderless' = 1 }
  & $set "$docs\Skyrim.ini" 'General' @{ 'bAlwaysActive' = 1 }
  # No compass and no quest marker (1.2 §a, Morrowind's way): the player finds places by the chart and directions.
  & $set "$docs\SkyrimPrefs.ini" 'Interface' @{ 'bShowCompass' = 0 }
  & $set "$docs\SkyrimPrefs.ini" 'GamePlay' @{ 'bShowQuestMarkers' = 0; 'bShowFloatingQuestMarkers' = 0 }
  # Skyrim does not declare DPI awareness, so on a scaled desktop Windows enlarges its window past the screen edge.
  $layers = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
  New-Item -Path $layers -Force | Out-Null
  Set-ItemProperty -Path $layers -Name "$Game\SkyrimSE.exe" -Value '~ HIGHDPIAWARE'
  # Third person only (owner, 2026-10-29): scrolling in stops before first person.
  & $set "$docs\Skyrim.ini" 'Camera' @{ 'fMinCurrentZoom' = '0.1' }
  # The Papyrus log, so a smoke run can read script errors (a missing native from a cut helper mod reads
  # "Unable to bind" or "Cannot call"); a dev machine's setting, never a player's.
  & $set "$docs\Skyrim.ini" 'Papyrus' @{ 'bEnableLogging' = 1; 'bEnableTrace' = 1; 'bLoadDebugInformation' = 1 }
}

function Focus-Skyrim {
  $p = Get-Process SkyrimSE -EA SilentlyContinue | Select -First 1
  if (-not $p) { return $false }
  Add-Type @'
using System; using System.Runtime.InteropServices;
public static class Fg { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c); }
'@
  [void][Fg]::ShowWindow($p.MainWindowHandle, 9); [void][Fg]::SetForegroundWindow($p.MainWindowHandle)
  return $true
}

switch ($Cmd) {
  'on' {
    if (Get-Process SkyrimSE -EA SilentlyContinue) { throw 'Skyrim is running; quit it first' }
    & $PSCommandPath off | Out-Null
    Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class HL {
      [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
      public static extern bool CreateHardLink(string link, string target, IntPtr sa); }'
    $order = @(Get-Content "$Profile\modlist.txt" | ? { $_ -like '+*' } | % { $_.Substring(1) })
    [array]::Reverse($order)  # modlist.txt lists the highest priority first; lay the lowest first
    $n = 0
    foreach ($m in $order) {
      $src = "$Mo2\mods\$m"
      if (-not (Test-Path $src)) { continue }
      foreach ($f in [IO.Directory]::EnumerateFiles($src, '*', 'AllDirectories')) {
        $dst = "\\?\$Data" + $f.Substring($src.Length)
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst))
        if ([IO.File]::Exists($dst)) { [IO.File]::Delete($dst) }
        if (-not [HL]::CreateHardLink($dst, "\\?\$f", [IntPtr]::Zero)) { throw "link failed: $f" }
        $n++
      }
    }
    # SKSE's loader and DLLs beside the game (inert unless launched through skse64_loader.exe)
    if (Test-Path "$Mo2\root") { Copy-Item "$Mo2\root\*" $Game -Force }
    # the gamepad layout (controlmap.py makes it from the player's own Interface archive): loose in Data, which
    # Skyrim reads over its archive; ControlMap_Custom.txt in My Games was not read (2026-10-29)
    if (Test-Path "$Root\controls\controlmap.txt") {
      New-Item -ItemType Directory -Force "$Data\Interface\Controls\PC" | Out-Null
      Copy-Item "$Root\controls\controlmap.txt" "$Data\Interface\Controls\PC\controlmap.txt" -Force
    }
    foreach ($k in $Keep) { if (Test-Path "$State\keep\$k") {
      Remove-Item -LiteralPath "$Data\$k" -Force -EA SilentlyContinue   # never write through a hard link into a mod
      New-Item -ItemType Directory -Force (Split-Path "$Data\$k") | Out-Null; Copy-Item "$State\keep\$k" "$Data\$k" -Force } }
    # Community Shaders' first-run modal ("choose a hotkey ... Press Escape or Enter") takes no scripted key, so a
    # fresh profile starts with its setup marked done (Menu.FirstTimeSetupCompleted, read over SettingsDefault.json)
    $csUser = "$Data\SKSE\Plugins\CommunityShaders\SettingsUser.json"
    if ((Test-Path "$Data\SKSE\Plugins\CommunityShaders.dll") -and -not (Test-Path $csUser)) {
      New-Item -ItemType Directory -Force (Split-Path $csUser) | Out-Null
      '{"Menu":{"FirstTimeSetupCompleted":true}}' | Set-Content $csUser -Encoding ASCII
    }
    Copy-Item "$Profile\plugins.txt" "$Prefs\Plugins.txt" -Force
    New-Item -ItemType File -Force "$State\mode-on" | Out-Null
    "argonia profile on: $n files from $($order.Count) mods"
  }
  'off' {
    # Independent of any record: everything in Data that the vanilla install does not have goes (the game's own
    # shader cache stays). Vanilla Data has no loose files the mods replace, so nothing needs restoring.
    if (Get-Process SkyrimSE -EA SilentlyContinue) { throw 'Skyrim is running; quit it first' }
    foreach ($k in $Keep) { if (Test-Path "$Data\$k") {
      New-Item -ItemType Directory -Force (Split-Path "$State\keep\$k") | Out-Null; Copy-Item "$Data\$k" "$State\keep\$k" -Force } }
    $vanilla = @{}; Get-Content "$Root\infra\vanilla-data-files.txt" | % { $vanilla[$_.ToLower()] = 1 }
    $removed = 0
    # The \\?\ form reaches paths that ordinary Windows paths cannot (names ending in a dot or space); .NET's
    # enumeration, not cmd's dir, whose OEM code page mangled non-ASCII names so they were never removed (2026-10-29).
    foreach ($f in @([IO.Directory]::EnumerateFiles("\\?\$Data", '*', 'AllDirectories'))) {
      $rel = $f.Substring($f.IndexOf('\Data\') + 6).ToLower()
      if ($vanilla[$rel] -or $rel.StartsWith('shadercache\')) { continue }
      try { [IO.File]::SetAttributes($f, 'Normal'); [IO.File]::Delete($f); $removed++ } catch { "not removed: $rel ($($_.Exception.Message))" }
    }
    Get-ChildItem $Data -Recurse -Directory | Sort { $_.FullName.Length } -Descending |
      ? { -not (Get-ChildItem -LiteralPath $_.FullName -Force) } | % { Remove-Item -LiteralPath ("\\?\" + $_.FullName) -Force }
    Remove-Item "$Prefs\Plugins.txt", "$State\mode-on" -Force -EA SilentlyContinue
    "argonia profile off (vanilla): $removed files removed"
  }
  'pandora' {
    # Pandora (a GUI app: run in the desktop session) writes to the outputPath in its Settings.json and, with
    # --auto_run, patches the mods cached in <output>\Pandora_Engine\ActiveMods.json (code, active, priority).
    $out = "$Mo2\mods\pandora-output"; Remove-Item $out -Recurse -Force -EA SilentlyContinue
    & $PSCommandPath on | Out-Null   # Data must be this profile without an older output
    New-Item -ItemType Directory -Force "$out\Pandora_Engine" | Out-Null
    $tool = "$Mo2\tools\pandora"
    $settings = @{ app = @{ theme = 0 }; games = @{ SkyrimSE = @{ gameDataPath = $Data; outputPath = $out } } }
    $settings | ConvertTo-Json -Depth 5 | Set-Content "$tool\Settings.json" -Encoding ASCII
    $codes = @(Get-ChildItem "$Data\Nemesis_Engine\mod", "$Data\Pandora_Engine\mod" -Directory -EA SilentlyContinue | % Name)
    $i = 0; $entries = foreach ($c in $codes) { [ordered]@{ code = $c; active = $true; priority = ++$i } }
    ConvertTo-Json @($entries) | Set-Content "$out\Pandora_Engine\ActiveMods.json" -Encoding ASCII
    $exe = Get-ChildItem $tool -Recurse -Filter 'Pandora Behaviour Engine+.exe' | Select -First 1
    $p = Start-Process $exe.FullName -WorkingDirectory $exe.DirectoryName -ArgumentList "--tesv:`"$Game`" --auto_run --auto_close" -PassThru
    if (-not $p.WaitForExit(600000)) { $p.Kill(); throw 'Pandora did not finish in 600 s' }
    $n = (Get-ChildItem "$out\meshes" -Recurse -File -EA SilentlyContinue).Count
    if ($n -eq 0) { throw "Pandora wrote no behaviours (exit $($p.ExitCode)); see $out\Engine.log" }
    Remove-Item "$out\Pandora_Engine" -Recurse -Force -EA SilentlyContinue
    Move-Item "$out\Engine.log" "$Root\logs\pandora-engine.log" -Force -EA SilentlyContinue
    & $PSCommandPath on | Out-Null
    "pandora: $n behaviour files from $($codes.Count) mods ($($codes -join ', '))"
  }
  'menu' {
    if (Get-Process SkyrimSE -EA SilentlyContinue) { Stop-Process -Name SkyrimSE -Force; Start-Sleep 3 }
    if (-not (Test-Path "$State\mode-on")) { & $PSCommandPath on | Out-Null }
    $skse = "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE"
    Remove-Item "$skse\skse64.log" -EA SilentlyContinue
    $crashes = @(Get-ChildItem "$skse\crash-*.log" -EA SilentlyContinue).Count
    Set-GameWindow
    $t0 = Get-Date
    Start-Process "$Game\skse64_loader.exe" -WorkingDirectory $Game
    $ok = $false
    for ($i = 0; $i -lt 300; $i++) {
      Start-Sleep 1
      if ((Test-Path "$skse\skse64.log") -and (Select-String -Path "$skse\skse64.log" -Pattern 'dispatch message \(8\)' -Quiet)) { $ok = $true; break }
      if ($i -gt 30 -and -not (Get-Process SkyrimSE -EA SilentlyContinue)) { break }
    }
    if ($ok) { Start-Sleep 15; & C:\argonia\infra\grab.ps1 C:\argonia\logs\menu.png | Out-Null }
    $alive = [bool](Get-Process SkyrimSE -EA SilentlyContinue)
    "data loaded after $([int]((Get-Date) - $t0).TotalSeconds) s; running: $alive"
    Get-Content "$skse\skse64.log" -EA SilentlyContinue | ? { $_ -match '^plugin ' }
    $new = @(Get-ChildItem "$skse\crash-*.log" -EA SilentlyContinue | Sort LastWriteTime)
    if ($new.Count -gt $crashes) { "CRASH: $($new[-1].Name)"; Get-Content $new[-1].FullName -TotalCount 40 }
    elseif ($ok -and $alive) { 'MAIN-MENU OK' }
    if (-not $env:ARGONIA_KEEP) { Stop-Process -Name SkyrimSE -Force -EA SilentlyContinue }
  }
  'verify' {
    # Fast and visible (2026-10-29: the serial pass printed nothing for 17 min over 69k files). A file whose size
    # and mtime match the hash cache of the last pass takes its cached hash (a hard link shares both with its mod
    # file, so the cache holds across off/on); the rest are hashed on every core, with progress every 500.
    # -Full ignores the cache.
    $t0 = Get-Date
    $inst = Get-Content "$Mo2\installed.json" -Raw -Encoding UTF8 | ConvertFrom-Json  # 5.1 reads ANSI otherwise
    $rec = @{}; foreach ($p in $inst.files.PSObject.Properties) { $rec[$p.Name.ToLower()] = $p.Value }
    $cacheFile = "$State\hashcache.tsv"; $cache = @{}
    if (-not $Full -and (Test-Path $cacheFile)) {
      foreach ($l in [IO.File]::ReadLines($cacheFile)) { $c = $l.Split("`t"); if ($c.Count -eq 4) { $cache[$c[0]] = $c } } }
    Add-Type -TypeDefinition @'
using System; using System.IO; using System.Security.Cryptography; using System.Threading; using System.Threading.Tasks;
public static class ParHash {
  public static string[] Run(string[] paths, int every) {
    var res = new string[paths.Length]; int done = 0;
    Parallel.For(0, paths.Length, new ParallelOptions { MaxDegreeOfParallelism = 8 }, i => {
      try {
        using (var s = new FileStream(paths[i], FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete, 1 << 20))
        using (var h = SHA256.Create()) res[i] = BitConverter.ToString(h.ComputeHash(s)).Replace("-", "").ToLower();
      } catch (Exception e) { res[i] = "error: " + e.Message; }
      int d = Interlocked.Increment(ref done);
      if (d % every == 0) Console.WriteLine("hashed " + d + " of " + paths.Length);
    });
    return res;
  }
}
'@
    # Pandora's outputs replace some mods' behaviour files in Data: those paths hold Pandora's file, not the mod's;
    # the generated LOD (lod.ps1) is made on the machine too, so neither is in installed.json
    $pandora = @{}; foreach ($gen in 'pandora-output', 'Argonia LOD (generated)') { if (Test-Path "$Mo2\mods\$gen") {
      Get-ChildItem "$Mo2\mods\$gen" -Recurse -File | % { $pandora[$_.FullName.Substring("$Mo2\mods\$gen\".Length).ToLower()] = 1 } } }
    $bad = 0; $n = 0; $todo = New-Object System.Collections.Generic.List[object]; $hits = 0
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($k in $rec.Keys) {
      if ($k.StartsWith('..\')) { $f = "\\?\$Game\" + $k.Substring(3) } else { $f = "\\?\$Data\" + $k }
      $n++
      if ($pandora[$k]) { continue }
      $fi = New-Object IO.FileInfo $f
      if (-not $fi.Exists) { "missing: $k"; $bad++; continue }
      $c = $cache[$k]
      if ($c -and $c[1] -eq "$($fi.Length)" -and $c[2] -eq "$($fi.LastWriteTimeUtc.Ticks)") {
        $hits++; if ($c[3] -ne $rec[$k][1]) { "differs: $k ($($rec[$k][0]))"; $bad++ }
        $out.Add(($c -join "`t")); continue }
      $todo.Add(@($k, $f, $fi.Length, $fi.LastWriteTimeUtc.Ticks))
    }
    "$n recorded: $hits from the cache, $($todo.Count) to hash ($([int]((Get-Date) - $t0).TotalSeconds) s)"
    if ($todo.Count) {
      $hs = [ParHash]::Run([string[]]($todo | % { $_[1] }), 500)
      for ($i = 0; $i -lt $todo.Count; $i++) {
        $k = $todo[$i][0]
        if ($hs[$i] -ne $rec[$k][1]) { "differs: $k ($($rec[$k][0])) $($hs[$i])"; $bad++ }
        if (-not $hs[$i].StartsWith('error')) { $out.Add("$k`t$($todo[$i][2])`t$($todo[$i][3])`t$($hs[$i])") }
      }
      [IO.File]::WriteAllLines($cacheFile, $out)  # UTF-8, as ReadLines reads it
    }
    $vanilla = @{}; Get-Content "$Root\infra\vanilla-data-files.txt" | % { $vanilla[$_.ToLower()] = 1 }
    $keepSet = @{}; $Keep | % { $keepSet[$_.ToLower()] = 1 }
    $extra = 0
    # .NET's enumeration, not cmd's dir: dir prints in the OEM code page, which mangles non-ASCII names
    foreach ($f in [IO.Directory]::EnumerateFiles("\\?\$Data", '*', 'AllDirectories')) {
      $rel = $f.Substring($f.IndexOf('\Data\') + 6).ToLower()
      if ($vanilla[$rel] -or $pandora[$rel] -or $rec[$rel] -or $keepSet[$rel] -or $rel.StartsWith('shadercache\') -or $rel.StartsWith('mcm\settings\') -or $rel -eq 'interface\controls\pc\controlmap.txt' -or $rel -eq 'skse\plugins\argoniabridge.dll' -or $rel -eq 'skse\plugins\argoniacore.dll' -or
          ($rel -match '^skse\\(plugins\\[^\\]+\.ini|[^\\]+\.log)$')) { continue }  # inis and logs the plugins write at first run
      "unrecorded: $rel"; $extra++
    }
    "$n recorded files checked, $bad bad, $extra unrecorded, $($pandora.Count) Pandora outputs, $([int]((Get-Date) - $t0).TotalSeconds) s"
    if ($bad -eq 0 -and $extra -eq 0) { 'VERIFY OK' }
  }
  { $_ -in 'play-vanilla', 'play-modded' } {
    # Already running (a reconnect, or the other card): bring it to the front; never start a second copy.
    if (Focus-Skyrim) {
      'Skyrim already running: brought to the front'
      if ($Wait) { while (Get-Process SkyrimSE -EA SilentlyContinue) { Start-Sleep 2 } }
      break
    }
    Set-GameWindow
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-ExecutionPolicy', 'Bypass', '-File', "$Root\infra\splash.ps1"
    if ($Cmd -eq 'play-vanilla') { & $PSCommandPath off; Start-Process "$Game\SkyrimSE.exe" -WorkingDirectory $Game }
    else { & $PSCommandPath on; Start-Process "$Game\skse64_loader.exe" -WorkingDirectory $Game }
    if ($Wait) {
      for ($i = 0; $i -lt 60 -and -not (Get-Process SkyrimSE -EA SilentlyContinue); $i++) { Start-Sleep 1 }
      while (Get-Process SkyrimSE -EA SilentlyContinue) { Start-Sleep 2 }
    }
  }
  default { throw "unknown command $Cmd" }
}

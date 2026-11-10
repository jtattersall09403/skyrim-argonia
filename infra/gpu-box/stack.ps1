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
#   stack.ps1 play-newworld [-Wait]  the same for the NewWorld profile (its own card, "Argonia: New World")
#   -World Argonia|NewWorld        the profile on/verify/menu use (default: the one laid last, else Argonia). NewWorld
#                                  is Argonia's stack plus the new-world rows, with ours\newworld\ArgoniaNewWorld.esm last
#   stack.ps1 play-modded -Shaders on|off [-Wait]   the same with Community Shaders' DLL laid or set aside (the
#                                  owner's on/off comparison, #16); the next `on` lays it again (exact undo)
param([Parameter(Mandatory)][string]$Cmd, [switch]$Wait, [switch]$Full, [ValidateSet('', 'on', 'off')][string]$Shaders = '',
      [ValidateSet('', 'Argonia', 'NewWorld')][string]$World = '')
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Data = "$Game\Data"
$Root = 'C:\argonia'
$Mo2 = "$Root\MO2"
$State = "$Root\stack-state"
if (-not $World) { $World = if (Test-Path "$State\world") { (Get-Content "$State\world" -TotalCount 1).Trim() } else { 'Argonia' } }
$Profile = "$Mo2\profiles\$World"
$Installed = if ($World -eq 'Argonia') { "$Mo2\installed.json" } else { "$Mo2\installed-$World.json" }
# our own plugins this profile lays last, in order (Argonia.esp; the new world's master after it)
$OursPlugins = @(@{ name = 'Argonia.esp'; src = "$Root\ours\Argonia.esp" })
if ($World -eq 'NewWorld') { $OursPlugins += @{ name = 'ArgoniaNewWorld.esm'; src = "$Root\ours\newworld\ArgoniaNewWorld.esm" } }
# the place layer (places_deploy.sh): Helstrom and the other built places, an ESP over the world ESM, last
if ($World -eq 'NewWorld') { $OursPlugins += @{ name = 'ArgoniaNWPlaces.esp'; src = "$Root\ours\newworld\ArgoniaNWPlaces.esp" } }
# derived folders laid over every mod (decision 0014): ours\derived\<name> in both worlds; ours\derived-NewWorld\<name>
# (the new world's LOD, infra/gpu-box/lod.sh) in the NewWorld profile only
$Derived = @("$Root\ours\derived") + @(if ($World -eq 'NewWorld') { "$Root\ours\derived-NewWorld" })
$Prefs = "$env:LOCALAPPDATA\Skyrim Special Edition"
New-Item -ItemType Directory -Force $State, $Prefs | Out-Null

# Files the game or a mod writes into Data and must keep across off/on (else Community Shaders greets every launch
# as a new install): saved under $State\keep by off, put back by on, never hashed by verify.
$Keep = @('SKSE\Plugins\CommunityShaders\SettingsUser.json', 'SKSE\Plugins\CommunityShaders\SettingsDefault.json',
          'SKSE\Plugins\CommunityShaders_ImGui.ini')

function Get-Mode { if (Test-Path "$State\mode-on") { 'on' } else { 'off' } }
function Wait-Steam {
  # Steam restarts itself to apply an update about 5–6 min after a boot (bootstrap_log "Checking for available
  # updates" then "Startup"); every launch before that died within 30 s with no SKSE log, every launch after it
  # lived (2026-11-02, nine launches). So: the client (steamwebhelper) must be up and steam.exe itself at least
  # 150 s old; a Steam restart resets its start time and the wait begins again. Up to 12 min. Every launch path.
  # Steam gone altogether (its self-update restart sometimes never comes back: no steam.exe for an hour on Paris,
  # 2026-11-03 04:20, two launches lost to a 12 min wait): start it after 30 s without one.
  $w = 0; $age = 0
  while ($w -lt 720) {
    $st = Get-Process steam -EA SilentlyContinue | Sort-Object StartTime | Select-Object -First 1
    if (-not $st -and $w -ge 30) {
      $exe = "C:\Program Files (x86)\Steam\steam.exe"
      if (Test-Path $exe) { Start-Process $exe -ArgumentList '-silent'; "steam: not running, started it" }
    }
    $age = if ($st) { ((Get-Date) - $st.StartTime).TotalSeconds } else { 0 }
    if ($st -and (Get-Process steamwebhelper -EA SilentlyContinue) -and $age -ge 150) { break }
    Start-Sleep 5; $w += 5
  }
  "steam: client up, steam.exe $([int]$age) s old, waited $w s"
}

# Skyrim fills the current desktop (sunshine-prep.ps1 sized it to the client) and keeps running without focus,
# so a reconnect or a click elsewhere never pauses it.
function Set-GameWindow {
  # The display's real pixels (Screen.Bounds is DPI-scaled), from the mode sunshine-prep.ps1 set.
  . C:\argonia\infra\display.ps1 -Cmd modes
  Add-Type -AssemblyName System.Windows.Forms
  $cur = Get-CurrentMode ([System.Windows.Forms.Screen]::AllScreens | ? Primary).DeviceName
  $b = @{ Width = $cur.W; Height = $cur.H }
  $docs = "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition"
  # A machine where the Skyrim launcher never ran has no ini files yet; make them as the launcher does, from the game's
  # own presets (a fresh g4dn had none, and every card failed here, 2026-11-06).
  New-Item -ItemType Directory -Force $docs | Out-Null
  if (-not (Test-Path "$docs\SkyrimPrefs.ini")) { Copy-Item "$Game\High.ini" "$docs\SkyrimPrefs.ini" }
  if (-not (Test-Path "$docs\Skyrim.ini")) { Copy-Item "$Game\Skyrim_Default.ini" "$docs\Skyrim.ini" }
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
  # the auto-vanity camera: after fAutoVanityModeDelay seconds idle the camera orbits the player and no first-person
  # switch takes; never in the studio
  & $set "$docs\Skyrim.ini" 'Camera' @{ 'fAutoVanityModeDelay' = 1000000 }
  # The compass is on (owner walk 2026-11-07: "I need the compass so I can follow directions"); quest markers stay off
  # (below, Morrowind's way), so the compass shows places and directions but no quest target.
  & $set "$docs\SkyrimPrefs.ini" 'Interface' @{ 'bShowCompass' = 1 }
  # Light shafts: the engine's volumetric lighting, linked per weather (WTHR HNAM, lane 1.15-r6-light); off by default in the prefs the stack writes.
  & $set "$docs\SkyrimPrefs.ini" 'Display' @{ 'bVolumetricLightingEnable' = 1 }
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

# Processes that hold Data's files open: wait at most 30 s for them to exit, then fail naming them (game-12: the
# deploy's and LOD's fresh lay died on an IOException deleting SkyUI_SE.bsa that a leftover xLODGen held).
function Wait-DataFree {
  $names = 'SkyrimSE', 'skse64_loader', 'xLODGenx64', 'TexGenx64', 'DynDOLODx64', 'LODGenx64*', 'Texconv*'
  for ($i = 0; $i -lt 30; $i++) { if (-not (Get-Process $names -EA SilentlyContinue)) { return }; Start-Sleep 1 }
  $held = (Get-Process $names -EA SilentlyContinue | % { "$($_.ProcessName) ($($_.Id))" }) -join ', '
  throw "Data is held by $held after 30 s; quit or kill it first"
}

switch ($Cmd) {
  'on' {
    Wait-DataFree
    # Laid in place (game-12): what the profile lays is mapped first (the highest priority wins); a Data file that
    # already is that file (a hard link to it: the same length and write time) is left alone, so an unchanged file
    # is never deleted; everything else that is not vanilla goes, as `off` does.
    foreach ($k in $Keep) { if (Test-Path "$Data\$k") {
      New-Item -ItemType Directory -Force (Split-Path "$State\keep\$k") | Out-Null; Copy-Item "$Data\$k" "$State\keep\$k" -Force } }
    Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class HL {
      [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
      public static extern bool CreateHardLink(string link, string target, IntPtr sa); }'
    $order = @(Get-Content "$Profile\modlist.txt" | ? { $_ -like '+*' } | % { $_.Substring(1) })
    [array]::Reverse($order)  # modlist.txt lists the highest priority first; lay the lowest first
    $want = @{}
    foreach ($m in $order) {
      $src = "$Mo2\mods\$m"
      if (-not (Test-Path $src)) { continue }
      foreach ($f in [IO.Directory]::EnumerateFiles($src, '*', 'AllDirectories')) { $want[$f.Substring($src.Length).ToLower()] = $f }
    }
    # Derived folders (decision 0014: made at install on the build VM from the player's mods, sent by deploy.sh to
    # ours\derived\<name>, e.g. argonia-ground's textures with mips and normals): over every mod
    foreach ($d in @($Derived | % { Get-ChildItem $_ -Directory -EA SilentlyContinue })) {
      foreach ($f in [IO.Directory]::EnumerateFiles($d.FullName, '*', 'AllDirectories')) { $want[$f.Substring($d.FullName.Length).ToLower()] = $f } }
    $vanilla = @{}; Get-Content "$Root\infra\vanilla-data-files.txt" | % { $vanilla[$_.ToLower()] = 1 }
    $removed = 0
    foreach ($f in @([IO.Directory]::EnumerateFiles("\\?\$Data", '*', 'AllDirectories'))) {
      $rel = $f.Substring($f.IndexOf('\Data\') + 5).ToLower()   # with its leading \, as $want's keys
      if ($want.ContainsKey($rel) -or $vanilla[$rel.Substring(1)] -or $rel.StartsWith('\shadercache\')) { continue }
      [IO.File]::SetAttributes($f, 'Normal'); [IO.File]::Delete($f); $removed++
    }
    $n = 0; $kept = 0
    foreach ($rel in $want.Keys) {
      $f = $want[$rel]; $dst = "\\?\$Data" + $f.Substring($f.Length - $rel.Length)  # the mod's or derived folder's own case
      $a = [IO.FileInfo]::new("\\?\$f"); $b = [IO.FileInfo]::new($dst)
      if ($b.Exists -and $b.Length -eq $a.Length -and $b.LastWriteTimeUtc -eq $a.LastWriteTimeUtc) { $kept++; continue }
      [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst))
      if ($b.Exists) { [IO.File]::SetAttributes($dst, 'Normal'); [IO.File]::Delete($dst) }
      if (-not [HL]::CreateHardLink($dst, "\\?\$f", [IntPtr]::Zero)) { throw "link failed: $f" }
      $n++
    }
    Get-ChildItem $Data -Recurse -Directory | Sort { $_.FullName.Length } -Descending |
      ? { -not (Get-ChildItem -LiteralPath $_.FullName -Force) } | % { Remove-Item -LiteralPath ("\\?\" + $_.FullName) -Force }
    # SKSE's loader and DLLs beside the game (inert unless launched through skse64_loader.exe)
    if (Test-Path "$Mo2\root") { Copy-Item "$Mo2\root\*" $Game -Force }
    # the gamepad layout (a pad layout made on the machine, if any): loose in Data, which
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
    # Our own plugin (enabled, last in Plugins.txt), its ini and compiled scripts, laid with the profile so the laid
    # Data can be read back before any launch (2026-11-06; until then only the Argonia card's launch laid them).
    # Argonia.esp (decision 0038); the dead total conversion's ArgoniaWorld.esm/Argonia.esm are never laid.
    foreach ($o in $OursPlugins) { $e = $o.name; if (Test-Path $o.src) {
      Copy-Item $o.src "$Data\$e" -Force
      $lines = @(Get-Content "$Prefs\Plugins.txt" | ? { $_.TrimStart('*') -ne $e }); $lines += "*$e"
      $lines | Set-Content "$Prefs\Plugins.txt" -Encoding ASCII } }
    if (Test-Path "$Root\ours\Argonia.ini") { Copy-Item "$Root\ours\Argonia.ini" "$Data\Argonia.ini" -Force }
    $seq = @(Get-ChildItem "$Root\ours\SEQ\*.seq" -EA SilentlyContinue)   # its SEQ (Seq.cs): start-game quests a new game starts first
    if ($World -eq 'NewWorld') { $seq += @(Get-ChildItem "$Root\ours\newworld\SEQ\*.seq" -EA SilentlyContinue) }  # the place layer's
    if ($seq) { New-Item -ItemType Directory -Force "$Data\SEQ" | Out-Null; $seq | Copy-Item -Destination "$Data\SEQ" -Force }
    $pex = @(Get-ChildItem "$Root\ours\scripts\*.pex" -EA SilentlyContinue)
    if ($pex) { New-Item -ItemType Directory -Force "$Data\Scripts" | Out-Null; $pex | Copy-Item -Destination "$Data\Scripts" -Force }
    "argonia: $((Get-Content "$Prefs\Plugins.txt" | ? { $_.TrimStart('*') -in $OursPlugins.name }) -join ', '); $($pex.Count) .pex"
    New-Item -ItemType File -Force "$State\mode-on" | Out-Null
    Set-Content "$State\world" $World -Encoding ASCII
    "$World profile on: $n files laid, $kept already laid, $removed removed, from $($order.Count) mods"
  }
  'off' {
    # Independent of any record: everything in Data that the vanilla install does not have goes (the game's own
    # shader cache stays). Vanilla Data has no loose files the mods replace, so nothing needs restoring.
    Wait-DataFree
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
  'nemesis' {
    # Nemesis 0.84-beta (DSC sets B and B2 only: Pandora did not wire DSC's FNIS list, game-10). Its output goes in
    # the same pandora-output mod, so the profile, verify and pandora-check read it unchanged. Nemesis has no output
    # path: it writes into Data, and a file there is a hard link into a mod, so every file it may write is first made
    # a copy (never write through a link). Its own bundled patches (mod\tkuc and 15 more) are never laid: it
    # generates only the codes our stack laid.
    $out = "$Mo2\mods\pandora-output"; Remove-Item $out -Recurse -Force -EA SilentlyContinue
    & $PSCommandPath on -World $World | Out-Null
    $codes = @(Get-ChildItem "$Data\Nemesis_Engine\mod" -Directory -EA SilentlyContinue | % Name)
    $tool = "$Mo2\tools\nemesis\Nemesis_Engine"
    foreach ($f in [IO.Directory]::EnumerateFiles($tool, '*', 'AllDirectories')) {
      $rel = $f.Substring($tool.Length + 1)
      if ($rel -like 'mod\*') { continue }
      $dst = "$Data\Nemesis_Engine\$rel"; [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst))
      [IO.File]::Copy($f, $dst, $true)
    }
    $unlinked = 0
    foreach ($f in @([IO.Directory]::EnumerateFiles("$Data\meshes", '*', 'AllDirectories') | ? { $_ -match '\\(behaviors|characters|character assets)[^\\]*\\[^\\]+\.hkx$|\.txt$' }) +
                   @(Get-ChildItem "$Data\scripts" -Filter 'fnis*.pex' -EA SilentlyContinue | % FullName)) {
      $tmp = "$f.unlink"; [IO.File]::Copy($f, $tmp, $true); [IO.File]::Delete($f); [IO.File]::Move($tmp, $f); $unlinked++
    }
    $t0 = (Get-Date).ToUniversalTime().AddSeconds(-2)
    $exe = "$Data\Nemesis_Engine\Nemesis Unlimited Behavior Engine.exe"
    $log = "$Root\logs\pandora-engine.log"
    "engine: Nemesis 0.84-beta; codes $($codes -join ' '); $unlinked files made copies" | Set-Content $log
    foreach ($na in @('-update', ('-generate ' + ($codes -join ' ')))) {
      $p = Start-Process $exe -WorkingDirectory (Split-Path $exe) -ArgumentList $na -PassThru
      if (-not $p.WaitForExit(900000)) { $p.Kill(); "nemesis $na did not finish in 900 s" | Add-Content $log; throw "Nemesis $na did not finish in 900 s" }
      "nemesis $na exit $($p.ExitCode)" | Add-Content $log
    }
    Get-ChildItem "$Data\Nemesis_Engine" -Recurse -File -Include *.txt, *.log -EA SilentlyContinue |
      ? { $_.LastWriteTimeUtc -ge $t0 -and $_.FullName -notlike '*\mod\*' } |
      % { "== $($_.Name)"; Get-Content $_.FullName -TotalCount 400 } | Add-Content $log
    # Its output: every file in Data written since the run began, outside its own engine folder
    $n = 0
    foreach ($f in @([IO.Directory]::EnumerateFiles($Data, '*', 'AllDirectories'))) {
      $rel = $f.Substring($Data.Length + 1)
      if ($rel -like 'Nemesis_Engine\*' -or $rel -like 'shadercache\*') { continue }
      if ([IO.File]::GetLastWriteTimeUtc($f) -lt $t0 -and [IO.File]::GetCreationTimeUtc($f) -lt $t0) { continue }
      $dst = "$out\$rel"; [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst)); [IO.File]::Copy($f, $dst, $true); $n++
    }
    if ($n -eq 0) { throw "Nemesis wrote no behaviours; see $log" }
    & $PSCommandPath on -World $World | Out-Null
    "nemesis: $n output files from $($codes.Count) mods ($($codes -join ', '))"
  }
  'pandora' {
    if (Test-Path "$Mo2\tools\nemesis") { & $PSCommandPath nemesis; break }  # the DSC sets' engine (stack.py lays it)
    # Pandora (a GUI app: run in the desktop session) writes to the outputPath in its Settings.json and, with
    # --auto_run, patches the mods cached in <output>\Pandora_Engine\ActiveMods.json (code, active, priority).
    $out = "$Mo2\mods\pandora-output"; Remove-Item $out -Recurse -Force -EA SilentlyContinue
    & $PSCommandPath on -World $World | Out-Null   # Data must be this profile without an older output
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
    & $PSCommandPath on -World $World | Out-Null
    "pandora: $n behaviour files from $($codes.Count) mods ($($codes -join ', '))"
  }
  'menu' {
    if (Get-Process SkyrimSE -EA SilentlyContinue) { Stop-Process -Name SkyrimSE -Force; Start-Sleep 3 }
    if (-not (Test-Path "$State\mode-on")) { & $PSCommandPath on -World $World | Out-Null }
    # -Shaders on|off (round 5's sky A/B, 2026-11-03): only Community Shaders' DLL is laid or set aside, as the
    # play-modded cards do (its settings files stay).
    $cs = "$Data\SKSE\Plugins\CommunityShaders.dll"
    if ($Shaders -eq 'on' -and -not (Test-Path $cs)) {
      $src = Get-ChildItem "$Mo2\mods\*\SKSE\Plugins\CommunityShaders.dll" -EA SilentlyContinue | Select -First 1
      if ($src) { Copy-Item -LiteralPath $src.FullName $cs -Force; 'community shaders: on (DLL laid again)' } else { 'community shaders: on asked, DLL not in any mod' } }
    elseif ($Shaders -eq 'off' -and (Test-Path $cs)) { Remove-Item -LiteralPath $cs -Force; 'community shaders: off (DLL set aside)' }
    elseif ($Shaders) { "community shaders: $Shaders (already so)" }
    $skse = "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE"
    Remove-Item "$skse\skse64.log" -EA SilentlyContinue
    $crashes = @(Get-ChildItem "$skse\crash-*.log" -EA SilentlyContinue).Count
    Set-GameWindow
    # Steam restarts and self-updates after every boot; a launch inside that window dies silently with no SKSE log
    # (2026-11-02, three launches 2 min after boot). Wait for the client proper (steamwebhelper) before launching.
    Wait-Steam
    $t0 = Get-Date
    Start-Process "$Game\skse64_loader.exe" -WorkingDirectory $Game
    $ok = $false
    for ($i = 0; $i -lt 300; $i++) {
      Start-Sleep 1
      if ((Test-Path "$skse\skse64.log") -and (Select-String -Path "$skse\skse64.log" -Pattern 'dispatch message \(8\)' -Quiet)) { $ok = $true; break }
      if ($i -gt 30 -and -not (Get-Process SkyrimSE -EA SilentlyContinue)) { break }
    }
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
    $inst = Get-Content $Installed -Raw -Encoding UTF8 | ConvertFrom-Json  # 5.1 reads ANSI otherwise
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
    # the machine-made outputs are not in installed.json
    # our own files, laid by `on` from C:\argonia\ours (Argonia.esp, Argonia.ini, scripts\*.pex): expected, not extra
    $ours = @{}; foreach ($f in @(Get-ChildItem "$Root\ours" -Recurse -File -EA SilentlyContinue | ? { $_.FullName -notlike "$Root\ours\derived\*" -and $_.FullName -notlike "$Root\ours\derived-*" })) {
      $ours[$f.FullName.Substring("$Root\ours\".Length).ToLower()] = 1 }
    foreach ($o in $OursPlugins) { $ours[$o.name.ToLower()] = 1 }
    $pandora = @{}; foreach ($gen in 'pandora-output') { if (Test-Path "$Mo2\mods\$gen") {
      Get-ChildItem "$Mo2\mods\$gen" -Recurse -File | % { $pandora[$_.FullName.Substring("$Mo2\mods\$gen\".Length).ToLower()] = 1 } } }
    # Files a derived folder lays over every mod (DynDOLOD Resources, LOD, TexGen; decision 0014) win by design:
    # a recorded mod file under one is the derived folder's, so it is neither compared nor counted as unrecorded.
    $derivedSet = @{}; foreach ($d in $Derived) { foreach ($g in @(Get-ChildItem $d -Directory -EA SilentlyContinue)) {
      foreach ($f in [IO.Directory]::EnumerateFiles($g.FullName, '*', 'AllDirectories')) { $derivedSet[$f.Substring($g.FullName.Length + 1).ToLower()] = 1 } } }
    $bad = 0; $n = 0; $todo = New-Object System.Collections.Generic.List[object]; $hits = 0
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($k in $rec.Keys) {
      if ($k.StartsWith('..\')) { $f = "\\?\$Game\" + $k.Substring(3) } else { $f = "\\?\$Data\" + $k }
      $n++
      if ($pandora[$k] -or $derivedSet[$k]) { continue }
      # Files a mod rewrites while the game runs (Engine Fixes' enginefixes_snct.ini, 2026-11-06): present is enough.
      if ($k -like 'skse\plugins\*_snct.ini') { if (-not (Test-Path -LiteralPath $f)) { "missing: $k"; $bad++ }; continue }
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
      if ($vanilla[$rel] -or $pandora[$rel] -or $rec[$rel] -or $keepSet[$rel] -or $ours[$rel] -or $rel.StartsWith('shadercache\') -or $rel.StartsWith('mcm\settings\') -or $rel -eq 'interface\controls\pc\controlmap.txt' -or
          ($rel -match '^skse\\(plugins\\[^\\]+\.ini|[^\\]+\.log)$')) { continue }  # inis and logs the plugins write at first run
      if ($derivedSet[$rel]) { continue }  # a derived folder's (on)
      "unrecorded: $rel"; $extra++
    }
    "$n recorded files checked, $bad bad, $extra unrecorded, $($pandora.Count) Pandora outputs, $([int]((Get-Date) - $t0).TotalSeconds) s"
    if ($bad -eq 0 -and $extra -eq 0) { 'VERIFY OK' }
  }
  { $_ -in 'play-vanilla', 'play-modded', 'play-newworld' } {
    # Already running (a reconnect, or the other card): bring it to the front; never start a second copy.
    if (Focus-Skyrim) {
      'Skyrim already running: brought to the front'
      if ($Wait) { while (Get-Process SkyrimSE -EA SilentlyContinue) { Start-Sleep 2 } }
      break
    }
    Set-GameWindow
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-ExecutionPolicy', 'Bypass', '-File', "$Root\infra\splash.ps1"
    if ($Cmd -eq 'play-vanilla') { & $PSCommandPath off; Wait-Steam | Out-Null; Start-Process "$Game\SkyrimSE.exe" -WorkingDirectory $Game }
    else {
      & $PSCommandPath on -World $(if ($Cmd -eq 'play-newworld') { 'NewWorld' } else { 'Argonia' })
      # our own plugin, its ini and scripts are laid by `on` itself (above), so Data is checkable before a launch
      # Shaders off: only CS's DLL leaves Data (a hard link: its mod file stays); its settings files stay ($Keep)
      $cs = "$Data\SKSE\Plugins\CommunityShaders.dll"
      if ($Shaders -eq 'off' -and (Test-Path $cs)) { Remove-Item -LiteralPath $cs -Force; 'community shaders: off (DLL set aside)' }
      elseif ($Shaders) { "community shaders: $(if (Test-Path $cs) { 'on' } else { 'on asked, DLL not in the profile' })" }
      Wait-Steam | Out-Null
      Start-Process "$Game\skse64_loader.exe" -WorkingDirectory $Game
    }
    if ($Wait) {
      for ($i = 0; $i -lt 60 -and -not (Get-Process SkyrimSE -EA SilentlyContinue); $i++) { Start-Sleep 1 }
      while (Get-Process SkyrimSE -EA SilentlyContinue) { Start-Sleep 2 }
    }
  }
  default { throw "unknown command $Cmd" }
}

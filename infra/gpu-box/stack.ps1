# The Argonia profile on the game machine (chunk 0.2 §b), laid over Data and taken off exactly. stack.py stages and
# pushes C:\argonia\MO2\mods\<id>\ and the profile; this script does the machine's half.
#   stack.ps1 off                  Data back to the vanilla install exactly (every file not in vanilla-data-files.txt
#                                  removed, Plugins.txt cleared)
#   stack.ps1 on                   off, then every mod in the profile's modlist hard-linked into Data, lowest priority
#                                  first (a later mod's file replaces an earlier one), the controlmap, Plugins.txt
#   stack.ps1 pandora              on, Pandora run on that Data into the pandora-output mod, then on again (desktop session)
#   stack.ps1 menu                 launch through SKSE, wait for the main menu, keep a still, print SKSE's plugin lines
#   stack.ps1 verify               every laid file's hash against installed.json
#   stack.ps1 play-vanilla | play-modded [-Wait]   switch, then launch (the owner's stream cards)
param([Parameter(Mandatory)][string]$Cmd, [switch]$Wait)
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
    $lines = [System.Collections.Generic.List[string]](Get-Content $file)
    foreach ($k in $values.Keys) {
      $i = $lines.FindIndex([Predicate[string]]{ param($l) $l -match "^$([regex]::Escape($k))=" })
      if ($i -ge 0) { $lines[$i] = "$k=$($values[$k])" }
      else { $s = $lines.IndexOf("[$section]"); if ($s -lt 0) { $lines.Add("[$section]"); $s = $lines.Count - 1 }; $lines.Insert($s + 1, "$k=$($values[$k])") }
    }
    $lines | Set-Content $file -Encoding ASCII
  }
  & $set "$docs\SkyrimPrefs.ini" 'Display' @{ 'iSize W' = $b.Width; 'iSize H' = $b.Height; 'bFull Screen' = 0; 'bBorderless' = 1 }
  & $set "$docs\Skyrim.ini" 'General' @{ 'bAlwaysActive' = 1 }
  # Skyrim does not declare DPI awareness, so on a scaled desktop Windows enlarges its window past the screen edge.
  $layers = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
  New-Item -Path $layers -Force | Out-Null
  Set-ItemProperty -Path $layers -Name "$Game\SkyrimSE.exe" -Value '~ HIGHDPIAWARE'
  # Third person only (owner, 2026-10-29): scrolling in stops before first person.
  & $set "$docs\Skyrim.ini" 'Camera' @{ 'fMinCurrentZoom' = '0.1' }
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
    # cmd's dir and the \\?\ form reach paths that ordinary Windows paths cannot (names ending in a dot or space).
    foreach ($f in (cmd /c "dir /s /b /a-d `"\\?\$Data`"" 2>$null)) {
      $rel = $f.Substring($f.IndexOf('\Data\') + 6).ToLower()
      if ($vanilla[$rel] -or $rel.StartsWith('shadercache\')) { continue }
      Remove-Item -LiteralPath $f -Force -EA SilentlyContinue; $removed++
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
    $inst = Get-Content "$Mo2\installed.json" -Raw | ConvertFrom-Json
    $bad = 0; $n = 0
    foreach ($p in $inst.files.PSObject.Properties) {
      if ($p.Name.StartsWith('..\')) { $f = "$Game\" + $p.Name.Substring(3) } else { $f = "\\?\$Data\" + $p.Name }
      $n++
      if (-not (Test-Path -LiteralPath $f)) { "missing: $($p.Name)"; $bad++; continue }
      $h = (Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash.ToLower()
      if ($h -ne $p.Value[1]) { "differs: $($p.Name) ($($p.Value[0]))"; $bad++ }
    }
    $vanilla = @{}; Get-Content "$Root\infra\vanilla-data-files.txt" | % { $vanilla[$_.ToLower()] = 1 }
    $pandora = @{}; if (Test-Path "$Mo2\mods\pandora-output") {
      Get-ChildItem "$Mo2\mods\pandora-output" -Recurse -File | % { $pandora[$_.FullName.Substring("$Mo2\mods\pandora-output\".Length).ToLower()] = 1 } }
    $extra = 0
    foreach ($f in (cmd /c "dir /s /b /a-d `"\\?\$Data`"" 2>$null)) {
      $rel = $f.Substring($f.IndexOf('\Data\') + 6).ToLower()
      if ($vanilla[$rel] -or $pandora[$rel] -or $inst.files.$rel -or $rel.StartsWith('shadercache\') -or $rel.StartsWith('mcm\settings\') -or $rel -eq 'interface\controls\pc\controlmap.txt' -or ($Keep | ? { $_.ToLower() -eq $rel })) { continue }
      "unrecorded: $rel"; $extra++
    }
    "$n recorded files checked, $bad bad, $extra unrecorded, $($pandora.Count) Pandora outputs"
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

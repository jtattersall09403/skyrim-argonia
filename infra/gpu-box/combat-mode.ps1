# Switch the game machine's Skyrim between vanilla and the 0.0 combat-test mods (§d), and launch it.
#   combat-mode.ps1 build          merge the staged mods (C:\argonia\MO2\mods, list order) into C:\argonia\combat-overlay
#   combat-mode.ps1 on|off         off: Data back to the vanilla install exactly (every file not in
#                                  vanilla-data-files.txt removed, Plugins.txt cleared); on: off, then the overlay
#   combat-mode.ps1 pandora        with the overlay on, run Pandora and add its behaviour output to the overlay
#   combat-mode.ps1 play-vanilla | play-modded [-Wait]   switch, then launch (the owner's desktop shortcuts);
#                                  -Wait stays until Skyrim exits, so Sunshine knows when the game is open
# Replaces MO2 for this throwaway test: MO2 2.5 would not take a scripted portable instance unattended.
param([Parameter(Mandatory)][string]$Cmd, [switch]$Wait)
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Data = "$Game\Data"
$Root = 'C:\argonia'
$Overlay = "$Root\combat-overlay"
$State = "$Root\combat-state"
$Prefs = "$env:LOCALAPPDATA\Skyrim Special Edition"
New-Item -ItemType Directory -Force $State, $Prefs | Out-Null

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
  'build' {
    $order = Get-Content "$Root\MO2\profiles\Default\modlist.txt" | ? { $_ -like '+*' } | % { $_.Substring(1) }
    [array]::Reverse($order)  # modlist.txt lists the highest priority first; copy lowest first
    Remove-Item $Overlay -Recurse -Force -EA SilentlyContinue
    foreach ($m in $order) {
      $src = "$Root\MO2\mods\$m"
      if (Test-Path $src) { robocopy $src $Overlay /E /NFL /NDL /NJH /NJS /NP | Out-Null }
    }
    Copy-Item "$Root\MO2\profiles\Default\plugins.txt" "$State\plugins-modded.txt" -Force
    "overlay: $((Get-ChildItem $Overlay -Recurse -File).Count) files"
  }
  'on' {
    if (Get-Process SkyrimSE -EA SilentlyContinue) { throw 'Skyrim is running; quit it first' }
    & $PSCommandPath off | Out-Null
    robocopy $Overlay $Data /E /NFL /NDL /NJH /NJS /NP | Out-Null
    # the gamepad in DS1's layout (controlmap.py makes it from the player's own Interface archive): loose in
    # Data, which Skyrim reads over its archive; ControlMap_Custom.txt in My Games was not read (2026-10-29)
    if (Test-Path "$Root\controls\controlmap.txt") {
      New-Item -ItemType Directory -Force "$Data\Interface\Controls\PC" | Out-Null
      Copy-Item "$Root\controls\controlmap.txt" "$Data\Interface\Controls\PC\controlmap.txt" -Force
    }
    Copy-Item "$State\plugins-modded.txt" "$Prefs\Plugins.txt" -Force
    New-Item -ItemType File -Force "$State\mode-on" | Out-Null
    "combat mods on: $((Get-ChildItem $Overlay -Recurse -File).Count) files"
  }
  'off' {
    # Independent of any record: everything in Data that the vanilla install does not have goes (the game's own
    # shader cache stays). Vanilla Data has no loose files the mods replace, so nothing needs restoring.
    if (Get-Process SkyrimSE -EA SilentlyContinue) { throw 'Skyrim is running; quit it first' }
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
    "combat mods off (vanilla): $removed files removed"
  }
  'pandora' {
    # Pandora (a GUI app: run in the desktop session) writes to the outputPath in its Settings.json and, with
    # --auto_run, patches the mods cached in <output>\Pandora_Engine\ActiveMods.json (code, active, priority).
    if ((Get-Mode) -ne 'on') { & $PSCommandPath on | Out-Null }
    $out = "$Root\pandora-out"; Remove-Item $out -Recurse -Force -EA SilentlyContinue
    New-Item -ItemType Directory -Force "$out\Pandora_Engine" | Out-Null
    $tool = "$Root\MO2\tools\Pandora"
    $settings = @{ app = @{ theme = 0 }; games = @{ SkyrimSE = @{ gameDataPath = $Data; outputPath = $out } } }
    $settings | ConvertTo-Json -Depth 5 | Set-Content "$tool\Settings.json" -Encoding ASCII
    $codes = @(Get-ChildItem "$Data\Nemesis_Engine\mod", "$Data\Pandora_Engine\mod" -Directory -EA SilentlyContinue | % Name)
    $i = 0; $entries = foreach ($c in $codes) { [ordered]@{ code = $c; active = $true; priority = ++$i } }
    ConvertTo-Json @($entries) | Set-Content "$out\Pandora_Engine\ActiveMods.json" -Encoding ASCII
    $p = Start-Process "$tool\Pandora Behaviour Engine+.exe" -WorkingDirectory $tool -ArgumentList "--tesv:`"$Game`" --auto_run --auto_close" -PassThru
    if (-not $p.WaitForExit(240000)) { $p.Kill(); throw 'Pandora did not finish in 240 s' }
    $n = (Get-ChildItem "$out\meshes" -Recurse -File -EA SilentlyContinue).Count
    if ($n -eq 0) { throw "Pandora wrote no behaviours (exit $($p.ExitCode)); see $out\Engine.log" }
    robocopy $out $Overlay /E /XD Pandora_Engine /XF Engine.log /NFL /NDL /NJH /NJS /NP | Out-Null
    & $PSCommandPath on | Out-Null
    "pandora: $n behaviour files from $($codes.Count) mods ($($codes -join ', '))"
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

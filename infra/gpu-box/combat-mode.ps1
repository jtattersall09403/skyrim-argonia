# Switch the game machine's Skyrim between vanilla and the 0.0 combat-test mods (§d), and launch it.
#   combat-mode.ps1 build          merge the staged mods (C:\argonia\MO2\mods, list order) into C:\argonia\combat-overlay
#   combat-mode.ps1 on|off         lay the overlay over Data (recording every file and backing up any it replaces),
#                                  or take it off again exactly; sets Plugins.txt to match
#   combat-mode.ps1 pandora        with the overlay on, run Pandora and add its behaviour output to the overlay
#   combat-mode.ps1 play-vanilla | play-modded    switch, then launch (the owner's desktop shortcuts)
# Replaces MO2 for this throwaway test: MO2 2.5 would not take a scripted portable instance unattended.
param([Parameter(Mandatory)][string]$Cmd)
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Data = "$Game\Data"
$Root = 'C:\argonia'
$Overlay = "$Root\combat-overlay"
$State = "$Root\combat-state"
$Prefs = "$env:LOCALAPPDATA\Skyrim Special Edition"
New-Item -ItemType Directory -Force $State, $Prefs | Out-Null

function Get-Mode { if (Test-Path "$State\files.txt") { 'on' } else { 'off' } }

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
    if ((Get-Mode) -eq 'on') { 'already on'; break }
    if (Get-Process SkyrimSE -EA SilentlyContinue) { throw 'Skyrim is running; quit it first' }
    $files = Get-ChildItem $Overlay -Recurse -File | % { $_.FullName.Substring($Overlay.Length + 1) }
    New-Item -ItemType Directory -Force "$State\backup" | Out-Null
    foreach ($f in $files) {
      $dst = Join-Path $Data $f
      if (Test-Path $dst) { $b = Join-Path "$State\backup" $f; New-Item -ItemType Directory -Force (Split-Path $b) | Out-Null; Copy-Item $dst $b -Force }
    }
    robocopy $Overlay $Data /E /NFL /NDL /NJH /NJS /NP | Out-Null
    $files | Set-Content "$State\files.txt"
    if (Test-Path "$Prefs\Plugins.txt") { Copy-Item "$Prefs\Plugins.txt" "$State\plugins-vanilla.txt" -Force }
    Copy-Item "$State\plugins-modded.txt" "$Prefs\Plugins.txt" -Force
    "combat mods on: $($files.Count) files"
  }
  'off' {
    if ((Get-Mode) -eq 'off') { 'already off'; break }
    if (Get-Process SkyrimSE -EA SilentlyContinue) { throw 'Skyrim is running; quit it first' }
    # The \\?\ form, because some mod folders end in a dot or space, which ordinary Windows paths cannot reach.
    foreach ($f in Get-Content "$State\files.txt") { Remove-Item -LiteralPath ("\\?\" + (Join-Path $Data $f)) -Force -EA SilentlyContinue }
    Get-ChildItem $Data -Recurse -Directory | Sort { $_.FullName.Length } -Descending |
      ? { -not (Get-ChildItem -LiteralPath $_.FullName -Force) } | % { Remove-Item -LiteralPath ("\\?\" + $_.FullName) -Force }
    if (Test-Path "$State\backup") { robocopy "$State\backup" $Data /E /NFL /NDL /NJH /NJS /NP | Out-Null; Remove-Item "$State\backup" -Recurse -Force }
    if (Test-Path "$State\plugins-vanilla.txt") { Copy-Item "$State\plugins-vanilla.txt" "$Prefs\Plugins.txt" -Force } else { Remove-Item "$Prefs\Plugins.txt" -EA SilentlyContinue }
    Remove-Item "$State\files.txt"
    'combat mods off (vanilla)'
  }
  'pandora' {
    if ((Get-Mode) -ne 'on') { throw 'turn the overlay on first' }
    $out = "$Root\pandora-out"; Remove-Item $out -Recurse -Force -EA SilentlyContinue
    $exe = "$Root\MO2\tools\Pandora\Pandora Behaviour Engine+.exe"
    $p = Start-Process $exe -WorkingDirectory (Split-Path $exe) -ArgumentList '--tesv', "`"$Game`"", '--auto_run', '--auto_close', '-o', "`"$out`"" -PassThru
    if (-not $p.WaitForExit(240000)) { $p.Kill(); throw 'Pandora did not finish in 240 s' }
    $n = (Get-ChildItem $out -Recurse -File -EA SilentlyContinue).Count
    if ($n -eq 0) { throw "Pandora wrote nothing (exit $($p.ExitCode)); see its Engine.log" }
    # Take the overlay off, fold Pandora's output into it, and put it back on so off stays exact.
    & $PSCommandPath off | Out-Null
    robocopy $out $Overlay /E /NFL /NDL /NJH /NJS /NP | Out-Null
    & $PSCommandPath on
    "pandora: $n files added to the overlay"
  }
  'play-vanilla' { & $PSCommandPath off; Start-Process "$Game\SkyrimSE.exe" -WorkingDirectory $Game }
  'play-modded'  { & $PSCommandPath on; Start-Process "$Game\skse64_loader.exe" -WorkingDirectory $Game }
  default { throw "unknown command $Cmd" }
}

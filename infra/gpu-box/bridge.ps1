# DEV ONLY: the game machine's half of tools/bridge.py (chunk 0.3 §a). One line of JSON out per call.
#   bridge.ps1 health              is SkyrimSE alive, responding, and has Crash Logger written a log since this launch
#   bridge.ps1 token               the token ArgoniaBridge wrote at this launch (and its time)
#   bridge.ps1 kill                end SkyrimSE and its loader; a zombie (not responding, or surviving a kill) is
#                                  taskkilled with its tree, and the call fails if anything survives 20 s
#   bridge.ps1 prepare [-Fresh]    the profile on (stack.ps1 on, only if it is off, or always with -Fresh), then ArgoniaBridge.dll, ArgoniaCore.dll, our ESMs and .pex (C:\argonia\ours) copied from
#                                  the dev-only MO2 folder into Data\SKSE\Plugins (a copy, not a link, so a rebuild
#                                  never meets a locked file); stack.ps1 off removes it
#   bridge.ps1 hang                suspends SkyrimSE (NtSuspendProcess): a zombie on purpose, for the relaunch check
#   bridge.ps1 grab -Out <png>     one still of the desktop as the stream sees it (grab.ps1; run in the desktop session)
# The launch itself is stack.ps1 menu with ARGONIA_KEEP=1 (0.2's), run by bridge.py after `kill` and `prepare`.
param([Parameter(Mandatory)][ValidateSet('health', 'token', 'kill', 'prepare', 'grab', 'hang')][string]$Cmd,
      [string]$Out = 'C:\argonia\logs\bridge-grab.png', [switch]$Fresh)
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Skse = "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE"
$Token = "$Skse\ArgoniaBridge.token"
function J($o) { $o | ConvertTo-Json -Compress -Depth 4 }

switch ($Cmd) {
  'health' {
    $p = Get-Process SkyrimSE -EA SilentlyContinue | Select -First 1
    $since = if (Test-Path $Token) { (Get-Item $Token).LastWriteTime } else { [datetime]::MinValue }
    $crash = Get-ChildItem "$Skse\crash-*.log" -EA SilentlyContinue | ? { $_.LastWriteTime -ge $since } |
      Sort LastWriteTime | Select -Last 1
    $head = if ($crash) { (Get-Content $crash.FullName -TotalCount 12) -join "`n" } else { '' }
    # Responding reads the window from this (SSH) session, which may not see it; a process with most of its threads
    # suspended is hung whatever the window says. Not "every": a thread in a kernel wait (WaitReason Executive)
    # stays unsuspended until it returns (live, 2026-10-29: 62 of 63 after NtSuspendProcess). A running game has none.
    $susp = if ($p) { 2 * @($p.Threads | ? { $_.ThreadState -eq 'Wait' -and $_.WaitReason -eq 'Suspended' }).Count -gt $p.Threads.Count } else { $false }
    J ([ordered]@{ alive = [bool]$p; pid = $(if ($p) { $p.Id } else { 0 }); responding = $(if ($p) { $p.Responding -and -not $susp } else { $false })
                   launched = $since.ToString('o'); crash_log = $(if ($crash) { $crash.Name } else { '' }); crash_head = $head })
  }
  'token' {
    if (-not (Test-Path $Token)) { J @{ token = ''; written = '' }; break }
    J ([ordered]@{ token = (Get-Content $Token -Raw).Trim(); written = (Get-Item $Token).LastWriteTime.ToString('o') })
  }
  'kill' {
    $names = 'SkyrimSE', 'skse64_loader'
    $before = @(Get-Process $names -EA SilentlyContinue | % Id)
    Get-Process $names -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
    for ($i = 0; $i -lt 10 -and (Get-Process $names -EA SilentlyContinue); $i++) { Start-Sleep 1 }
    $zombie = @(Get-Process $names -EA SilentlyContinue | % Id)
    foreach ($id in $zombie) { cmd /c "taskkill /F /T /PID $id" 2>&1 | Out-Null }
    for ($i = 0; $i -lt 10 -and (Get-Process $names -EA SilentlyContinue); $i++) { Start-Sleep 1 }
    $left = @(Get-Process $names -EA SilentlyContinue | % Id)
    J ([ordered]@{ killed = $before; zombies = $zombie; survivors = $left })
    if ($left) { exit 1 }
  }
  'prepare' {
    if (Get-Process SkyrimSE -EA SilentlyContinue) { J @{ laid = $false; error = 'Skyrim is running: kill first' }; exit 1 }
    # -Fresh lays the profile again (stack.ps1 on is off then on, and seeds the first-run settings).
    if ($Fresh -or -not (Test-Path C:\argonia\stack-state\mode-on)) { & C:\argonia\infra\stack.ps1 on | Out-Null }
    $src = 'C:\argonia\MO2\mods\Argonia SKSE (dev only)\SKSE\Plugins\ArgoniaBridge.dll'
    $dst = "$Game\Data\SKSE\Plugins"
    if (-not (Test-Path $src)) { J @{ laid = $false; error = "no $src (skse_build.sh build windows-dev)" }; exit 1 }
    New-Item -ItemType Directory -Force $dst | Out-Null
    # A file already laid (same length and write time; Copy-Item keeps the time) is not copied again (game-12): a
    # relaunch was copying the 229 MB world ESM each time, and LOD's tools hold Data's plugins open while they run.
    function Lay($from, $to) { $a = Get-Item $from; $b = Get-Item $to -EA SilentlyContinue
      if (-not $b -or $a.Length -ne $b.Length -or $a.LastWriteTimeUtc -ne $b.LastWriteTimeUtc) { Copy-Item $from $to -Force } }
    Lay $src "$dst\ArgoniaBridge.dll"
    $h = (Get-FileHash "$dst\ArgoniaBridge.dll" -Algorithm SHA256).Hash.ToLower()
    # ArgoniaCore (0.3 §b, 1.1) is laid beside it (skse_build.sh puts it in MO2's Argonia SKSE, outside the modlist)
    $core = 'C:\argonia\MO2\mods\Argonia SKSE\SKSE\Plugins\ArgoniaCore.dll'; $ch = $null
    if (Test-Path $core) { Lay $core "$dst\ArgoniaCore.dll"; $ch = (Get-FileHash "$dst\ArgoniaCore.dll").Hash.ToLower() }
    # Our plugins (make deploy puts out/*.esm into C:\argonia\ours): copied into Data and enabled last in Plugins.txt,
    # ArgoniaWorld.esm before Argonia.esm (its master). stack.ps1 off removes them with everything else.
    $esms = @(); $prefs = "$env:LOCALAPPDATA\Skyrim Special Edition\Plugins.txt"
    foreach ($e in 'ArgoniaWorld.esm', 'Argonia.esm') { if (Test-Path "C:\argonia\ours\$e") {
      Lay "C:\argonia\ours\$e" "$Game\Data\$e"; $esms += $e
      $lines = @(Get-Content $prefs | ? { $_.TrimStart('*') -ne $e }); $lines += "*$e"; $lines | Set-Content $prefs -Encoding ASCII } }
    # Our compiled Papyrus (make deploy puts it in C:\argonia\ours\scripts) into Data\Scripts; stack.ps1 off removes it.
    $pex = @(Get-ChildItem C:\argonia\ours\scripts\*.pex -EA SilentlyContinue)
    if ($pex) { New-Item -ItemType Directory -Force "$Game\Data\Scripts" | Out-Null; $pex | Copy-Item -Destination "$Game\Data\Scripts" -Force }
    J ([ordered]@{ laid = $true; file = "$dst\ArgoniaBridge.dll"; sha256 = $h; bytes = (Get-Item $src).Length; core_sha256 = $ch; esms = $esms; pex = $pex.Count })
  }
  'hang' {
    $p = Get-Process SkyrimSE -EA SilentlyContinue | Select -First 1
    if (-not $p) { J @{ hung = $false; error = 'SkyrimSE is not running' }; exit 1 }
    Add-Type 'using System; using System.Runtime.InteropServices; public static class Nt {
      [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr h); }'
    $rc = [Nt]::NtSuspendProcess($p.Handle)
    J ([ordered]@{ hung = ($rc -eq 0); pid = $p.Id; status = $rc })
  }
  'grab' {
    Remove-Item $Out -EA SilentlyContinue
    & C:\argonia\infra\grab.ps1 $Out | Out-Null
    if (-not (Test-Path $Out)) { J @{ grabbed = $false }; exit 1 }
    J ([ordered]@{ grabbed = $true; file = $Out; bytes = (Get-Item $Out).Length })
  }
}

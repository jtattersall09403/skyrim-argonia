# Make the 0.0 test saves and measure frame time (§c, §d), in the logged-in desktop session (run.sh desktop).
#   test-saves.ps1
# Vanilla Skyrim, reached without the new-game flow: the start-up console command jumps to Riverwood; console
# batch files typed in by injected scancodes add gear and save ("Argonia Riverwood"), measure 60 s of frame time
# with PresentMon, then go to the bandits in Embershard Mine and save there ("Argonia Bandit Camp"). Cheats are
# for setup only (owner ruling); the saves hold no god mode.
$ErrorActionPreference = 'Stop'
Start-Transcript C:\argonia\logs\test-saves.log -Force | Out-Null
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Docs = "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition"
$Logs = 'C:\argonia\logs'
Add-Type @'
using System; using System.Runtime.InteropServices; using System.Threading;
public static class Keys {
  [StructLayout(LayoutKind.Sequential)] struct KI { public ushort vk, scan; public uint flags, time; public IntPtr extra; }
  [StructLayout(LayoutKind.Explicit, Size = 40)] struct IN { [FieldOffset(0)] public uint type; [FieldOffset(8)] public KI ki; }
  [DllImport("user32.dll", SetLastError = true)] static extern uint SendInput(uint n, IN[] i, int size);
  static void Scan(ushort sc, bool up, bool ext) {
    var i = new IN[1]; i[0].type = 1; i[0].ki.scan = sc; i[0].ki.flags = 0x8u | (up ? 0x2u : 0u) | (ext ? 0x1u : 0u);
    if (SendInput(1, i, Marshal.SizeOf(typeof(IN))) != 1) throw new Exception("SendInput refused: " + Marshal.GetLastWin32Error());
  }
  public static void Tap(ushort sc, bool ext = false) { Scan(sc, false, ext); Thread.Sleep(40); Scan(sc, true, ext); Thread.Sleep(40); }
  const string Row1 = "1234567890-", Row2 = "qwertyuiop", Row3 = "asdfghjkl", Row4 = "zxcvbnm,.";
  public static void Type(string s) {
    foreach (char c in s.ToLower()) {
      int k;
      if (c == ' ') Tap(0x39);
      else if ((k = Row1.IndexOf(c)) >= 0) Tap((ushort)(0x02 + k));
      else if ((k = Row2.IndexOf(c)) >= 0) Tap((ushort)(0x10 + k));
      else if ((k = Row3.IndexOf(c)) >= 0) Tap((ushort)(0x1E + k));
      else if ((k = Row4.IndexOf(c)) >= 0) Tap((ushort)(0x2C + k));
      else throw new Exception("no scancode for " + c);
    }
  }
}
'@
function Console-Run($line) {
  [Keys]::Tap(0x29); Start-Sleep -Milliseconds 600   # ` opens the console
  [Keys]::Type($line); [Keys]::Tap(0x1C); Start-Sleep -Milliseconds 800
  [Keys]::Tap(0x29); Start-Sleep -Milliseconds 600
}
function Shot { [Keys]::Tap(0x37, $true); Start-Sleep 2 }  # Print Screen: Skyrim writes ScreenShot<n>.png

# Steam must be running (and offline) for the game to start.
if (-not (Get-Process steam -EA SilentlyContinue)) { Start-Process 'C:\Program Files (x86)\Steam\steam.exe' -ArgumentList '-silent'; Start-Sleep 25 }
& C:\argonia\infra\combat-mode.ps1 off | Out-Null
# steam_appid.txt lets SkyrimSE.exe run directly under the signed-in Steam instead of exiting to relaunch through
# Steam's launcher (exit code 53), so scripts and the owner's shortcuts skip the launcher window.
Set-Content "$Game\steam_appid.txt" '489830' -Encoding ASCII

# Batch files (one console command per line) and the start-up jump.
Set-Content "$Game\argonia-start.txt" 'coc Riverwood' -Encoding ASCII
Set-Content "$Game\argonia-gear.txt" @(
  'player.additem 00012eb7 1', 'player.additem 00012eb6 1', 'player.additem 00012e49 1', 'player.additem 00012e4d 1',
  'player.additem 00012e4b 1', 'player.additem 00012e46 1', 'player.additem 0003eade 10', 'save ArgoniaRiverwood') -Encoding ASCII
Set-Content "$Game\argonia-camp.txt" 'coc EmbershardMine' -Encoding ASCII
Set-Content "$Game\argonia-campsave.txt" 'save ArgoniaBanditCamp' -Encoding ASCII
$ini = "$Docs\Skyrim.ini"; $t = Get-Content $ini
$t = $t | ? { $_ -notmatch '^sStartingConsoleCommand=|^bAllowScreenShot=' }
$t = $t -replace '^\[General\]', "[General]`r`nsStartingConsoleCommand=bat argonia-start"
$t = $t -replace '^\[Display\]', "[Display]`r`nbAllowScreenShot=1"
$t | Set-Content $ini -Encoding ASCII

Get-ChildItem "$Game\ScreenShot*.png" -EA SilentlyContinue | Remove-Item
$p = Start-Process "$Game\SkyrimSE.exe" -WorkingDirectory $Game -PassThru
Start-Sleep 90
if ($p.HasExited) { throw "Skyrim exited early (code $($p.ExitCode))" }
Shot
Console-Run 'bat argonia-gear'; Start-Sleep 5; Shot

# Frame time: 60 s at Riverwood, standing in the village.
$pm = 'C:\argonia\downloads\PresentMon.exe'
if (-not (Test-Path $pm)) { Invoke-WebRequest 'https://github.com/GameTechDev/PresentMon/releases/download/v2.6.0/PresentMon-2.6.0-x64.exe' -OutFile $pm -UseBasicParsing }
& $pm --process_name SkyrimSE.exe --timed 60 --terminate_after_timed --output_file "$Logs\frametime-riverwood.csv" --no_console_stats 2>&1 | Out-Null

Console-Run 'bat argonia-camp'; Start-Sleep 40; Shot
Console-Run 'bat argonia-campsave'; Start-Sleep 8; Shot
Stop-Process -Id $p.Id -Force

# The jump is for this script only: the owner's own launches start at the main menu.
(Get-Content $ini) | ? { $_ -notmatch '^sStartingConsoleCommand=' } | Set-Content $ini -Encoding ASCII
"saves: " + ((Get-ChildItem "$Docs\Saves\*Argonia*" -EA SilentlyContinue | % Name) -join ', ')
"screenshots: " + ((Get-ChildItem "$Game\ScreenShot*.png" -EA SilentlyContinue | % Name) -join ', ')
"frametime csv: " + (Test-Path "$Logs\frametime-riverwood.csv")

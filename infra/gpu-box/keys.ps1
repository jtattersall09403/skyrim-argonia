# Press keyboard keys in the desktop session by scan code (SendInput), which DirectInput and ImGui overlays read;
# WScript's SendKeys does not reach Skyrim (2026-10-29). Run through run.sh desktop.
#   keys.ps1 -Keys 'ENTER'      keys.ps1 -Keys 'GRAVE,ESC'      (names below; each pressed for -HoldMs)
param([Parameter(Mandatory)][string]$Keys, [int]$HoldMs = 80, [int]$GapMs = 150)
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class Kb {
  [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort vk, scan; public uint flags, time; public IntPtr extra; }
  [StructLayout(LayoutKind.Explicit, Size = 40)] struct INPUT { [FieldOffset(0)] public uint type; [FieldOffset(8)] public KEYBDINPUT ki; }
  [DllImport("user32.dll")] static extern uint SendInput(uint n, INPUT[] i, int size);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  public static void Key(ushort scan, bool up) {
    var i = new INPUT[1]; i[0].type = 1; i[0].ki.scan = scan; i[0].ki.flags = 0x0008u | (up ? 0x0002u : 0u);
    SendInput(1, i, Marshal.SizeOf(typeof(INPUT)));
  }
}
'@
$codes = @{ ENTER = 0x1C; ESC = 0x01; GRAVE = 0x29; TAB = 0x0F; SPACE = 0x39; E = 0x12; W = 0x11; A = 0x1E; S = 0x1F; D = 0x20; END = 0xCF }
$p = Get-Process SkyrimSE -EA SilentlyContinue | Select -First 1
if ($p) { [void][Kb]::SetForegroundWindow($p.MainWindowHandle); Start-Sleep -Milliseconds 300 }
foreach ($k in ($Keys -split ',')) {
  $c = [uint16]$codes[$k.Trim().ToUpper()]
  [Kb]::Key($c, $false); Start-Sleep -Milliseconds $HoldMs; [Kb]::Key($c, $true); Start-Sleep -Milliseconds $GapMs
  "$((Get-Date).ToString('HH:mm:ss.fff')) key $k"
}

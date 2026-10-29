# Display helpers for the game machine's desktop session (chunk 0.0 §b): list modes, set a mode on a display.
#   display.ps1 list | display.ps1 set <\\.\DISPLAYn> <width> <height> [hz] [primary]
#   display.ps1 modes    (dot-source) define Get-Modes <device> for other scripts
#   display.ps1 pin      set the primary display to 1920x1080@60 (at logon: the head Windows picks varies by boot)
param([string]$Cmd = 'list', [string]$Dev, [int]$W, [int]$H, [int]$Hz = 60, [switch]$Primary)
Add-Type @'
using System; using System.Runtime.InteropServices;
public class Disp {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)] public struct DEVMODE {
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmDeviceName; public short dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra; public int dmFields;
    public int dmPositionX, dmPositionY, dmDisplayOrientation, dmDisplayFixedOutput; public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmFormName; public short dmLogPixels; public int dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags, dmDisplayFrequency;
    public int dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight; }
  [DllImport("user32.dll")] public static extern bool EnumDisplaySettings(string dev, int mode, ref DEVMODE dm);
  [DllImport("user32.dll")] public static extern int ChangeDisplaySettingsEx(string dev, ref DEVMODE dm, IntPtr hwnd, int flags, IntPtr lParam);
}
'@
function New-Mode { $m = New-Object Disp+DEVMODE; $m.dmSize = [Runtime.InteropServices.Marshal]::SizeOf($m); $m }
function Get-Modes([string]$Device) {
  $m = New-Mode; $i = 0; $seen = @{}
  while ([Disp]::EnumDisplaySettings($Device, $i, [ref]$m)) {
    $k = "$($m.dmPelsWidth)x$($m.dmPelsHeight)@$($m.dmDisplayFrequency)"
    if (-not $seen[$k]) { $seen[$k] = 1; [pscustomobject]@{ W = $m.dmPelsWidth; H = $m.dmPelsHeight; Hz = $m.dmDisplayFrequency } }
    $i++
  }
}
if ($Cmd -eq 'modes') { return }
if ($Cmd -eq 'pin') {
  Add-Type -AssemblyName System.Windows.Forms
  $Dev = ([System.Windows.Forms.Screen]::AllScreens | ? Primary).DeviceName; $W = 1920; $H = 1080; $Hz = 60; $Primary = $true; $Cmd = 'set'
}
if ($Cmd -eq 'list') {
  Add-Type -AssemblyName System.Windows.Forms
  foreach ($s in [System.Windows.Forms.Screen]::AllScreens) {
    $seen = @{}; $m = New-Mode; $i = 0
    while ([Disp]::EnumDisplaySettings($s.DeviceName, $i, [ref]$m)) { $seen["$($m.dmPelsWidth)x$($m.dmPelsHeight)@$($m.dmDisplayFrequency)"] = 1; $i++ }
    "$($s.DeviceName) primary=$($s.Primary) $($s.Bounds.Width)x$($s.Bounds.Height): $(($seen.Keys | Sort-Object) -join ' ')"
  }
} else {
  $m = New-Mode; [void][Disp]::EnumDisplaySettings($Dev, -1, [ref]$m)
  $m.dmPelsWidth = $W; $m.dmPelsHeight = $H; $m.dmDisplayFrequency = $Hz; $m.dmFields = 0x180000 -bor 0x400000
  $flags = 0x1  # CDS_UPDATEREGISTRY
  if ($Primary) { $m.dmPositionX = 0; $m.dmPositionY = 0; $m.dmFields = $m.dmFields -bor 0x20; $flags = $flags -bor 0x10 }
  "set $Dev ${W}x${H}@${Hz}: $([Disp]::ChangeDisplaySettingsEx($Dev, [ref]$m, [IntPtr]::Zero, $flags, [IntPtr]::Zero)) (0 = ok)"
}

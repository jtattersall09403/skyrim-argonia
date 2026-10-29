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
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)] public struct DISPLAY_DEVICE { public int cb;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string DeviceName; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string DeviceString;
    public int StateFlags; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string DeviceID; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string DeviceKey; }
  [DllImport("user32.dll", CharSet=CharSet.Ansi)] public static extern bool EnumDisplayDevices(string dev, int i, ref DISPLAY_DEVICE dd, int flags);
  public static string FindDevice(string match) {   // the \\.\DISPLAYn whose adapter description contains match
    for (int i = 0; i < 64; i++) {
      var d = new DISPLAY_DEVICE(); d.cb = Marshal.SizeOf(typeof(DISPLAY_DEVICE));
      if (!EnumDisplayDevices(null, i, ref d, 0)) break;
      if (d.DeviceString != null && d.DeviceString.IndexOf(match, StringComparison.OrdinalIgnoreCase) >= 0) return d.DeviceName;
    }
    return null;
  }
  [DllImport("user32.dll", EntryPoint="ChangeDisplaySettingsExA")] public static extern int ApplyAll(string dev, IntPtr dm, IntPtr hwnd, int flags, IntPtr lParam);
  /// Make dev the only attached display, primary at w x h @ hz: detach every other display, then apply at once.
  public static int SoleDisplay(string dev, int w, int h, int hz) {
    const int UPDATEREGISTRY = 0x1, SET_PRIMARY = 0x10, NORESET = 0x10000000;
    // the target first, as primary (Windows will not detach the current primary before there is a new one)
    var m = new DEVMODE(); m.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));
    EnumDisplaySettings(dev, -1, ref m);
    m.dmPelsWidth = w; m.dmPelsHeight = h; m.dmDisplayFrequency = hz; m.dmPositionX = 0; m.dmPositionY = 0;
    m.dmFields = 0x20 | 0x80000 | 0x100000 | 0x400000;
    int r = ChangeDisplaySettingsEx(dev, ref m, IntPtr.Zero, UPDATEREGISTRY | SET_PRIMARY | NORESET, IntPtr.Zero);
    for (int i = 0; i < 64; i++) {   // then every other attached display off
      var d = new DISPLAY_DEVICE(); d.cb = Marshal.SizeOf(typeof(DISPLAY_DEVICE));
      if (!EnumDisplayDevices(null, i, ref d, 0)) break;
      if ((d.StateFlags & 1) == 0 || d.DeviceName == dev) continue;
      var off = new DEVMODE(); off.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));
      off.dmFields = 0x20 | 0x80000 | 0x100000;
      ChangeDisplaySettingsEx(d.DeviceName, ref off, IntPtr.Zero, UPDATEREGISTRY | NORESET, IntPtr.Zero);
    }
    int a = ApplyAll(null, IntPtr.Zero, IntPtr.Zero, 0, IntPtr.Zero);
    return r != 0 ? r : a;
  }
  public static string ListDevices() {
    var s = new System.Text.StringBuilder();
    for (int i = 0; i < 64; i++) {
      var d = new DISPLAY_DEVICE(); d.cb = Marshal.SizeOf(typeof(DISPLAY_DEVICE));
      if (!EnumDisplayDevices(null, i, ref d, 0)) break;
      s.AppendLine(d.DeviceName + " [" + d.DeviceString + "] flags=" + d.StateFlags);
    }
    return s.ToString();
  }
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
function Get-CurrentMode([string]$Device) {
  $m = New-Mode; [void][Disp]::EnumDisplaySettings($Device, -1, [ref]$m)
  [pscustomobject]@{ W = $m.dmPelsWidth; H = $m.dmPelsHeight; Hz = $m.dmDisplayFrequency }
}
function Get-VddDevice { [Disp]::FindDevice('Virtual Display') }   # its \\.\DISPLAYn, or $null
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

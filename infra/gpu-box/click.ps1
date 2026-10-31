# A real mouse on the game machine's desktop (1.12: Wind UI's windows are mouse-driven ImGui; the phone's touch
# arrives as the mouse too). Run in the logged-in desktop session (run.sh desktop):
#   click.ps1 -X 1240 -Y 1036 [-Button left|right] [-Drag 'X2,Y2'] [-Wheel N]
# X and Y are screen pixels at the game's resolution. -Drag holds the button from (X,Y) to (X2,Y2) over ~300 ms;
# -Wheel scrolls N notches at (X,Y) (positive away from the user). Prints one line per action.
param([int]$X, [int]$Y, [string]$Button = 'left', [string]$Drag = '', [int]$Wheel = 0)
Add-Type @"
using System; using System.Runtime.InteropServices;
public static class M {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, int d, UIntPtr e);
}
"@
$down = @{ left = 0x0002; right = 0x0008 }[$Button]; $up = @{ left = 0x0004; right = 0x0010 }[$Button]
# The game reads relative mouse motion (DirectInput), not the OS cursor: pin the cursor to the top-left corner with
# large relative moves, then move by (X,Y) in steps the game takes as 1:1 in menus.
function Move([int]$dx, [int]$dy) { [M]::mouse_event(0x0001, [uint32]($dx -band 0xFFFFFFFF), [uint32]($dy -band 0xFFFFFFFF), 0, [UIntPtr]::Zero) }
for ($i = 0; $i -lt 8; $i++) { Move -800 -800; Start-Sleep -Milliseconds 15 }
$sx = 0; $sy = 0
while ($sx -lt $X -or $sy -lt $Y) { $mx = [Math]::Min(40, $X - $sx); $my = [Math]::Min(40, $Y - $sy); Move $mx $my; $sx += $mx; $sy += $my; Start-Sleep -Milliseconds 8 }
Start-Sleep -Milliseconds 60
if ($Wheel -ne 0) { [M]::mouse_event(0x0800, 0, 0, 120 * $Wheel, [UIntPtr]::Zero); "wheel $Wheel at $X,$Y"; exit 0 }
[M]::mouse_event($down, 0, 0, 0, [UIntPtr]::Zero)
if ($Drag) {
  $x2, $y2 = $Drag.Split(',') | ForEach-Object { [int]$_ }
  for ($i = 1; $i -le 10; $i++) { Move (($x2 - $X) / 10) (($y2 - $Y) / 10); Start-Sleep -Milliseconds 30 }
}
Start-Sleep -Milliseconds 70
[M]::mouse_event($up, 0, 0, 0, [UIntPtr]::Zero)
"$Button at $X,$Y$(if ($Drag) { " to $Drag" })"

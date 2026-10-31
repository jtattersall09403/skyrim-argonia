# Play a timed gamepad sequence on a virtual Xbox 360 pad (ViGEmBus, installed with Sunshine), so a check presses
# the real buttons the owner presses (0.2 §c). Run in the desktop session (run.sh desktop); Skyrim reads it by XInput.
#   pad.ps1 -Seq 'B:150 wait:900 LB:1200 RT:150 RS:150 LX=-1:800 LY=1,LX=1:700'
# Steps: BUTTON:ms presses and releases (A B X Y LB RB LS RS START BACK UP DOWN LEFT RIGHT), LT/RT:ms pull a trigger,
# AXIS=v[,AXIS=v]:ms holds sticks (LX LY RX RY, -1..1) then centres them, +AXIS=v[,...]:ms sets them and keeps them
# set through the next steps (also +LT=1 / +RT=1 a held trigger and +LB=1 a held button: a bash or parry is L1/L2 held
# while R1 taps), -:ms centres the sticks and releases every held trigger and button, wait:ms pauses. Each step prints a timestamped line, the
# journey's event record. The pad itself lives in padhost.ps1, plugged once per game session and never unplugged
# between calls (diag6 7: a pad hot-plugged inside a paused menu never went live); this script starts the host if none
# runs and sends it the sequence.
param([Parameter(Mandatory)][string]$Seq)
$ErrorActionPreference = 'Stop'
function Open([int]$ms) {
  $c = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'argonia-pad', [System.IO.Pipes.PipeDirection]::InOut)
  try { $c.Connect($ms); return $c } catch { $c.Dispose(); return $null }
}
$c = Open 300
if (-not $c) {
  Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-ExecutionPolicy Bypass -File C:\argonia\infra\padhost.ps1'
  $c = Open 15000
  if (-not $c) { throw 'pad: the pad host did not come up in 15 s' }
}
try {
  $w = New-Object System.IO.StreamWriter($c); $w.AutoFlush = $true; $r = New-Object System.IO.StreamReader($c)
  $w.WriteLine($Seq)
  while (($ln = $r.ReadLine()) -ne $null -and $ln -ne 'END') { $ln }
} finally { $c.Dispose() }

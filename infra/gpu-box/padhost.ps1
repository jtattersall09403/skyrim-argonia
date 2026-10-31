# The persistent pad (diag3 item 2, diag6 7): one virtual Xbox 360 pad (ViGEmBus) plugged once per game session and
# kept plugged, so the game takes it up once, in play, and a press sent inside a paused menu reaches it. pad.ps1 starts
# this host on its first call and sends it each sequence over the named pipe \\.\pipe\argonia-pad; the host plays
# it (the step grammar is pad.ps1's), writes one timestamped line per step back, then END. It unplugs the pad and exits
# only when the game's process is gone (the session ended), so the next session plugs a fresh one. One host at a time:
# a second finds the pipe taken and exits. The client DLL is Nefarius.ViGEm.Client (MIT, NuGet 1.21.256).
param([int]$Settle = 1500)
$ErrorActionPreference = 'Stop'
$Pipe = 'argonia-pad'
try {
  $srv = New-Object System.IO.Pipes.NamedPipeServerStream($Pipe, [System.IO.Pipes.PipeDirection]::InOut, 1,
    [System.IO.Pipes.PipeTransmissionMode]::Byte, [System.IO.Pipes.PipeOptions]::Asynchronous)
} catch { "padhost: the pipe is taken; another host runs"; exit 0 }
Add-Type -Path 'C:\argonia\tools\vigem\Nefarius.ViGEm.Client.dll'
$client = New-Object Nefarius.ViGEm.Client.ViGEmClient
$pad = $client.CreateXbox360Controller()
$pad.Connect()
Start-Sleep -Milliseconds $Settle   # the game notices a new pad on its next poll
# The game's first read of a new pad only switches it to the pad (diag3-g15): a right-stick nudge does it, once, at
# the plug (the host is started by a call in play, never in a paused menu, where the nudge does nothing).
$pad.SetAxisValue([Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::RightThumbY, 6000); Start-Sleep -Milliseconds 120
$pad.SetAxisValue([Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::RightThumbY, 0); Start-Sleep -Milliseconds 300
$B = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Button]
$names = @{ A = $B::A; B = $B::B; X = $B::X; Y = $B::Y; LB = $B::LeftShoulder; RB = $B::RightShoulder; LS = $B::LeftThumb;
            RS = $B::RightThumb; START = $B::Start; BACK = $B::Back; UP = $B::Up; DOWN = $B::Down; LEFT = $B::Left; RIGHT = $B::Right }
$axes = @{ LX = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::LeftThumbX; LY = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::LeftThumbY
           RX = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::RightThumbX; RY = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::RightThumbY }
$sl = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Slider]

function Play([string]$Seq, $out) {
  $held = @()
  foreach ($step in ($Seq -split '\s+' | ? { $_ })) {
    $what, $ms = $step -split ':', 2; $ms = [int]$ms
    $out.WriteLine("$((Get-Date).ToString('HH:mm:ss.fff')) $step")
    if ($what -eq 'wait') { Start-Sleep -Milliseconds $ms; continue }
    if ($what -in 'LT', 'RT') {
      $s = if ($what -eq 'LT') { $sl::LeftTrigger } else { $sl::RightTrigger }
      $pad.SetSliderValue($s, 255); Start-Sleep -Milliseconds $ms; $pad.SetSliderValue($s, 0); continue
    }
    if ($what -eq '-') {
      foreach ($k in $axes.Keys) { $pad.SetAxisValue($axes[$k], 0) }
      $pad.SetSliderValue($sl::LeftTrigger, 0); $pad.SetSliderValue($sl::RightTrigger, 0)
      foreach ($n in $held) { $pad.SetButtonState($names[$n], $false) }; $held = @()
      Start-Sleep -Milliseconds $ms; continue
    }
    if ($what.StartsWith('+')) {   # sticks held across the following steps (a roll's direction while B is tapped)
      foreach ($a in ($what.Substring(1) -split ',')) {
        $k, $v = $a -split '='
        if ($k -eq 'LT') { $pad.SetSliderValue($sl::LeftTrigger, [byte]([double]$v * 255)) }
        elseif ($k -eq 'RT') { $pad.SetSliderValue($sl::RightTrigger, [byte]([double]$v * 255)) }
        elseif ($names.ContainsKey($k)) { $pad.SetButtonState($names[$k], [double]$v -ne 0); $held += $k }
        else { $pad.SetAxisValue($axes[$k], [int16]([double]$v * 32767)) }
      }
      Start-Sleep -Milliseconds $ms; continue
    }
    if ($what -match '=') {
      $set = $what -split ','
      foreach ($a in $set) { $k, $v = $a -split '='; $pad.SetAxisValue($axes[$k], [int16]([double]$v * 32767)) }
      Start-Sleep -Milliseconds $ms
      foreach ($a in $set) { $k, $v = $a -split '='; $pad.SetAxisValue($axes[$k], 0) }
      continue
    }
    $pad.SetButtonState($names[$what], $true); Start-Sleep -Milliseconds $ms; $pad.SetButtonState($names[$what], $false)
  }
  foreach ($k in $axes.Keys) { $pad.SetAxisValue($axes[$k], 0) }   # nothing stays held between calls
  $pad.SetSliderValue($sl::LeftTrigger, 0); $pad.SetSliderValue($sl::RightTrigger, 0)
  foreach ($n in $held) { $pad.SetButtonState($names[$n], $false) }
  Start-Sleep -Milliseconds 300
}

try {
  while ($true) {
    $t = $srv.WaitForConnectionAsync()
    while (-not $t.Wait(2000)) {
      if (-not (Get-Process SkyrimSE -EA SilentlyContinue)) { "padhost: the game ended; the pad is unplugged"; exit 0 }
    }
    $r = New-Object System.IO.StreamReader($srv); $w = New-Object System.IO.StreamWriter($srv); $w.AutoFlush = $true
    try { Play $r.ReadLine() $w } catch { $w.WriteLine("ERROR $($_.Exception.Message)") }
    try { $w.WriteLine('END'); $srv.WaitForPipeDrain() } catch {}
    $srv.Disconnect()
  }
} finally { $pad.Disconnect(); $client.Dispose(); $srv.Dispose() }

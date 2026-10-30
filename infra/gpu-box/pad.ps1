# Play a timed gamepad sequence on a virtual Xbox 360 pad (ViGEmBus, installed with Sunshine), so a check presses
# the real buttons the owner presses (0.2 §c). Run in the desktop session (run.sh desktop); Skyrim reads it by XInput.
#   pad.ps1 -Seq 'B:150 wait:900 LB:1200 RT:150 RS:150 LX=-1:800 LY=1,LX=1:700'
# Steps: BUTTON:ms presses and releases (A B X Y LB RB LS RS START BACK UP DOWN LEFT RIGHT), LT/RT:ms pull a trigger,
# AXIS=v[,AXIS=v]:ms holds sticks (LX LY RX RY, -1..1) then centres them, +AXIS=v[,...]:ms sets them and keeps them
# set through the next steps (also +LT=1 / +RT=1 a held trigger and +LB=1 a held button: a bash or parry is L1/L2 held
# while R1 taps), -:ms centres the sticks and releases every held trigger and button, wait:ms pauses. Each step prints a timestamped line, the
# journey's event record. The client DLL is Nefarius.ViGEm.Client (MIT, NuGet 1.21.256) in C:\argonia\tools\vigem.
param([Parameter(Mandatory)][string]$Seq, [int]$Settle = 1500)
$ErrorActionPreference = 'Stop'
Add-Type -Path 'C:\argonia\tools\vigem\Nefarius.ViGEm.Client.dll'
$client = New-Object Nefarius.ViGEm.Client.ViGEmClient
$pad = $client.CreateXbox360Controller()
$pad.Connect()
Start-Sleep -Milliseconds $Settle   # the game notices a new pad on its next poll
$B = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Button]
$names = @{ A = $B::A; B = $B::B; X = $B::X; Y = $B::Y; LB = $B::LeftShoulder; RB = $B::RightShoulder; LS = $B::LeftThumb;
            RS = $B::RightThumb; START = $B::Start; BACK = $B::Back; UP = $B::Up; DOWN = $B::Down; LEFT = $B::Left; RIGHT = $B::Right }
$axes = @{ LX = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::LeftThumbX; LY = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::LeftThumbY
           RX = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::RightThumbX; RY = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Axis]::RightThumbY }
$sl = [Nefarius.ViGEm.Client.Targets.Xbox360.Xbox360Slider]
$held = @()
try {
  foreach ($step in ($Seq -split '\s+' | ? { $_ })) {
    $what, $ms = $step -split ':', 2; $ms = [int]$ms
    "$((Get-Date).ToString('HH:mm:ss.fff')) $step"
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
  Start-Sleep -Milliseconds 300
} finally { $pad.Disconnect(); $client.Dispose() }

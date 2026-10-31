# Set up the Windows game machine argonia-play (chunk 0.0 §b, §c). Run from the build VM:
#   infra/gpu-box/run.sh setup [stage]
# Idempotent: each step checks before it acts. Stages: base (driver, Steam, MO2, tools), stream (hosts),
# all (default). Reboots are requested by printing REBOOT-NEEDED; run.sh reboots and runs it again.
param([string]$Stage = 'all')
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = 'C:\argonia'
$Dl = "$Root\downloads"
New-Item -ItemType Directory -Force -Path $Root, $Dl, "$Root\logs" | Out-Null

function Get-File($Url, $Name) {
  $out = Join-Path $Dl $Name
  if (-not (Test-Path $out)) { Write-Host "download $Name"; Invoke-WebRequest -Uri $Url -OutFile $out -UseBasicParsing }
  return $out
}

function Install-Base {
  # The AWS GRID driver: public bucket, NVENC, licensed automatically on EC2 (the _aws_swl build).
  $nv = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -like 'NVIDIA*' }
  if (-not $nv) {
    $key = (Invoke-RestMethod 'https://ec2-windows-nvidia-drivers.s3.amazonaws.com/?prefix=latest/').ListBucketResult.Contents |
      Where-Object { $_.Key -like '*server2022*.exe' } | Select-Object -First 1 -ExpandProperty Key
    $exe = Get-File "https://ec2-windows-nvidia-drivers.s3.amazonaws.com/$key" 'nvidia-grid.exe'
    Write-Host "install NVIDIA driver $key"
    Start-Process $exe -ArgumentList '-s', '-noreboot', '-clean' -Wait
    Write-Host 'REBOOT-NEEDED'
    return
  }
  Write-Host "driver: $($nv.Name) $($nv.DriverVersion)"

  # High performance power plan, no sleep, no screen saver.
  powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
  powercfg /change monitor-timeout-ac 0; powercfg /change standby-timeout-ac 0

  if (-not (Test-Path 'C:\Program Files (x86)\Steam\steam.exe')) {
    $s = Get-File 'https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe' 'SteamSetup.exe'
    Start-Process $s -ArgumentList '/S' -Wait
  }
  Write-Host 'steam: installed'

  if (-not (Test-Path "$Root\MO2\ModOrganizer.exe")) {
    $rel = Invoke-RestMethod 'https://api.github.com/repos/ModOrganizer2/modorganizer/releases/latest'
    $asset = $rel.assets | Where-Object { $_.name -match '^Mod\.Organizer-[\d.]+\.7z$' } | Select-Object -First 1
    $7z = Get-File 'https://www.7-zip.org/a/7zr.exe' '7zr.exe'
    $arc = Get-File $asset.browser_download_url $asset.name
    & $7z x $arc "-o$Root\MO2" -y | Out-Null
  }
  Write-Host 'mo2: installed'
}

function Install-Stream {
  # The desktop must be on the T4, not EC2's basic adapter, for NVENC capture.
  Get-PnpDevice -Class Display | Where-Object { $_.FriendlyName -eq 'Microsoft Basic Display Adapter' -and $_.Status -eq 'OK' } |
    ForEach-Object { pnputil /disable-device $_.InstanceId | Out-Null; Write-Host 'basic display adapter disabled' }

  # Xbox 360 controller driver: missing on Windows Server; from the Microsoft Update Catalog (2.5 MB, signed).
  if (-not (Get-WindowsDriver -Online | Where-Object { $_.OriginalFileName -like '*xusb*' })) {
    $cab = Get-File 'https://catalog.s.download.windowsupdate.com/msdownload/update/driver/drvs/2013/01/20289581_7385d6be1b053a35955a910f11436729a1d4cb56.cab' 'xusb.cab'
    $x = "$Dl\xusb"; New-Item -ItemType Directory -Force $x | Out-Null
    expand.exe $cab -F:* $x | Out-Null
    Get-ChildItem $x -Filter *.inf | ForEach-Object { pnputil /add-driver $_.FullName /install | Out-Null }
  }
  Write-Host "xusb: $([bool](Get-WindowsDriver -Online | Where-Object { $_.OriginalFileName -like '*xusb*' }))"

  # ViGEmBus (virtual Xbox 360 pad for Sunshine): every installer refuses Server, so the signed driver comes out
  # of the v1.17.333 MSI by an admin extract and goes in with nefarius's nefcon.
  if (-not (Get-PnpDevice -FriendlyName '*Virtual Gamepad Emulation Bus*' -ErrorAction SilentlyContinue)) {
    $nz = Get-File 'https://github.com/nefarius/nefcon/releases/download/v1.21.0/nefcon_v1.21.0.zip' 'nefcon.zip'
    Expand-Archive $nz "$Dl\nefcon" -Force
    $nef = Get-ChildItem "$Dl\nefcon" -Recurse -Filter nefconw.exe | Where-Object { $_.FullName -match 'x64' } | Select-Object -First 1
    $msi = Get-File 'https://github.com/nefarius/ViGEmBus/releases/download/setup-v1.17.333/ViGEmBusSetup_x64.msi' 'vigembus-1.17.msi'
    $vx = "$Dl\vigem"
    Start-Process msiexec.exe -ArgumentList '/a', $msi, '/qn', "TARGETDIR=$vx" -Wait
    $inf = Get-ChildItem $vx -Recurse -Filter ViGEmBus.inf | Select-Object -First 1
    if (-not $inf -or -not $nef) { throw "ViGEmBus: driver files not found under $vx" }
    & $nef.FullName --create-device-node --hardware-id 'Nefarius\ViGEmBus\Gen1' --class-name System --class-guid '4D36E97D-E325-11CE-BFC1-08002BE10318'
    & $nef.FullName --install-driver --inf-path $inf.FullName
  }
  Write-Host "vigembus: $((Get-PnpDevice -FriendlyName '*Virtual Gamepad Emulation Bus*' -ErrorAction SilentlyContinue).Status)"

  if (-not (Test-Path 'C:\Program Files\Sunshine\sunshine.exe')) {
    $msi = Get-File 'https://github.com/LizardByte/Sunshine/releases/download/v2026.914.233613/Sunshine-Windows-AMD64-installer.msi' 'sunshine.msi'
    Start-Process msiexec.exe -ArgumentList '/i', $msi, '/qn', '/norestart' -Wait
  }
  # Moonlight's app list starts the game directly: Argonia with shaders on or off (deploy.sh lays it again each deploy).
  & "$Root\infra\make-cards.ps1" | Out-Null
  Copy-Item "$Root\infra\sunshine-apps.json" 'C:\Program Files\Sunshine\config\apps.json' -Force
  Write-Host "sunshine: $((Get-Service SunshineService -ErrorAction SilentlyContinue).Status)"

  if (-not (Test-Path "$Root\moonlight-web\web-server.exe")) {
    $z = Get-File 'https://github.com/MrCreativ3001/moonlight-web-stream/releases/download/v3.0.1/moonlight-web-x86_64-pc-windows-gnu.zip' 'moonlight-web.zip'
    Expand-Archive $z "$Root\moonlight-web" -Force
    $exe = Get-ChildItem "$Root\moonlight-web" -Recurse -Filter web-server.exe | Select-Object -First 1
    if ($exe.DirectoryName -ne "$Root\moonlight-web") { Copy-Item "$($exe.DirectoryName)\*" "$Root\moonlight-web" -Recurse -Force }
  }
  Write-Host 'moonlight-web: installed'
  if (-not (Get-ScheduledTask -TaskName argonia-moonlight-web -ErrorAction SilentlyContinue)) {
    $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-ExecutionPolicy Bypass -File $Root\infra\moonlight-web.ps1"
    Register-ScheduledTask -TaskName argonia-moonlight-web -Action $a -Trigger (New-ScheduledTaskTrigger -AtStartup) -User SYSTEM -RunLevel Highest | Out-Null
  }

  if (-not (Test-Path "$Root\cloudflared.exe")) {
    Invoke-WebRequest 'https://github.com/cloudflare/cloudflared/releases/download/2026.10.5/cloudflared-windows-amd64.exe' -OutFile "$Root\cloudflared.exe" -UseBasicParsing
  }
  Write-Host 'cloudflared: installed'
  # The desktop is pinned to 1920x1080 at every logon, so the stream is never letterboxed.
  if (-not (Get-ScheduledTask -TaskName argonia-display -ErrorAction SilentlyContinue)) {
    $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File $Root\infra\display.ps1 pin"
    Register-ScheduledTask -TaskName argonia-display -Action $a -Trigger (New-ScheduledTaskTrigger -AtLogOn -User Administrator) -User Administrator -RunLevel Highest | Out-Null
  }
  Write-Host 'display: pinned at logon'
  # With the Virtual Display Driver installed, it is loaded with every screen shape at logon (vdd-boot.ps1).
  if ((Get-PnpDevice -Class Display -EA SilentlyContinue | ? { $_.FriendlyName -eq 'Virtual Display Driver' }) -and
      -not (Get-ScheduledTask -TaskName argonia-vdd -ErrorAction SilentlyContinue)) {
    $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File $Root\infra\vdd-boot.ps1"
    Register-ScheduledTask -TaskName argonia-vdd -Action $a -Trigger (New-ScheduledTaskTrigger -AtLogOn -User Administrator) -User Administrator -RunLevel Highest | Out-Null
    Disable-ScheduledTask -TaskName argonia-display | Out-Null   # the virtual display replaces the T4 head pin
  }
  # The machine stops itself after 15 minutes with no stream client and no agent (idle-stop.ps1).
  if (-not (Get-ScheduledTask -TaskName argonia-idle-stop -ErrorAction SilentlyContinue)) {
    $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File $Root\infra\idle-stop.ps1"
    $tr = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 5)
    Register-ScheduledTask -TaskName argonia-idle-stop -Action $a -Trigger $tr -User SYSTEM -RunLevel Highest | Out-Null
  }
  # The owner's desktop launchers: vanilla, or the 0.0 combat-test mods.
  $sh = New-Object -ComObject WScript.Shell
  foreach ($l in @(@('Skyrim (vanilla)', 'play-vanilla'), @('Skyrim (souls-like mods)', 'play-modded'))) {
    $s = $sh.CreateShortcut("C:\Users\Public\Desktop\$($l[0]).lnk")
    $s.TargetPath = 'powershell.exe'
    $s.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File $Root\infra\combat-mode.ps1 $($l[1])"
    $s.IconLocation = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\SkyrimSE.exe,0'
    $s.Save()
  }
  Write-Host 'idle-stop and launchers: set'
  # Host-side stream numbers for every client type (host-metrics.ps1), for comparing the three setups.
  if (-not (Get-ScheduledTask -TaskName argonia-host-metrics -ErrorAction SilentlyContinue)) {
    $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File $Root\infra\host-metrics.ps1"
    Register-ScheduledTask -TaskName argonia-host-metrics -Action $a -Trigger (New-ScheduledTaskTrigger -AtStartup) -User SYSTEM -RunLevel Highest | Out-Null
  }
}

function Install-Dcv {
  # Amazon DCV with its bundled virtual display and gamepad driver; licensed free on EC2 through the instance
  # role's read of the dcv-license bucket.
  if (-not (Get-Service dcvserver -ErrorAction SilentlyContinue)) {
    $msi = Get-File 'https://d1uj6qtbmh3dt5.cloudfront.net/nice-dcv-server-x64-Release.msi' 'dcv-server.msi'
    Start-Process msiexec.exe -ArgumentList '/i', $msi, 'ADDLOCAL=ALL', 'AUTOMATIC_SESSION_OWNER=Administrator', '/qn', '/norestart', "/l*v $Root\logs\dcv-install.log" -Wait
  }
  # DCV (it reads its settings from the system account's hive, not HKLM): no resize to the browser, no lock on
  # disconnect (a locked desktop hides the marker and blocks Sunshine), and no second sign-in: the Cloudflare
  # Access gate is the only way in and already admits only the owner (owner, 2026-10-29).
  New-PSDrive -Name HKU -PSProvider Registry -Root HKEY_USERS -ErrorAction SilentlyContinue | Out-Null
  $k = 'HKU:\S-1-5-18\Software\GSettings\com\nicesoftware\dcv'
  New-Item -Path "$k\display", "$k\security" -Force | Out-Null
  New-ItemProperty -Path "$k\display" -Name enable-client-resize -PropertyType DWord -Value 0 -Force | Out-Null
  New-ItemProperty -Path "$k\security" -Name os-auto-lock -PropertyType DWord -Value 0 -Force | Out-Null
  New-ItemProperty -Path "$k\security" -Name authentication -PropertyType String -Value 'none' -Force | Out-Null
  $perm = 'C:\Program Files\NICE\DCV\Server\conf\default.perm'
  $pl = @(Get-Content $perm)
  if (-not ($pl | ? { $_ -match '^\s*%any%\s+allow' })) {
    $i = [array]::IndexOf($pl, '[permissions]'); ($pl[0..$i] + '%any% allow builtin' + $pl[($i + 1)..($pl.Count - 1)]) | Set-Content $perm -Encoding ASCII
  }
  New-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name InactivityTimeoutSecs -PropertyType DWord -Value 0 -Force | Out-Null
  New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization' -Force | Out-Null
  New-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization' -Name NoLockScreen -PropertyType DWord -Value 1 -Force | Out-Null
  powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_NONE CONSOLELOCK 0; powercfg /SETACTIVE SCHEME_CURRENT
  New-NetFirewallRule -Name dcv-8443 -DisplayName 'DCV 8443' -Protocol TCP -LocalPort 8443 -Action Allow -ErrorAction SilentlyContinue | Out-Null
  New-NetFirewallRule -Name dcv-8443u -DisplayName 'DCV 8443 UDP' -Protocol UDP -LocalPort 8443 -Action Allow -ErrorAction SilentlyContinue | Out-Null
  Write-Host "dcv: $((Get-Service dcvserver -ErrorAction SilentlyContinue).Status)"
}

function Install-GameRedist {
  # Skyrim's runtimes (DirectX June 2010 for XINPUT1_3, VC++ 2015): Steam installs them on a first launch through
  # its own installer, but the game files here were copied in, and Windows Server ships neither.
  $g = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\_CommonRedist'
  if (-not (Test-Path C:\Windows\System32\xinput1_3.dll)) {
    Start-Process "$g\DirectX\Jun2010\DXSETUP.exe" -ArgumentList '/silent' -Wait
  }
  foreach ($vc in 'vc_redist.x64.exe', 'vc_redist.x86.exe') {
    Start-Process "$g\vcredist\2015\$vc" -ArgumentList '/install', '/quiet', '/norestart' -Wait
  }
  # Skyrim 1.7 aborts at start-up (0xC0000409 in ucrtbase) without Media Foundation, an optional feature on Server.
  if ((Get-WindowsFeature Server-Media-Foundation).InstallState -ne 'Installed') {
    Install-WindowsFeature Server-Media-Foundation | Out-Null
    Write-Host 'REBOOT-NEEDED'
  }
  Write-Host "game runtimes: xinput1_3 $(Test-Path C:\Windows\System32\xinput1_3.dll)"
}

function Install-Combat {
  # The 0.0 combat test (§d): the MO2 instance staged by combat_test_stage.py and copied to
  # C:\argonia\combat-stage. Steam's own launch stays vanilla; MO2's "SKSE" executable is the modded game.
  $game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
  $stage = "$Root\combat-stage"
  if (-not (Test-Path $stage)) { throw "no stage at ${stage}; run combat_test_stage.py and copy it first" }
  Copy-Item "$stage\root\*" $game -Force
  Copy-Item "$stage\MO2\*" "$Root\MO2" -Recurse -Force
  $g = $game.Replace('\', '\\')
  $m = "$Root\MO2".Replace('\', '/')
  @"
[General]
gameName=Skyrim Special Edition
gamePath=@ByteArray($g)
selected_profile=@ByteArray(Default)
first_start=false

[Settings]
check_for_updates=false
profile_local_inis=false
profile_local_saves=false

[customExecutables]
size=2
1\title=SKSE
1\binary=$($game.Replace('\', '/'))/skse64_loader.exe
1\workingDirectory=$($game.Replace('\', '/'))
1\arguments=
1\toolbar=true
1\ownicon=true
2\title=Pandora
2\binary=$m/tools/Pandora/Pandora Behaviour Engine+.exe
2\workingDirectory=$m/tools/Pandora
2\arguments=--auto_run --auto_close -o "$m/mods/Pandora Output"
2\toolbar=true
2\ownicon=true
"@ | Set-Content "$Root\MO2\ModOrganizer.ini" -Encoding ASCII
  Write-Host "combat: $((Get-ChildItem "$Root\MO2\mods" -Directory).Count) mod folders, skse loader $(Test-Path "$game\skse64_loader.exe")"
}

switch ($Stage) {
  'base' { Install-Base }
  'stream' { Install-Stream }
  'dcv'    { Install-Dcv }
  'combat' { Install-Combat }
  'redist' { Install-GameRedist }
  'all'  { Install-Base; Install-Stream; Install-Dcv }
  default { throw "unknown stage $Stage" }
}

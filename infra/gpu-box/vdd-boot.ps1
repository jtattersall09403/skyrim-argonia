# Once per boot, at logon (chunk 0.0 §c): load the Virtual Display Driver with a fine grid of sizes in every shape a
# player's screen can have, make it the primary display, and point Sunshine at it. Each stream then only picks the
# closest size (sunshine-prep.ps1), with no driver reload: a reload renumbers \\.\DISPLAYn, and Sunshine reads its
# output_name only when it starts. Run by the scheduled task "argonia-vdd" (setup.ps1); log in logs\vdd-boot.log.
$log = 'C:\argonia\logs\vdd-boot.log'
try {
  # Shapes (width / height): square, the Magic V5 unfolded (~1.08), 5:4, 4:3, 3:2, 16:10, 16:9, 2:1 and the V5
  # folded (~2.24), each at four widths. The driver takes only a few dozen sizes (81 failed, 24 loaded), so ~37.
  $aspects = 1.0, 1.083, 1.25, 1.333, 1.5, 1.538, 1.6, 1.778, 2.0, 2.24   # 1.538: MacBook Air
  $widths = 1600, 1920, 2240, 2560
  $sizes = New-Object System.Collections.Generic.List[object]
  foreach ($a in $aspects) {
    foreach ($w in $widths) {
      $h = [int]([math]::Round($w / $a / 2) * 2)
      if ($h -ge 720 -and $w * $h -le 2560 * 1600 * 1.4) { $sizes.Add(@($w, $h)) }
    }
  }
  $sizes.Add(@(1920, 1080))
  $xmlPath = 'C:\VirtualDisplayDriver\vdd_settings.xml'
  $x = [xml](Get-Content $xmlPath)
  $x.vdd_settings.gpu.friendlyname = 'Tesla T4'
  $res = $x.vdd_settings.resolutions; $res.RemoveAll()
  $seen = @{}
  foreach ($s in $sizes) {
    $k = "$($s[0])x$($s[1])"; if ($seen[$k]) { continue }; $seen[$k] = 1
    $e = $x.CreateElement('resolution')
    foreach ($kv in @(@('width', $s[0]), @('height', $s[1]), @('refresh_rate', 60))) {
      $c = $x.CreateElement($kv[0]); $c.InnerText = "$($kv[1])"; [void]$e.AppendChild($c)
    }
    [void]$res.AppendChild($e)
  }
  $x.Save($xmlPath)
  # The driver reads its settings only when it starts.
  $pnp = Get-PnpDevice -Class Display | ? { $_.FriendlyName -eq 'Virtual Display Driver' } | Select -First 1
  if (-not $pnp) { Add-Content $log "$(Get-Date -Format o) no Virtual Display Driver"; exit 0 }
  Disable-PnpDevice -InstanceId $pnp.InstanceId -Confirm:$false
  Enable-PnpDevice -InstanceId $pnp.InstanceId -Confirm:$false
  . C:\argonia\infra\display.ps1 -Cmd modes
  for ($i = 0; $i -lt 40 -and -not (Get-VddDevice); $i++) { Start-Sleep -Milliseconds 300 }
  Start-Sleep 1
  $vdd = Get-VddDevice
  $r = [Disp]::SoleDisplay($vdd, 1920, 1080, 60)
  # Sunshine captures this display from now on.
  $conf = 'C:\Program Files\Sunshine\config\sunshine.conf'
  $lines = @(Get-Content $conf -EA SilentlyContinue | ? { $_ -notmatch '^(output_name|address_family)\s*=' })
  ($lines + "output_name = $vdd") | Set-Content $conf -Encoding ASCII
  Restart-Service SunshineService
  Add-Content $log "$(Get-Date -Format o) $($seen.Count) sizes loaded; $vdd primary at 1920x1080 ($r); Sunshine output_name = $vdd"
} catch {
  Add-Content $log "$(Get-Date -Format o) error: $_"
}

# A black full-screen cover while the game launches, so the stream never shows the Windows desktop first.
# Step 1, only when a card switch has files to lay or remove: a bar and "Switching to <world>'s files: N of M", read
# from the progress file stack.ps1 writes ("phase|done|total"). Step 2: "Starting Skyrim" with moving dots.
# Closes when Skyrim's window appears, when the stack.ps1 that started it ($Parent) has gone without a game, or after
# 10 minutes. Started by stack.ps1 for every card.
param([int]$Parent = 0, [string]$World = '')
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$Progress = Join-Path (Split-Path $PSScriptRoot) 'stack-state\progress.txt'
$what = switch ($World) { 'NewWorld' { "the new world's files" } 'Argonia' { "Argonia's files" } 'vanilla' { 'plain Skyrim' } default { 'the game files' } }
$fg = [System.Drawing.Color]::FromArgb(220, 210, 190); $dim = [System.Drawing.Color]::FromArgb(60, 58, 52)
$f = New-Object System.Windows.Forms.Form
$f.FormBorderStyle = 'None'; $f.WindowState = 'Maximized'; $f.TopMost = $true; $f.ShowInTaskbar = $false
$f.BackColor = [System.Drawing.Color]::Black
$font = New-Object System.Drawing.Font('Segoe UI', 32)
$script:text = 'Starting Skyrim'; $script:frac = -1.0; $script:tick = 0
$f.Add_Paint({
  $g = $_.Graphics; $W = $f.ClientSize.Width; $H = $f.ClientSize.Height
  $g.TextRenderingHint = 'AntiAlias'
  if ($script:frac -ge 0) {
    $bw = [int]($W * 0.6); $bh = 28; $x = [int](($W - $bw) / 2); $y = [int]($H / 2 - 60)
    $g.FillRectangle((New-Object System.Drawing.SolidBrush $dim), $x, $y, $bw, $bh)
    $g.FillRectangle((New-Object System.Drawing.SolidBrush $fg), $x, $y, [int]($bw * $script:frac), $bh)
  }
  $sz = $g.MeasureString($script:text, $font)
  $g.DrawString($script:text, $font, (New-Object System.Drawing.SolidBrush $fg), ($W - $sz.Width) / 2, $H / 2)
})
$t = New-Object System.Windows.Forms.Timer; $t.Interval = 250
$start = Get-Date
$t.Add_Tick({
  $p = Get-Process SkyrimSE -EA SilentlyContinue | ? { $_.MainWindowHandle -ne 0 }
  $gone = $Parent -and -not (Get-Process -Id $Parent -EA SilentlyContinue) -and -not (Get-Process SkyrimSE -EA SilentlyContinue)
  if ($p -or $gone -or ((Get-Date) - $start).TotalSeconds -gt 600) { $t.Stop(); $f.Close(); return }
  $script:tick++
  $s = $null; try { $s = [IO.File]::ReadAllText($Progress).Split('|') } catch { }
  if ($s -and $s[0] -eq 'files' -and [int]$s[2] -gt 0) {
    $script:frac = [Math]::Min(1.0, [double]$s[1] / [double]$s[2])
    $script:text = "Step 1 of 2: switching to ${what}: {0:N0} of {1:N0}" -f [int]$s[1], [int]$s[2]
  } else {
    if ($script:frac -ge 0) { $script:frac = 1.0 }
    $script:text = 'Step 2 of 2: starting Skyrim' + ('.' * (1 + $script:tick % 3)).PadRight(3)
    if ($script:frac -lt 0) { $script:text = 'Starting Skyrim' + ('.' * (1 + $script:tick % 3)).PadRight(3) }
  }
  $f.Invalidate()
})
$t.Start()
[void]$f.ShowDialog()

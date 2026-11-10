# A black full-screen "Starting Skyrim..." cover while the game launches, so the stream never shows the Windows
# desktop first. Closes when Skyrim's window appears, when the stack.ps1 that started it ($Parent) has gone without
# a game, or after 10 minutes: laying a profile when the cards switch worlds takes minutes, so a short cap shows the desktop.
param([int]$Parent = 0)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$f = New-Object System.Windows.Forms.Form
$f.FormBorderStyle = 'None'; $f.WindowState = 'Maximized'; $f.TopMost = $true; $f.ShowInTaskbar = $false
$f.BackColor = [System.Drawing.Color]::Black; $f.Cursor = [System.Windows.Forms.Cursors]::Default
$l = New-Object System.Windows.Forms.Label
$l.Text = 'Starting Skyrim...'; $l.ForeColor = [System.Drawing.Color]::FromArgb(200, 200, 190, 160)
$l.Font = New-Object System.Drawing.Font('Segoe UI', 28); $l.AutoSize = $false; $l.Dock = 'Fill'; $l.TextAlign = 'MiddleCenter'
$f.Controls.Add($l)
$t = New-Object System.Windows.Forms.Timer; $t.Interval = 500
$start = Get-Date
$t.Add_Tick({
  $p = Get-Process SkyrimSE -EA SilentlyContinue | ? { $_.MainWindowHandle -ne 0 }
  $gone = $Parent -and -not (Get-Process -Id $Parent -EA SilentlyContinue) -and -not (Get-Process SkyrimSE -EA SilentlyContinue)
  if ($p -or $gone -or ((Get-Date) - $start).TotalSeconds -gt 600) { $t.Stop(); $f.Close() }
})
$t.Start()
[void]$f.ShowDialog()

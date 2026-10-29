# A black full-screen "Starting Skyrim..." cover while the game launches, so the stream never shows the Windows
# desktop first (owner, 2026-10-29). Closes when Skyrim's window appears, or after 90 s. Started by stack.ps1.
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
  if ($p -or ((Get-Date) - $start).TotalSeconds -gt 90) { $t.Stop(); $f.Close() }
})
$t.Start()
[void]$f.ShowDialog()

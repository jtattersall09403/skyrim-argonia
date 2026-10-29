# Moonlight shows each app as a picture only, so the cards carry the names (chunk 0.0 §c). Plain UI cards made
# here, not art: a dark panel, the name, a short line under it. Written to C:\argonia\cards\ for apps.json.
Add-Type -AssemblyName System.Drawing
$out = 'C:\argonia\cards'; New-Item -ItemType Directory -Force $out | Out-Null
$cards = @(
  @{ file = 'skyrim.png';       title = "SKYRIM";       sub = "vanilla";                 colour = '#2b3a2b' },
  @{ file = 'skyrim-souls.png'; title = "SKYRIM";       sub = "souls-like mods";         colour = '#3a2b2b' }
)
foreach ($c in $cards) {
  $bmp = New-Object System.Drawing.Bitmap 600, 800
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'
  $g.Clear([System.Drawing.ColorTranslator]::FromHtml($c.colour))
  $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(160, 201, 182, 122)), 6
  $g.DrawRectangle($pen, 24, 24, 552, 752)
  $fmt = New-Object System.Drawing.StringFormat; $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
  $big = New-Object System.Drawing.Font 'Segoe UI', 64, ([System.Drawing.FontStyle]::Bold)
  $small = New-Object System.Drawing.Font 'Segoe UI', 34
  $g.DrawString($c.title, $big, [System.Drawing.Brushes]::White, (New-Object System.Drawing.RectangleF 0, 250, 600, 140), $fmt)
  $g.DrawString($c.sub, $small, (New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(230, 232, 220, 190))), (New-Object System.Drawing.RectangleF 0, 400, 600, 120), $fmt)
  $bmp.Save("$out\$($c.file)", [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose()
}
"cards: $((Get-ChildItem $out -Filter *.png).Count)"

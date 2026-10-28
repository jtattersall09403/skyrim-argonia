# Capture the desktop as the stream sees it (Desktop Duplication through ffmpeg's ddagrab), unlike GDI capture,
# which returns stale frames for a DirectX game. Run in the desktop session (run.sh desktop).
#   grab.ps1 [out.png]
param([string]$Out = 'C:\argonia\logs\grab.png')
$ff = 'C:\argonia\tools\ffmpeg\bin\ffmpeg.exe'
if (-not (Test-Path $ff)) {
  $rel = Invoke-RestMethod 'https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest'
  $a = $rel.assets | ? { $_.name -match '^ffmpeg-N-.*-win64-gpl\.zip$' } | Select -First 1
  $z = 'C:\argonia\downloads\ffmpeg.zip'; Invoke-WebRequest $a.browser_download_url -OutFile $z -UseBasicParsing
  Expand-Archive $z C:\argonia\tools\ffmpeg-x -Force
  Move-Item (Get-ChildItem C:\argonia\tools\ffmpeg-x -Directory | Select -First 1).FullName C:\argonia\tools\ffmpeg
}
& $ff -hide_banner -loglevel error -y -f lavfi -i 'ddagrab=output_idx=0:framerate=10,hwdownload,format=bgra' -frames:v 1 $Out
"grabbed $Out $(Test-Path $Out)"

# Capture the desktop as the stream sees it (Desktop Duplication through ffmpeg's ddagrab), unlike GDI capture,
# which returns stale frames for a DirectX game. Run in the desktop session (run.sh desktop).
#   grab.ps1 [out.png] [-Frames N -Fps F]   N > 1: a still loop to out_01.png.. (a screen too short for one still)
param([string]$Out = 'C:\argonia\logs\grab.png', [int]$Frames = 1, [double]$Fps = 2)
$ff = 'C:\argonia\tools\ffmpeg\bin\ffmpeg.exe'
if (-not (Test-Path $ff)) {
  $rel = Invoke-RestMethod 'https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest'
  $a = $rel.assets | ? { $_.name -match '^ffmpeg-N-.*-win64-gpl\.zip$' } | Select -First 1
  $z = 'C:\argonia\downloads\ffmpeg.zip'; Invoke-WebRequest $a.browser_download_url -OutFile $z -UseBasicParsing
  Expand-Archive $z C:\argonia\tools\ffmpeg-x -Force
  Move-Item (Get-ChildItem C:\argonia\tools\ffmpeg-x -Directory | Select -First 1).FullName C:\argonia\tools\ffmpeg
}
# Fast clips (fps > 4 or more than 40 frames): PNGs written live drop and lag at 10+ fps, so the screen is recorded
# as a video (x264 ultrafast keeps 15 fps in real time: 45 frames in 3.4 s; this ffmpeg's nvenc does not open on the
# machines' driver), then cut into the same out_NN.png frames once it ends; the .mp4 is kept
# beside them (1.12 look 1: four lanes' L5 clips needed 10-30 fps, 2026-11-01).
if ($Frames -gt 40 -or ($Frames -gt 1 -and $Fps -gt 4)) {
  $mp4 = $Out -replace '\.png$', '.mp4'; $pat = $Out -replace '\.png$', '_%03d.png'
  & $ff -hide_banner -loglevel error -y -f lavfi -i "ddagrab=output_idx=0:framerate=$Fps,hwdownload,format=bgra" -frames:v $Frames -c:v libx264 -preset ultrafast -crf 16 -pix_fmt yuv420p $mp4
  & $ff -hide_banner -loglevel error -y -i $mp4 -fps_mode passthrough $pat
  "clipped $Frames at $Fps fps to $mp4 and $pat"; return
}
if ($Frames -gt 1) {
  $pat = $Out -replace '\.png$', '_%02d.png'
  & $ff -hide_banner -loglevel error -y -f lavfi -i "ddagrab=output_idx=0:framerate=$Fps,hwdownload,format=bgra" -frames:v $Frames $pat
  "grabbed $Frames to $pat"; return
}
& $ff -hide_banner -loglevel error -y -f lavfi -i 'ddagrab=output_idx=0:framerate=10,hwdownload,format=bgra' -frames:v 1 $Out
"grabbed $Out $(Test-Path $Out)"

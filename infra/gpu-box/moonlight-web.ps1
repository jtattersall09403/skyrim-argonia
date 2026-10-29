# Start Moonlight-Web next to Sunshine (chunk 0.0 §c). Run at boot by the scheduled task "argonia-moonlight-web".
# The page listens on localhost only (the sign-in gate fronts it); WebRTC media uses UDP 40000-40020 on the
# public address, which changes at every start, so it is read here each time.
$ErrorActionPreference = 'Stop'
$dir = 'C:\argonia\moonlight-web'
$t = Invoke-RestMethod -Method Put -Uri 'http://169.254.169.254/latest/api/token' -Headers @{ 'X-aws-ec2-metadata-token-ttl-seconds' = '60' }
$ip = Invoke-RestMethod -Uri 'http://169.254.169.254/latest/meta-data/public-ipv4' -Headers @{ 'X-aws-ec2-metadata-token' = $t }
New-NetFirewallRule -Name mlw-webrtc -DisplayName 'Moonlight-Web WebRTC' -Protocol UDP -LocalPort 40000-40020 -Action Allow -ErrorAction SilentlyContinue | Out-Null
Get-Process web-server -ErrorAction SilentlyContinue | Stop-Process -Force
# Start only once Sunshine answers: until then the tunnel's origin is down, so the play page keeps its "Starting
# the game machine" screen, instead of Moonlight-Web listing the host as offline with errors on "reload" and
# "wake" for a minute or two after boot (owner, 2026-10-29).
for ($i = 0; $i -lt 180; $i++) {
  $c = New-Object Net.Sockets.TcpClient
  try { $c.Connect('127.0.0.1', 47989); $c.Close(); break } catch { Start-Sleep 1 } finally { $c.Dispose() }
}
# One log pair per start, kept a week: a restart used to overwrite the log that explained the last session's drops.
$logs = 'C:\argonia\logs\moonlight-web'
New-Item -ItemType Directory -Force $logs | Out-Null
Get-ChildItem $logs -File | ? LastWriteTime -lt (Get-Date).AddDays(-7) | Remove-Item -Force
$stamp = Get-Date -Format 'yyyy-MM-ddTHH-mm-ss'
Start-Process "$dir\web-server.exe" -WorkingDirectory $dir -WindowStyle Hidden `
  -ArgumentList '--bind-address', '127.0.0.1:8080', '--webrtc-port-range', '40000:40020', '--webrtc-nat-1to1-host', $ip `
  -RedirectStandardOutput "$logs\$stamp.log" -RedirectStandardError "$logs\$stamp.err.log"
"moonlight-web started, WebRTC on $ip udp 40000-40020"

# Start Moonlight-Web next to Sunshine (chunk 0.0 §c). Run at boot by the scheduled task "argonia-moonlight-web".
# The page listens on localhost only (the sign-in gate fronts it); WebRTC media uses UDP 40000-40020 on the
# public address, which changes at every start, so it is read here each time.
$ErrorActionPreference = 'Stop'
$dir = 'C:\argonia\moonlight-web'
$t = Invoke-RestMethod -Method Put -Uri 'http://169.254.169.254/latest/api/token' -Headers @{ 'X-aws-ec2-metadata-token-ttl-seconds' = '60' }
$ip = Invoke-RestMethod -Uri 'http://169.254.169.254/latest/meta-data/public-ipv4' -Headers @{ 'X-aws-ec2-metadata-token' = $t }
New-NetFirewallRule -Name mlw-webrtc -DisplayName 'Moonlight-Web WebRTC' -Protocol UDP -LocalPort 40000-40020 -Action Allow -ErrorAction SilentlyContinue | Out-Null
Get-Process web-server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process "$dir\web-server.exe" -WorkingDirectory $dir -WindowStyle Hidden `
  -ArgumentList '--bind-address', '127.0.0.1:8080', '--webrtc-port-range', '40000:40020', '--webrtc-nat-1to1-host', $ip `
  -RedirectStandardOutput 'C:\argonia\logs\moonlight-web.log' -RedirectStandardError 'C:\argonia\logs\moonlight-web.err.log'
"moonlight-web started, WebRTC on $ip udp 40000-40020"

# The spot interruption watcher (chunk 1.8 §2): AWS gives a spot machine two minutes' notice before it takes it
# back (IMDSv2 latest/meta-data/spot/instance-action). On a notice the saves are pushed to the shared copy
# (saves-sync.ps1) and C:\argonia\state\interrupted.json says why the stream stopped ({utc, action, time}).
# Run at boot as SYSTEM by the scheduled task "argonia-spot-watch" (setup.ps1), polling every 5 s for ever.
#   spot-watch.ps1 [-Metadata <base url>] [-Once]     -Once: one poll, then exit (it prints what it did)
# The base URL is the parameter, else $env:ARGONIA_IMDS, else the real http://169.254.169.254.
# Nothing happens while SkyrimSE is not running (no game, nothing to save).
param([string]$Metadata = $(if ($env:ARGONIA_IMDS) { $env:ARGONIA_IMDS } else { 'http://169.254.169.254' }),
      [switch]$Once, [int]$Every = 5)
$State = 'C:\argonia\state'; New-Item -ItemType Directory -Force $State | Out-Null
$Saves = 'C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\Saves'
function J($o) { $o | ConvertTo-Json -Compress -Depth 4 }

# The notice, or $null (404: none). IMDSv2: a session token by PUT, then the read with it.
function Get-Notice([string]$base) {
  try {
    $tok = Invoke-RestMethod -Method Put -Uri "$base/latest/api/token" -TimeoutSec 2 -UseBasicParsing `
      -Headers @{ 'X-aws-ec2-metadata-token-ttl-seconds' = '300' }
    $r = Invoke-WebRequest -Uri "$base/latest/meta-data/spot/instance-action" -TimeoutSec 2 -UseBasicParsing `
      -Headers @{ 'X-aws-ec2-metadata-token' = "$tok" }
    if ($r.StatusCode -ne 200) { return $null }
    return ($r.Content | ConvertFrom-Json)
  } catch { return $null }  # 404 (no notice) or no metadata service
}

# One poll: returns what it did ('no game', 'no notice', 'handled', 'already handled').
function Invoke-Poll([string]$base) {
  if (-not (Get-Process SkyrimSE -EA SilentlyContinue)) { return 'no game' }
  $n = Get-Notice $base
  if (-not $n) { return 'no notice' }
  $f = "$State\interrupted.json"
  if (Test-Path $f) {  # one save per notice: AWS repeats the same notice until the machine goes
    $old = Get-Content $f -Raw | ConvertFrom-Json
    if ($old.time -eq $n.time -and $old.action -eq $n.action) { return 'already handled' }
  }
  J ([ordered]@{ utc = (Get-Date).ToUniversalTime().ToString('o'); action = "$($n.action)"; time = "$($n.time)" }) |
    Set-Content $f -Encoding ASCII
  # the saves to the pool's shared copy within the two minutes (1.8 §7)
  powershell -ExecutionPolicy Bypass -File C:\argonia\infra\saves-sync.ps1 push
  Write-EventLog -LogName Application -Source 'Application' -EventId 1 -EA SilentlyContinue `
    -Message "argonia spot-watch: notice $($n.action) at $($n.time)"
  return "handled"
}

if ($Once) { Invoke-Poll $Metadata; return }
while ($true) { $null = Invoke-Poll $Metadata; Start-Sleep -Seconds $Every }

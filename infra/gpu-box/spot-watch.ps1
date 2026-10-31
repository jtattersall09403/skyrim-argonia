# The spot interruption watcher (chunk 1.8 §2): AWS gives a spot machine two minutes' notice before it takes it
# back (IMDSv2 latest/meta-data/spot/instance-action). On a notice, ArgoniaCore writes the hidden suspend save for
# reason spot_reclaim (the bridge's `core-suspend` seam, the same line tools/bridge.py sends), and
# C:\argonia\state\interrupted.json says why the stream stopped ({utc, action, time}).
# Run at boot as SYSTEM by the scheduled task "argonia-spot-watch" (setup.ps1), polling every 5 s for ever.
#   spot-watch.ps1 [-Metadata <base url>] [-Once]     -Once: one poll, then exit (it prints what it did)
#   spot-watch.ps1 -Drill                             the check (tests/journeys/spot-watch.yaml): a mock metadata
#       server on 127.0.0.1 answers a stop notice, the watcher is pointed at it, and the JSON line printed says
#       whether ArgoniaSuspend.ess was written for spot_reclaim within 30 s of the mock's start.
# The base URL is the parameter, else $env:ARGONIA_IMDS, else the real http://169.254.169.254.
# Nothing happens while SkyrimSE is not running (no game, nothing to save).
param([string]$Metadata = $(if ($env:ARGONIA_IMDS) { $env:ARGONIA_IMDS } else { 'http://169.254.169.254' }),
      [switch]$Once, [switch]$Drill, [int]$Every = 5)
$State = 'C:\argonia\state'; New-Item -ItemType Directory -Force $State | Out-Null
$Skse = 'C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\SKSE'  # fixed: the task runs as SYSTEM
$Saves = 'C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\Saves'
$BridgePort = 47615
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

# The suspend save through ArgoniaBridge's socket: one line `<token> core-suspend spot_reclaim`, one JSON line back.
function Request-SuspendSave {
  $tf = "$Skse\ArgoniaBridge.token"
  if (-not (Test-Path $tf)) { return @{ ok = $false; error = 'no ArgoniaBridge token (the plugin is not loaded)' } }
  $token = (Get-Content $tf -Raw).Trim()
  try {
    $c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', $BridgePort)
    $c.ReceiveTimeout = 45000
    $s = $c.GetStream()
    $w = New-Object System.IO.StreamWriter($s); $w.NewLine = "`n"; $w.AutoFlush = $true
    $w.WriteLine("$token core-suspend spot_reclaim")
    $line = (New-Object System.IO.StreamReader($s)).ReadLine()
    $c.Close()
    return ($line | ConvertFrom-Json)
  } catch { return @{ ok = $false; error = "$_" } }
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
  $r = Request-SuspendSave
  Write-EventLog -LogName Application -Source 'Application' -EventId 1 -EA SilentlyContinue `
    -Message "argonia spot-watch: notice $($n.action) at $($n.time); suspend save: $(J $r)"
  return "handled: $(J $r)"
}

if ($Drill) {
  $port = 47620
  $t0 = Get-Date
  # The mock: IMDSv2's token PUT and a stop notice two minutes out, until stopped.
  $mock = Start-Job -ArgumentList $port -ScriptBlock {
    param($port)
    $l = New-Object System.Net.HttpListener; $l.Prefixes.Add("http://127.0.0.1:$port/"); $l.Start()
    $notice = '{"action":"stop","time":"' + (Get-Date).ToUniversalTime().AddMinutes(2).ToString('yyyy-MM-ddTHH:mm:ssZ') + '"}'
    while ($true) {
      $ctx = $l.GetContext(); $p = $ctx.Request.Url.AbsolutePath
      $body = if ($p -eq '/latest/api/token') { 'mock-token' } elseif ($p -eq '/latest/meta-data/spot/instance-action') { $notice } else { $ctx.Response.StatusCode = 404; '' }
      $b = [Text.Encoding]::ASCII.GetBytes($body); $ctx.Response.OutputStream.Write($b, 0, $b.Length); $ctx.Response.Close()
    }
  }
  Remove-Item "$State\interrupted.json" -EA SilentlyContinue
  $out = @(); $ok = $false
  try {
    while (((Get-Date) - $t0).TotalSeconds -lt 30 -and -not $ok) {
      $did = Invoke-Poll "http://127.0.0.1:$port"
      $out += $did
      $ess = Get-Item "$Saves\ArgoniaSuspend.ess" -EA SilentlyContinue
      $ok = $did -like 'handled*' -and $ess -and $ess.LastWriteTime -gt $t0
      if (-not $ok) { Start-Sleep -Seconds 1 }
    }
  } finally { Stop-Job $mock; Remove-Job $mock -Force }
  $ess = Get-Item "$Saves\ArgoniaSuspend.ess" -EA SilentlyContinue
  J ([ordered]@{ ok = [bool]$ok; seconds = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1); mock_start = $t0.ToString('o')
                 save_time = $(if ($ess) { $ess.LastWriteTime.ToString('o') } else { '' }); polls = $out
                 interrupted = $(if (Test-Path "$State\interrupted.json") { Get-Content "$State\interrupted.json" -Raw | ConvertFrom-Json } else { $null }) })
  return
}

if ($Once) { Invoke-Poll $Metadata; return }
while ($true) { $null = Invoke-Poll $Metadata; Start-Sleep -Seconds $Every }

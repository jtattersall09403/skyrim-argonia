# Talk to SkyLink AI's SKSE plugin (Nexus 175682, dev only) on its named pipe, without its MCP server: one JSON
# request per line ({"id","action","params"}), one JSON response per line (read from its PipeServer.cpp/Protocol.cpp).
# 0.2 uses it to read state in the smoke scene; 0.3 wraps it as tools/bridge.py.
#   skylink.ps1 -Calls '[{"action":"get_player_info"},{"action":"execute_command","params":{"command":"player.getpos x"}}]'
#   skylink.ps1 -CallsFile C:\argonia\logs\skylink-calls.json      the same, from a file (no quoting over SSH)
# Each answer is printed as "<ms>`t<response line>", the time from send to reply on the machine.
param([string]$Calls = '', [string]$CallsFile = '', [int]$TimeoutMs = 5000)
if ($CallsFile) { $Calls = Get-Content $CallsFile -Raw }
$ErrorActionPreference = 'Stop'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'SkyrimMCP', [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect($TimeoutMs)
$w = New-Object System.IO.StreamWriter($pipe); $w.AutoFlush = $true
$r = New-Object System.IO.StreamReader($pipe)
$i = 0
foreach ($c in (ConvertFrom-Json $Calls)) {
  $i++
  $req = [ordered]@{ id = "$i"; action = $c.action; params = $(if ($c.params) { $c.params } else { @{} }) }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $w.WriteLine((ConvertTo-Json $req -Compress -Depth 6))
  $t = $r.ReadLineAsync()
  if (-not $t.Wait($TimeoutMs)) { throw "no answer to $($c.action) in $TimeoutMs ms" }
  "$($sw.ElapsedMilliseconds)`t$($t.Result)"
  if ($c.sleep) { Start-Sleep -Milliseconds $c.sleep }
}
$pipe.Dispose()

# Ask houseCARL (Nexus 181738, dev only: an MCP server over the MO2 instance C:\argonia\MO2) questions without an AI
# host: speak MCP's stdio JSON-RPC to housecarl-mcp.exe directly (0.2 §b, the conflict report).
#   housecarl.ps1 -List                                   print the tool names and their input schemas
#   housecarl.ps1 -Calls '[{"name":"housecarl_load_order_status","arguments":{}}]'
param([string]$Calls = '[]', [switch]$List, [int]$TimeoutS = 600)
$ErrorActionPreference = 'Stop'
$exe = (Get-ChildItem C:\argonia\MO2\tools\housecarl -Recurse -Filter housecarl-mcp.exe | Select -First 1).FullName
$psi = New-Object System.Diagnostics.ProcessStartInfo $exe
$psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true; $psi.CreateNoWindow = $true
$psi.EnvironmentVariables['DOTNET_ROOT'] = 'C:\argonia\tools\dotnet'
$psi.EnvironmentVariables['DOTNET_gcServer'] = '0'
$p = [System.Diagnostics.Process]::Start($psi)
$utf8 = New-Object System.Text.UTF8Encoding $false
$in = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream, $utf8); $in.AutoFlush = $true
$script:id = 0
function Rpc($method, $params, [switch]$Note) {
  $msg = [ordered]@{ jsonrpc = '2.0'; method = $method; params = $params }
  if (-not $Note) { $script:id++; $msg.id = $script:id }
  $in.WriteLine((ConvertTo-Json $msg -Compress -Depth 20))
  if ($Note) { return }
  $deadline = (Get-Date).AddSeconds($TimeoutS)
  while ((Get-Date) -lt $deadline) {
    $t = $p.StandardOutput.ReadLineAsync()
    if (-not $t.Wait([int](($deadline - (Get-Date)).TotalMilliseconds))) { break }
    if ($null -eq $t.Result) { break }
    $r = $t.Result | ConvertFrom-Json
    if ($r.id -eq $script:id) { return $r }
  }
  throw "no answer to $method; stderr: $($p.StandardError.ReadToEnd())"
}
try {
  [void](Rpc 'initialize' @{ protocolVersion = '2025-06-18'; capabilities = @{}; clientInfo = @{ name = 'argonia-stack'; version = '0.2' } })
  Rpc 'notifications/initialized' @{} -Note
  if ($List) {
    (Rpc 'tools/list' @{}).result.tools | % { "== $($_.name)"; ConvertTo-Json $_.inputSchema -Depth 8 -Compress }
  }
  foreach ($c in (ConvertFrom-Json $Calls)) {
    $r = Rpc 'tools/call' @{ name = $c.name; arguments = $c.arguments }
    "== $($c.name)"
    if ($r.error) { "ERROR: $(ConvertTo-Json $r.error -Compress)" } else { $r.result.content | % { $_.text } }
  }
} finally { $in.Close(); if (-not $p.WaitForExit(5000)) { $p.Kill() } }

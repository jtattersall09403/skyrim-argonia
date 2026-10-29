# DEV ONLY: send one request to ArgoniaBridge and print its reply line. On the game machine:
#   powershell -File ping.ps1 [-Command ping] [-Token <hex>]   (the token defaults to the file the plugin wrote)
# Exit 0 when the reply says ok, 1 otherwise; `-Token bad` is the fail-on-purpose case.
param([string]$Command = 'ping', [string]$Token = '', [int]$TimeoutMs = 5000)
$ErrorActionPreference = 'Stop'
if (-not $Token) {
  $f = Get-ChildItem "$env:USERPROFILE\Documents\My Games\Skyrim Special Edition*\SKSE\ArgoniaBridge.token" -EA SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $f) { Write-Output '{"ok":false,"error":"no ArgoniaBridge.token: is the game running with the plugin?"}'; exit 1 }
  $Token = (Get-Content $f.FullName -Raw).Trim()
}
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'argonia-bridge', [System.IO.Pipes.PipeDirection]::InOut)
try { $pipe.Connect($TimeoutMs) } catch { Write-Output '{"ok":false,"error":"pipe not reachable"}'; exit 1 }
$w = New-Object System.IO.StreamWriter($pipe); $w.AutoFlush = $true
$r = New-Object System.IO.StreamReader($pipe)
$w.Write("$Token $Command`n")
$reply = $r.ReadLine()
$pipe.Dispose()
Write-Output $reply
if ($reply -match '"ok":true') { exit 0 } else { exit 1 }

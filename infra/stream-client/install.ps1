# Install our client page on the game machine (chunk 0.0 §c). Run by deploy.sh from C:\argonia\stream-client\
# after it copies static\, marker\ and collector\ there.
#   install.ps1            compile the marker and collector, register their tasks, swap in our static\, restart Moonlight-Web
#   install.ps1 -Restore   put upstream's original static\ back and restart Moonlight-Web
param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$mlw = 'C:\argonia\moonlight-web'
$backup = "$mlw\static.upstream-v3.0.1"
$bin = "$here\bin"
$csc = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'

function Restart-MoonlightWeb {
  Start-ScheduledTask argonia-moonlight-web
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try { if ((Invoke-WebRequest http://127.0.0.1:8080/stream.html -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { "moonlight-web serving"; return } } catch { }
  }
  throw 'moonlight-web did not come back on 8080'
}

if ($Restore) {
  if (-not (Test-Path $backup)) { throw "no backup at $backup" }
  robocopy $backup "$mlw\static" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
  Restart-MoonlightWeb
  'restored upstream static'
  return
}

# 1. the two programs, compiled here with the .NET Framework's compiler
New-Item -ItemType Directory -Force $bin, 'C:\argonia\logs\stream-metrics', 'C:\argonia\logs\marker' | Out-Null
Get-Process argonia-input-marker, argonia-stream-collector -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 300
& $csc /nologo /optimize+ /target:winexe /out:"$bin\argonia-input-marker.exe" /r:System.Windows.Forms.dll /r:System.Drawing.dll "$here\marker\marker.cs"
if ($LASTEXITCODE) { throw 'marker did not compile' }
& $csc /nologo /optimize+ /target:exe /out:"$bin\argonia-stream-collector.exe" "$here\collector\collector.cs"
if ($LASTEXITCODE) { throw 'collector did not compile' }

# 2. the collector at boot (SYSTEM, local only); the marker at the Administrator's logon, in that interactive desktop
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1)
$col = New-ScheduledTaskAction -Execute "$bin\argonia-stream-collector.exe"
Register-ScheduledTask -TaskName argonia-stream-collector -Action $col -Trigger (New-ScheduledTaskTrigger -AtStartup) -Settings $set `
  -Principal (New-ScheduledTaskPrincipal -UserId SYSTEM -LogonType ServiceAccount -RunLevel Highest) -Force | Out-Null
$mk = New-ScheduledTaskAction -Execute "$bin\argonia-input-marker.exe" -Argument '24 60'
Register-ScheduledTask -TaskName argonia-input-marker -Action $mk -Trigger (New-ScheduledTaskTrigger -AtLogOn -User Administrator) -Settings $set `
  -Principal (New-ScheduledTaskPrincipal -UserId Administrator -LogonType Interactive -RunLevel Highest) -Force | Out-Null
Start-ScheduledTask argonia-stream-collector
Start-ScheduledTask argonia-input-marker  # runs only while Administrator is logged on (the box auto-logs on)

# 3. our static\ in place of upstream's (backed up once)
if (-not (Test-Path $backup)) { Copy-Item "$mlw\static" $backup -Recurse; "backed up upstream static to $backup" }
robocopy "$here\static" "$mlw\static" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
Restart-MoonlightWeb

# 4. checks
for ($i = 0; $i -lt 20; $i++) { try { $h = Invoke-RestMethod http://127.0.0.1:8091/argonia-metrics/health -TimeoutSec 2; break } catch { Start-Sleep -Milliseconds 300 } }
"collector: $($h | ConvertTo-Json -Compress)"
"marker running: $([bool](Get-Process argonia-input-marker -ErrorAction SilentlyContinue))"
$page = (Invoke-WebRequest http://127.0.0.1:8080/stream.html -UseBasicParsing).Content
"stream.html loads argonia.js: $($page.Contains('argonia.js'))"
"argonia.js status: $((Invoke-WebRequest http://127.0.0.1:8080/argonia.js -UseBasicParsing).StatusCode)"

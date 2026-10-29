# The record pipeline's game-machine jobs (0.4 §a), run by records_jobs.sh from the build VM. Inputs arrive in
# C:\argonia\records\in, outputs leave from C:\argonia\records\out. Nothing here is committed or shipped.
#   -Stage papyrus   compile in\papyrus\*.psc with the CK's PapyrusCompiler against the base sources from the CK's
#                    own Scripts.zip (unpacked once to Data\Source\Scripts), out\papyrus\*.pex + compile.log
#   -Stage ckload    load in\Argonia.esm in the Creation Kit with file logging on, out\ck-warnings.log
#                    (advisory until stable twice, decision 0018 §3; the plugin is chosen in the Data dialog by
#                    UI Automation, unproven until its first run)
#   -Stage bsarch    pack our own files (out\papyrus\*.pex as scripts\) into out\Argonia.bsa with BSArch
param([ValidateSet('papyrus', 'ckload', 'bsarch')][string]$Stage = 'papyrus')
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Data = "$Game\Data"
$Root = 'C:\argonia\records'
$In = "$Root\in"; $Out = "$Root\out"
New-Item -ItemType Directory -Force $In, $Out | Out-Null

function Need($path, $what) { if (-not (Test-Path $path)) { throw "$what missing: $path" } }

switch ($Stage) {
  'papyrus' {
    $pc = "$Game\Papyrus Compiler\PapyrusCompiler.exe"
    Need $pc 'the Creation Kit (Steam: Skyrim Special Edition: Creation Kit)'
    $base = "$Data\Source\Scripts"
    if (-not (Test-Path "$base\Actor.psc")) {
      Need "$Data\Scripts.zip" "the CK's Scripts.zip"
      Expand-Archive "$Data\Scripts.zip" -DestinationPath $Data -Force   # unpacks Source\Scripts
    }
    $flags = "$base\TESV_Papyrus_Flags.flg"; Need $flags 'the Papyrus flags file'
    $dst = "$Out\papyrus"; Remove-Item $dst -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory $dst | Out-Null
    & $pc "$In\papyrus" -all -f="$flags" -i="$In\papyrus;$base" -o="$dst" *> "$Out\compile.log"
    $rc = $LASTEXITCODE
    Get-Content "$Out\compile.log" -Tail 20
    $n = @(Get-ChildItem "$dst\*.pex").Count
    "papyrus: rc=$rc, $n .pex"
    if ($rc -ne 0) { exit 1 }
  }
  'ckload' {
    $ck = "$Game\CreationKit.exe"; Need $ck 'the Creation Kit'
    Need "$In\Argonia.esm" 'the plugin'
    # Whatever stood in Data and the CK's custom ini is set aside and put back, whatever happens.
    $keep = "$Root\kept"; New-Item -ItemType Directory -Force $keep | Out-Null
    foreach ($f in "$Data\Argonia.esm", "$Game\CreationKitCustom.ini") { if (Test-Path $f) { Move-Item $f $keep -Force } }
    $p = $null
    try {
    Copy-Item "$In\Argonia.esm" "$Data\Argonia.esm" -Force
    $log = "$Out\ck-warnings.log"; Remove-Item $log -EA SilentlyContinue
    # CreationKitCustom.ini overrides CreationKit.ini; file logging writes every load warning.
    "[General]`r`nbAllowMultipleMasterLoads=1`r`n[Log]`r`nbEnableFileLog=1`r`nsFileName=$log`r`n" |
      Set-Content "$Game\CreationKitCustom.ini" -Encoding ascii
    $p = Start-Process $ck -WorkingDirectory $Game -PassThru
    Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms
    $A = [System.Windows.Automation.AutomationElement]
    $deadline = (Get-Date).AddMinutes(3); $dlg = $null
    while (-not $dlg -and (Get-Date) -lt $deadline) {
      Start-Sleep 2
      $dlg = $A::RootElement.FindFirst('Children', (New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, 'Data')))
    }
    if (-not $dlg) { throw 'ckload: the Data dialog never opened' }
    $item = $dlg.FindFirst('Descendants', (New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, 'Argonia.esm')))
    if (-not $item) { throw 'ckload: Argonia.esm not listed in the Data dialog' }
    $item.SetFocus(); [System.Windows.Forms.SendKeys]::SendWait(' ')        # tick it
    $ok = $dlg.FindFirst('Descendants', (New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, 'OK')))
    $ok.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    # Loading ends when the log stops growing for 20 s.
    $last = -1; $still = 0
    while ($still -lt 10 -and -not $p.HasExited) {
      Start-Sleep 2; $len = (Get-Item $log -EA SilentlyContinue).Length
      if ($len -eq $last) { $still++ } else { $still = 0; $last = $len }
    }
    } finally {
      if ($p) { Stop-Process $p -Force -EA SilentlyContinue }
      Remove-Item "$Data\Argonia.esm", "$Game\CreationKitCustom.ini" -Force -EA SilentlyContinue
      if (Test-Path "$keep\Argonia.esm") { Move-Item "$keep\Argonia.esm" $Data -Force }
      if (Test-Path "$keep\CreationKitCustom.ini") { Move-Item "$keep\CreationKitCustom.ini" $Game -Force }
    }
    "ckload: $(@(Get-Content $log -EA SilentlyContinue).Count) log lines"
  }
  'bsarch' {
    $ba = 'C:\argonia\tools\BSArch\BSArch.exe'; Need $ba 'BSArch (xEdit tools; setup.ps1 installs it)'
    $stage = "$Root\bsa"; Remove-Item $stage -Recurse -Force -EA SilentlyContinue
    New-Item -ItemType Directory -Force "$stage\scripts" | Out-Null
    Copy-Item "$Out\papyrus\*.pex" "$stage\scripts\"
    & $ba pack $stage "$Out\Argonia.bsa" -sse -z -mt
    if ($LASTEXITCODE -ne 0) { exit 1 }
    & $ba "$Out\Argonia.bsa" -list | Set-Content "$Out\bsa-contents.txt"
    "bsarch: $(@(Get-Content "$Out\bsa-contents.txt").Count) listed"
  }
}

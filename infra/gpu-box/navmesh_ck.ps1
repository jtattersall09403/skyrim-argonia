# The Creation Kit's own navmesh generator as the check on our DotRecast job (2.W4 §b, decision 0018), on the
# Windows game machine. DRAFTED, NOT RUN: the UI Automation names below are unproven until the first run, which is
# owed with 0.2's machine. Nothing here is committed or shipped; the CK's output stays on the machine or in out/.
#   in\ArgoniaWorld.esm   built by `make plugin` on the build VM (no navmesh), copied in by records_jobs.sh
#   -Cells "-60,8,-53,15" the box to generate (default: the Claywater block, `python -m tools.navmesh block claywater`)
#   out\ArgoniaWorld-ck.esm  the plugin as the CK saved it, with its NAVM per cell and its NAVI
# The build VM then reads out\ArgoniaWorld-ck.esm with tools/navmesh (esm.py, nvnm.py) and runs the same L1 checks
# and the comparison (triangle count, walkable coverage, islands, seam links per cell) against out/navmesh/claywater.
param([string]$Cells = '-60,8,-53,15', [int]$TimeoutMin = 60)
$ErrorActionPreference = 'Stop'
$Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$Data = "$Game\Data"
$Root = 'C:\argonia\records'
$In = "$Root\in"; $Out = "$Root\out"
New-Item -ItemType Directory -Force $In, $Out | Out-Null
function Need($path, $what) { if (-not (Test-Path $path)) { throw "$what missing: $path" } }
$ck = "$Game\CreationKit.exe"; Need $ck 'the Creation Kit'
Need "$In\ArgoniaWorld.esm" 'the world plugin'
$x0, $y0, $x1, $y1 = $Cells.Split(',') | ForEach-Object { [int]$_ }

$keep = "$Root\kept-nav"; New-Item -ItemType Directory -Force $keep | Out-Null
foreach ($f in "$Data\ArgoniaWorld.esm", "$Game\CreationKitCustom.ini") { if (Test-Path $f) { Move-Item $f $keep -Force } }
$p = $null
try {
  Copy-Item "$In\ArgoniaWorld.esm" "$Data\ArgoniaWorld.esm" -Force
  $log = "$Out\ck-navmesh.log"; Remove-Item $log -EA SilentlyContinue
  # The CK's Recast generator with its defaults (the values tools/navmesh/params.py copies), file logging on.
  "[General]`r`nbAllowMultipleMasterLoads=1`r`n[Log]`r`nbEnableFileLog=1`r`nsFileName=$log`r`n" |
    Set-Content "$Game\CreationKitCustom.ini" -Encoding ascii
  $p = Start-Process $ck -WorkingDirectory $Game -PassThru
  Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms
  $A = [System.Windows.Automation.AutomationElement]
  function Find($root, $name, $min = 3) {
    $deadline = (Get-Date).AddMinutes($min)
    while ((Get-Date) -lt $deadline) {
      $e = $root.FindFirst('Descendants', (New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, $name)))
      if ($e) { return $e }
      Start-Sleep 2
    }
    throw "navmesh_ck: '$name' never appeared"
  }
  function Click($e) { $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }
  # 1. Data dialog: ArgoniaWorld.esm ticked and set active (unproven names: 'Data', 'Set as Active File', 'OK').
  $dlg = Find $A::RootElement 'Data'
  $item = Find $dlg 'ArgoniaWorld.esm'
  $item.SetFocus(); [System.Windows.Forms.SendKeys]::SendWait(' ')
  Click (Find $dlg 'Set as Active File')
  Click (Find $dlg 'OK')
  $main = Find $A::RootElement 'Creation Kit' 20
  # 2. Per cell of the box: load it in the render window (Cell View: worldspace ARG_Province, the cell's X, Y),
  #    then Navmesh > Generate (Recast, the dialog's defaults) for the loaded cell. The CK offers no command line
  #    for this, so each step is a menu path; the whole box can instead go through "Generate for this worldspace"
  #    with a cell range when the dialog offers it (unproven).
  for ($y = $y1; $y -ge $y0; $y--) {
    for ($x = $x0; $x -le $x1; $x++) {
      [System.Windows.Forms.SendKeys]::SendWait('^{F7}')  # unproven: the CK's "go to cell" binding
      $go = Find $A::RootElement 'Go to Cell' 1
      [System.Windows.Forms.SendKeys]::SendWait("ARG_Province $x $y{ENTER}")
      Click (Find $main 'Navmesh')
      Click (Find $main 'Generate Navmesh...')
      $gen = Find $A::RootElement 'Navmesh Generation' 1
      Click (Find $gen 'Generate')
      $deadline = (Get-Date).AddMinutes(5)
      while ((Find $A::RootElement 'Navmesh Generation' 0) -and (Get-Date) -lt $deadline) { Start-Sleep 2 }
      "navmesh_ck: cell $x,$y generated"
    }
  }
  # 3. Finalize (Navmesh > Finalize Cell Navmesh links the seams and writes the NAVI), then save.
  Click (Find $main 'Navmesh'); Click (Find $main 'Finalize Cell Navmesh')
  [System.Windows.Forms.SendKeys]::SendWait('^s')
  Start-Sleep 10
  Copy-Item "$Data\ArgoniaWorld.esm" "$Out\ArgoniaWorld-ck.esm" -Force
} finally {
  if ($p) { Stop-Process $p -Force -EA SilentlyContinue }
  Remove-Item "$Data\ArgoniaWorld.esm", "$Game\CreationKitCustom.ini" -Force -EA SilentlyContinue
  if (Test-Path "$keep\ArgoniaWorld.esm") { Move-Item "$keep\ArgoniaWorld.esm" $Data -Force }
  if (Test-Path "$keep\CreationKitCustom.ini") { Move-Item "$keep\CreationKitCustom.ini" $Game -Force }
}
"navmesh_ck: $(@(Get-Content $log -EA SilentlyContinue).Count) log lines; out\ArgoniaWorld-ck.esm"

# DEV ONLY: take named laid paths out of Data for a bisect, and put them back exactly (a move keeps the hard link,
# so stack.ps1 verify passes once they are back). 0.2 §c's dodge bisect.
#   aside.ps1 -Do out  -Paths 'SKSE\Plugins\AnimationMotionRevolution.dll','meshes\...\Dynamic Dodge - TK Dodge RE-0.55-rc3'
#   aside.ps1 -Do back                     every path taken out, returned
param([Parameter(Mandatory)][ValidateSet('out', 'back')][string]$Do, [string[]]$Paths = @())
$ErrorActionPreference = 'Stop'
$Data = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
$Hold = 'C:\argonia\stack-state\aside'
if (Get-Process SkyrimSE -EA SilentlyContinue) { throw 'Skyrim is running: kill first' }
if ($Do -eq 'out') {
  foreach ($p in $Paths) {
    $src = Join-Path $Data $p; $dst = Join-Path $Hold $p
    if (-not (Test-Path -LiteralPath $src)) { throw "not laid: $p" }
    New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
    Move-Item -LiteralPath $src $dst
    "aside: $p"
  }
} else {
  if (-not (Test-Path $Hold)) { 'nothing aside'; return }
  Get-ChildItem $Hold -Recurse -File | % {
    $rel = $_.FullName.Substring($Hold.Length + 1); $dst = Join-Path $Data $rel
    New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
    Move-Item -LiteralPath $_.FullName $dst
  }
  Remove-Item $Hold -Recurse -Force
  'back: all'
}

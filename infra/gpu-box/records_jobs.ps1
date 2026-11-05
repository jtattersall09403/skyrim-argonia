# The game-machine jobs, run by records_jobs.sh from the build VM. Inputs arrive in
# C:\argonia\records\in, outputs leave from C:\argonia\records\out. Nothing here is committed or shipped.
#   -Stage papyrus   compile in\papyrus\*.psc with the CK's PapyrusCompiler against the base sources from the CK's
#                    own Scripts.zip (unpacked once to records\base\Source\Scripts), out\papyrus\*.pex + compile.log
#   -Stage bsarch    pack our own files (out\papyrus\*.pex as scripts\) into out\Argonia.bsa with BSArch
param([ValidateSet('papyrus', 'bsarch')][string]$Stage = 'papyrus')
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
    # The compiler is built for CLR 2 (.NET 3.5), which the machine lacks (rc 0x80131700, game-9); it runs on CLR 4.
    $cfg = "$pc.config"
    if (-not (Test-Path $cfg)) {
      '<?xml version="1.0"?><configuration><startup useLegacyV2RuntimeActivationPolicy="true"><supportedRuntime version="v4.0"/></startup></configuration>' |
        Set-Content $cfg -Encoding ascii
    }
    # Unpacked outside Data, where stack.ps1 off (every deploy's fresh launch) would remove it.
    $base = "$Root\base\Source\Scripts"
    if (-not (Test-Path "$base\Actor.psc")) {
      Need "$Data\Scripts.zip" "the CK's Scripts.zip"
      Expand-Archive "$Data\Scripts.zip" -DestinationPath "$Root\base" -Force   # unpacks Source\Scripts
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

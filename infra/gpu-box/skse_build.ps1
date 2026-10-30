# Build Argonia's SKSE plugins on the game machine with MSVC (chunk 0.3 §b; driven by skse_build.sh from the
# build VM). Idempotent: each tool step checks before it acts.
#   -Stage tools   VS 2026 Build Tools (C++ workload: MSVC, Windows SDK, CMake, Ninja), MinGit, vcpkg
#   -Stage build   unpack C:\argonia\skse\src.tar, configure, build, run the core tests under MSVC, install,
#                  copy the plugins into the MO2 mod folders (dist and dev-only apart)
#   -Stage all     both (the default)
# Prints REBOOT-NEEDED when the Build Tools installer asks for one (run.sh's convention), SKSE-BUILD OK at the end.
param([ValidateSet('tools', 'build', 'all')][string]$Stage = 'all',
      [ValidateSet('windows-dev', 'windows-release')][string]$Preset = 'windows-dev',
      [string]$Root = 'C:\argonia\skse',
      [string]$ModDir = 'C:\argonia\MO2\mods',
      # A compile-only pass on one target (SKSE_TARGET in skse_build.sh): no tests, no install, for fixing compile errors fast
      [string]$Target = '')
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Tools = 'C:\argonia\tools'
$Vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
# CommonLibSSE-NG v15.2.0's prebuilt bundle was made by cl 19.51 (its TOOLSET_VERSION.txt): VS 2026 (18.x).
# A different major.minor still builds, from source (~16 min) instead of linking the bundle.
$VsBootstrapper = 'https://aka.ms/vs/18/stable/vs_buildtools.exe'
$MinGitUrl = 'https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.4/MinGit-2.56.0.4-64-bit.zip'
$MinGitSha256 = 'e3bf78351fe777fba47ddee5950082f8a98bb0f02604fdc7ba3ee2cb68ffa877'
New-Item -ItemType Directory -Force $Tools, $Root, 'C:\argonia\logs' | Out-Null

function Find-VS {
  if (-not (Test-Path $Vswhere)) { return $null }
  $p = & $Vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
  if ($p) { return $p.Trim() } else { return $null }
}

function Install-Tools {
  if (-not (Find-VS)) {
    $exe = "$Tools\vs_buildtools.exe"
    Invoke-WebRequest $VsBootstrapper -OutFile $exe
    $p = Start-Process $exe -Wait -PassThru -ArgumentList @('--quiet', '--wait', '--norestart', '--nocache',
      '--add', 'Microsoft.VisualStudio.Workload.VCTools', '--includeRecommended')
    if ($p.ExitCode -eq 3010) { Write-Host 'vs: installed, REBOOT-NEEDED'; return }
    if ($p.ExitCode -ne 0) { throw "vs_buildtools exit $($p.ExitCode) (logs: %TEMP%\dd_*.log)" }
  }
  Write-Host "vs: $(Find-VS)"

  $git = "$Tools\mingit\cmd\git.exe"
  if (-not (Test-Path $git)) {
    $zip = "$Tools\mingit.zip"
    Invoke-WebRequest $MinGitUrl -OutFile $zip
    if ((Get-FileHash $zip -Algorithm SHA256).Hash -ne $MinGitSha256.ToUpper()) { throw 'MinGit hash mismatch' }
    Expand-Archive $zip "$Tools\mingit" -Force; Remove-Item $zip
  }
  Write-Host "git: $(& $git --version)"

  # vcpkg needs history for vcpkg.json's builtin-baseline, so a full clone; bootstrap fetches its pinned tool.
  $vcpkg = "$Tools\vcpkg"
  if (-not (Test-Path "$vcpkg\vcpkg.exe")) {
    if (-not (Test-Path "$vcpkg\.git")) { Run 'vcpkg clone' "$git clone --quiet https://github.com/microsoft/vcpkg.git $vcpkg" }
    Run 'vcpkg bootstrap' "$vcpkg\bootstrap-vcpkg.bat -disableMetrics"
  }
  Write-Host "vcpkg: $(& "$vcpkg\vcpkg.exe" version | Select-Object -First 1)"
}

function Enter-VsDevShell {
  $vs = Find-VS
  if (-not $vs) { throw 'no VS Build Tools: run -Stage tools' }
  $env:PATH = "$Tools\mingit\cmd;$env:PATH"
  # vcvars64 sets cl, link, the SDK, and VS's bundled CMake and Ninja on PATH.
  cmd /c "call `"$vs\VC\Auxiliary\Build\vcvars64.bat`" >nul && set" | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') { Set-Item "env:$($Matches[1])" $Matches[2] }
  }
  $env:VCPKG_ROOT = "$Tools\vcpkg"
  Write-Host "msvc: $((cmd /c 'cl 2>&1') | Select-Object -First 1)"
  Write-Host "cmake: $((cmake --version) | Select-Object -First 1)"
}

# Native tools run through cmd so their stderr never becomes a PowerShell error record (Windows PowerShell 5.1);
# everything goes to the log, and a failure prints the log's tail. Paths under C:\argonia have no spaces, so
# the command lines need no inner quotes (cmd /c strips a leading quote pair).
$Log = "C:\argonia\logs\skse-build.log"
function Run([string]$what, [string]$cmdline) {
  Add-Content $Log "== ${what}: $cmdline"
  cmd /c "$cmdline >> $Log 2>&1"
  if ($LASTEXITCODE -ne 0) { Get-Content $Log -Tail 40 | Write-Host; throw "$what failed (exit $LASTEXITCODE), log $Log" }
}

function Build {
  $src = "$Root\src"
  if (-not (Test-Path "$Root\src.tar")) { throw "no $Root\src.tar: skse_build.sh sends it" }
  # The tar keeps each file's time, so a fresh tree rebuilds only what changed.
  if (Test-Path $src) { Remove-Item $src -Recurse -Force }
  New-Item -ItemType Directory -Force $src | Out-Null
  Set-Content $Log "skse_build $Preset $(Get-Date -Format s)"
  Run 'unpack' "tar -xf $Root\src.tar -C $src"
  Enter-VsDevShell
  Push-Location $src
  try {
    Run 'configure' "cmake --preset $Preset"
    Select-String -Path $Log -Pattern 'CommonLibSSE|prebuilt' | Select-Object -Last 4 | ForEach-Object { Write-Host $_.Line }
    if ($Target) { Run 'build' "cmake --build --preset $Preset --target $Target"; Write-Host "SKSE-TARGET OK ($Target, compile only)"; return }
    Run 'build' "cmake --build --preset $Preset"
    Run 'tests' "ctest --test-dir $Root\build\$Preset --output-on-failure"
    Select-String -Path $Log -Pattern 'tests passed|tests failed' | ForEach-Object { Write-Host "ctest: $($_.Line)" }
    $out = "$Root\out\$Preset"
    if (Test-Path $out) { Remove-Item $out -Recurse -Force }
    Run 'install dist' "cmake --install $Root\build\$Preset --component dist --prefix $out\dist"
    if ($Preset -eq 'windows-dev') {
      Run 'install dev' "cmake --install $Root\build\$Preset --component dev --prefix $out\dev"
    }
  } finally { Pop-Location }

  # The dev-only guard on the real outputs: no DLL named in dev-only.txt may sit in the dist tree.
  $devOnly = Get-Content "$src\dev-only.txt" | Where-Object { $_ -match '^[^#].*\.dll$' }
  $leaked = Get-ChildItem "$out\dist" -Recurse -Filter *.dll | Where-Object { $devOnly -contains $_.Name }
  if ($leaked) { throw "dev-only DLL in the dist tree: $($leaked.Name -join ', ')" }

  # MO2 mod folders: dist plugins in one, dev-only in another, so a release profile simply lacks the second.
  if (Test-Path $ModDir) {
    foreach ($pair in @(@('dist', 'Argonia SKSE'), @('dev', 'Argonia SKSE (dev only)'))) {
      $from = "$out\$($pair[0])"; $to = Join-Path $ModDir $pair[1]
      if (-not (Test-Path $from)) { continue }
      if (Test-Path "$to\SKSE") { Remove-Item "$to\SKSE" -Recurse -Force }
      New-Item -ItemType Directory -Force $to | Out-Null
      Copy-Item "$from\*" $to -Recurse -Force
      Write-Host "mo2: $to"
    }
  } else { Write-Host "mo2: $ModDir absent; outputs left in $out" }
  Get-ChildItem $out -Recurse -Filter *.dll | ForEach-Object { Write-Host "dll: $($_.FullName) $($_.Length) bytes" }
  Write-Host "SKSE-BUILD OK $Preset"
}

if ($Stage -in 'tools', 'all') { Install-Tools }
if ($Stage -in 'build', 'all') { Build }

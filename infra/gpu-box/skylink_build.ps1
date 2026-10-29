# Build SkyLink AI's SKSE plugin from its source for 1.7.104 (skse/third_party/skylink) in a tree of its own,
# so it never meets another lane's build in C:\argonia\skse, then lay it in its own MO2 mod folder.
# DEV ONLY (skse/dev-only.txt). Driven from the build VM:
#   (cd skse && git ls-files -co --exclude-standard -z . | tar --null -cf /tmp/skse.tar -T -)
#   infra/gpu-box/run.sh ps 'New-Item -ItemType Directory -Force C:\argonia\skylink | Out-Null'
#   infra/gpu-box/run.sh put /tmp/skse.tar C:/argonia/skylink/src.tar
#   infra/gpu-box/run.sh put infra/gpu-box/skylink_build.ps1 C:/argonia/infra/skylink_build.ps1
#   infra/gpu-box/run.sh ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\skylink_build.ps1'
# It configures skse/ there (its own deps, vcpkg_installed and build dirs), builds only SkyrimMCPPlugin, then
# installs the `skylink` component into
# MO2\mods\SkyLink (dev, rebuilt)\SKSE\Plugins. Never touches the game or the profile. Prints SKYLINK-BUILD OK.
param([string]$Root = 'C:\argonia\skylink',
      [string]$ModDir = 'C:\argonia\MO2\mods',
      [string]$ModName = 'SkyLink (dev, rebuilt)')
$ErrorActionPreference = 'Stop'
$Preset = 'windows-dev'

# skse/CMakeLists.txt builds third_party/skylink only with this set. The fetched source is dropped each run so
# FetchContent re-applies a changed skylink-1.7.104.patch (its patch step does not track the file's content).
# Only the SkyrimMCPPlugin target is built: Argonia's own plugins and tests are skse_build.ps1's job.
$env:ARGONIA_SKYLINK = '1'
$env:VCPKG_ROOT = 'C:\argonia\tools\vcpkg'
$env:PATH = "C:\argonia\tools\mingit\cmd;$env:PATH"
$Log = 'C:\argonia\logs\skylink-build.log'
function Run([string]$what, [string]$cmdline) {
  Add-Content $Log "== ${what}: $cmdline"
  cmd /c "$cmdline >> $Log 2>&1"
  if ($LASTEXITCODE -ne 0) { Get-Content $Log -Tail 40 | Write-Host; throw "$what failed (exit $LASTEXITCODE), log $Log" }
}
Set-Content $Log "skylink_build $(Get-Date -Format s)"
$vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath
cmd /c "call `"$($vs.Trim())\VC\Auxiliary\Build\vcvars64.bat`" >nul && set" | ForEach-Object {
  if ($_ -match '^([^=]+)=(.*)$') { Set-Item "env:$($Matches[1])" $Matches[2] }
}
$src = "$Root\src"
if (Test-Path $src) { Remove-Item $src -Recurse -Force }
New-Item -ItemType Directory -Force $src | Out-Null
Run 'unpack' "tar -xf $Root\src.tar -C $src"
Get-ChildItem "$Root\deps" -Directory -Filter 'skylink-*' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Push-Location $src
try {
  Run 'configure' "cmake --preset $Preset -DARGONIA_SKYLINK=ON"
  Run 'build' "cmake --build --preset $Preset --target SkyrimMCPPlugin"
} finally { Pop-Location }
Select-String -Path $Log -Pattern 'warning C\d+' | Select-Object -First 10 | ForEach-Object { Write-Host $_.Line }
$out = "$Root\out\skylink"
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
Run 'install' "cmake --install $Root\build\$Preset --component skylink --prefix $out"

$to = Join-Path $ModDir $ModName
if (Test-Path "$to\SKSE") { Remove-Item "$to\SKSE" -Recurse -Force }
New-Item -ItemType Directory -Force $to | Out-Null
Copy-Item "$out\*" $to -Recurse -Force
Get-ChildItem $to -Recurse -File | ForEach-Object { Write-Host "laid: $($_.FullName) $($_.Length) bytes" }
Write-Host "SKYLINK-BUILD OK"

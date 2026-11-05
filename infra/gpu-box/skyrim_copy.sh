#!/usr/bin/env bash
# Put the pinned Skyrim SE (build 24914197, runtime 1.7.104.0; decision 0002) on the play machine from the build VM's
# own copy (~/games/skyrimse, the owner's licence), the way 0.0 did it: Steam accepts copied files as installed. The
# owner must have logged in to Steam on the machine first. Run under tooling/job_guard.sh; resumable: the game is cut
# into 1 GiB tar parts once (kept in ~/.argonia/skyrim-parts until the end), a part already on the machine at the
# same size is not sent again, and the unpack and the manifest steps are idempotent.
#   infra/gpu-box/skyrim_copy.sh
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
SRC="$HOME/games/skyrimse"
PARTS="$HOME/.argonia/skyrim-parts"
DST='C:\Program Files (x86)\Steam\steamapps'
run() { "$here/run.sh" "$@"; }

[ -f "$SRC/SkyrimSE.exe" ] || { echo "no Skyrim at $SRC" >&2; exit 2; }
grep -q '"buildid"[[:space:]]*"24914197"' "$SRC/steamapps/appmanifest_489830.acf" || { echo "source is not build 24914197" >&2; exit 2; }

# 1. The parts, made once (a .done marker records a complete split).
if [ ! -f "$PARTS/.done" ]; then
  rm -rf "$PARTS"; mkdir -p "$PARTS"
  tar -C "$SRC" --exclude=./steamapps -cf - . | split -b 1G -d -a 3 - "$PARTS/skyrim.tar."
  touch "$PARTS/.done"
fi
echo "parts: $(ls "$PARTS"/skyrim.tar.* | wc -l)"

# 2. Send each part not already there at its size.
run ps 'New-Item -ItemType Directory -Force C:\argonia\skyrim-parts | Out-Null' >/dev/null
have=$(run ps 'Get-ChildItem C:\argonia\skyrim-parts -File | ForEach-Object { "$($_.Name) $($_.Length)" }' | tr -d '\r')
for p in "$PARTS"/skyrim.tar.*; do
  n=$(basename "$p"); sz=$(stat -c %s "$p")
  grep -qx "$n $sz" <<<"$have" && continue
  echo "send $n ($((sz / 1048576)) MiB)"
  run put "$p" 'C:/argonia/skyrim-parts/'
done

# 3. Unpack into Steam's library (skipped when the exe is there at the pinned version), then the manifest, read-only,
#    and steam_appid.txt so the game starts without the launcher.
run put "$SRC/steamapps/appmanifest_489830.acf" 'C:/argonia/skyrim-parts/'
run ps '
Get-Process steam -EA SilentlyContinue | Stop-Process -Force; Start-Sleep 3   # Steam reads manifests at start
$g = "'"$DST"'\common\Skyrim Special Edition"
$v = if (Test-Path "$g\SkyrimSE.exe") { (Get-Item "$g\SkyrimSE.exe").VersionInfo.FileVersion } else { "" }
if ($v -ne "1.7.104.0") {
  New-Item -ItemType Directory -Force $g | Out-Null
  cmd /c "copy /b C:\argonia\skyrim-parts\skyrim.tar.* C:\argonia\skyrim-parts\skyrim.tar >nul"
  tar -xf C:\argonia\skyrim-parts\skyrim.tar -C $g
  Remove-Item C:\argonia\skyrim-parts\skyrim.tar
}
$m = "'"$DST"'\appmanifest_489830.acf"
if (Test-Path $m) { Set-ItemProperty $m -Name IsReadOnly -Value $false }
Copy-Item C:\argonia\skyrim-parts\appmanifest_489830.acf $m -Force
Set-ItemProperty $m -Name IsReadOnly -Value $true
Set-Content "$g\steam_appid.txt" "489830" -Encoding ascii
"SkyrimSE.exe: $((Get-Item "$g\SkyrimSE.exe").VersionInfo.FileVersion); manifest read-only: $((Get-Item $m).IsReadOnly)"
'

# 4. Steam again, in the owner's desktop session, silent (it signs in with the remembered login).
run desktop 'Start-Process "C:\Program Files (x86)\Steam\steam.exe" -ArgumentList "-silent"'

# 5. Tidy both sides once the game is in place.
run ps 'Remove-Item C:\argonia\skyrim-parts -Recurse -Force' >/dev/null
rm -rf "$PARTS"
echo SKYRIM-COPY-DONE

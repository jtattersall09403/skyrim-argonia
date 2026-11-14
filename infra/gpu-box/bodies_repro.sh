#!/usr/bin/env bash
# The walk's bodies-and-sinking console batches (repro_a.txt to repro_g.txt) laid in the game's root folder, beside
# SkyrimSE.exe where `bat` reads them, with ArgoniaNewWorld.esm's load index read from the machine's Plugins.txt.
#   bodies_repro.sh      (deploy.sh runs it after the stack is on, so a changed load order regenerates them)
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd); cd "$repo"
run="$here/run.sh"; t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
esm=out/newworld/plugin/ArgoniaNewWorld.esm
[ -f "$esm" ] || { echo "bodies_repro: no $esm, skipped"; exit 0; }
D='C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
"$run" ps "\$d='$D\\Data'; foreach(\$l in Get-Content \"\$env:LOCALAPPDATA\\Skyrim Special Edition\\Plugins.txt\"){ \$n=\$l.TrimStart('*'); if(\$l.StartsWith('*')){ \$b=[IO.File]::ReadAllBytes(\"\$d\\\$n\")[0..11]; '{0}|{1}' -f \$n,[BitConverter]::ToUInt32(\$b,8) } }" | tr -d '\r' > "$t/order.txt"
py=$HOME/.argonia/venv/bin/python; [ -x "$py" ] || py=python3
"$py" -m tools.newworld.ecology.bodies_repro --esm "$esm" --out "$t" --load-order "$t/order.txt"
"$run" put "$t"/repro_?.txt "$(sed 's|\\|/|g' <<<"$D")/"  >/dev/null
"$run" ps "Get-ChildItem '$D\\repro_?.txt' | % { \$_.Name; Get-Content \$_ }" | tr -d '\r' | head -80

#!/usr/bin/env bash
# The record pipeline's game-machine jobs (0.4 §a): Papyrus compile, the CK load check, BSArch packing.
#   records_jobs.sh papyrus [file.psc|dir ...] | ckload | bsarch | all
#   papyrus compiles papyrus/, papyrus/generated/ and skse/ArgoniaCore/papyrus/ (every .psc we have, into one
#   in-folder, so the fragments find ArgoniaCore.psc), or the .psc files and directories (their *.psc) given after it.
# Run under the GPU lock:  tooling/job_guard.sh run --gpu records -- infra/gpu-box/records_jobs.sh all
# Outputs come back to out/gpu/ (build outputs, never committed): papyrus/*.pex, compile.log, ck-warnings.log,
# Argonia.bsa and its contents list. The machine is not stopped here; the batch that runs this stops it.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
run="$here/run.sh"
stage=${1:-all}
case "$stage" in papyrus|ckload|bsarch|all) ;; *) sed -n '2,4p' "$0"; exit 2 ;; esac
shift || true
srcs=()
[ $# -gt 0 ] || set -- "$repo/papyrus" "$repo/papyrus/generated" "$repo/skse/ArgoniaCore/papyrus"
for a in "$@"; do
  if [ -d "$a" ]; then srcs+=("$a"/*.psc); else srcs+=("$a"); fi
done
for f in "${srcs[@]}"; do [ -f "$f" ] || { echo "no such .psc: $f" >&2; exit 2; }; done
mkdir -p "$repo/out/gpu"

"$run" ps 'New-Item -ItemType Directory -Force C:\argonia\infra,C:\argonia\records\in\papyrus | Out-Null'
"$run" put "$here/records_jobs.ps1" C:/argonia/infra/records_jobs.ps1 >/dev/null

job() {
  "$run" ps "powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\records_jobs.ps1 -Stage $1"
}
papyrus() {
  "$run" ps 'Remove-Item C:\argonia\records\in\papyrus\* -Force -EA SilentlyContinue'
  for f in "${srcs[@]}"; do "$run" put "$f" C:/argonia/records/in/papyrus/ >/dev/null; done
  job papyrus
  "$run" get C:/argonia/records/out/papyrus "$repo/out/gpu/" >/dev/null
  "$run" get C:/argonia/records/out/compile.log "$repo/out/gpu/" >/dev/null
}
ckload() {
  [ -f "$repo/out/Argonia.esm" ] || { echo "no out/Argonia.esm: run make plugin" >&2; exit 1; }
  "$run" put "$repo/out/Argonia.esm" C:/argonia/records/in/Argonia.esm >/dev/null
  DESKTOP_WAIT=600 "$run" desktop 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\records_jobs.ps1 -Stage ckload'
  "$run" get C:/argonia/records/out/ck-warnings.log "$repo/out/gpu/" >/dev/null
}
bsarch() {
  job bsarch
  "$run" get C:/argonia/records/out/Argonia.bsa "$repo/out/gpu/" >/dev/null
  "$run" get C:/argonia/records/out/bsa-contents.txt "$repo/out/gpu/" >/dev/null
}
case "$stage" in
  all) papyrus; ckload; bsarch ;;
  *) "$stage" ;;
esac

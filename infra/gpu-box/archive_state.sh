#!/usr/bin/env bash
# Archive C:\argonia folders that no tool makes (machine_inventory.sh's "state" kind), then remove them from the
# machine, so nothing lives only there (docs/machine-moves.md). Each goes to
# s3://argonia-private-…/machines/<machine>/state/<folder>.tar; the machine's copy is removed only once the bucket
# holds a tar of the size the machine made.
#   archive_state.sh [--machine <name>] <folder>...       e.g. archive_state.sh --machine argonia-play-london ut
#   archive_state.sh [--machine <name>] --list            each top-level C:\argonia folder with its size in MB
# Get one back: aws s3 cp s3://…/machines/<m>/state/<f>.tar . && run.sh put <f>.tar C:/argonia/ and tar -xf it there.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
case "${1:-}" in --machine) export ARGONIA_PLAY=$2; shift 2 ;; esac
M=${ARGONIA_PLAY:-argonia-play}
BUCKET=argonia-private-050977237313
run="$here/run.sh"
[ $# -gt 0 ] || { sed -n 2,8p "$0"; exit 2; }
if [ "$1" = --list ]; then
  "$run" ps 'Get-ChildItem C:\argonia -Directory | % { "{0}`t{1:N0}" -f $_.Name, ((Get-ChildItem $_.FullName -Recurse -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum/1MB) }'
  exit 0
fi
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for f in "$@"; do
  case "$f" in *[\\/:]*|..|.|'') echo "bad folder name: $f" >&2; exit 2 ;; esac
  n=$("$run" ps "if (!(Test-Path 'C:\\argonia\\$f')) { 'missing'; return }; tar.exe -cf 'C:\\argonia\\logs\\state-$f.tar' -C 'C:\\argonia' '$f'; (Get-Item 'C:\\argonia\\logs\\state-$f.tar').Length" | tr -d '\r' | tail -1)
  [ "$n" = missing ] && { echo "$M: C:\\argonia\\$f is not there"; continue; }
  "$run" get "C:/argonia/logs/state-$f.tar" "$tmp/$f.tar"
  aws s3 cp "$tmp/$f.tar" "s3://$BUCKET/machines/$M/state/$f.tar" --only-show-errors
  got=$(aws s3api head-object --bucket "$BUCKET" --key "machines/$M/state/$f.tar" --query ContentLength --output text)
  [ "$got" = "$n" ] || { echo "$f: bucket holds $got bytes, the machine made $n: kept on the machine" >&2; exit 1; }
  "$run" ps "Remove-Item -Recurse -Force 'C:\\argonia\\$f', 'C:\\argonia\\logs\\state-$f.tar'" >/dev/null
  echo "$M: $f archived ($((n >> 20)) MB, s3://$BUCKET/machines/$M/state/$f.tar) and removed"
  rm -f "$tmp/$f.tar"
done

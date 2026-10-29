#!/usr/bin/env bash
# The game machine's saves backed up to our own S3 bucket, and restored (chunk 0.2 §e, decision 0007 §4).
#   saves.sh backup            zip My Games\...\Saves on the machine, copy it here, upload as <UTC stamp>.zip and latest.zip
#   saves.sh restore [stamp]   download latest (or the stamp), keep the machine's current saves as a zip beside them,
#                              then replace them; Skyrim must not be running
#   saves.sh list
# run.sh stop calls backup first. The bucket is private (block public access, owner-only); the machine's own role
# cannot write S3, so the build VM carries the files (an owner IAM step would let the machine back up on its own stop).
# The machine is run.sh's (ARGONIA_PLAY, default argonia-play); argonia-play keeps saves/, a clone uses saves/<name>/,
# so one machine's stop never overwrites another's latest.zip.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
BUCKET=${ARGONIA_SAVES_BUCKET:-argonia-saves-050977237313}
SAVES='$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\Saves'
M=${ARGONIA_PLAY:-argonia-play}
P=saves; [ "$M" = argonia-play ] || P="saves/$M"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
case "${1:-}" in
  backup)
    n=$("$here/run.sh" ps "\$s=\"$SAVES\"; \$n=@(Get-ChildItem \$s -File -EA SilentlyContinue).Count; if (\$n) { Compress-Archive -Path \"\$s\\*\" -DestinationPath C:\\argonia\\logs\\saves.zip -Force }; \$n" | tr -d '\r')
    [ "${n:-0}" -gt 0 ] || { echo "no saves on the machine"; exit 0; }
    "$here/run.sh" get 'C:/argonia/logs/saves.zip' "$tmp/saves.zip"
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    aws s3 cp "$tmp/saves.zip" "s3://$BUCKET/$P/$stamp.zip" --only-show-errors
    aws s3 cp "$tmp/saves.zip" "s3://$BUCKET/$P/latest.zip" --only-show-errors
    echo "backed up $n save files ($(du -h "$tmp/saves.zip" | cut -f1)) as $stamp" ;;
  restore)
    key="$P/${2:-latest}.zip"
    aws s3 cp "s3://$BUCKET/$key" "$tmp/saves.zip" --only-show-errors
    "$here/run.sh" put "$tmp/saves.zip" 'C:/argonia/logs/restore.zip'
    "$here/run.sh" ps "if (Get-Process SkyrimSE -EA SilentlyContinue) { throw 'Skyrim is running' }
\$s=\"$SAVES\"; New-Item -ItemType Directory -Force \$s | Out-Null
if (Get-ChildItem \$s -File) { Compress-Archive -Path \"\$s\\*\" -DestinationPath \"C:\\argonia\\logs\\saves-before-restore-\$(Get-Date -Format yyyyMMddHHmmss).zip\" -Force }
Get-ChildItem \$s -File | Remove-Item -Force
Expand-Archive C:\\argonia\\logs\\restore.zip -DestinationPath \$s -Force
\"restored \$(@(Get-ChildItem \$s -File).Count) save files\"" ;;
  list) aws s3 ls "s3://$BUCKET/$P/" ;;
  *) sed -n 2,8p "$0"; exit 2 ;;
esac

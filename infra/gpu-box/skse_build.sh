#!/usr/bin/env bash
# make deploy's first half (chunk 0.3 §b): send skse/ to the game machine and build it there with MSVC.
# SKSE_TARGET=<target> (e.g. ArgoniaBridge) compiles that one target only (no tests, no install): fast compile-error loops.
#   skse_build.sh [--machine argonia-play-N] [--worktree] [tools|build|all] [windows-dev|windows-release]   default: build windows-dev
#   on argonia-play (or $ARGONIA_PLAY); ARGONIA_MODDIR='C:\argonia\no-deploy' leaves the DLLs in the build tree
#   (the game holds MO2's copies locked while it runs; the game lane deploys)
# Default: the committed tree (git archive HEAD skse), so no lane's half-done edits are built; --worktree tars the
# working tree (tracked and new files, for a lane compiling its own uncommitted change). Commit, or --worktree knowingly.
# Windows' OpenSSH has no rsync, so the tree goes as one tar (tracked and new files under skse/, ignored ones
# left out, file times kept so Ninja rebuilds only what changed) over scp, then skse_build.ps1 unpacks and builds.
# The first run on a fresh machine is `all` (installs VS 2026 Build Tools, MinGit, vcpkg; tens of minutes): run it
# under tooling/job_guard.sh. A Build Tools install that asks for a reboot is rebooted and resumed, as run.sh setup does.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
worktree=0
while [ "${1:-}" = --machine ] || [ "${1:-}" = --worktree ]; do
  if [ "$1" = --machine ]; then export ARGONIA_PLAY=$2; shift 2; else worktree=1; shift; fi
done
stage=${1:-build}
preset=${2:-windows-dev}
case "$stage" in tools|build|all) ;; *) sed -n '2,4p' "$0"; exit 2 ;; esac
run="$here/run.sh"

tarball=$(mktemp --suffix=.tar)
filelist=$(mktemp)
stagedir=$(mktemp -d)
trap 'rm -rf "$tarball" "$filelist" "$stagedir"' EXIT
if [ "$worktree" = 1 ]; then
  tree="$repo/skse"
  (cd "$tree" && git ls-files -co --exclude-standard -z . > "$filelist")
else
  # committed files only: another lane's half-done edits never reach the build
  (cd "$repo" && git archive HEAD skse | tar -x -C "$stagedir")
  tree="$stagedir/skse"
  (cd "$repo" && git ls-tree -r -z --name-only HEAD:skse > "$filelist")
  # git archive stamps every file with the commit time, which a new commit would make newer than every .obj:
  # a fixed old time instead, so only the hash-changed files (touched to now below) can ever look newer
  (cd "$tree" && xargs -0 touch -d 2001-01-01 -- < "$filelist")
fi
# Content-aware times: a file whose hash differs from the last good build for this machine and preset gets mtime=now,
# so Ninja never skips an edit that carries a time older than its .obj; unchanged files keep their time.
manifest="$HOME/.argonia/skse-manifest.${ARGONIA_PLAY:-argonia-play}.$preset"; mkdir -p "$(dirname "$manifest")"
python3 "$here/skse_manifest.py" touch "$tree" "$manifest" "$filelist"
(cd "$tree" && tar --null -cf "$tarball" -T "$filelist")
echo "skse: $(tar -tf "$tarball" | wc -l) files, $(du -h "$tarball" | cut -f1)"

"$run" ps 'New-Item -ItemType Directory -Force C:\argonia\skse,C:\argonia\infra | Out-Null'
"$run" put "$tarball" C:/argonia/skse/src.tar >/dev/null
"$run" put "$here/skse_build.ps1" C:/argonia/infra/skse_build.ps1 >/dev/null

for pass in 1 2 3; do
  out=$("$run" ps "powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\skse_build.ps1 -Stage $stage -Preset $preset${ARGONIA_MODDIR:+ -ModDir $ARGONIA_MODDIR}${SKSE_TARGET:+ -Target $SKSE_TARGET}" 2>&1) \
    || { echo "$out"; exit 1; }
  echo "$out"
  grep -q REBOOT-NEEDED <<<"$out" || break
  echo "rebooting for the Build Tools (pass $pass)"
  "$run" ps 'Restart-Computer -Force' >/dev/null 2>&1 || true
  read -t 45 < /dev/zero 2>/dev/null || true
  for i in $(seq 1 24); do "$run" ps hostname >/dev/null 2>&1 && break; read -t 10 < /dev/zero 2>/dev/null || true; done
done
if [ -n "${SKSE_TARGET:-}" ]; then  # a compile-only pass: the manifest stays as the last full build left it
  grep -q "SKSE-TARGET OK" <<<"$out" && exit 0 || { echo "no SKSE-TARGET OK line" >&2; exit 1; }
fi
grep -q "SKSE-BUILD OK" <<<"$out" || [ "$stage" = tools ] || { echo "no SKSE-BUILD OK line" >&2; exit 1; }
[ "$stage" = tools ] || python3 "$here/skse_manifest.py" save "$tree" "$manifest" "$filelist"
# the stamp deploy.sh reads to skip an unchanged build: written only after success, and only for a clean skse/ tree
if [ "$stage" != tools ] && { [ "$worktree" = 0 ] || [ -z "$(cd "$repo" && git status --porcelain -- skse)" ]; }; then
  "$run" ps "Set-Content -NoNewline -Path C:\\argonia\\skse\\out\\$preset\\skse.stamp -Value '$(cd "$repo" && git rev-parse HEAD:skse):$preset'" >/dev/null
fi

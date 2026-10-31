#!/usr/bin/env bash
# The build VM's disk stays lean and loses nothing (docs/machine-moves.md, "The build VM's disk").
#   tooling/disk.sh report            what fills the disk, by kind, and what tidy would free
#   tooling/disk.sh tidy [--dry-run]  archive each idle lane worktree to the private bucket, then remove it;
#                                     evict cached mod archives the bucket already holds (stack.py evict)
# A worktree is idle when no process works inside it and nothing in it changed for IDLE_H hours (default 3).
# Its archive is s3://<bucket>/worktrees/<name>/: out/ (run dirs, batches, stills; built plugins excepted),
# untracked.tgz (files git doesn't track), changes.patch (uncommitted edits), head.bundle (commits not on
# origin/main) and manifest.txt. Evidence a doc cites as wt-<name>/out/... is at that prefix, same relative path.
# The owner, 2026-10-31: "I have to pay for disk space"; 21 lane worktrees held 13 GB, merged and idle.
set -euo pipefail
main=$(cd "$(dirname "$0")/.." && pwd)
BUCKET=argonia-private-050977237313
IDLE_H=${IDLE_H:-3}
dry=; [ "${2:-}" = --dry-run ] && dry=1
export PATH="$HOME/.local/bin:$PATH"

worktrees() { git -C "$main" worktree list --porcelain | awk '/^worktree /{print substr($0,10)}' | grep -vxF "$main" || true; }
busy() {  # a process whose working directory is inside $1
  local p c; for p in /proc/[0-9]*; do c=$(readlink "$p/cwd" 2>/dev/null) || continue
    case "$c/" in "$1"/*) return 0 ;; esac; done; return 1; }
recent() { [ -n "$(find "$1" -xdev -newermt "-$IDLE_H hours" -not -path '*/.git*' -print -quit 2>/dev/null)" ]; }
gb() { du -sb "$@" 2>/dev/null | awk '{s+=$1} END {printf "%.1f GB", s/2^30}'; }

archive() {  # $1 worktree -> s3://$BUCKET/worktrees/<name>/
  local wt=$1 name dst tmp head
  name=$(basename "$wt"); dst="s3://$BUCKET/worktrees/$name"; tmp=$(mktemp -d)
  head=$(git -C "$wt" rev-parse HEAD)
  { echo "worktree $wt"; echo "head $head"; echo "branch $(git -C "$wt" branch --show-current)"
    echo "archived $(date -u +%FT%TZ) by tooling/disk.sh"; } > "$tmp/manifest.txt"
  git -C "$wt" diff HEAD > "$tmp/changes.patch"; [ -s "$tmp/changes.patch" ] || rm "$tmp/changes.patch"
  (cd "$wt" && git ls-files -o --exclude-standard -z -- . ':!out' | tar --null -T - -czf "$tmp/untracked.tgz")
  [ "$(tar -tzf "$tmp/untracked.tgz" | wc -l)" -gt 0 ] || rm "$tmp/untracked.tgz"
  if ! git -C "$main" merge-base --is-ancestor "$head" origin/main; then
    git -C "$wt" bundle create -q "$tmp/head.bundle" HEAD --not origin/main  # a ref: a bare sha bundles empty
    echo "unmerged $(git -C "$main" log --oneline origin/main.."$head" | wc -l) commits in head.bundle" >> "$tmp/manifest.txt"
  fi
  [ -d "$wt/out" ] && aws s3 sync "$wt/out" "$dst/out" --no-follow-symlinks --only-show-errors \
    --storage-class STANDARD_IA --exclude '*.esm' --exclude '*.esp' --exclude '*.bsa'
  aws s3 cp "$tmp" "$dst" --recursive --only-show-errors --storage-class STANDARD_IA
  rm -rf "$tmp"
}

case "${1:-}" in
report)
  df -h / | tail -1 | awk '{print "disk: " $3 " used of " $2 " (" $5 "); AWS bills the size, not the use"}'
  echo "lane worktrees ($(worktrees | wc -l)): $(gb $(worktrees))"
  echo "mod archives (~/.argonia/mods, all in s3 mods/; tidy evicts): $(gb "$HOME/.argonia/mods")"
  echo "staged mods (~/.argonia/stack/MO2; stack push and ui_theme read it): $(gb "$HOME/.argonia/stack/MO2")"
  echo "owned games (~/games: Skyrim SE data for ArgoniaGen, DSR for combat measurement): $(gb "$HOME/games")"
  echo "main tree out/: $(gb "$main/out")   Claude transcripts: $(gb "$HOME/.claude/projects")"
  for wt in $(worktrees); do
    s=idle; busy "$wt" && s=busy; [ $s = idle ] && recent "$wt" && s=recent
    echo "  $(basename "$wt") $s $(gb "$wt")"
  done ;;
tidy)
  git -C "$main" fetch -q origin
  for wt in $(worktrees); do
    [ -d "$wt" ] || continue
    if busy "$wt" || recent "$wt"; then echo "keep $(basename "$wt") (in use)"; continue; fi
    if [ -n "$dry" ]; then echo "would archive and remove $(basename "$wt") ($(gb "$wt"))"; continue; fi
    archive "$wt"
    br=$(git -C "$wt" branch --show-current)
    git -C "$main" worktree remove --force "$wt"
    [ -n "$br" ] && git -C "$main" branch -d -q "$br" 2>/dev/null || true  # only if merged
    echo "archived to s3://$BUCKET/worktrees/$(basename "$wt")/ and removed $(basename "$wt")"
  done
  git -C "$main" worktree prune
  if [ -z "$dry" ] && [ -n "$(ls -A "$HOME/.argonia/mods" 2>/dev/null)" ]; then
    "$HOME/.argonia/venv/bin/python" "$main/infra/gpu-box/stack.py" evict
  fi
  df -h / | tail -1 | awk '{print "disk: " $3 " used of " $2 " (" $5 ")"}' ;;
*) sed -n 2,9p "$0"; exit 2 ;;
esac

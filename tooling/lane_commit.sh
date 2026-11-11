#!/usr/bin/env bash
# Commit exactly the given paths and land them on origin/main without touching other lanes' dirty edits.
# Usage: tooling/lane_commit.sh -m "<message>" -- <pathspec>...
# Never runs stash, checkout of paths, reset --hard, or pull. Env: LANE_COAUTHOR overrides the trailer name.
# Refused in a lane's worktree (branch worktree-*): a lane commits on its branch and tooling/lane_land.sh lands it.
set -u
COAUTHOR="${LANE_COAUTHOR:-Claude Sonnet 5.5 <noreply@anthropic.com>}"
die() { echo "lane_commit: $*" >&2; exit 1; }

msg=""
paths=()
while [ $# -gt 0 ]; do
  case "$1" in
    -m) [ $# -ge 2 ] || die "-m needs a message"; msg="$2"; shift 2 ;;
    --) shift; paths=("$@"); break ;;
    -a|--all|-A) die "refused: $1 (name the paths after --)" ;;
    *) die "unknown argument: $1 (usage: -m msg -- paths)" ;;
  esac
done
# A lane in its own worktree commits on its branch and the lead lands it (tooling/lane_land.sh: rebase, gate, push,
# worktree and branch removed). This command pushes to main, so it is for the main tree alone.
if [ "$(git rev-parse --path-format=absolute --git-dir)" != "$(git rev-parse --path-format=absolute --git-common-dir)" ]; then
  case "$(git symbolic-ref -q --short HEAD)" in
    worktree-*) die "refused: this is a lane's worktree. Commit on its branch (git commit -m msg -- paths) and leave it clean; the lead lands it with tooling/lane_land.sh" ;;
  esac
fi
[ -n "$msg" ] || die "no message (-m)"
[ "${#paths[@]}" -gt 0 ] || die "no pathspec after --"
for p in "${paths[@]}"; do
  case "$p" in .|./|:/|/|'') die "refused pathspec '$p' (too broad)" ;; esac
done

git add -- "${paths[@]}" || die "git add failed"
if git diff --cached --quiet -- "${paths[@]}"; then die "nothing to commit in the given paths"; fi
# A commit made from a tree behind main must not undo other lanes' work: refuse any staged file that goes back to an
# earlier version from main's last 50 commits, or that deletes a file main added in that span (a stale tree swept
# into one commit deleted and reverted another lane's files, 2026-11-08). LANE_ALLOW_REVERT=1 for a deliberate revert.
if [ -z "${LANE_ALLOW_REVERT:-}" ]; then
  bad=()
  while IFS=$'\t' read -r st f; do
    if [ "$st" = D ]; then
      [ -n "$(git log -n1 --format=%h --diff-filter=A HEAD~50..HEAD -- "$f" 2>/dev/null)" ] && bad+=("$f (deletes a file added in main's last 50 commits)")
      continue
    fi
    staged=$(git rev-parse ":$f" 2>/dev/null) || continue
    [ "$staged" = "$(git rev-parse "HEAD:$f" 2>/dev/null)" ] && continue
    for c in $(git log -n 20 --format=%H HEAD~50..HEAD -- "$f" 2>/dev/null); do
      [ "$(git rev-parse "$c^:$f" 2>/dev/null)" = "$staged" ] && { bad+=("$f (back to its version before ${c:0:8})"); break; }
    done
  done < <(git diff --cached --name-status --no-renames -- "${paths[@]}")
  if [ "${#bad[@]}" -gt 0 ]; then
    printf '  %s\n' "${bad[@]}" >&2
    die "refused: this commit would undo recent work on main (staged, not committed). Bring your tree level with origin/main and commit only your own files; LANE_ALLOW_REVERT=1 if the revert is deliberate"
  fi
fi
# A commit that touches the C# plugin tool must leave it building: build HEAD plus exactly the staged change in a
# scratch worktree (another lane's half-done .cs swept into a commit broke main's build for every lane, 2026-11-08).
if [ -z "${LANE_SKIP_CS_BUILD:-}" ] && git diff --cached --name-only -- "${paths[@]}" | grep -qE '^tools/ArgoniaPlugin/.*\.(cs|csproj)$'; then
  cs=$(mktemp -d "${TMPDIR:-/tmp}/lane_cs.XXXXXX") || die "mktemp failed"
  git worktree add -q --detach "$cs/wt" HEAD || die "worktree add failed"
  git diff --cached --binary -- "${paths[@]}" | git -C "$cs/wt" apply --index - || { git worktree remove --force "$cs/wt"; rm -rf "$cs"; die "could not apply the staged change for the build check"; }
  dn=$(command -v dotnet || echo "$HOME/.dotnet/dotnet")
  if ! out=$(cd "$cs/wt/tools/ArgoniaPlugin" && "$dn" build -nologo -v q -o "$cs/bin" 2>&1); then
    git worktree remove --force "$cs/wt"; rm -rf "$cs"; git worktree prune
    echo "$out" | grep -oE '[A-Za-z0-9_]+\.cs\([0-9]+,[0-9]+\): error [A-Z0-9]+: [^[]*' | sort -u | head -10 >&2
    die "refused: tools/ArgoniaPlugin does not build with this commit (staged, not committed; commit only your own compiling files)"
  fi
  git worktree remove --force "$cs/wt"; rm -rf "$cs"; git worktree prune
fi
git commit -q -m "$msg" -m "Co-Authored-By: $COAUTHOR" -- "${paths[@]}" || die "commit failed"
new=$(git rev-parse HEAD)
echo "committed $new"

if git push -q origin HEAD:main 2>/dev/null; then
  echo "pushed; main is at $(git rev-parse --short HEAD) ($new)"
  exit 0
fi

echo "push refused; landing via a scratch worktree (working tree untouched)"
git fetch -q origin || die "fetch failed"
scratch=$(mktemp -d "${TMPDIR:-/tmp}/lane_commit.XXXXXX") || die "mktemp failed"
cleanup() { git worktree remove --force "$scratch/wt" >/dev/null 2>&1; rm -rf "$scratch"; git worktree prune; }
trap cleanup EXIT

landed=""
for _ in 1 2 3; do
  git worktree add -q --detach "$scratch/wt" origin/main || die "worktree add failed"
  if ! git -C "$scratch/wt" cherry-pick "$new" >/dev/null 2>&1; then
    git -C "$scratch/wt" cherry-pick --abort >/dev/null 2>&1
    echo "lane_commit: cherry-pick of $new onto origin/main conflicts; resolve by hand. Commit $new is kept locally." >&2
    exit 2
  fi
  if git -C "$scratch/wt" push -q origin HEAD:main 2>/dev/null; then
    landed=$(git -C "$scratch/wt" rev-parse HEAD); break
  fi
  git worktree remove --force "$scratch/wt" >/dev/null 2>&1
  git fetch -q origin || die "fetch failed"
done
[ -n "$landed" ] || die "push still refused after retries; commit $new kept locally"

git fetch -q origin
branch=$(git symbolic-ref -q HEAD || true)
if [ "$branch" = "refs/heads/main" ] && [ "$(git rev-parse HEAD)" = "$new" ] && git diff --cached --quiet; then
  # two-way merge keeps local edits; it refuses (changing nothing) if one collides with upstream changes
  if git read-tree -m -u "$new" origin/main 2>/dev/null; then
    git update-ref refs/heads/main origin/main "$new" && echo "local main moved to origin/main"
  else
    echo "local main NOT moved (a dirty file collides with upstream changes); it is behind origin/main."
    echo "do NOT run: git pull / git stash / git reset --hard / git checkout -- <paths>"
  fi
else
  echo "local HEAD left as is (not main at the new commit, or staged changes exist); it is diverged from origin/main."
  echo "do NOT run: git pull / git stash / git reset --hard / git checkout -- <paths>"
fi
echo "main on origin is at $landed"

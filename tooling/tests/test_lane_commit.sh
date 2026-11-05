#!/usr/bin/env bash
# Test tooling/lane_commit.sh against a temp bare repo with two clones.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
script="$here/lane_commit.sh"
t=$(mktemp -d)
trap 'rm -rf "$t"' EXIT
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
fail() { echo "FAIL: $*" >&2; exit 1; }
git init -q --bare -b main "$t/o.git"
git clone -q "$t/o.git" "$t/a" 2>/dev/null
git clone -q "$t/o.git" "$t/b" 2>/dev/null
cd "$t/a"; git switch -q -c main 2>/dev/null || true
echo base > base.txt; echo x > other.txt; git add .; git commit -qm base; git push -q origin HEAD:main
cd "$t/b"; git fetch -q origin; git switch -q -c main --track origin/main 2>/dev/null || git switch -q main

# refusals
cd "$t/a"
"$script" -m x 2>/dev/null && fail "no pathspec accepted"
"$script" -m x -- . 2>/dev/null && fail "dot accepted"
"$script" -a -m x -- f 2>/dev/null && fail "-a accepted"

# 1: clean push
echo one > one.txt
"$script" -m "add one" -- one.txt >/dev/null || fail "clean push"
[ "$(git rev-parse HEAD)" = "$(git -C "$t/o.git" rev-parse main)" ] || fail "origin not at HEAD"
git log -1 --format=%B | grep -q '^Co-Authored-By:' || fail "no trailer"

# 2: b pushes, a is behind with a dirty unrelated file
cd "$t/b"; git merge -q --ff-only origin/main 2>/dev/null || { git fetch -q origin; git merge -q --ff-only origin/main; }
echo two > two.txt
"$script" -m "add two" -- two.txt >/dev/null || fail "b push"
cd "$t/a"
echo dirty >> other.txt; echo ours > three.txt
out=$("$script" -m "add three" -- three.txt) || fail "worktree route: $out"
echo "$out" | grep -q "scratch worktree" || fail "did not take worktree route"
o=$(git -C "$t/o.git" rev-parse main)
[ "$(git rev-parse HEAD)" = "$o" ] || fail "local main not moved"
for f in one two three; do git -C "$t/o.git" cat-file -e "main:$f.txt" || fail "origin lacks $f"; done
[ -f two.txt ] || fail "upstream file missing locally"
[ "$(tail -1 other.txt)" = dirty ] || fail "dirty file touched"
[ "$(git status --porcelain)" = " M other.txt" ] || fail "status changed: $(git status --porcelain)"
[ -z "$(git worktree list | sed -n 2p)" ] || fail "worktree left behind"
echo PASS

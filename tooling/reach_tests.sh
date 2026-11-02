#!/usr/bin/env bash
# The gate for what a change reaches (CLAUDE.md: "run only what the change reaches"): pytest on the test dirs beside
# the files changed against origin/main (committed, staged, unstaged and untracked), ruff on the changed Python, the
# guards. Nine lanes each running the whole `make check` on the shared 4-CPU build VM took 8+ minutes each and
# timed out (round 4, 2026-11-02); the planner runs the full gate once before the batch.
#   tooling/reach_tests.sh [base-ref]       default origin/main
set -uo pipefail
base=${1:-origin/main}
PY=${PY:-$HOME/.argonia/venv/bin/python}; [ -x "$PY" ] || PY=python3
RUFF=$HOME/.argonia/venv/bin/ruff; [ -x "$RUFF" ] || RUFF=$(command -v ruff || true)
files=$( { git diff --name-only "$base"...HEAD 2>/dev/null; git diff --name-only HEAD; git ls-files -o --exclude-standard; } | sort -u | grep -E '\.(py|sh|cs|yaml|json|sql)$' || true)
[ -n "$files" ] || { echo "reach: nothing changed against $base"; exit 0; }
tests=""
for f in $files; do
  [ -e "$f" ] || continue
  d=$(dirname "$f")
  case "$(basename "$f")" in test_*.py|*_test.py) tests="$tests $f"; continue;; esac
  while [ "$d" != . ] && [ -n "$d" ]; do
    [ -d "$d/tests" ] && tests="$tests $d/tests"
    ls "$d"/test_*.py >/dev/null 2>&1 && tests="$tests $(ls "$d"/test_*.py | tr '\n' ' ')"
    [ -d "$d/tests" ] && break
    d=$(dirname "$d")
  done
done
tests=$(echo $tests | tr ' ' '\n' | sort -u | tr '\n' ' ')
rc=0
pyfiles=$(echo "$files" | grep '\.py$' | while read -r f; do [ -e "$f" ] && echo "$f"; done | tr '\n' ' ')
if [ -n "$RUFF" ] && [ -n "$pyfiles" ]; then $RUFF check -q $pyfiles || { echo "reach: ruff RED"; rc=1; }; fi
if [ -n "$tests" ]; then
  echo "reach: pytest $tests"
  $PY -m pytest -q -p no:cacheprovider --ignore=tooling/tests/test_word_budget.py $tests; prc=$?
  [ $prc -eq 0 ] || [ $prc -eq 5 ] || { echo "reach: pytest RED"; rc=1; }
else echo "reach: no tests beside the changed files"; fi
python3 tooling/guards/no_assets.py --tree >/dev/null 2>&1 || { echo "reach: no_assets guard RED"; rc=1; }
[ $rc -eq 0 ] && echo "REACH GREEN ($(echo $files | wc -w) files)" || echo "REACH RED"
exit $rc

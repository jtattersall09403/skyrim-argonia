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
# A lane that pushed before running the gate has HEAD == origin/main, so the diff is empty and nothing ran (round 5,
# 2026-11-03, the System pane lane): then the last commit is what the change reaches.
[ "$(git rev-parse HEAD)" = "$(git rev-parse "$base" 2>/dev/null)" ] && [ -z "$(git diff --name-only HEAD; git ls-files -o --exclude-standard)" ] && { base=HEAD~1; echo "reach: HEAD is $1-or-origin/main already; gating the last commit"; }
all=$( { git diff --name-only "$base"...HEAD 2>/dev/null; git diff --name-only HEAD; git ls-files -o --exclude-standard; } | sort -u)
files=$(echo "$all" | grep -E '\.(py|sh|cs|yaml|json|sql)$' || true)
uifiles=$(echo "$all" | grep -E '^(ui/|tools/schema_gen/).*\.(ts|css|html)$' || true)
[ -n "$files$uifiles" ] || { echo "reach: nothing changed against $base"; exit 0; }
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
# UI and schema TypeScript or CSS changed: the node test suites (the Makefile's ui-test line), ~20 s
if [ -n "$uifiles" ]; then
  echo "reach: node tests for $(echo $uifiles | wc -w) ui files"
  NODE=${NODE:-node}; $NODE --experimental-strip-types --disable-warning=ExperimentalWarning --test --test-reporter=dot 'ui/schema/tests/*.test.ts' 'tools/schema_gen/tests/*.test.ts' 'ui/views/tests/*.test.ts' || { echo "reach: node tests RED"; rc=1; }
fi
python3 tooling/guards/no_assets.py --tree >/dev/null 2>&1 || { echo "reach: no_assets guard RED"; rc=1; }
[ $rc -eq 0 ] && echo "REACH GREEN ($(echo $files $uifiles | wc -w) files)" || echo "REACH RED"
exit $rc

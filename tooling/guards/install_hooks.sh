#!/usr/bin/env bash
# The git pre-commit hook: the no-assets guard, and the ledger check when a checks.md is staged. Safe to run again.
set -eu
root=$(git rev-parse --show-toplevel)
cat > "$root/.git/hooks/pre-commit" <<'H'
#!/usr/bin/env bash
top=$(git rev-parse --show-toplevel)
python3 "$top/tooling/guards/no_assets.py" --staged || exit 1
# A ledger row the checker rejects turned main red for every lane three times on 2026-11-01: check it at the commit
# (0.3 s), in whichever worktree commits it.
if git diff --cached --name-only | grep -q 'checks\.md$'; then python3 "$top/tools/check_ledger.py" >/dev/null || { python3 "$top/tools/check_ledger.py" | tail -5; echo "pre-commit: fix the ledger rows above"; exit 1; }; fi
H
chmod +x "$root/.git/hooks/pre-commit"
echo "pre-commit hook installed"

#!/usr/bin/env bash
# The git pre-commit hook: the no-assets guard. Safe to run again.
set -eu
root=$(git rev-parse --show-toplevel)
cat > "$root/.git/hooks/pre-commit" <<'H'
#!/usr/bin/env bash
top=$(git rev-parse --show-toplevel)
python3 "$top/tooling/guards/no_assets.py" --staged || exit 1
H
chmod +x "$root/.git/hooks/pre-commit"
echo "pre-commit hook installed"

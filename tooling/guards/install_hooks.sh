#!/usr/bin/env bash
# Link the no-assets guard as the git pre-commit hook. Safe to run again.
set -eu
root=$(git rev-parse --show-toplevel)
cat > "$root/.git/hooks/pre-commit" <<'H'
#!/usr/bin/env bash
exec python3 "$(git rev-parse --show-toplevel)/tooling/guards/no_assets.py" --staged
H
chmod +x "$root/.git/hooks/pre-commit"
echo "pre-commit hook installed"

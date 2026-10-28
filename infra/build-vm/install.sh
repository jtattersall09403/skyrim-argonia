#!/usr/bin/env bash
# Install the build VM's unattended-running units (chunk 0.0 §a). Idempotent. Needs lingering for `ubuntu`
# (already on: the VS Code tunnel uses it).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
chmod +x "$here"/*.sh "$here"/../../tooling/*.sh
mkdir -p "$HOME/.config/systemd/user" "$HOME/.argonia/state" "$HOME/.argonia/jobs"
cp "$here"/systemd/argonia-* "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable argonia-resume.service
systemctl --user enable --now argonia-idle-stop.timer
echo "installed: argonia-resume.service (at boot), argonia-idle-stop.timer (every minute)"

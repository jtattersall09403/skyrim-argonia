#!/usr/bin/env bash
# Install the build VM's unattended-running units (chunk 0.0 §a). Idempotent. Needs lingering for `ubuntu`
# (already on: the VS Code tunnel uses it).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
chmod +x "$here"/*.sh "$here"/../../tooling/*.sh
mkdir -p "$HOME/.config/systemd/user" "$HOME/.argonia/state" "$HOME/.argonia/jobs"
cp "$here"/systemd/argonia-* "$HOME/.config/systemd/user/"
# An OOM kill inside tmux must not stop the whole tmux scope (systemd's default OOMPolicy=stop killed every lane twice).
mkdir -p "$HOME/.config/systemd/user/tmux-spawn-.scope.d"
cp "$here"/systemd/tmux-spawn-.scope.d/oom.conf "$HOME/.config/systemd/user/tmux-spawn-.scope.d/"
# 8 GB of swap (16 GB cost too much disk on the 116 GB root): parallel lanes on a 16 GB VM ran it out of memory.
if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 8G /swapfile && sudo chmod 600 /swapfile && sudo mkswap -q /swapfile && sudo swapon /swapfile
  grep -q /swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi
systemctl --user daemon-reload
systemctl --user enable argonia-resume.service
systemctl --user enable --now argonia-idle-stop.timer
systemctl --user enable --now argonia-watchdog.timer
echo "installed: argonia-resume.service (at boot), argonia-idle-stop.timer (every minute), argonia-watchdog.timer (every 2 min: resume if Claude died without a reboot)"

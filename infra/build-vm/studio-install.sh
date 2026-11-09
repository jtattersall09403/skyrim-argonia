#!/usr/bin/env bash
# Install the place studio on the build VM: the pinned cloudflared, the search model, the tunnel and Access app
# (studio_gate.py apply), and two user units started at boot (lingering is on): argonia-studio (the server) and
# argonia-studio-tunnel (cloudflared). Idempotent; rerun after any change to the units.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd)
CF_VERSION=2026.10.7
CF_SHA=1f99fb518b83dec2ba8d870a7cc991d82a77e6196295a3d2754ba17ab9f91872
bin="$HOME/.local/bin/cloudflared"; mkdir -p "$HOME/.local/bin"
if ! echo "$CF_SHA  $bin" | sha256sum -c --quiet 2>/dev/null; then
  curl -sSfL -o "$bin.part" "https://github.com/cloudflare/cloudflared/releases/download/$CF_VERSION/cloudflared-linux-amd64"
  echo "$CF_SHA  $bin.part" | sha256sum -c --quiet && mv "$bin.part" "$bin" && chmod +x "$bin"
fi
"$HOME/.argonia/venv/bin/pip" install -q aiohttp==3.14.5 brotli==1.2.1 onnxruntime==1.31.1 tokenizers==0.23.3
(cd "$repo" && "$HOME/.argonia/venv/bin/python" -c "from tools.places.search.embed import fetch; fetch()")
grep -q '^CLOUDFLARE_TUNNEL_TOKEN_STUDIO=' "$HOME/.argonia/secrets.env" || python3 "$here/studio_gate.py" apply
mkdir -p "$HOME/.config/systemd/user"
cp "$here/studio.service" "$HOME/.config/systemd/user/argonia-studio.service"
cp "$here/studio-tunnel.service" "$HOME/.config/systemd/user/argonia-studio-tunnel.service"
systemctl --user daemon-reload
systemctl --user enable argonia-studio.service argonia-studio-tunnel.service
systemctl --user restart argonia-studio.service argonia-studio-tunnel.service
echo "installed: argonia-studio (localhost:8765), argonia-studio-tunnel -> $(python3 "$here/studio_gate.py" url)"

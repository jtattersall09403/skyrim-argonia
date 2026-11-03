#!/usr/bin/env bash
# Builds Ruffle's headless exporter (MIT/Apache-2.0; sourcing register) at a pinned nightly with our two-hunk patch
# (AVM traces to stderr; a navigator that serves Scaleform's Windows paths from a lowercase staged tree) into
# ~/.argonia/tools/ruffle/ruffle-exporter. Resumable: each step skips work already done. Needs Java (Ruffle's AVM2
# playerglobal build step): sudo apt-get install -y openjdk-21-jre-headless. Never commit the binary.
#   tools/ui_theme/ruffle/build_exporter.sh            (~10 min cold on 4 cores, seconds warm)
set -euo pipefail
export RUSTUP_HOME=$HOME/.argonia/tools/rust/rustup CARGO_HOME=$HOME/.argonia/tools/rust/cargo
TAG=nightly-2026-11-03; D=$HOME/.argonia/tools/ruffle; HERE=$(cd "$(dirname "$0")" && pwd)
command -v java >/dev/null || { echo "java missing: sudo apt-get install -y openjdk-21-jre-headless" >&2; exit 2; }
[ -x $CARGO_HOME/bin/cargo ] || curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --no-modify-path
export PATH=$CARGO_HOME/bin:$PATH
[ -d $D/src/ruffle/.git ] || git clone --depth 1 --branch $TAG https://github.com/ruffle-rs/ruffle $D/src/ruffle
cd $D/src/ruffle
# the patch applied once: applied already (reverse applies) or apply now
git apply --reverse --check "$HERE/exporter-argonia.patch" 2>/dev/null || git apply "$HERE/exporter-argonia.patch"
git rev-parse HEAD > $D/exporter.commit
cargo build --release -p exporter -j "$(nproc)"
cp target/release/exporter $D/ruffle-exporter.new && mv $D/ruffle-exporter.new $D/ruffle-exporter
sha256sum $D/ruffle-exporter

#!/usr/bin/env bash
# Build our client page (chunk 0.0 §c): upstream Moonlight-Web v3.0.1's built web frontend (the release's static/,
# checked against GitHub's sha256) plus our bundle (src/ -> argonia.js), loaded by stream.html before upstream's
# stream.js. Output: build/static/, ready for deploy.sh. Nothing upstream is committed; build/ is gitignored.
#   build.sh            install deps, test, lint, bundle, assemble build/static
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); cd "$here"
TAG=v3.0.1
ZIP=moonlight-web-x86_64-pc-windows-gnu.zip
SHA=7680f8ebb547f6bf1ba7e2056794bdd10d849685d954167fecdec79f2f240b1f
REPO=MrCreativ3001/moonlight-web-stream
mkdir -p build/cache
[ -d node_modules ] || npm ci --no-audit --no-fund
npm test --silent
npm run -s lint
npm run -s bundle

z=build/cache/$TAG-$ZIP
if [ ! -f "$z" ] || ! echo "$SHA  $z" | sha256sum -c --status; then
  curl -fsSL -o "$z.part" "https://github.com/$REPO/releases/download/$TAG/$ZIP"
  echo "$SHA  $z.part" | sha256sum -c --status || { echo "upstream $ZIP does not match its published sha256" >&2; exit 1; }
  mv "$z.part" "$z"
fi
lic=build/cache/$TAG-LICENSE
[ -s "$lic" ] || curl -fsSL -o "$lic" "https://raw.githubusercontent.com/$REPO/$TAG/LICENSE"

rm -rf build/upstream build/static && mkdir -p build/upstream
python3 -I -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' "$z" build/upstream
src=$(dirname "$(find build/upstream -name stream.html -path '*static*' | head -1)")
[ -f "$src/stream.js" ] || { echo "no static/stream.js in $ZIP" >&2; exit 1; }
cp -r "$src" build/static
cp build/argonia.js build/argonia.js.map build/static/
cp "$lic" build/static/LICENSE.txt
cp NOTICE build/static/NOTICE.txt

# the one change to upstream's files: load argonia.js just before stream.js
anchor='<script src=stream.js></script>'
n=$(grep -o "$anchor" build/static/stream.html | wc -l)
[ "$n" = 1 ] || { echo "stream.html: expected the anchor once, found $n (upstream changed?)" >&2; exit 1; }
sed -i "s#$anchor#<script src=argonia.js></script>$anchor#" build/static/stream.html
(cd build/static && sha256sum stream.html argonia.js > ../argonia.sha256)
echo "built $(du -sh build/static | cut -f1) in build/static (upstream $TAG + argonia.js $(stat -c %s build/argonia.js) bytes)"

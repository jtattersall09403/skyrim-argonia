#!/usr/bin/env bash
# Community Shaders' cache across deploys and machines (1.15-r4-fast-loop; the owner: loops massively faster).
# CS keeps its compiled cache in Data\ShaderCache (stack.ps1 never touches it), so a machine pays the ~11 min compile
# once per shader set; a new machine from an older image paid it again. Keyed by shader_cache.py (the shader sources,
# the CS DLL, its settings): the machine's key sits in Data\ShaderCache\argonia-shader.key.
#   shader_cache.sh ensure   deploy, before the launch: current -> nothing; archived -> laid; else the launch compiles
#   shader_cache.sh save     deploy, after the launch (compile done): archive the cache under its key if none is
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd)
run="$here/run.sh"; PY=$(command -v "$HOME/.argonia/venv/bin/python" || command -v python3)
bucket=${ARGONIA_PRIVATE_BUCKET:-argonia-private-050977237313}
cache='C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\ShaderCache'
key=$("$PY" "$here/shader_cache.py" key)
have=$("$run" ps "Get-Content '$cache\argonia-shader.key' -EA SilentlyContinue" | tr -d '\r\n ' || true)
case "${1:-}" in
  ensure)
    if [ "$have" = "$key" ]; then echo "shader cache current ($key)"; exit 0; fi
    if ! aws s3 ls "s3://$bucket/shadercache/$key.tar" >/dev/null 2>&1; then
      echo "shader cache: none archived for $key (machine has ${have:-none}); the launch compiles (~11 min), save archives it"; exit 0
    fi
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    aws s3 cp "s3://$bucket/shadercache/$key.tar" "$tmp/sc.tar" --only-show-errors
    "$run" ps "Stop-Process -Name SkyrimSE -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force C:\argonia\MO2\push | Out-Null" >/dev/null
    "$run" put "$tmp/sc.tar" C:/argonia/MO2/push/shadercache.tar >/dev/null
    "$run" ps "Remove-Item '$cache' -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force '$cache' | Out-Null; tar -xf C:\argonia\MO2\push\shadercache.tar -C '$cache'; Remove-Item C:\argonia\MO2\push\shadercache.tar; Set-Content '$cache\argonia-shader.key' '$key'; 'shader cache laid: ' + (Get-ChildItem '$cache' -Recurse -File).Count + ' files ($key)'" ;;
  save)
    if aws s3 ls "s3://$bucket/shadercache/$key.tar" >/dev/null 2>&1; then
      "$run" ps "Set-Content '$cache\argonia-shader.key' '$key'" >/dev/null; echo "shader cache archived already ($key)"; exit 0
    fi
    n=$("$run" ps "if (Test-Path '$cache') { (Get-ChildItem '$cache' -Recurse -File | ? Name -ne 'argonia-shader.key').Count } else { 0 }" | tr -d '\r')
    [ "${n:-0}" -gt 100 ] || { echo "shader cache: only ${n:-0} files on the machine; not archived (compile not finished?)"; exit 0; }
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    "$run" ps "Set-Content '$cache\argonia-shader.key' '$key'; tar -cf C:\argonia\logs\shadercache.tar -C '$cache' ." >/dev/null
    "$run" get 'C:/argonia/logs/shadercache.tar' "$tmp/sc.tar"
    aws s3 cp "$tmp/sc.tar" "s3://$bucket/shadercache/$key.tar" --only-show-errors
    "$run" ps 'Remove-Item C:\argonia\logs\shadercache.tar' >/dev/null
    echo "shader cache archived: $n files, $(du -m "$tmp/sc.tar" | cut -f1) MB, s3://$bucket/shadercache/$key.tar" ;;
  *) sed -n '2,8p' "$0"; exit 2 ;;
esac

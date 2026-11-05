#!/usr/bin/env bash
# Our build onto the game machine: the plugins (out/*.esp, out/*.esm, Argonia.esp's own out/Argonia.ini) and compiled Papyrus (out/gpu/papyrus/*.pex),
# then stack.ps1 on. The machine holds the key of what it was last given (C:\argonia\state\deployed.key); a deploy
# whose inputs hash to the same key sends nothing and lays nothing ("DEPLOY held").
#   deploy.sh [--no-papyrus]      --no-papyrus: send the last compile; DEPLOY_FORCE=1 ignores the held key
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd); cd "$repo"
papyrus=1
for a in "$@"; do case "$a" in --no-papyrus) papyrus=0 ;; *) sed -n '2,6p' "$0"; exit 2 ;; esac; done
run="$here/run.sh"; t0=$SECONDS
step() { local s=$SECONDS; echo "== $1"; shift; "$@"; echo "== $(( SECONDS - s )) s"; }
[ $papyrus = 1 ] && step "papyrus" "$here/records_jobs.sh" papyrus
plugins=(out/*.esm out/*.esp out/Argonia.ini); pex=(out/gpu/papyrus/*.pex)
plugins=($(printf '%s\n' "${plugins[@]}" | while read -r f; do [ -f "$f" ] && echo "$f"; done)) || true
[ -f "${pex[0]:-}" ] || pex=()
[ ${#plugins[@]} -gt 0 ] || [ ${#pex[@]} -gt 0 ] || { echo "nothing to send: no out/*.esp|esm and no out/gpu/papyrus/*.pex" >&2; exit 1; }
key=$({ [ ${#plugins[@]} -gt 0 ] && sha256sum "${plugins[@]}"; [ ${#pex[@]} -gt 0 ] && sha256sum "${pex[@]}"; true; } | sha256sum | cut -c1-12)
step "machine up" "$run" up
have=$("$run" ps 'Get-Content C:\argonia\state\deployed.key -EA SilentlyContinue' 2>/dev/null | tr -d '\r\n ' || true)
if [ -z "${DEPLOY_FORCE:-}" ] && [ "$have" = "$key" ]; then echo "DEPLOY held: $key, skipped in $(( SECONDS - t0 )) s"; exit 0; fi
echo "deploy: machine holds ${have:-nothing}, laying $key"
[ -n "$have" ] && "$run" ps 'Remove-Item C:\argonia\state\deployed.key -EA SilentlyContinue' >/dev/null 2>&1 || true

send() {
  "$run" ps 'New-Item -ItemType Directory -Force C:\argonia\ours, C:\argonia\infra, C:\argonia\state | Out-Null' >/dev/null
  for f in "${plugins[@]}"; do "$run" put "$f" "C:/argonia/ours/$(basename "$f")" >/dev/null; echo "$(basename "$f") sent"; done
  "$run" ps 'Remove-Item C:\argonia\ours\scripts -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force C:\argonia\ours\scripts | Out-Null' >/dev/null
  [ ${#pex[@]} -gt 0 ] && { "$run" put "${pex[@]}" C:/argonia/ours/scripts/ >/dev/null; echo "${#pex[@]} .pex sent"; }
  # the machine-side helpers and Moonlight's cards
  "$run" put "$here"/{stack.ps1,idle-stop.ps1,spot-watch.ps1,stream-activity.ps1,saves-sync.ps1,vanilla-data-files.txt,sunshine-apps.json,make-cards.ps1} C:/argonia/infra/ >/dev/null
  "$run" ps "& C:\\argonia\\infra\\make-cards.ps1; \$a='C:\\Program Files\\Sunshine\\config\\apps.json'; \$n='C:\\argonia\\infra\\sunshine-apps.json'; if ((Get-FileHash \$n).Hash -ne (Get-FileHash \$a -EA SilentlyContinue).Hash) { Copy-Item \$n \$a -Force; Restart-Service SunshineService; 'sunshine: app list changed, restarted' } else { 'sunshine: app list unchanged' }"
}
step "send" send
step "stack on" "$run" ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\stack.ps1 on'
"$run" ps "Set-Content -NoNewline C:\\argonia\\state\\deployed.key '$key'" >/dev/null
echo "DEPLOY OK in $(( SECONDS - t0 )) s"

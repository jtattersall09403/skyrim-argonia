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
plugins=(out/*.esm out/*.esp out/Argonia.ini)
plugins=($(printf '%s\n' "${plugins[@]}" | while read -r f; do [ -f "$f" ] && echo "$f"; done)) || true
# only the compiled scripts whose source we still have (papyrus/ and papyrus/generated/, the scripts the plugin's records
# name, as questcheck checks): a retired quest's .pex left in out/gpu/papyrus is never sent
pex=(); for f in out/gpu/papyrus/*.pex; do s=$(basename "$f" .pex); { [ -f "papyrus/$s.psc" ] || [ -f "papyrus/generated/$s.psc" ]; } && pex+=("$f"); done
[ ${#plugins[@]} -gt 0 ] || [ ${#pex[@]} -gt 0 ] || { echo "nothing to send: no out/*.esp|esm and no out/gpu/papyrus/*.pex" >&2; exit 1; }
seq=(out/SEQ/*.seq); [ -f "${seq[0]:-}" ] || seq=()  # Seq.cs: the start-game quests a new game starts first
key=$({ [ ${#plugins[@]} -gt 0 ] && sha256sum "${plugins[@]}"; [ ${#seq[@]} -gt 0 ] && sha256sum "${seq[@]}"; [ ${#pex[@]} -gt 0 ] && sha256sum "${pex[@]}"; true; } | sha256sum | cut -c1-12)
step "machine up" "$run" up
# never under the owner's stream: a deploy restarts the stack. DEPLOY_STREAM_WAITED=1 says the caller already waited.
if [ -z "${DEPLOY_STREAM_WAITED:-}" ]; then
  live=$(ARGONIA_PEEK=1 "$run" ps '. C:\argonia\infra\stream-activity.ps1; (Get-StreamActivity).streaming' 2>/dev/null | tr -d '\r' | tail -1)
  [ "$live" = True ] && { echo "deploy refused: a stream session is live on the machine; wait for it to end (or DEPLOY_STREAM_WAITED=1 after waiting)" >&2; exit 3; }
fi
have=$("$run" ps 'Get-Content C:\argonia\state\deployed.key -EA SilentlyContinue' 2>/dev/null | tr -d '\r\n ' || true)
if [ -z "${DEPLOY_FORCE:-}" ] && [ "$have" = "$key" ]; then echo "DEPLOY held: $key, skipped in $(( SECONDS - t0 )) s"; exit 0; fi
echo "deploy: machine holds ${have:-nothing}, laying $key"
[ -n "$have" ] && "$run" ps 'Remove-Item C:\argonia\state\deployed.key -EA SilentlyContinue' >/dev/null 2>&1 || true

send() {
  "$run" ps 'New-Item -ItemType Directory -Force C:\argonia\ours, C:\argonia\infra, C:\argonia\state | Out-Null' >/dev/null
  for f in "${plugins[@]}"; do "$run" put "$f" "C:/argonia/ours/$(basename "$f")" >/dev/null; echo "$(basename "$f") sent"; done
  "$run" ps 'Remove-Item C:\argonia\ours\scripts -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force C:\argonia\ours\scripts | Out-Null' >/dev/null
  [ ${#pex[@]} -gt 0 ] && { "$run" put "${pex[@]}" C:/argonia/ours/scripts/ >/dev/null; echo "${#pex[@]} .pex sent"; }
  "$run" ps 'Remove-Item C:\argonia\ours\SEQ -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force C:\argonia\ours\SEQ | Out-Null' >/dev/null
  [ ${#seq[@]} -gt 0 ] && { "$run" put "${seq[@]}" C:/argonia/ours/SEQ/ >/dev/null; echo "${#seq[@]} .seq sent"; }
  # the machine-side helpers and Moonlight's cards
  "$run" put "$here"/{stack.ps1,idle-stop.ps1,spot-watch.ps1,stream-activity.ps1,saves-sync.ps1,vanilla-data-files.txt,sunshine-apps.json,make-cards.ps1} C:/argonia/infra/ >/dev/null
  "$run" ps "& C:\\argonia\\infra\\make-cards.ps1; \$a='C:\\Program Files\\Sunshine\\config\\apps.json'; \$n='C:\\argonia\\infra\\sunshine-apps.json'; if ((Get-FileHash \$n).Hash -ne (Get-FileHash \$a -EA SilentlyContinue).Hash) { Copy-Item \$n \$a -Force; Restart-Service SunshineService; 'sunshine: app list changed, restarted' } else { 'sunshine: app list unchanged' }"
}
step "send" send
# The pad layout follows controlmap.py (owner ruling #51): the machine's made controlmap.txt fetched, GAMEPLAY
# re-applied, sent back; stack.ps1 on lays it in Data. No file there: make it once with controlmap.py from the BSA.
controls() {
  local t; t=$(mktemp -d)
  if "$run" get 'C:/argonia/controls/controlmap.txt' "$t/was.txt" 2>/dev/null; then
    python3 "$here/controlmap.py" --remap "$t/was.txt" "$t/controlmap.txt" && "$run" put "$t/controlmap.txt" 'C:/argonia/controls/controlmap.txt'
  else echo "controls: no C:\argonia\controls\controlmap.txt on the machine; make it with controlmap.py"; fi
  rm -rf "$t"
}
step "controls" controls
# A child powershell's failure (stack.ps1's throw, e.g. "Data is held by ...") does not reach ssh's exit code on its
# own: the outer shell exits 0 unless it passes $LASTEXITCODE on. Without this the deploy said OK over a failed lay.
step "stack on" "$run" ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\stack.ps1 on; if ($LASTEXITCODE) { exit $LASTEXITCODE }'
# The walk's console batches (repro_a, repro_b) beside SkyrimSE.exe, with the laid load order's index; never fails the deploy.
step "console batches" bash -c '"$0" || echo "console batches: failed; run infra/gpu-box/bodies_repro.sh"' "$here/bodies_repro.sh"
# Community Shaders' cache for the laid card: laid from the archive of its key when the machine lacks it, archived when
# the machine holds a compiled one the archive lacks. Never fails the deploy; a world-file-only deploy keeps the key.
step "shader cache" bash -c '"$0" ensure && "$0" save || echo "shader cache: failed; the next deploy retries"' "$here/shader_cache.sh"
"$run" ps "Set-Content -NoNewline C:\\argonia\\state\\deployed.key '$key'" >/dev/null
echo "DEPLOY OK in $(( SECONDS - t0 )) s"

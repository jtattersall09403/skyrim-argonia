#!/usr/bin/env bash
# What exists only on one game machine, and whether the private buckets hold it (docs/machine-moves.md).
#   machine_inventory.sh --machine <name>     read-only: one listing over run.sh ps, then S3 listings here; the raw
#                                             listing is kept as out/inventory/<name>.tsv
#   machine_inventory.sh --replay <tsv>       classify a kept listing again (no machine)
# Every line: <kind> <tab> <path on the machine> <tab> <size> <tab> archived | UNARCHIVED | not counted (scratch); what the repo rebuilds is not listed.
# Exit 0 when nothing is UNARCHIVED, 1 when something is (the move rule: no retirement until 0), 2 on usage.
# Read-only on the machine: Get-ChildItem only; nothing is written, tarred or started there. Kinds:
#   mod    an MO2 mod folder whose name is no row of data/dependencies.json or combat-test-mods.json (their archives
#          are in s3://<private>/mods/) and that deploy.sh does not build (Argonia SKSE, SkyLink (dev, rebuilt));
#          "Argonia LOD (generated)" counts as archived when s3://<private>/lod/ holds a tar of its size (lod.sh archive)
#   save   a save that isn't ours (argoniabase*, ArgoniaRest, ArgoniaSuspend, quicksave/autosave are ours or Skyrim's
#          scratch); archived when the machine's saves.sh latest.zip (or the legacy saves/latest.zip) has it, same size
#   ck     a Creation Kit or records-job output in C:\argonia\records\out; the Papyrus compile is rebuilt by deploy;
#          anything else is archived when the build VM's out/gpu holds a file of that name and size (fetched back)
#   state  a C:\argonia top-level folder deploy.sh, setup.ps1 or the tools don't make (UNARCHIVED: archive it or say why
#          not); a loose top-level file is listed as scratch (an agent's one-off script) and not counted
set -euo pipefail
R=
case "${1:-}" in --machine) M=${2:?} ;; --machine=*) M=${1#--machine=} ;; --replay) R=${2:?}; M=$(basename "$R" .tsv) ;; *) sed -n 2,16p "$0"; exit 2 ;; esac
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd)
PRIV=${ARGONIA_PRIVATE_BUCKET:-argonia-private-050977237313}
SAVEB=${ARGONIA_SAVES_BUCKET:-argonia-saves-050977237313}
# C:\argonia entries made by deploy.sh, setup.ps1, stack.py, lod.sh and the bridge (grep of infra/ and tools/, 2026-10-31).
KNOWN='infra logs MO2 tools ours stream-client state skse records cards stack-state skylink moonlight-web lod controls downloads argonia-chrome no-deploy combat-stage cache'
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

# One read-only call: mods (name, bytes, files), saves, records\out, C:\argonia's top level (d = folder, f = file).
if [ -z "$R" ]; then
  mkdir -p "$repo/out/inventory"; R="$repo/out/inventory/$M.tsv"
  "$here/run.sh" --machine "$M" ps '
$m="C:\argonia\MO2\mods"; if (Test-Path $m) { Get-ChildItem $m -Directory | % { $f=@(Get-ChildItem $_.FullName -Recurse -File -EA SilentlyContinue); "mod`t$($_.Name)`t$(($f | Measure-Object Length -Sum).Sum + 0)`t$($f.Count)" } }
$s="$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\Saves"; if (Test-Path $s) { Get-ChildItem $s -File | % { "save`t$($_.Name)`t$($_.Length)`t1" } }
$r="C:\argonia\records\out"; if (Test-Path $r) { Get-ChildItem $r -Recurse -File | % { "ck`t$($_.FullName.Substring($r.Length+1))`t$($_.Length)`t1" } }
Get-ChildItem C:\argonia -Force | % { if ($_.PSIsContainer) { "top`t$($_.Name)`t0`td" } else { "top`t$($_.Name)`t$($_.Length)`tf" } }' | tr -d '\r' > "$R"
fi

aws s3 ls "s3://$PRIV/lod/" 2>/dev/null | awk '{print $3}' > "$tmp/lod.sizes" || true
for p in "saves/$M" saves; do
  aws s3 cp "s3://$SAVEB/$p/latest.zip" "$tmp/s.zip" --only-show-errors 2>/dev/null &&
    python3 -c 'import sys,zipfile; [print(i.filename.split("/")[-1]+"\t"+str(i.file_size)) for i in zipfile.ZipFile(sys.argv[1]).infolist()]' "$tmp/s.zip" >> "$tmp/saves.tsv" || true
done
touch "$tmp/saves.tsv"
find "$repo/out/gpu" -type f -printf '%f\t%s\n' 2>/dev/null > "$tmp/vm.tsv" || true

KNOWN="$KNOWN" python3 - "$R" "$repo" "$tmp" "$M" <<'PY'
import os, re, sys
tsv, repo, tmp, machine = sys.argv[1:]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
names = set()
for f in ("data/dependencies.json", "infra/gpu-box/combat-test-mods.json"):
    names |= {norm(m) for m in re.findall(r'"(?:name|id|mod)":\s*"([^"]+)"', open(os.path.join(repo, f)).read())}
built = {norm(x) for x in ("Argonia SKSE", "Argonia SKSE (dev only)", "SkyLink (dev, rebuilt)")}
lod = [int(x) for x in open(f"{tmp}/lod.sizes").read().split()]
saves = set(open(f"{tmp}/saves.tsv").read().splitlines())
vm = set(open(f"{tmp}/vm.tsv").read().splitlines())
known = set(os.environ["KNOWN"].split())
ours = re.compile(r"^(argoniabase|ArgoniaRest|ArgoniaSuspend|quicksave|autosave)|\.skse$", re.I)
bad = 0
for line in open(tsv):
    kind, name, size, n = (line.rstrip("\n").split("\t") + ["", "", ""])[:4]
    size_i = int(size) if size.isdigit() else 0
    if kind == "mod":
        if name == "Argonia LOD (generated)":  # a tar: the files plus a 512-byte header each, within 1%
            st = "archived" if any(abs(t - (size_i + 512 * int(n or 0))) <= 0.01 * t + 20480 for t in lod) else "UNARCHIVED"
        elif norm(name) in names or norm(name) in built or size_i == 0:
            continue
        else:
            st = "UNARCHIVED"
    elif kind == "save":
        if ours.search(name):
            continue
        st = "archived" if f"{name}\t{size}" in saves else "UNARCHIVED"
    elif kind == "ck":
        if name.startswith("papyrus") or name == "compile.log":
            continue
        st = "archived (build VM out/gpu)" if f"{name.split(chr(92))[-1]}\t{size}" in vm else "UNARCHIVED"
    elif kind == "top":
        if name in known:
            continue
        kind, st = ("state", "UNARCHIVED") if n == "d" else ("scratch", "not counted")
    else:
        continue
    bad += st == "UNARCHIVED"
    print(f"{kind}\t{name}\t{size if kind != 'state' else '-'}\t{st}")
print(f"{machine}: {bad} unarchived")
sys.exit(1 if bad else 0)
PY

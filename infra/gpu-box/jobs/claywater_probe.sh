#!/usr/bin/env bash
# Claywater on the round-5 close build (2026-11-04): the saves job crashed there at 00:16 (d3d11.dll null read while
# textures streamed, NiSourceTexture on the stack, the player still in the holding cell) and timed out on the save at
# 00:36. This measures the place with patience: a fresh launch, the base save, the teleport to the station marker, the
# game's health every 10 s for up to 4 minutes with a still at the end, then the save with a long wait; the newest
# crash log is fetched whole. Shaders on first (the owner's launch), then off if the first fails. Every end wakes the
# agent. Under job_guard --gpu=argonia-play.
set -u; cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=argonia-play
PY=$HOME/.argonia/venv/bin/python; OUT=out/diag/claywater-20261104; mkdir -p $OUT
SK='C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\SKSE'
fetch_crash() { infra/gpu-box/run.sh ps "Get-ChildItem '$SK\crash-*.log' | sort LastWriteTime | select -last 1 | % { Get-Content \$_.FullName }" > $OUT/crash-$1.log 2>&1; echo "crash log -> $OUT/crash-$1.log ($(wc -l < $OUT/crash-$1.log) lines)"; }
probe() {  # $1 = shaders on|off
  echo "== probe shaders $1 $(date -u +%H:%M:%S)"
  ARGONIA_SHADERS=$1 $PY tools/bridge.py launch || { echo "PROBE $1: no main menu"; return 3; }
  $PY tools/bridge.py load argoniabase >/dev/null 2>&1 || true
  $PY - "$1" "$OUT" <<'EOF'
import json, subprocess, sys, time
sys.path.insert(0, "/home/ubuntu/skyrim-argonia")
from tools.bridge import Bridge, BridgeError, GameDown
mode, out = sys.argv[1], sys.argv[2]
b = Bridge()
def settle_load(since, cap):
    end = time.monotonic() + cap
    while time.monotonic() < end:
        try:
            ev = b.call("events", since, "load")["events"]
            if any(e.get("kind") == "load" and e.get("state") in ("done", "finished") for e in ev): return True
        except BridgeError: pass
        time.sleep(2)
    return False
t0 = time.monotonic(); since = b.call("events")["last"]
try:
    r = b.call("console", "player.moveto ARG_Ref_ClaywaterStationQuestBoard")
    print("moveto:", str(r)[:120])
except BridgeError as e:
    print("moveto raised (the load holds the thread):", str(e)[:120])
ok = None
for i in range(24):
    time.sleep(10)
    try:
        h = b.call("ping"); p = b.call("player")
        print(f"  +{int(time.monotonic()-t0):3d}s health ok, cell {p.get('cell',{}).get('id')} ws {(p.get('worldspace') or {}).get('editor_id')} main_thread {h.get('ping',{}).get('main_thread')}", flush=True)
        if (p.get('worldspace') or {}).get('editor_id') == 'ARG_Province':
            ok = int(time.monotonic()-t0); break
    except GameDown as e:
        print(f"  +{int(time.monotonic()-t0):3d}s GAME DOWN: {str(e)[:160]}", flush=True); ok = False; break
    except BridgeError as e:
        print(f"  +{int(time.monotonic()-t0):3d}s busy: {str(e)[:100]}", flush=True)
print("ARRIVED after", ok, "s" if ok else "")
if ok:
    time.sleep(20)
    subprocess.run([sys.executable, "tools/bridge.py", "screenshot", f"{out}/claywater-{mode}.png"], timeout=120)
    t1 = time.monotonic()
    try:
        r = b.call("save", "Argonia Claywater"); print("save:", str(r)[:200], f"in {time.monotonic()-t1:.1f} s")
    except BridgeError as e:
        print("save error:", str(e)[:200])
    for i in range(12):
        time.sleep(10)
        try:
            h = b.call("ping"); print(f"  save wait +{(i+1)*10}s health ok", flush=True)
        except GameDown as e:
            print("  GAME DOWN after save:", str(e)[:160]); ok = False; break
sys.exit(0 if ok else 3)
EOF
  rc=$?; fetch_crash $1; return $rc
}
if probe on; then echo "CLAYWATER PROBE: shaders on OK $(date -u +%H:%M)"; res="on OK"
else echo "CLAYWATER PROBE: shaders on FAILED $(date -u +%H:%M)"; if probe off; then res="on FAILED, off OK"; else res="on FAILED, off FAILED"; fi; fi
infra/gpu-box/run.sh ps "Get-ChildItem 'C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\Saves\Argonia Claywater.ess' | % { \$_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') + ' ' + \$_.Length }"
echo "CLAYWATER PROBE DONE: $res $(date -u +%H:%M)"
infra/build-vm/agent-wake.sh "Claywater probe DONE: $res. Read ~/.argonia/jobs/claywater-probe.log and $OUT; if OK push the save (saves_push.sh) and hand over on #37; the machine is left up."

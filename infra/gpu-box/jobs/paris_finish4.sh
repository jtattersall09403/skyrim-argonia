#!/usr/bin/env bash
# Paris, resumable (owner, 2026-11-02). Like paris_finish3, but a DynDOLOD run is never cut while it progresses:
# finish3's 1 h timeout on the LOD run plus a 50 min re-attach bound would have killed any run longer than ~1 h 50
# and restarted it from scratch (17:24, with DynDOLOD at 12 min of CPU and no finished run ever measured). Now the
# run is bounded only by the desktop job's 4 h; a re-attached run waits up to 4 h and is killed only when stalled
# (no CPU time added in 10 min). Then mark the step done so the LOD run skips straight to collect and archive.
#   paris_finish4.sh <issue-number> [tries]
set -u
issue=${1:?issue}; tries=${2:-10}
cd /home/ubuntu/skyrim-argonia
export ARGONIA_PLAY=argonia-play
run=infra/gpu-box/run.sh
marks=~/.argonia/lod-steps/argonia-play/$(sha256sum out/ArgoniaWorld.esm | cut -c1-12); mkdir -p "$marks"
reattach() {  # 0 when a running DynDOLOD finished under us (marker written), 1 when none was running
  $run ps 'if (Get-Process DynDOLODx64 -EA SilentlyContinue) { "running" } else { "none" }' | grep -q running || return 1
  echo "DynDOLOD already running on Paris: waiting for its desktop job $(date -u +%H:%M)"
  # the driver (lod.ps1, a desktop job on the machine) writes "dyndolod OK" or an error to its log when the run ends;
  # a stale desktop-job.done from an earlier job says nothing (15:23: it made us kill a healthy run)
  last=0; same=0
  for i in $(seq 1 240); do
    if $run ps 'Get-Content C:\argonia\lod\logs\dyndolod.log -Tail 3 -EA SilentlyContinue' | grep -qE "dyndolod OK|did not complete|unknown pop-up|no wizard"; then break; fi
    cpu=$($run ps '$p=Get-Process DynDOLODx64,LODGen* -EA SilentlyContinue; if ($p) { [int](($p | Measure-Object CPU -Sum).Sum) } else { "none" }' | tail -1 | tr -d '\r')
    [ "$cpu" = none ] && break
    if [ "${cpu:-0}" -gt "$last" ] 2>/dev/null; then last=$cpu; same=0; else same=$((same+1)); fi
    [ $same -ge 10 ] && { echo "DynDOLOD stalled: no CPU added in 10 min (at ${last}s) $(date -u +%H:%M)"; break; }
    [ $((i % 15)) = 0 ] && echo "DynDOLOD at ${cpu}s of CPU $(date -u +%H:%M)"
    sleep 60
  done
  if $run ps 'Get-Content C:\argonia\lod\logs\dyndolod.log -Tail 3 -EA SilentlyContinue' | grep -q "dyndolod OK"; then
    date -u +%FT%TZ > "$marks/dyndolod"; echo "DynDOLOD finished under the previous attempt: marked"; return 0
  fi
  echo "DynDOLOD did not finish cleanly: it will run again"; $run ps 'Get-Process DynDOLOD* -EA SilentlyContinue | Stop-Process -Force' >/dev/null; return 1
}
for i in $(seq 1 "$tries"); do
  echo "== attempt $i $(date -u +%H:%M)"
  ~/.argonia/scripts/up_until.sh argonia-play 120 || continue
  if ARGONIA_PEEK=1 $run ps '. C:\argonia\infra\stream-activity.ps1; (Get-StreamActivity).streaming' 2>/dev/null | grep -q True; then
    echo "the owner is streaming on Paris: waiting"; sleep 600; continue
  fi
  $run put infra/gpu-box/stack.ps1 infra/gpu-box/bridge.ps1 infra/gpu-box/lod.ps1 C:/argonia/infra/ || continue
  if [ ! -f ~/.argonia/lod-steps/argonia-play/objlod-archived ]; then
    reattach || true
    $run ps 'Get-Process SkyrimSE,skse64_loader,TexGen*,LODGen*,Texconv* -EA SilentlyContinue | Stop-Process -Force; "clean"' || continue
    if timeout 15000 infra/gpu-box/lod.sh run resources dyndolod collect && infra/gpu-box/lod.sh archive; then
      date -u +%FT%TZ > ~/.argonia/lod-steps/argonia-play/objlod-archived; echo "OBJECT LOD ARCHIVED $(date -u +%H:%M)"
    else echo "object LOD did not finish this attempt"; sleep 60; continue; fi
  else echo "object LOD already archived ($(cat ~/.argonia/lod-steps/argonia-play/objlod-archived))"; fi
  if make deploy; then
    echo "DEPLOY OK on Paris $(date -u +%H:%M)"
    $run stop
    printf 'Paris ready: the round-3 world with terrain and object LOD, the nine region saves in the shared copy, the launcher waiting for Steam. Open play.jacktat-play.stream.\n' > ~/.argonia/paris-ready.md
    python3 tooling/owner_inbox.py --comment "$issue" --body-file ~/.argonia/paris-ready.md || true
    exit 0
  fi
  echo "deploy did not finish; next attempt resumes"; sleep 120
done
printf 'Paris: the job gave up after %s attempts; the planner needs to look.\n' "$tries" > ~/.argonia/paris-failed.md
python3 tooling/owner_inbox.py --comment "$issue" --body-file ~/.argonia/paris-failed.md || true
exit 3

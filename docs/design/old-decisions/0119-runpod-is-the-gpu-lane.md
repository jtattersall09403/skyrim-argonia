<!-- imported unchanged from elder-souls-argonia docs/decisions/0119-runpod-is-the-gpu-lane.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0119 — RunPod is the GPU lane: fifteen dollars a month, nothing slower than SwiftShader

Status: accepted. The lane serves the main-studio (WebGL) performance loop and
heavy render sweeps; the WebGL studio on `dev` is the one build
([0122](0122-webgpu-retired-webgl-studio-is-canonical.md)), so there is no
WebGPU loop. Extends the GPU options in
[gpu-dev-machine-cost-analysis.md](../research/infrastructure/gpu-dev-machine-cost-analysis.md)
(option F).

## Context

The VM has no GPU. Headless Chrome falls back to SwiftShader, which renders
the full studio so slowly that an agent cannot loop on frame-cost and
visual defects (under 10 fps, GPU memory never above 100 MB). The owner
installed the RunPod plugin at user scope and signed it in with OAuth; no
API key is stored anywhere in the repo or on the VM.

## Decisions

1. **Spend to go faster when it is cheap.** The GPU
   measure-diagnose-fix loops and the frame-cost numbers come first; any
   heavy render or capture sweep (an eyes-loop sweep over every place, a
   strip set, a look pass) also goes to a pod when a cheap GPU finishes
   it much faster than this CPU. Price before creating, one pod per
   sweep, delete it after, log the cost; the owner watches the monthly
   total and raises or lowers it.
2. **Only when faster end to end than SwiftShader on this box.** Boot,
   setup and sync time count: a pod that needs a long setup every time is
   not worth it. The setup is one script,
   `tooling/gpu-lane/runpod-setup.sh`, so a pod is ready in one step.
3. **Price first.** The agent states the hourly price before creating
   anything billable.
4. **One pod per lane, lanes in parallel, deleted (not stopped) when the
   lane's loop ends.** A fan-out job such as the agent walks audit runs one
   pod per parallel worker when that is faster end to end, each deleted the
   moment its worker ends. A stopped pod still bills its disk. Within a
   lane, a pod stays up across fix-measure iterations when that saves wall
   time (sync the build to it rather than booting a new pod) and is deleted
   the moment the lane has no next measurement queued.
5. **Every pod minute and dollar is logged in the lane report** (pod id,
   GPU type, $/h, start, end, minutes, dollars), so the month's spend is
   summable from the reports.
6. **A render probe over 5 min on SwiftShader runs on the pod.**
7. **A pod is deleted or handed over by id.** A lane report or walk packet
   that leaves a pod up names its id, who owns it next and when it is
   deleted. The lane that creates a pod deletes it before it hands back;
   handing deletion to a lead is forbidden.
8. **Blender work does not use RunPod.** Headless Blender on this box
   renders a place in minutes on CPU (`wb.py bpy`), and the budget is for
   the GPU loop.
9. **Every pod job prices its machine first and deletes it as soon as its verdicts are in.**
   There is no fixed time cap (the owner ruled the old 30-minute cap arbitrary, 2026-10-25): a job takes the time
   it takes. `agent_guard.py` refuses `create-pod` and `runpodctl pod create` unless the command or brief states the
   price (`$0.25/h`, read from the catalogue) and writes `pending-<agent>.json` (`lane`, `purpose`, `start`,
   `priceUsdPerHour`), which the agent renames to `<id>.json` once the id is known. `pod-shoot.sh` refuses every
   run, dry runs included, without `--price <$/h>` and either `--last` (it deletes the pod itself right after the
   pull, by PID 1's id and key) or `--more "<what follows>"` (the pod stays for the lane's next job, named in the
   ledger). `--max-minutes <n>` is optional: a job that has measured its own length may arm a dead-man timer, never
   a default. `lane_watch.py` (`pod_watch.py`) flags a pod past its marker's stated `maxMinutes` and STOPS one with no
   live marker lane (or no marker) after a 10-minute marker grace, logging it in `pods/stops.log`; the stop does
   not replace deleting a pod when its lane ends.
10. **The first job of any RunPod lane** is the README's open harness defects
    section (`tooling/gpu-lane/README.md`), emptied before its first capture.

## Where each lives

- Setup and the measure harness: `tooling/gpu-lane/`.
- The rule line: CLAUDE.md § GPU and visuals; the cost row in
  [gpu-dev-machine-cost-analysis.md](../research/infrastructure/gpu-dev-machine-cost-analysis.md).

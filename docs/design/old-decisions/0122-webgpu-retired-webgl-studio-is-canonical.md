<!-- imported unchanged from elder-souls-argonia docs/decisions/0122-webgpu-retired-webgl-studio-is-canonical.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0122 — WebGPU is retired; the WebGL studio on `dev` is the one canonical build

Status: accepted (owner 2026-10-03, 16k walk 11). Supersedes
[0121](0121-webgpu-stays-a-second-build-until-parity.md) and the WebGPU parts
of 0111 (the WebGPU port, on branch `webgpu` only) and of
[0119](0119-runpod-is-the-gpu-lane.md) (the WebGPU pod loop).

## Context

Owner, 2026-10-03: "Let's ditch webGPU. It's not working super well, while
the main studio is looking fantastic and running brilliantly on mobile and
desktop. Make that the canonical branch and retire the webgpu option. Don't
delete the code we might refer back to it." Walk 10 left the WebGPU build
below the frame bar (froxel cost, TSL material cost, a 30 s precompile) while
the WebGL studio met 49 of 50 performance rows.

## Decisions

1. **The WebGL studio on `dev` (deployed at `/studio/`) is the one build.**
   There is no second build, no `/webgpu/` path on the site, no parity bar
   and no one-branch call left to make.
2. **Branch `webgpu` is kept, read-only, as reference.** Nobody commits to
   it, merges into it, builds it, tests it or deploys it. Its records (0110
   volume fire, 0111 WebGPU port, 0112 volumetrics) stay on that branch as
   history; read them with `git show webgpu:docs/decisions/<file>`.
3. **Nothing on `dev` reads the branch.** Removed in this change: the
   preflight gate `webgpu-merged` and its script `merge_forward.py`, the
   Pages workflow steps that built `/webgpu/`, the WebGPU boot check and
   the `--renderer webgpu` option and pod flags in `tooling/gpu-lane/`
   (the gpu-lane harness stays for main-studio performance loops; its
   static server is `apps/world-studio/scripts/lib/studio-static.mjs`).
4. **The indoor player-fill light is dropped.** It existed only on the
   `webgpu` branch (`playerFill.ts`, `&playerfill`); `dev` never had it.
5. **The RunPod lane (0119) serves the main-studio performance loop only.**
6. **The volumetric work comes to WebGL as its own lanes.** The WebGL
   successors of 0110 and 0112 (interior light shafts, marsh mist, cap
   clouds) are walk-11 lanes and get their own records (0123, 0124); they
   may read the branch's code as reference, never merge it.

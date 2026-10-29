<!-- imported unchanged from elder-souls-argonia docs/decisions/0156-test-each-building-block-at-its-cheapest-level-compose-once.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0156 — Test each building block at its cheapest level, compose once

Status: accepted (owner, 2026-10-22). Supersedes the pod-strip part of
[0155](0155-journeys-are-staged-scenes.md) and the seam rules it implied.

Retires (clauses `decision_drift.py` reds in a brief): `pod strip`, `step by step by a .?reader`,
`strips? per journey`, `owes more than one strip`, `seam cuts on pods`, `four strips`

## The problem

2.10 spent most of its sessions on the filming rig: a driver that stood
the player up too long, a camera-centring bug in the test driver, aims
that pointed at feet or stale positions, screenshots too slow to catch an
arrow, readers sampling frames, pods lost with sessions. Twelve filming
passes for one feature, almost none of them finding a game defect. The
owner's words: inexcusable; we build the game, not the tools.

The cause was the shape of the check, not the care taken: every seam
re-played mechanics earlier phases had already proved (crouch-walking,
aiming, a melee blow landing, a door opening), on the most expensive
harness we own (a GPU pod, a filmed strip, a frame-by-frame reader), so
every harness defect in that long chain read as a game red.

## The rule

A feature is a composition of building blocks. Each block is checked
**once, at the cheapest level that can prove it**, and the composition
is checked only for what composition can break. From cheapest up:

| Level | Harness | Proves | Cost |
|---|---|---|---|
| 1 data | unit and table tests over the records and the one service (a detection table across light, gait, distance; a damage multiplier; an Owing rate; a lock threshold) | the numbers and the rules | seconds, no GPU |
| 2 still | ui-lab stills on three viewports, `look` sheets, the sandbox's static frames | a screen, an icon's states, a pose, a prompt | seconds; a reader over a handful of images |
| 3 motion | the combat sandbox `visual:check` groups, the animation seam checks | one animation or transition in isolation (a crouched attack, a sneak-bow draw, a backstab) | a minute; CPU render or one pod burst |
| 4 headless play | the scene and game runners playing a staged script (`journey.ts`), both runners agreeing | that blocks join: the state flows from one to the next, the save round trip | seconds, no GPU |
| 5 filmed seam | a 3–8 s strip on a pod, read frame by frame | only what no lower level can see: that a player watching the join understands it (the eye word turning as the guard turns, the stop opening on the right speaker) | minutes and dollars per pass |
| 6 journey | the owner playing the deployed studio | the whole, as a player | the owner's time |

Rules that follow:

1. **A check lives at the lowest level that proves it, never higher.**
   Damage is a level-1 test, never a filmed stab. An icon's four states
   are level-2 stills, never four filmed approaches. A crouched attack
   animation is level 3 by the standard animation route (source the clip,
   wire it, the sandbox check), never a scene.
2. **Levels 4 and 5 stage every block proved below them.** A staged scene
   sets the body at the blow's reach, fires the arrow through the game's
   own hit path onto its mark, opens the door, places the witness in
   view: it plays only the join it tests, so it can fail only on that.
   Playing a proved block again is a defect in the check.
3. **A filmed seam needs a reason a lower level cannot give.** The brief
   names it. A feature with no such join films nothing.
4. **Journeys are the owner's.** They run at level 4 as the cheap gate
   on both runners; no agent films or reads them.
5. **Blocks loop in parallel, then compose once.** The stills, the data
   tests, the animations and the headless joins of one feature run as
   parallel small loops with disjoint files; the filmed seam, if any,
   runs after they are green, on one pod the lane keeps up for its whole
   loop, filming several cuts at once (`measure-parallel --parallel N`,
   N by measured fps; more pods when one is saturated).
6. **The harness is tested before a lane uses it.** A change to the
   driver, the capture or the reader carries its own test and a dry run
   on a known-green cut; a harness defect found in a lane is fixed at
   source with that test before the lane films again.

## Worked example: sneaking (2.10)

| Block | Level | Check |
|---|---|---|
| detection numbers (stay hidden where you should, get seen where you should) | 1 | table tests over observers × light × gait × distance; the eye word per band |
| the eye's look and four words | 2 | ui-lab stills of the HUD, one per state, three viewports; a reader |
| crouch, crouch-walk | proved in 2.1/2.7 | nothing |
| crouched attack, sneak-bow draw, backstab animations | 3 | the animation route and the sandbox group |
| sneak-attack damage and the one-shot rule | 1 | `stealthStep.test` |
| noise → search → give up | 4 | a staged headless script on both runners |
| the eye word turning as a camper turns on the player | 5 | one 5 s strip, read |
| creep up on a camp and stab | 6 | the owner |

## Consequences

- `loops.md § Rules` carries the table and rules 1–6; phase briefs name
  each loop row's level and, for a level-5 row, its reason.
- `brief_template.py --type loop` asks for the level per row and refuses
  a level-5 row without a reason line; `agent_guard` enforces it.
- The 2.10 journeys capture lane is void; 2.10's remaining seams stage
  their proved blocks.

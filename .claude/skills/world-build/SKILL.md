---
name: world-build
description: Change the new world (its relief, water, ground, plants, air, navmesh, map) and rebuild it with one command that runs only the stages the change made stale, each check straight after its stage. Holds the rules that keep a change from breaking what stands on the ground, what goes stale on the other machines, and how lanes work beside a build. Use for any change to the new world's generated ground or world file, and whenever the world is rebuilt.
---

# Change and rebuild the new world

The new world is built by stages under `out/newworld/` into one world file, `ArgoniaNewWorld.esm`. One command
knows the stages, their order and what each reads: `tools/newworld/rebuild.sh`. A stage runs only when something it
reads has changed. Nothing that is current is built again, here or on the other machines.

## The order of work

| Step | What | Where |
|---|---|---|
| 1 | Measure before you set a rule; check the change against what stands on the ground | sections 1 and 2 |
| 2 | Make the change at its source | section 3, and [changes.md](changes.md) |
| 3 | Read the plan: which stages are stale and why | section 4 |
| 4 | Run the rebuild once, under the job guard | section 5 |
| 5 | Mend a red check at its cause and run again | section 6, and [checks.md](checks.md) |
| 6 | Commit what the run rewrote; bring the built places and the other machines level | section 7 |
| 7 | The owner's walk check | section 9 |

Lanes working beside a build: section 8. Costs: section 10.

## 1. Measure first

A threshold, a profile or a limit comes from a measurement of Skyrim's own data (decision 0034), taken before the
rule is written and kept with its number in `docs/research/` or `docs/design/`. A rule with no measurement behind
it is not ready to build.

- The reference ground is `out/newworld/terrain_ref/tamriel_h.npy`; `python3 -m tools.newworld.terrain_quality`
  and `python3 -m tools.newworld.terrain_character` measure Skyrim beside ours.
- Banks and the water's edge: the navmesh walks ground up to 45 degrees. Every terrain rule is measured at the
  waterline against that limit, per water kind, against Skyrim's shores
  ([relief research](../../../docs/research/nw-02-walk5-relief.md): held ground and banks).
- Ground and roads: [ground research](../../../docs/research/nw-02-walk5-ground.md). Water's look and seams:
  [water research](../../../docs/research/nw-02-walk5-water.md). Air and mist:
  [the atmosphere design](../../../docs/design/atmosphere.md). Far view and teleports:
  [far-view research](../../../docs/research/nw-02-walk5-L.md).

## 2. What a change may not break

- **A built place's ground is held.** Every folder under `newworld/places/` has a row in
  `newworld/sources/terrain_held.json`: the terrain build it was seated on and its cells. Inside them the beds are
  that build's, sample for sample, and the land is that build's plus a lift that ramps from nothing at the old
  waterline. A terrain change is tried on the built places before the world is rebuilt:
  `ARGONIA_TERRAIN_PROBE=<place>,<place> tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run --to needs`
  builds the terrain, runs `terrain check` (held ground exact, each water kind's waterline triangles over 45
  degrees within Skyrim's share) and judges every place's needs, and stops there
  (`tooling/job_guard.sh wait nw-rebuild`). Read both before anything later runs.
- **The waterline does not move without the owner.** `water_kinds` fails when a kind's bodies or area leave the
  accepted classification (`newworld/sources/water_accepted.json`) or the waterline moves. When the change is
  meant to move them, show the owner the new classification (the Atlas, section 7), and only on the owner's word
  run `python3 -m tools.newworld.water_kinds --accept`, then the rebuild again.
- **The owner's water edits hold their water.** Each kind edit keeps the water of the body it was made on
  (`newworld/sources/water_owner_bodies.png`). An edit is taken in only by the pull in [changes.md](changes.md);
  never edit `water_overrides.json` by hand.
- **One frame.** Every raster and position is the picture's own pixels and world units, whatever the grid's
  size: a tool finds a sample through the build's origin (`build.json`, the landcover legend, `units.Grid`),
  never by an index it kept. A new consumer of the grid gets a row and a test in the
  [frame audit](../../../docs/research/nw-02-walk5-water-frame.md).
- **Ids stay.** Noise, rounding and seeds are anchored to the picture's grid, so a wider scope moves no ground.
  Atmosphere records have fixed form ids. The world's copied records count up in the listed order of
  `tex/materials.json`: add a material at the end of its list, and rebuild the place layer after the world.
- **A terrain need is mended, not waved through.** `terrain_needs` fails on a failure that
  `newworld/sources/terrain_needs_accepted.json` does not name. A row is added there only when the map gives the
  place no such ground, with that reason, the judge's own words for the failure (`reason`) and the value it was
  measured at (`bound`): the same need failing for another reason, or worse than its bound, fails the stage again.

## 3. Make the change at its source

Change the source file, the rule's code or the database's source, never an output. [changes.md](changes.md) names,
for each kind of change, the source to edit, the stages it makes stale, the stages it leaves alone, and what
follows on the other machines. The plan (next section) is the authority: the table tells you what to expect, the
plan tells you what is so.

## 4. Plan

    tools/newworld/rebuild.sh plan

It prints the order (derived from what each stage reads and writes) and each stage's state:

- `current`: what it reads is what its last green run read. It will not run.
- `stale`, with the reason: the inputs that changed, a missing output, or an output that names another build. It
  runs.
- `follows` a stale stage: it runs only if that stage changes something it reads. A stage whose inputs come out
  the same bytes is skipped at its turn. A terrain build whose heightmap comes out the same bytes is the same
  build: it keeps its id, and the stages after it are skipped.
- `proved`: the rebuild has no record of the stage, and its own tool proves its output was made from today's
  inputs. Its checks alone run, and the run marks it; from then on it goes stale by everything it reads.

If the plan shows more stale than the table led you to expect, find out why before running: a file changed that
you did not mean to change.

The rebuild keeps one record for each stage (`out/newworld/rebuild/<stage>.json`), written only by a run: that the
stage's commands have started, that they are done, and, when its checks are green, the key of everything the stage
read. A run that was killed or went red part-way through a stage leaves that stage stale, whatever is done to its
inputs afterwards. A stage with no record is current only when its own tool proves it: the record the tool left
beside its output, computed again from today's inputs, is the same (the terrain, the land shards, the landcover,
the placed refs, the ground paint, the cells). Matching build ids are not proof. A stage that cannot prove it runs.
Never write a record by hand.

The land shards, the landcover, the placed refs, the ground paint and the world file each skip, or resume by row,
on a key of their own that covers less than their stage reads. The rebuild hands each its own key for the stage
(`tools/newworld/keyed.py`, `world.sh`), so a stage the plan calls stale is always built again and a stopped run
resumes where it stopped. Run by hand, each tool keeps its own key.

A tool that hashes its own file into its key (`world/land.py`, `landcover.py`, `world/texture.py`,
`place/place.py`) goes stale with any edit to that file, a comment included: its whole output is built again, and
everything after it. Put what is not the rule itself in another file (`tools/newworld/proofs.py` and
`tools/newworld/keyed.py` hold those tools' proofs and the rebuild's key for that reason).

`plan` reads each file once and remembers its digest while the file is untouched; `run` reads every file it
decides on.

## 5. Run

    tools/newworld/rebuild.sh preflight
    tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run
    tooling/job_guard.sh wait nw-rebuild

- Run it in the main tree, level with `origin/main`. One rebuild at a time, never beside a place build or a
  studio finalise. `preflight` proves all of that, the inputs, the accepted records, the disk and the memory, and
  that every stale stage's tool starts; `run` runs it first and starts nothing if it is red.
- Before a run that reaches a long stage (`paint`, `navmesh`, `esm`), clear what can be cleared first:
  `make check`, and the terrain's own trial for a terrain change (section 2).
- The run starts each stale stage as soon as the stages it reads from are done, side by side where the machine's
  memory allows. Every cheap check (the terrain check, the needs, the water kinds, the relief rows, the teleports'
  landings, the placement check) is green before the paint or the navmesh starts.
- A stopped run is resumed by the same command: stamped stages are current, the stage that was stopped runs
  again, and the long stages keep the rows and cells they had built for it.
- `run --to <stage>` runs only what that stage needs. `run --force <stage>` runs a current stage again.
- Never run a stage's tool by hand in the main tree to move the build on: the plan cannot tell what it read.
- The run ends with a summary: stages run, stages skipped, checks passed and failed, what went stale beyond
  this build, and the tracked files it rewrote.

## 6. A red check

A red command or check stops the run there: nothing new starts, the stages already running finish, and the
check's own lines are printed (`out/newworld/rebuild/logs/<stage>.log` has the whole output).

1. Read what the check proves in [checks.md](checks.md). A check reads the written output, never the plan that
   made it.
2. Mend the cause in the stage that owns it (a rule, a source, a tool). The world is never bent to pass a check
   and a check is never loosened to pass a world; a limit changes only with a new measurement (section 1).
3. Run the same command again. Only the mended stage and what follows it run; if the stage's commands stood and
   only its check's reading changed, the check alone runs.

## 7. After a green run

1. Commit by path the tracked files the summary lists (`mods/dependencies.json`, tables under
   `newworld/story/data/db/`) with the change that caused them.
2. Republish the Atlas when the terrain or the water changed: `python3 -m tools.newworld.map_page`, then publish
   `out/newworld/map/index.html` to the Atlas's own link (`tools/newworld/water_overrides_pull.py` names it).
3. Bring level what the summary lists as stale beyond this build, in this order, each only if listed:
   - **Each built place.** Its ground must be checked before any LOD is built over it. Re-extract its ground
     bundle (`python3 -m tools.places extract --ground <place_id>`), then run the stages that the change calls for
     in the table of the skill `place-build`, section 7 (a relief change: `seating`; re-scattered plants:
     `clearance`; then `streets` where pieces or doors moved), then its build and check (section 8 there).
   - **The LOD.** See the section below.
   - **The deploy** of the world file and the stack to the play machine. See the section below.
4. Run the whole read-back once the other machines are level: `python3 -m tools.newworld.verify` (every group,
   the LOD's, the deploy's and the places' rows included). It must pass in full before the owner is asked to walk.

### The LOD and the deploy

[docs/design/lod.md](../../../docs/design/lod.md) is the recipe for the play machine's steps: which LOD step a
change makes stale, its preflight, and the deploy of the world file and the stack. Two rules hold here: no LOD step
starts before every built place's ground is level and checked on this world file, and the LOD is built for our
worldspace only.

## 8. Lanes in worktrees

- The main tree is the one writer of `out/`. A lane in its own worktree changes code and sources, proves them
  with tests on tmp paths, and lands; the rebuild runs in the main tree after the lane has landed.
- A lane that must read the build's outputs links them, never copies and never writes them:
  `cp -al <main tree>/out/newworld out/newworld` in the worktree, made again after each rebuild and removed when
  the reading is done (`rm -rf out/newworld` there removes the links alone). A hard link is the main tree's own
  file: a tool that writes under `out/newworld` in a worktree writes the main tree's build. So in a worktree
  `rebuild.sh run` refuses, no stage tool is run on its default paths, and nothing is driven through
  `tools.newworld.rebuild` from Python. What may run there: `tools/newworld/rebuild.sh plan`, and a tool told to
  write to another folder (`--out`, `--plugin`, `ARGONIA_TERRAIN_OUT=<dir>` for a trial terrain).
- A test never reads the tree's `out/`: it builds its own inputs under its tmp path (`tools/tests/conftest.py`
  points every module's `out/` path at a tmp folder).
- A lane that changes a rule says, in its hand-over, which row of [changes.md](changes.md) its change is, so the
  rebuild after it is planned before it lands.

## 9. The owner's walk check

- What the owner judges: look and feel in the game (relief, water, ground, plants, air, the far view, the map).
  What a file proves is never asked of the owner.
- The walk list is `docs/phases/new-worldspace-plan/nw-02-walk.md`: one check per bullet, the place named, how to
  get there, what to look for, how to reply. Each check starts with a console teleport from
  `out/newworld/plugin/map/teleports.md` (`coc ANW<Place>` for every place, `coc ANWWalk<Water>` for each kind of
  water, `coc ArgoniaNWStart`); never a cell number.
- Post it with `tooling/owner_inbox.py --post` only when the whole read-back has passed and the play machine
  holds this world file, its LOD and the stack.

## 10. Costs

- The rebuild runs on the build VM: about an hour of stage time when everything is stale, a few minutes for a
  change late in the order. The plan prints the stale stages' time and largest memory peak. Stop the VM when the
  work is done (`tooling/agent_stop.sh`).
- The play machine costs about $0.80 an hour while it runs (decision 0039) and stops itself when idle. The agent
  starts it for the LOD, the deploy and the place checks that need it, as jobs under
  `tooling/job_guard.sh run --gpu`, and never leaves it waiting on a build that has not finished here.

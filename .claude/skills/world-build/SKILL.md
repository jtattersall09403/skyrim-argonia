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
| 4 | Run the stale stages on the small world, and mend what it finds | section 5 |
| 5 | Run the rebuild once, under the job guard | section 5 |
| 6 | Mend a red check at its cause and run again | section 6, and [checks.md](checks.md) |
| 7 | Commit what the run rewrote; bring the play machine's copy, the built places and the LOD level, in that order | section 7 |
| 8 | The owner's walk check | section 9 |

The order of the stages is the command's, never yours: no stage is run by hand, and no check is saved for the end.
Lanes working beside a build: section 8. Weighing a review's findings: section 6. Costs: section 10.

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
  waterline. A pad's level ground begins behind the bank, never at the water's edge: the bank keeps a slope the
  navmesh walks.
- **A terrain change is tried before the world is rebuilt.**
  `tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run --to needs` builds the terrain, runs
  `terrain check` (held ground exact, each water kind's waterline triangles over 45 degrees within Skyrim's share)
  and judges every place's needs, and stops there (`tooling/job_guard.sh wait nw-rebuild`). Read both before
  anything later runs. With `ARGONIA_TERRAIN_PROBE=<place>,<place>` set, the terrain build also logs the ground at
  those places after each of its steps, which names the step that moved a place.
- **The waterline does not move without the owner.** `water_kinds` fails when a kind's bodies or area leave the
  accepted classification (`newworld/sources/water_accepted.json`) or the waterline moves. When the change is
  meant to move them, show the owner the new classification on the Atlas (the map page of section 7, step 2), and only on the owner's word
  run `python3 -m tools.newworld.water_kinds --accept`, then the rebuild again.
- **The owner's water edits hold their water.** Each kind edit keeps the water of the body it was made on
  (`newworld/sources/water_owner_bodies.png`), however the bodies are cut on a later build; it sets that water's
  kind and its bed and moves no land. An edit is taken in only by the pull in [changes.md](changes.md); never edit
  `water_overrides.json` by hand.
- **One frame.** Every raster and position is the picture's own pixels and world units, whatever the grid's
  size: a tool finds a sample through the build's origin (`build.json`, the landcover legend, `units.Grid`),
  never by an index it kept. A new consumer of the grid gets a row and a test in the
  [frame audit](../../../docs/research/nw-02-walk5-water-frame.md).
- **The same inputs build the same bytes.** Noise, rounding and seeds are anchored to the picture's grid, so a
  wider scope moves no ground, and a stage run twice on the same inputs writes the same output: the placement
  places the same references. The world file comes out the same bytes however often its map data is applied.
- **Ids stay.** Form ids are registered, never renumbered: `newworld/sources/world_formids.json` holds the id of
  every land texture, water type, blend, region and copied base by its name, a new one takes the next id of its
  kind's block, and an entry is never edited or removed. Cells and atmosphere records are placed by formula, and
  a placed reference's id follows from its lasting identity (the cell the rules put it in, its base and place
  there), so an edit or a re-place of its neighbours leaves it.
- **Every allocator keeps to its range.** `tools/newworld/idspace.py` is the one table of the world file's form
  ids: each allocator's range, sized for the province, none overlapping. A new kind of record takes a new row
  there and gives ids inside it alone; a range is never moved once a build has shipped its ids.
  `python3 -m tools.newworld.idspace` prints the table and judges what is built.
  Commit the file after a run that added ids (section 7).
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

The small world first, before any full run:

    tools/newworld/rebuild.sh small

It cuts one 16 by 16 cell block of the real build (`tools/newworld/small`: three regions, still and flowing water,
forest, rocky upland with cliffs, a road with a junction, a place at the water) and runs the stages from `land` to
`readback` on it under `out/newworld-small/`: the same commands and checks, each tool's paths pointed at the small
world, nothing under `out/newworld/` written (the run ends by proving it). Twelve stages from nothing take about
two minutes; a stage whose inputs stand is not run again.

- A red check marks its stage and the run goes on, so one run shows every fault. Mend each at its cause and run
  it again until it is green.
- A lane runs it in its own worktree: it reads the main tree's build and writes the worktree's
  `out/newworld-small/`.
- `rebuild.sh run` refuses a stale stage whose code is not the code of its last green small run, and names it. A
  stage whose code stands is not asked to be proven again.
- What the block does not prove, so what a full run still risks: memory and time at the province's size; the
  province's connectivity (settlement paths, landings, the walk checks' anchors); the rows that count the province
  (water kinds against the accepted classification, mist densities, regions read apart); the terrain, needs and
  water stages, which run before the cut; and every rule on ground the block does not hold (sea, coast, the
  margin, the cells beyond the picture).

Then the full run:

    tools/newworld/rebuild.sh preflight
    tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run
    tooling/job_guard.sh wait nw-rebuild

- Run it in the main tree, level with `origin/main`. One rebuild at a time, never beside a place build or a
  studio finalise. `preflight` proves all of that, the inputs, the accepted records, the small world's proof of
  every stale stage's code, the disk and the memory, and that every stale stage's tool starts; `run` runs it first
  and starts nothing if it is red.
- Before a run that reaches a long stage (`paint`, `navmesh`, `esm`), clear what can be cleared first:
  `make check`, the terrain's own trial for a terrain change (section 2), and the navmesh's fast test for a change
  to the placement or the navmesh ([checks.md](checks.md)).
- The run starts each stale stage as soon as the stages it reads from are done, side by side where the machine's
  memory allows. Every cheap check (the terrain check, the needs, the water kinds, the relief rows that read the
  regions apart, the teleports' landings, the placement check, the edits' check) is green before the paint or the navmesh starts,
  and the read-back of the written file is the run's own last stage.
- A stopped run is resumed by the same command: stamped stages are current, the stage that was stopped runs
  again, and the long stages keep the rows and cells they had built for it.
- `run --to <stage>` runs only what that stage needs. `run --force <stage>` runs a current stage again.
- Never run a stage's tool by hand in the main tree to move the build on: the plan cannot tell what it read.
- The run ends with a summary: stages run, stages skipped, checks passed and failed, what went stale beyond
  this build, and the tracked files it rewrote.

## 6. A red check, and a review's findings

A red command or check stops the run there: nothing new starts, the stages already running finish, and the
check's own lines are printed (`out/newworld/rebuild/logs/<stage>.log` has the whole output).

1. Read what the check proves in [checks.md](checks.md). A check reads the written output, never the plan that
   made it.
2. Mend the cause in the stage that owns it (a rule, a source, a tool). The world is never bent to pass a check
   and a check is never loosened to pass a world; a limit changes only with a new measurement (section 1).
3. Run the same command again. Only the mended stage and what follows it run; if the stage's commands stood and
   only its check's reading changed, the check alone runs.

A review of the world, its LOD or a place ranks each finding by what the player would notice in the game.

- A fault that breaks the game or is plainly seen is mended, whatever it reruns.
- A fault the player would not really notice is mended only when the mend is cheap and reruns no long stage or
  step. Otherwise it is written as one line in the current phase's file in `docs/phases/`, and the work goes on.
- A mend is proved on the small world (section 5, and the skill `world-lod`, section 4) before any long job is
  run for it.

## 7. After a green run

What stands on the world file is brought level in this order, each step only when the run's summary lists it as
stale beyond this build. The order keeps every long job on a world file that can no longer change.

1. Commit by path the tracked files the summary lists (`mods/dependencies.json`, tables under
   `newworld/story/data/db/`, and `newworld/sources/world_formids.json` after a run that added form ids) with the
   change that caused them.
2. Republish the Atlas when the terrain or the water changed: `python3 -m tools.newworld.map_page`, then publish
   `out/newworld/map/index.html` to the Atlas's own link (`tools/newworld/water_overrides_pull.py` names it).
3. Prove the world file settled: `tools/newworld/rebuild.sh settled` exits 0 when the main tree is level with
   `origin/main`, no stage is stale, no rebuild runs and no lane's worktree holds a change to a source of the
   world file. Otherwise it names what is owed: land or wait for that lane, bring the tree level, rebuild.
   Nothing below starts on a world file that is not settled.
4. **The play machine's copy.** `infra/gpu-box/run.sh up`, then `infra/gpu-box/lod.sh map` and
   `infra/gpu-box/lod.sh send` (the skill `world-lod`, section 5): the world file with its map data and LOD plan
   is on the play machine, and its hash is recorded here.
5. **Each built place**, before any LOD is built over it. Re-extract its ground bundle
   (`python3 -m tools.places extract --ground <place_id>`, then `python3 -m tools.places ground-check <place_id>`),
   run the stages the change calls for (the skill `place-build`, section 7: a relief change, `seating`;
   re-scattered plants or a changed navmesh rule, `clearance`), then its build and check (section 8 there), then
   `streets` and the build and check again where pieces or doors moved or the `streets` check names a point off the
   network. Commit the place files a stage changed.
6. **The LOD**, and with it the deploy of the place layer and the stack: the skill `world-lod`, sections 4 to 8.
7. **The whole read-back**, once the other machines are level: `python3 -m tools.newworld.verify` (every group,
   the LOD's, the deploy's and the places' rows included). It must pass in full before the owner is asked to walk.

A built place carries the hash of the world file it was built over, and each LOD step a key read from that file.
Both stand while the file's bytes stand: after step 4 the file changes only by a rebuild.

## 8. Lanes in worktrees

- The main tree is the one writer of `out/`. A lane in its own worktree changes code and sources, proves them
  with tests on tmp paths and on the small world, and commits on its own branch; the rebuild runs in the main tree
  after the lane has landed.
- A lane reads the build's outputs through hard links and writes none of them:
  `cp -al <main tree>/out/newworld out/newworld` in the worktree, made again after each rebuild and removed when
  the reading is done (`rm -rf out/newworld` there removes the links alone). A hard link is the main tree's own
  file: a tool that rewrites it in place rewrites the main tree's build, and a rebuild in the main tree changes
  what the lane reads. So a file a lane's run rewrites is copied first (`cp --remove-destination`), never linked;
  in a worktree `rebuild.sh run` refuses, no stage tool is run on its default paths, and nothing is driven through
  `tools.newworld.rebuild` from Python.
- What may run in a worktree: `tools/newworld/rebuild.sh plan`, `tools/newworld/rebuild.sh small` (it reads the
  main tree's build and writes the worktree's `out/newworld-small/`; it needs no link), and a tool told to write
  to another folder (`--out`, `--plugin`, `ARGONIA_TERRAIN_OUT=<dir>` for a trial terrain).
- A test never reads the tree's `out/`: it builds its own inputs under its tmp path (`tools/tests/conftest.py`
  points every module's `out/` path at a tmp folder).
- A lane's scratch is a folder of its own, deleted by name when the lane ends; a shared scratch folder is never
  cleared with a glob. A tracked file a rehearsal rewrote is restored or committed before the lane returns.
- A lane ends committed and clean: `git commit -m "<message>" -- <paths>` on its branch, no uncommitted or
  untracked file. The lead lands it with `tooling/lane_land.sh <worktree>` (rebase, `make check`, push, the main
  tree brought level, the worktree and branch removed). `tooling/lane_commit.sh` is the main tree's command and
  refuses in a lane's worktree.
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
  holds this world file, its LOD, the place layer and the stack.

## 10. Costs

- The rebuild runs on the build VM: about an hour of stage time when everything is stale, a few minutes for a
  change late in the order; the small world about two minutes. The plan prints the stale stages' time and largest
  memory peak. Stop the VM when the work is done (`tooling/agent_stop.sh`).
- The play machine's cost and care are in the skill `world-lod`, section 9. It is started only once the world
  file is settled here (section 7).

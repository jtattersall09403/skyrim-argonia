---
name: world-build
description: Change the new world and rebuild it with one command that runs only the stages a change made stale, each check straight after its stage. The province's ground (relief, water, land, landcover, paint) is a fixed base that is never regenerated; every change of ground is a local patch over it. Holds the rules that keep a change from breaking what stands on the ground, what goes stale on the other machines, and how lanes work beside a build. Use for any change to the new world's generated content or world file, for any change of ground, and whenever the world is rebuilt.
---

# Change and rebuild the new world

The new world is built by stages under `out/newworld/` into one world file, `ArgoniaNewWorld.esm`. One command
knows the stages, their order and what each reads: `tools/newworld/rebuild.sh`. A stage runs only when something it
reads has changed. Nothing that is current is built again, here or on the other machines.

The province's ground is a **fixed base**: the stages that make it (`scope`, `regions`, `terrain`, `water`, `land`,
`landcover`, `cells`, `paint`) are never run. Their outputs are held to the identity recorded in
`newworld/sources/ground_base.json`, and the rebuild refuses to run while any of them differs. Every change of
ground after the base is a **local patch** laid over it in a bounded area:

- a place's own ground (its carried ground, `land.jsonl`, `paint.jsonl`, its paths) is patched by its place build
  (the skills `place-site` and `place-change`), in the place layer, over the cells the place covers;
- ground outside any place (a road's bed, a landing) is a row of `newworld/sources/ground_patches.jsonl`, laid by
  the `ground-patch` stage over the base's land, only in the cells the row reaches (section 3).

A patch is re-run alone, and its staleness never reaches the base. The base is made again only when the owner asks
for it in so many words (section 11).

## The order of work

| Step | What | Where |
|---|---|---|
| 1 | Measure before you set a rule; check the change against what stands on the ground | sections 1 and 2 |
| 2 | Make the change at its source: a change of ground is a patch | section 3, and [changes.md](changes.md) |
| 3 | Read the plan: the base fixed, which stages are stale and why, which patches are owed | section 4 |
| 4 | Run the stale stages on the small world, and mend what it finds | section 5 |
| 5 | Run the rebuild once, under the job guard | section 5 |
| 6 | Mend a red check at its cause and run again | section 6, and [checks.md](checks.md) |
| 7 | Commit what the run rewrote; bring the play machine's copy, the built places and the LOD level, in that order | section 7 |
| 8 | The owner's walk check | section 9 |

The order of the stages is the command's, never yours: no stage is run by hand, and no check is saved for the end.
Lanes working beside a build: section 8. Weighing a review's findings: section 6. Costs: section 10. A new base,
only on the owner's word: section 11.

## 1. Measure first

A threshold, a profile or a limit comes from a measurement of Skyrim's own data (decision 0034), taken before the
rule is written and kept with its number in `docs/research/` or `docs/design/`. A rule with no measurement behind
it is not ready to build.

- The reference ground is `out/newworld/terrain_ref/tamriel_h.npy`; `python3 -m tools.newworld.terrain_quality`
  and `python3 -m tools.newworld.terrain_character` measure Skyrim beside ours.
- Banks and the water's edge: the navmesh walks ground up to 45 degrees. A patch that shapes a bank keeps it within
  that limit, against Skyrim's shores ([relief research](../../../docs/research/nw-02-walk5-relief.md): held
  ground and banks).
- Ground and roads: [ground research](../../../docs/research/nw-02-walk5-ground.md). Water's look and seams:
  [water research](../../../docs/research/nw-02-walk5-water.md). Air and mist:
  [the atmosphere design](../../../docs/design/atmosphere.md). Far view and teleports:
  [far-view research](../../../docs/research/nw-02-walk5-L.md).

## 2. What a change may not break

- **The base stands.** No change regenerates the province's ground: the base stages are never stale, whatever a
  place, a road, a person or a note says, and `rebuild.sh plan` says so on its first line ("the province's ground:
  fixed base, never regenerated"). A base output that differs from its pin is shown as `broken` and the run
  refuses: it is restored (from the bucket or a copy), never rebuilt.
- **A change of ground is local.** A patch changes the cells it reaches and nothing else: the `ground-patch`
  stage writes a patched row beside the base's (`out/newworld/plugin/patch/land/`), byte for byte the base's
  outside the patched cells, and its check proves it. The world file's writer reads a patched row in place of the
  base's, and the file's own check holds a patched cell to its patch and every other cell to the base.
- **The owner's water stands.** The waterline, the water kinds and the owner's water edits are the base's. A
  patch never moves the waterline; a change to the water itself is a new base (section 11).
- **One frame.** Every raster and position is the picture's own pixels and world units, whatever the grid's
  size: a tool finds a sample through the build's origin (`build.json`, the landcover legend, `units.Grid`),
  never by an index it kept. A new consumer of the grid gets a row and a test in the
  [frame audit](../../../docs/research/nw-02-walk5-water-frame.md).
- **The same inputs build the same bytes.** Noise, rounding and seeds are anchored to the picture's grid, so a
  wider scope moves no ground, and a stage run twice on the same inputs writes the same output: the placement
  places the same references, a patch applied again writes the same rows. The world file comes out the same bytes
  however often its map data is applied.
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
- **A terrain need is mended by a patch, not waved through.** `terrain_needs` judges every place's need on the
  base and fails on a failure that `newworld/sources/terrain_needs_accepted.json` does not name. A failing need at
  a drafted place is met by the place's own ground (the skill `place-site`); a row is added to the accepted file
  only when the map gives the place no such ground, with that reason, the judge's own words for the failure
  (`reason`) and the value it was measured at (`bound`).

## 3. Make the change at its source

Change the source file, the rule's code or the database's source, never an output. [changes.md](changes.md) names,
for each kind of change, the source to edit, the stages it makes stale, the stages it leaves alone, and what
follows on the other machines. The plan (next section) is the authority: the table tells you what to expect, the
plan tells you what is so.

A change of ground is a patch, never a change to a base stage's rule or source:

- **At a place**: the place's own files, by its place build (the skills `place-site`, `place-change`). A place's
  footprint, a pad, a bank, a sap hollow, a path's paint: all are the place's patches, built into the place layer
  over the cells the place covers. The world rebuild does not read them as ground.
- **Outside any place** (a road's bed, a landing, a bank a walk fault names): one row of
  `newworld/sources/ground_patches.jsonl`, in a place's `land.jsonl` form with an id and a reason:

      {"id": "patch.0001", "by": "agent", "why": "...", "cell": [cx, cy], "verts": [[row, col, dz], ...]}

  `row` from the cell's south edge and `col` from its west edge (0 to 32), `dz` in game units added to the base's
  height. Every row is applied to the base each time, never over another patch's output, so removing a row returns
  its cells to the base. The `ground-patch` stage, then `esm`, run; nothing before them.
- **A road the database gains** after the base is not in the base's landcover or paint: the plan lists it as an
  owed patch. Its ground is the nearest place's path (its place build) or a row of the patches file.

A change to a place's record (its position, footprint, whether it stands on water, its terrain needs) never
reshapes the base: the place's ground is met by its own patch.

## 4. Plan

    tools/newworld/rebuild.sh plan

Its first line names the base: "the province's ground: fixed base, never regenerated", with the base's stages, the
date it was pinned and its terrain build. Then the order (derived from what each stage reads and writes) and each
stage's state:

- `base`: one of the province's ground stages, its outputs the pinned base. It never runs.
- `broken`: a base stage whose outputs on disk are not the pinned base. The run refuses until they are restored.
- `current`: what it reads is what its last green run read. It will not run.
- `stale`, with the reason: the inputs that changed, a missing output, or an output that names another build. It
  runs.
- `follows` a stale stage: it runs only if that stage changes something it reads. A stage whose inputs come out
  the same bytes is skipped at its turn.
- `proved`: the rebuild has no record of the stage, and its own tool proves its output was made from today's
  inputs. Its checks alone run, and the run marks it; from then on it goes stale by everything it reads.

Last come the owed patches: ground the database names that the base does not hold (a road added since), each with
where its patch belongs. If the plan shows more stale than the table led you to expect, find out why before
running: a file changed that you did not mean to change.

The rebuild keeps one record for each stage (`out/newworld/rebuild/<stage>.json`), written only by a run: that the
stage's commands have started, that they are done, and, when its checks are green, the key of everything the stage
read. A run that was killed or went red part-way through a stage leaves that stage stale, whatever is done to its
inputs afterwards. A stage with no record is current only when its own tool proves it: the record the tool left
beside its output, computed again from today's inputs, is the same (the placed refs, the cells). Matching build ids
are not proof. A stage that cannot prove it runs. Never write a record by hand, nor the base's pin.

The placed refs and the world file each skip, or resume by row, on a key of their own that covers less than their
stage reads. The rebuild hands each its own key for the stage (`tools/newworld/keyed.py`, `world.sh`), so a stage
the plan calls stale is always built again and a stopped run resumes where it stopped. Run by hand, each tool keeps
its own key.

A tool that hashes its own file into its key (`place/place.py`) goes stale with any edit to that file, a comment
included: its whole output is built again, and everything after it. Put what is not the rule itself in another file
(`tools/newworld/proofs.py` and `tools/newworld/keyed.py` hold those tools' proofs and the rebuild's key for that
reason).

`plan` reads each file once and remembers its digest while the file is untouched; `run` reads every file it
decides on. A read names exactly what its tool reads: the fields of a file (`<path>#<field>,<field>`, a dotted name
for a field inside a field, each row's fields of a `.jsonl`), the columns of a table (`db:<table>[col,col]`, or
`[-col]` for all but those), or some rows of a table (`db:<table>{col=value|value}`): the stage then goes stale by
those alone. A note, a person's words or a record's prose never marks a stage stale that does not read it.

## 5. Run

The small world first, before any full run:

    tools/newworld/rebuild.sh small

It cuts one 16 by 16 cell block of the real build (`tools/newworld/small`: three regions, still and flowing water,
forest, rocky upland with cliffs, a road with a junction, a place at the water) and runs the stages from `land` to
`readback` on it under `out/newworld-small/`: the same commands and checks, each tool's paths pointed at the small
world, nothing under `out/newworld/` written (the run ends by proving it). On the block the ground stages run: the
block's base is made from the cut, and its own patches (`out/newworld-small/ground_patches.jsonl`, absent until a
test writes rows) are laid over it as over the province's. Twelve stages from nothing take about two minutes; a
stage whose inputs stand is not run again.

- A red check marks its stage and the run goes on, so one run shows every fault. Mend each at its cause and run
  it again until it is green.
- A lane runs it in its own worktree: it reads the main tree's build and writes `out/newworld-small/`.
- `rebuild.sh run` refuses a stale stage whose code is not the code of its last green small run, and names it. A
  stage whose code stands is not asked to be proven again.
- What the block does not prove, so what a full run still risks: memory and time at the province's size; the
  province's connectivity (settlement paths, landings, the walk checks' anchors); the rows that count the province
  (mist densities, regions read apart); and every rule on ground the block does not hold (sea, coast, the margin,
  the cells beyond the picture).

Then the full run:

    tools/newworld/rebuild.sh preflight
    tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run
    tooling/job_guard.sh wait nw-rebuild

- A world rebuild runs only when the owner has asked for one. Run it in the main tree, level with `origin/main`.
  One rebuild at a time, never beside a place build or a studio finalise. `preflight` proves all of that, the base
  against its pin, the inputs, the accepted records, the small world's proof of every stale stage's code, the disk
  and the memory, and that every stale stage's tool starts; `run` runs it first and starts nothing if it is red.
- Before a run that reaches a long stage (`navmesh`, `esm`), clear what can be cleared first: `make check`, and
  the navmesh's fast test for a change to the placement or the navmesh ([checks.md](checks.md)).
- The run starts each stale stage as soon as the stages it reads from are done, side by side where the machine's
  memory allows. Every cheap check (the needs, the relief rows, the teleports' landings, the placement check, the
  edits' check, the patches' check) is green before the navmesh starts, and the read-back of the written file is
  the run's own last stage.
- A stopped run is resumed by the same command: stamped stages are current, the stage that was stopped runs
  again, and the long stages keep the rows and cells they had built for it.
- `run --to <stage>` runs only what that stage needs. `run --force <stage>` runs a current stage again; it refuses
  a base stage.
- Never run a stage's tool by hand in the main tree to move the build on: the plan cannot tell what it read.
- The run ends with a summary: stages run, stages skipped, checks passed and failed, what went stale beyond
  this build, and the tracked files it rewrote.

## 6. A red check, and a review's findings

A red command or check stops the run there: nothing new starts, the stages already running finish, and the
check's own lines are printed (`out/newworld/rebuild/logs/<stage>.log` has the whole output).

1. Read what the check proves in [checks.md](checks.md). A check reads the written output, never the plan that
   made it.
2. Mend the cause in the stage that owns it (a rule, a source, a tool, a patch). The world is never bent to pass a
   check and a check is never loosened to pass a world; a limit changes only with a new measurement (section 1). A
   fault in the ground is mended by a patch over the cells that hold it.
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
2. Republish the Atlas when a patch changed ground it shows: `python3 -m tools.newworld.map_page`, then publish
   `out/newworld/map/index.html` to the url in `tools/newworld/atlas.json`, then
   `python3 -m tools.newworld.atlas_state mark-published`. The page names the terrain build it shows (its id, date
   and heightmap checksum, with the height under the pointer) and the builder refuses a heightmap that is not that
   build's own.
3. Prove the world file settled: `tools/newworld/rebuild.sh settled` exits 0 when the main tree is level with
   `origin/main`, no stage is stale, no rebuild runs and no lane's worktree holds a change to a source of the
   world file (of a built place's files, a change to the fields the world reads: [changes.md](changes.md)).
   Otherwise it names what is owed: land or wait for that lane, bring the tree level, rebuild.
   Nothing below starts on a world file that is not settled.
4. **The play machine's copy.** `infra/gpu-box/run.sh up`, then `infra/gpu-box/lod.sh map` and
   `infra/gpu-box/lod.sh send` (the skill `world-lod`, section 5): the world file with its map data and LOD plan
   is on the play machine, and its hash is recorded here.
5. **Each built place the run left stale**, before any LOD is built over it.
   `python3 -m tools.places worldparts <place_id>` says whether the world records under its ground bundle or its
   build moved, and which; a place it calls current needs nothing. With the base fixed, only a world patch in the
   place's cells, a re-scattered plant or a changed navmesh rule moves them. For a stale one, extract its ground
   bundle again (`python3 -m tools.places extract --ground <place_id>`, then
   `python3 -m tools.places ground-check <place_id>`), run the stages the change calls for (the skill
   `place-change`: `clearance` for plants or a navmesh rule), then its build and check (the skill `place-check`),
   then `streets` and the build and check again where pieces or doors moved or the `streets` check names a point
   off the network. Commit the place files a stage changed.
6. **The LOD**, and with it the deploy of the place layer and the stack: the skill `world-lod`, sections 4 to 8.
7. **The whole read-back**, once the other machines are level: `python3 -m tools.newworld.verify` (every group,
   the LOD's, the deploy's and the places' rows included). It must pass in full before the owner is asked to walk.

A built place carries a stamp of the world records it stands on, and each LOD step a key read from the world
file's records. Both are read from the file by record, so each stands while what it reads stands, whatever else
of the file a rebuild rewrites; after step 4 the file changes only by a rebuild.

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
- What may run in a worktree: `tools/newworld/rebuild.sh plan` (it writes nothing there), `tools/newworld/rebuild.sh
  small` (it reads the main tree's build and writes `out/newworld-small/`; it needs no link), and a tool told to
  write to another folder (`--out`, `--plugin`).
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

- The rebuild runs on the build VM. With the base fixed, everything else stale is about half an hour of stage time
  (the navmesh about 17 minutes of it); a change late in the order a few minutes; a patch alone (`ground-patch`,
  then `esm` and `readback`) under ten; the small world about two minutes. The plan prints the stale stages' time
  and largest memory peak. Stop the VM when the work is done (`tooling/agent_stop.sh`).
- The play machine's cost and care are in the skill `world-lod`, section 9. It is started only once the world
  file is settled here (section 7).

## 11. A new base, only on the owner's word

The base is made again only when the owner asks, in his own words, for the province's ground to be regenerated.
No finding, check, review or agent's judgement is that word. Then, and only then:

1. **Held ground.** Every folder under `newworld/places/` has a row in `newworld/sources/terrain_held.json`: the
   terrain build it was seated on and its cells. Inside them the beds are that build's, sample for sample, and the
   land is that build's plus a lift that ramps from nothing at the old waterline.
2. **The terrain is tried first.** `tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run
   --regenerate-the-provinces-ground-because-the-owner-asked --to needs` builds the terrain, runs `terrain check`
   (held ground exact, each water kind's waterline triangles over 45 degrees within Skyrim's share) and judges every
   place's needs. With `ARGONIA_TERRAIN_PROBE=<place>,<place>` set, the terrain build logs the ground at those places
   after each of its steps.
3. **The waterline** does not move without the owner: `water_kinds` fails when a kind's bodies or area leave the
   accepted classification (`newworld/sources/water_accepted.json`); show him the new classification on the Atlas,
   and only on his word run `python3 -m tools.newworld.water_kinds --accept`. The owner's water edits are pulled,
   never typed ([changes.md](changes.md)).
4. **The whole run** with the same override. When it is green, it pins the new base itself
   (`newworld/sources/ground_base.json`): commit it by path with the run's other tracked files. Every built place
   is then brought level (section 7, step 5, with `seating` for the moved relief).

Without the override, `run --force` of a base stage, a second `rebuild.sh pin-base` and a run over a broken base
all refuse, naming the owner as the only one who can ask.

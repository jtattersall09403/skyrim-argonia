<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.12-loops/ladders.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.12 ladders: the piece, the mode, the placements

## The piece

`vanilla:dungeons/imperial/door/trapdoorladder01-open` in `settlement-stilt-v1`.
It is Skyrim's TrapdoorLadder01 (DOOR 0005AD3C) with its hatch shape dropped by
`tooling/asset-pipeline/pipeline/blender/mesh_edits/open_ladder.py`. The ladder
was chosen on geometry from three candidates:

| Option | Piece | Measured | Verdict |
|---|---|---|---|
| A | TrapdoorLadder01 (DOOR, 24 REFRs) | Rails about 0.76 m apart, rungs about 1.1 m wide, 12 rungs over 5.5 m, mean pitch 0.458 m (0.34–0.63), leans about 6°, top rail 5.53 m | **Chosen**, without the hatch |
| B | WHIntWoodLadder01 (STAT, 13 REFRs) | A 40.5° stair-ladder | Rejected: the vertical climb clip cannot play on a stair |
| C | `furniture/laddertall.nif` | Regular 0.391 m pitch, rails 0.52 m apart, 4.04 m, vertical | Rejected: no plugin record places it, so nothing says what it goes with |

**Why A loses its hatch.** On an open deck, pier or lookout, a hatch that never opens is a fake door.

**The clip and the rungs.**
- The FreeClimb loop climbs 1.29 m per 2.0 s cycle, three rungs of 0.43 m.
- A's mean of three rungs is 1.37 m, and its pitches are irregular.
- The rung contact error is measured per frame by the `ladder` visual group: `apps/combat-sandbox/src/scenes/ladder/`.

**Rise limits.**
- Seat the piece with its top at the walked surface: deck top 5.45 m over the piece's pivot.
- Any length beyond the rise goes under the ground or water.
- A rise over 5.4 m needs another answer.
- A rise under 1.2 m is a step, not a ladder.

**Surface.**
- The `assetPlacement` row (`placement-policies.json`) sets `climbSurface: "ladder"`, which rides into the kit manifest.
- The climb classifier's X7 (`ClimbBody.ladder`) reads it as `row.climbSurface === "ladder"` and hands the surface to ladder mode.

## The mode

`packages/game-core/src/locomotion/ladder/` holds a pure machine, `stepLadder(prev, {ladder, intent, rates, stamina, maxStamina, dt})`.

**States:**
- none
- mountBottom, mountTop
- climb (up or down)
- dismountTop, dismountBottom
- letGo

**Behaviour:**
- Loop speed is the clip's own: stride over cycle, 0.645 m/s.
- Released between rungs, the climber finishes to the next rung, then rests with `restOnHoldRegenFraction`.
- Moving costs `climbRates().drainPerSecond`, from the stats API.
- At zero stamina, climbing up lets go; climbing down stays allowed.
- Clip windows are the clips lane's (`humanoid-1h-combat.json`, pack `climb`):
  - LADDER_MOUNT_BOTTOM: 1.0667 s.
  - LADDER_DISMOUNT_TOP: 1.5 s.
  - LADDER_MOUNT_TOP: 1.5 s, reversed.
  - LADDER_DISMOUNT_BOTTOM: 1.0667 s, reversed.

### Wiring note for CombatRuntime (lane 2.12-climb-visual)

1. **Entry.**
   - When the climb probe's body is `ladder` (X7), do not start free climb.
   - Instead, on the climb press, call `stepLadder(LADDER_IDLE, {intent: {mount}})`.
   - `mount` is `"bottom"` when the player stands at the foot and faces the ladder.
   - It is `"top"` when the player stands on the walked top within reach of the top rung.
2. **Each fixed step.**
   - Map move-forward to `axis` (+1 up, −1 down) and jump to `letGo`.
   - Hold the kinematic body at the ladder's foot plus `heightM` up the rung line.
   - Stand it off by `CLIMB_CONTACT.standoffM`, facing the ladder.
3. **Animation.**
   - Play `motion.animation` with `startAt = motion.clipTime`.
   - Restart it on a mode change.
4. **Stamina.**
   - Subtract `staminaSpent`.
   - When `regenFraction > 0`, regenerate at that fraction.
5. **Exit.**
   - `dismounted` puts the player on the walked top (feet at `riseM`, stepped past the edge) or on the ground.
   - `letGo` hands over to falling.
6. **Rise.** The `Ladder` is `{riseM, pitchM}`:
   - `riseM` comes from the placement: deck top minus the foot's ground or water.
   - `pitchM` is the piece's mean rung pitch, 0.458 m.

### Measured on the clips (the `ladder` visual group)

The group runs, and it is red on the clips as they stand. The machine, the facing and the seating all check out.

| Check | ladder-up | ladder-down | Limit |
|---|---|---|---|
| Gripping hand off the rung, median / p90 | 0.154 / 0.236 m | 0.19 / 0.30 m | 0.13 m |
| Mount hand-over off a rung | 0.119 m (bottom) | 0.166 m (top) | 0.13 m |
| Largest one-frame limb move | 0.619 m, start of the top dismount | 0.533 m, start of the down loop | 0.2 m |
| Lower foot over the surface at the end | 0.092 m on the deck | 0.094 m on the ground | 0..0.2 m |

**What the reds come from:**
- **Rung error.** The loop's hands land 0.43 m apart, but A's rungs run 0.34–0.63 m apart. No body offset fits both, so the hands need IK onto the nearest rung. The climb-visual lane's limb IK is the owner.
- **The top dismount pop.** `LADDER_DISMOUNT_TOP` starts at source 3.67 s, already crouched on the top. The loop ends with the hands overhead.
- **The mount-top and down-loop pop.** `LADDER_MOUNT_TOP` is that same window reversed, so it ends crouched, and the down loop starts with the hands overhead.

Both pops are clip-window fixes (`humanoid-1h-combat.json`, pack `climb`) for the clips lane: start the top window where the Short Ladder's hands still hold the top rail.

## Placements the slice places need

The place-builder lanes place these from this table. Coordinates are world metres (x, y up, z), taken from the compiled settlements and the layouts.

| Place id | Structure | Foot position, facing | Rise | Why here? |
|---|---|---|---|---|
| `place.pirate-freeholds.opening-work-camp` | Barge pier, pieces 2 and 3: `dockstrsol01` (3964.9, 2.15, 1362.45) and `dockstrent02` (3964.9, 2.15, 1355.17), layout uids `bp-sol`, `bp-0` | Placed (8e0c9430d): uid `bp-ladder` on `bp-sol` at (3962.09, 1363.12), yaw 270, outward normal −x, top 0.0 m from the deck edge at 2.15 m, foot at −3.45 in the marsh bed; `bp-0`'s rope rail crosses its top, so the ladder stands at `bp-sol`'s rail gap with a clear 1.2 m dismount column. | 2.15 m (deck 2.15 over water 0.0, marsh-deep) | The gang is boated up to the pier and the barge. A deck standing 2.15 m over the water stops a swimmer or a skiff crew from boarding, so the pier carries a rung ladder down its water side, the working answer to a high deck that Black Marsh builders also give with flint-vine rope ladders (`world/sources/lore/topics/material-culture.md:44-46`, `:103`). |
| `place.route.border-road-greenspring-crossings` | Inlet deck on piles, `dockstrent02` runs at y 1.74, yaw 294.4, layout uids `ib-00`..`ib-05` | **None: removed by layer patch.** A rail-free stretch exists (local y 0.4 to 3.6 of each `dockstrent02`'s seaward edge), but the piece's rails end below the deck's thick fascia there. Even raised to the seat rule's 0.15 m handhold cap, a reader still sees the top short of the planks. Not in the owner's play. | 1.74 m (deck 1.74 over water 0.0) | The design's swimmer's way up stays the far stair (`border-road-greenspring-crossings.design.md:32`). |
| `place.naga-kur-deeps.naga-highway-camp-active-north` | `composite:works/stockade-watch-2stage` (2289.0, 10.1, 4571.0), yaw 225, uid `w-watch` | Placed (7991ce1d8): uid `w-ladder` at (2287.24, 10.166, 4569.24), yaw 315, on the SW face away from `w-stair`, foot on the ground (about 1.0 m of the piece below it), top rest 0.0003 m from the lookout deck edge. The 5.62 m piece cannot stand on the stage-1 deck for a 2.8 m rise without passing through it, so it runs from the ground. | About 4.5 m, ground to the lookout deck (measured). | The design says no plugin template pairs a stair from stage 1 to the lookout deck (`naga-highway-camp-active-north.design.md:68,103`). The Naga raiders' watch must still be climbed, so a ladder inside the frame is the plain answer, as Black Marsh builders reach their high platforms (`material-culture.md:26-29`, `:44-46`). |

### Checked and not needing a ladder

- **Stilt huts.** The bamboohut composites are closed shells. Their load door is at floor level, reached by graded earth or a ramp, so no walked exterior deck exists to climb to.
- **Xanmeer terraces.** No xanmeer terrace is placed in a slice place outside Helstrom, which is paused to 4.1b.
- **Other docks.** Every other dock deck is 0.15–0.56 m over the water: a step, not a ladder. These are riverwalk, lighter-flotilla, the opening-work-camp landing, upriver-hist-village, pearl-lots, the border-road river bridge, the claywater-station landing stage, and the riverwalk swamp house.
- **Stairs already serve** the Gang Ground way-down, the border-road bank stair and the Voriplasm Vault stair.
- **2.12 §e journey.** Its "stilt house onto a xanmeer terrace" step has no slice target. The ladder journey climbs the barge pier or the Naga watch instead.

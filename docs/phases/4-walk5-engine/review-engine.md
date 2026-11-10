# Engine review: the opening act and the slice quests (records, packages, aliases, stages, triggers, Papyrus, read-backs)

Reviewed 2026-11-10 on a fresh `plugin.sh build` (out/Argonia.esp 961,373 bytes). Nothing tracked was edited. The game was
not run. CONFIRMED = measured here (command or file:line given). PLAUSIBLE = reasoned; where it rests on my memory of a
vanilla script (sources are not on this machine) it says so. Paths are under /home/ubuntu/skyrim-argonia.
Scratch probe used for the navmesh work (not tracked): scratchpad/navprobe/Program.cs (modes stat, grid, refs, border, corridor).

Live docs that cover this: docs/design/quests-on-a-world.md sections 4, 5, 8 and docs/design/blocks.md. Confirmed: "the
world's navmeshes carry no edge links" (5 link entries in 17,591 navmeshes; Valenwood.esp as control parses 10,154, so the
reader is sound). Contradicted: blocks.md E-package "none: the alias filling applies it" (a package must be started in
front of the player, section A); quests-on-a-world section 5 "an escort reaching a place: a follow package" without the
one-island rule; the completion rule "calls Stop()" (MQ04 and MQ05 do not). The one doc to edit: quests-on-a-world.md
(sections 4, 5, 8; text in F), with blocks.md's E-package, TR-zone and guard rows brought into line.

Counts: 19 bugs (B1 to B19): 12 CONFIRMED in the records or in game, 7 PLAUSIBLE (B2, B5, B9, B10, B13, B16, B17). 19 packages swept (C): 10 sound, 9 faulty. 9 checker gaps (D).

---------------------------------------------------------------------------------------------------------------------

## A. The march

### A1. Root cause (owner confirmed in game 2026-11-10: the gang was already at the dock's landward end)

`ARG_MQ01_MarchOff` (plugin/Argonia/Packages/ARG_MQ01_MarchOff - 000E56) is gated GetStage ARG_MQ01 >= 30 and < 35.
Stage 30 is set by the stair door inside the hold (MainQuest.cs:445), so the package becomes eligible while the pier's
cell is not loaded; `Fragment_30` then calls `TryToEvaluatePackage` on five unloaded actors (papyrus/ARG_QF_MQ01.psc:85-106).
The engine runs the 2,800-unit trip for unloaded persistent actors and they are at ARG_MQ01_DockEndMarker when the
player comes down the plank. Nothing else is wrong with the package itself: its record is field-for-field the block
test's proven ARG_BT_WalkPackage except the owner quest, the conditions and the radius (compared in YAML), and the route
is on one island (`inspect navpath:079823:...:5350:-7800:...:5340:-5000` CONNECTED, 68 triangles).
The class of fault: **a package's conditions turned true while its people's cell could not be loaded with the player.**

Second fault on the same beat, same owner complaint ("nothing else happened"): the next thing after the dock end is a
zone 9,000 units away (camp zone centre -3750,1300, half 2500; MainQuest.cs:394). A stage whose only way forward is a
place the player has not been shown, with the guides standing still, is a stall even when every record is right.

### A2. Other mechanisms checked and ruled out (so the fixer does not chase them)

| Suspect | Verdict | Measurement |
|---|---|---|
| No owner quest on the package | not a cause | `inspect aliaspack`: 295 of our 415 alias packages and about half of Skyrim.esm's carry none |
| Base has no AI data or packages from its template (MainQuest.cs:77-79 leaves AIData, AIPackages, DefPackList out) | not a cause of the walk; the owner saw them arrive | they did travel |
| Route leaves the island | no | navpath CONNECTED on 079823; the mesh is one connected piece (probe: 1 component, 189 triangles) |
| Navmesh 079823 replaced by Black Marsh North | no | winner is Black Marsh.esm's, 189 triangles, not among the 129 navmeshes BMN deletes |
| NAVI has no entry for the mesh | no | NAVI of Black Marsh.esm holds 079823 (cell 1,-2), 07990E, 07EEF8 |
| Conditions malformed | no | YAML: two GetStage conditions on quest 000E00, AND, run on subject |

### A3. The fix for the walk's start (keep; it is right)

The lead's plan is sound. Spelled out:
1. `ARG_QF_MQ01.Fragment_30`: keep the two objective calls; delete `March()`; add `RegisterForSingleUpdate(1.0)`.
2. `OnUpdate` (already used for the race menu; branch on stage): when `GetStage() == 30`, if
   `WuleenMarch.GetRef().Is3DLoaded()` then `SetStage(32)` else `RegisterForSingleUpdate(1.0)` again. No give-up counter is
   needed: an update only runs in game mode, costs nothing, and survives a save. Never set 32 without the 3D test.
3. New hidden stage 32 (no journal text; add 32 to the `hidden` array, MainQuest.cs:416). `Fragment_32`:
   `HoldParent.Disable()`, `CrewParent.Disable()` (B6: no second Wuleen-Sei behind the pier door), then for each of the
   five aliases `GetActorRef().EvaluatePackage()` (the block test's proven call, ARG_QF_BlockTest.psc Fragment_60).
4. `ARG_MQ01_MarchOff` conditions: GetStage >= 32 and < 35 (MainQuest.cs:409). Any zone that had prerequisite 30 takes 32.
5. `Ending()` no longer needs `CrewParent.Disable()`; leave it (idempotent).
Reuse-first note: a record cannot do step 2 (no condition reads "this actor's 3D is loaded"), so the script is right.

### A4. A real walk from the dock to the present camp (-3650,1250): measured

Probe `corridor` over the box x -6500..8200, y -9000..4500: 216 navmeshes, each one connected piece.
- **A chain of whole-cell navmeshes covers the way with no gap:** 079823 (cell 1,-2) -> 079828 (1,-1) -> 0798BA (0,-1) ->
  0798AA (-1,-1) -> 07990E (-1,0, the camp). Their border edges lie on the shared cell lines and overlap along them
  (probe `border`): 079823/079828 on y=-4096 from x 4096 to 6202; 079828/0798BA on x=4096, the whole side; 0798BA/0798AA
  on x=0 from y -1947 to -437; 0798AA/07990E on y=0 from x -4096 to -1510. (06EF41 in cell 0,0 does not join the camp:
  07990E has no border edge on x=0.) Walk length about 12,000 units (170 m).
- **No edge pair coincides.** Border edges that share both end points within 1 unit, anywhere in the box: 1 (two 2-to-4
  triangle scraps); within 3 units: 3; none on the chain. Example, y=-4096: 079823 has edges 4096..4378.8..4814.0..5091.4,
  079828 has 4096..4459.4..4787.4..5030.3. The cells were never finalised.
- **What an edge link needs, as Mutagen exposes it** (Inspect.cs:126-132 reads it this way; Valenwood.esp is the
  working example): on each side, the triangle's `EdgeLink_0_1 / _1_2 / _2_0` field for that edge holds an index into
  `Data.EdgeLinks`, the triangle's `Flags` bit 0/1/2 for that edge is set, and the `EdgeLinks` entry names the other
  NAVM (`Mesh`) and its `TriangleIndex`; the two edges must be the same segment. And NAVI: Valenwood's map has
  `MergedTo` filled on 904 infos against 894 navmeshes with links, BM&V's on 12 and 10, so the engine's map mirrors the
  links; our plugin would have to carry the linked meshes' NAVI entries with `MergedTo` (and whatever path table the
  record keeps) kept in step. Mutagen will write both; nothing here proves the engine accepts a hand-written NAVI.
- **Verdict: not feasible by edge links as a record edit.** Flags alone cannot do it; each of the four borders needs
  border triangles split so one edge matches on both sides (8 triangle splits in 5 NAVM overrides at the least, 4 link
  pairs, 8 EdgeLinks entries, 5 NAVI entries). That is navmesh authoring, which quests-on-a-world section 4 forbids
  ("No new navmesh"), and the right tool for it is the Creation Kit's finalise on those five cells, which decision 0018
  keeps out of the workflow. It is an owner call and a new block with its own proof; do not start it for the opening.
- **Feasible today as travel legs with hops:** five legs (one per island), four hops of about 100 units at the cell
  lines (MoveTo to a marker just across; the islands touch, so the hop is short but it is seen by a following player).
  Works within the rules; 2 to 3 minutes of walking; four visible skips; ground and clutter on the way unwalked.
- **Followers elsewhere in the slice do not need links:** every other route measured is on one island (C).

### A5. Recommended: host the camp where the pier comes ashore (the owner's direction)

The pier's island 079823 is not only planks: it runs up the pier (x about 5300, y -7900 to -5200) and spreads over land
from x 4096 to 6300, y -5100 to -4096 (probe `grid`, navmesh z 38 to 73; `plugin.sh surface`: land 64 under 5900,-4700,
6100,-4500, 5750,-4350, 5300,-4350, so the floor is real). The water is at 0 (worldspace default; the cell sets none).

| Thing | Spot (x, y) | Ground | On 079823 | Note |
|---|---|---|---|---|
| Gang's start (as now) | 5350,-7800 | pier, z 218 | yes | pier door arrival is 5570,-9381, about 1,600 off: loaded with the player |
| Fire | 5900,-4700 | land 64 | yes | 780 from the pier's landfall (5300,-5200) |
| Hatching shed | 6150,-4450 | land 64 | yes (navpath CONNECTED from the fire, 38 triangles) | |
| Hist cutting | 6100,-4300 | navmesh z 71 | yes | |
| Shore end (the endings) | 4350,-4450 | navmesh z 68 | yes (CONNECTED, 99) | the far, west side: the player crosses the camp to end |
| Water's edge (the leader leaves) | 4500,-5150 | land -5 | yes | |
| Planks out to the huts | from 4900,-5450 | land -60 (wading) | yes (navmesh runs under the shallows to z -87) | |
| Huts over the water | 4900,-5800 and 4750,-5900 | sea floor -600 and -710 | no (none needed: entered from the water, as now) | a real dive; floor falls from -103 at 5000,-5600 to -1700 at 5000,-6200 |
| Sunk fish-trap (MQ03) | about 4850,-5650 | floor about -300 | no | keep it shallow enough to reach: 5000,-5800 is already -600 |

- **Whole gang route plank to fire on one island: yes** (`inspect navpath:079823:...:5350:-7800:...:5900:-4700` CONNECTED,
  104 triangles); about 3,400 units. Player's walk from the pier door to the fire: about 5,000 units (70 m).
- **What stands in the footprint** (probe `refs`, x 4096..6500, y -5800..-4096; winners of BM, BMN, ours): no building, no
  door, no person. Clutter: a pile of 17 food barrels (11AD83..11AD94, BMN) at x 4736..4966, y -4900..-4600; three grain
  sacks (11ADC7/8/9) at 5524..5593, -5011..-4937; a lamp post and lantern (14162E, 141630..32) at 5148..5241,-5005; ferns,
  shrubs and thickets (00FEA9 at 5990,-4486; 00FE5E at 6255,-4583; 00FEB5 at 5839,-4296; 00FEB4 at 5276,-4611); kelp in the
  shallows; BM&V's road piece 00ABBA lies under the whole landing (surface: road top 59 to 69 over land 64), so the fire
  stands on or beside a road (the owner's look call). East of the pier a longboat (005AA4) fills 5480..5980, -7190..-5370:
  keep the huts west.
- **Talkers near:** Hard-Scale (ARG_Talker_03E413) at 5766,-3970 and Rakhee-Tul (03E415) at 5772,-3791 are 740 and 920
  units north of the fire, in sight of it; Lifts-The-Sacks, Hurz-Weel and Neeta-Lei are 2,200 or more away. The
  Root-Cutters are Aggressive (MainQuest.cs:284): two bystanders in range will be attacked or will flee. Either put
  both talkers under an enable parent that is off from stage 10 to MQ01's ending (they are ours to override already),
  or make the cutters Unaggressive (they never fight in the record: they walk off at 41).
- **Zones for this layout** (prerequisites as today, 30 replaced by 32): camp edge -> 35 is no longer needed (delete stage
  35, the camp zone, `Fragment_35` and `ARG_MQ01_WaitAtFire`); fire zone at the fire, half 300, prerequisite 32, sets 40;
  shed zone at 6150,-4450 half 200; huts water zone at 4830,-5850 half 300 x 300 x 250 centred on z -100; shore zones at
  4350,-4450 half 300. None overlaps another (fire to shed centres 350 apart with halves 300 + 200 would overlap: put the
  shed zone's centre at 6250,-4350, or shrink the fire zone to half 200).
- **The march package** then travels plank foot to the fire marker in one leg, radius 200, gated 32 <= stage < 40. The
  gang walks in front of the player the whole way and the strike fires when the player reaches the fire: no moment with
  the gang standing and nothing happening.
- **A new player cannot wander off:** nothing fences the landing (the road runs north to Hereguard's talkers). If the
  opening must complete first, the cheap guard is that the strike does not wait for the player: when Wuleen-Sei is
  within 300 of the fire marker (the same OnUpdate loop, `GetDistance`), set 40 if the player is within 1,500, so the
  strike is seen from wherever the player stands on the landing. Keep the fire zone as the other setter (both set one
  stage; Fragment_40 gains the read-and-set guard variable).
- **Never-standing rule for any guide** (goes in the recipe, F): a guide's walk ends inside the zone or distance test
  that sets the next stage, on the guide's own island.

---------------------------------------------------------------------------------------------------------------------

## B. Bugs, most severe first

**B1. MQ01: the march starts unseen and ends in a stall.** CONFIRMED (owner, in game). Section A; fix A3 + A5.

**B2. A finished quest can be started again by a zone it left armed.** PLAUSIBLE (engine behaviour from memory: the
vanilla `defaultSetStageTrigScript` tests `GetStageDone(prereq)` and calls `SetStage`, and `SetStage` on a stopped quest
starts it, which is exactly what our own TR-chain relies on, blocks.md:73); the armed zones are CONFIRMED in the records.
- MQ01 (Flags none, MainQuest.cs:172): ending 93 leaves ARG_MQ01_ZoneShed and ZoneHuts enabled with prerequisite 40
  done (ARG_QF_MQ01.psc:223-239 disables neither). Walking into the shed afterwards calls `SetStage(41)` on the stopped
  quest. If it restarts, `OnInit` registers the update again and `OnUpdate` (psc:54-71) finds stage 10 not done:
  `UnequipAll`, `RemoveAllItems`, the race menu, stage 10. The player loses everything they carry.
- BC02: an ending reached through Tsaxi's let-by topic (Chainbreakers.cs:253-257) leaves that choice's out-zone armed
  (prerequisite 31/32/33 done; ARG_QF_BC02.psc `End` disables only the smoke). The player is standing in it.
- TG01: stage 30 reached through the friend's topic leaves ARG_TG01_ZoneBed armed (prerequisite 20); after the quest
  stops, stepping on the bed spot can restart a Start Game Enabled quest at stage 0, and Tilts-The-Jug's opening
  line (gated stage 0) comes back.
Fix, all four parts: (1) every quest gets `Quest.Flag.RunOnce` (MQ01, MQ03, TG02 have no flags; BC01-03, LQ25, LQ30,
TG01 have only StartGameEnabled; MQ04 and MQ05 already have it); (2) every ending disables every zone of its quest
(one kit helper that the ending calls with the quest's zone list); (3) MQ01's `OnUpdate` chargen branch also requires
a script variable `started == False`, set True before `ShowRaceMenu`; (4) the read-back fails a quest without RunOnce
and an ending whose fragment does not name every zone (D).

**B3. LQ25 can start before MQ05 reaches 40.** CONFIRMED: every condition in
plugin/Argonia/DialogTopics/ARG_LQ25_TheBeast - 000C3E names quest 000C35 only; none names ARG_MQ05 (000D8D).
Cause: Generate.cs:177 runs `LocalQuests.Add` before `ARG_MQ05` is allocated at Generate.cs:185, so
LocalQuests.cs:347-349 takes the "not in the plugin" branch (it prints a line nobody fails on). Fix: add the condition
after MQ05 exists, as MQ05.AddNesh does: a `LocalQuests.Finish(mod)` called from Generate after `MQ05.Add` that appends
`GetStage ARG_MQ05 >= 40` to every INFO of ARG_LQ25_TheBeast gated on LQ25 stage 0; throw if ARG_MQ05 is missing;
localcheck asserts the condition instead of printing a note.

**B4. BC01's and BC02's follow packages are copies of a package template, not packages.** CONFIRMED shape
(`inspect aliaspack`: 4 template-type, ARG_BC01_DebtorFollow and BC02's three; YAML `Type: PackageTemplate`, no
PackageTemplate link, their own procedure tree, public data left unset; Chainbreakers.cs:171 and :231 duplicate
`FollowPlayer`, which is the template). No alias package in Skyrim.esm or the DLCs is template-type. PLAUSIBLE in game:
Rows-For-Another and the one chosen from the smoke do not follow. Fix: build them with the one kit `Follow` (E),
a duplicate of vanilla `WERoad02Follow` (a Package on template 019B2C, as MQ01's two are, MainQuest.cs:150-158),
target PlayerRef, owner quest set, gated on the stage; delete `Chainbreakers.Pack`'s use for follows; bccheck asserts
`Type == Package` and a non-null template for every alias package.

**B5. Never-Sold's walk to the landing cannot be walked; it only happens unseen.** CONFIRMED geometry: she stands in
BM&V's House interior 15635D, which has no navmesh in its rooms (Chainbreakers.cs:60-62), and ARG_BC01_PatronAtLanding
(a sandbox at the landing marker 128900,-46500, radius 400, from stage 10; Chainbreakers.cs:169) is about 10,000 units and
several islands from her door (the house's exterior marker is at 134450,-56350). PLAUSIBLE in game: she gets there only
by the same unloaded travel that broke the march, at a time nobody chose; if it does not happen she is at home while
the journal sends the player to the landing; if it does she is gone from the house BC02 opens in. No dead end (her
bring-down line is gated on her base only, anywhere). Fix: delete the package; a hidden stage set by the debt book
entering the player's inventory (TR-acquire on the book as a created-in-chest alias, the shape BC03's tokens already
use, Chainbreakers.cs:300-304) moves her to the landing marker with `MoveTo` only if the player has no line of sight
to the marker, else she stays home; both journal texts name where she is. Or keep her at home for the whole quest and
say so in the journal (the lighter change; the other reviewer owns the wording).

**B6. Two of the same person: the hold's Wuleen-Sei and Ux-Xeek stay in the hold until MQ01 ends, and the hold's gang
until 40, while their march copies stand on the pier from stage 10.** CONFIRMED: ARG_MQ01_CrewParent is disabled only
in `Ending` (psc:188), HoldParent at 40 (psc:133), MarchParent enabled at 10 (psc:123); the pier door 005AB4 leads back
into the hold and the stair door is unlocked from 20. Fix: A3 step 3.

**B7. Death triggers on people who cannot die; five journal stages can never be reached.** CONFIRMED in code:
MQ03's officer alias is Essential (MainQuest.cs:582) and carries OnDeath 10 -> 20 (:594); BC01's Patron and Debtor are
Essential with OnDeath -> 94 (Chainbreakers.cs:168-170, :180); BC02's Keeper and Patron (:228-229, :240-241); BC03's
Broker and CrewBoss (:297-298, :310). Stage 94 of BC01 and of BC03 has no other setter. Fix: one or the other per
person. Where the record wants the fail-forward, the alias flag is Protected (only the player can kill) and the death
script stays; where the person must live, Essential and the death script and its stage are deleted. The kit refuses
`DeathSets` on an alias flagged Essential.

**B8. Ten of the eleven quests have no objective targets.** CONFIRMED: `QuestObjectiveTarget` occurs in MainQuest.cs:447-448
only; no YAML of BC01-03, LQ25, LQ30, TG01, TG02, MQ03, MQ04, MQ05 carries a target. quests-on-a-world section 5 asks
for "an objective whose target is an alias on the person, door or marker". Fix: the kit's objective call takes the
target alias and has no overload without one (a stage with several places takes several); each builder names the
person, zone marker or item alias; the read-back fails an objective with no target.

**B9. MQ05 dead-ends if both tellers are dead before stage 40.** PLAUSIBLE: Kaska-Meen and Ei-Tuja have no Protected
or Essential flag (MQ05.cs:36-37; aliases :105-106 without flags); the only fail-forward is Kaska-Meen's death at 40
(:110). Fix: flag both aliases Protected and add `DeathSets(k, AEiTuja, 40, 91)`; or make Ei-Tuja Essential.

**B10. TG02's three pledges are ordinary items.** PLAUSIBLE: sold to a trader or dropped in the channel, stage 40 can
never end (both endings need the items; NightReed.cs Build2 topics). Fix: BC03's token shape for each of the three
(a created-in-container alias flagged QuestObject, cleared by the ending).

**B11. Builders snap to navmeshes the load order deleted.** CONFIRMED: MQ04.cs:19 names 06EF98 and 06EFDD; the winners
of both carry no data (Black Marsh North deletes 129 of Black Marsh.esm's navmeshes; `inspect navpath:06EF98:...` dies
with a NullReference at Inspect.cs:116) and the mesh under those spots in game is 0C7102:Black Marsh North.esp
(`inspect navnear:93650:-12850:100`). QuestKit.cs:20-22 and PlaceCheck.cs:80 take "the last copy that carries data",
which resurrects a deleted mesh. The spots happen to be within placecheck's 150 of 0C7102, and Pays-Late's night walk
is on one island of 0C7102 (navpath CONNECTED, 214 triangles), so nothing breaks today. Fix: one `Snap(x, y)` in the kit
that finds the winning, undeleted navmesh under the point and returns the mesh with the spot; it throws on a deleted
mesh; no builder passes a mesh id it has not been given by that call. `inspect navpath` prints "deleted" instead of dying.

**B12. MQ01 Deesh-Duun is put off the camp's island and cannot follow.** CONFIRMED: ARG_MQ01_HutsMarker (-4500,1450,
z 10, MainQuest.cs:361) has no navmesh within 200; the nearest is 07991B, another island. The shore zone fires on the
player, so nothing stalls; he blinks to the shore at the ending. Goes away with A5 (he waits in a hut over the water
and is moved at the ending, as now); the recipe says so plainly (F).

**B13. MQ01's fire zone and shed zone overlap** (fire x -4050..-3450, y 1000..1600; shed x -3700..-3200, y 1450..1950;
MainQuest.cs:395-396). CONFIRMED arithmetic; PLAUSIBLE stall: a zone fires on entering only, so a player who reaches the
fire through the overlap is already inside the shed zone when its prerequisite 40 turns true and must step out and in.
Fix with A5's layout; the kit refuses two zones of one quest that overlap when one's stage is the other's prerequisite.

**B14. MQ04 and MQ05 complete but never stop.** CONFIRMED (ARG_QF_MQ04.psc Fragment_91, ARG_QF_MQ05.psc Fragment_91/92:
no `Stop()`), against blocks.md's completion rule; their aliases and Pays-Late's package conditions stay live for the
rest of the game. Fix: `Stop()` last in each (after `NextQuest.SetStage(10)` in MQ04).

**B15. MQ05's two alias packages do nothing.** CONFIRMED: ARG_MQ05_KaskaGoPost and EiTujaGoPost have no conditions and
travel to markers at the spots the two are placed on (MQ05.cs:45-50, :87-88). Delete both packages and both markers.

**B16. TG01's endings and MQ03's Fragment_20/40 carry no read-and-set guard**, and TG01 90/91 are two stages for one
outcome set by two INFOs of one topic. PLAUSIBLE only under a double fire; low. Fix: the kit's ending helper always
emits the guard.

**B17. `ARG_QF_MQ01.Choose` and `Ending` kill and disable in a fixed order that depends on the caller having checked
the guard; `Fragment_93` sets `choiceTaken` after reading `endTaken`.** Correct today; fragile to edit. Fix: one guard
per decision, emitted by the kit, never hand-written.

**B18. Work in fragments a record could do.** CONFIRMED: BC01 Fragment_10 adds the debt book to the chest by script
(a created-in-container alias does it, as BC03); TG01 Fragment_20 adds the necklace to the thief (the base's inventory,
as MQ04's gum pot, MQ04.cs:74). Fix as named; not urgent.

**B19. Leftovers that reach the build:** ARG_Opening (a named Side Quest with an objective, never started),
ARG_BlockTest and ARG_BlockTestEnd and their people on Lilmoth's dock (the phase file says "removed with its forms"
once the slice is built), and the block test's untargeted walker. CONFIRMED present in plugin/Argonia/Quests. Remove
when the owner has ticked the block walk.

Checked and sound (no finding): every forced-ref alias names a persistent ref; every quest has a start (MQ01 by MQ101's
fragment; MQ03, MQ04, MQ05, TG02 by the previous ending's `SetStage`; the seven others Start Game Enabled and all seven
in out/SEQ/Argonia.seq); every base we add has a fixed level and no PC-level-mult flag; every fragment script's
properties are bound in the record for the scripts read (MQ01, MQ03, MQ04, MQ05, BC01-03, LQ25, LQ30, TG01, TG02);
the doors pair both ways; LQ30's and LQ25's race guards and clean-ups; TG02's three-of-three hidden stages.

---------------------------------------------------------------------------------------------------------------------

## C. Same-class sweep: every package a quest puts on a person

"Evaluated when" = what makes the package start. "Unseen start" = its conditions can turn true while its person's cell
is not loaded with the player.

| Quest | Package | Who | From | To | One island | Evaluated when | Verdict |
|---|---|---|---|---|---|---|---|
| MQ01 | MarchOff | Wuleen-Sei, Ux-Xeek, Dives, Finds (march copies), Mee-Tuja | 5350,-7800 | dock end 5340,-5000 | yes, 079823 (68 tris) | Fragment_30, player in the hold | FAULTY: unseen start (B1) |
| MQ01 | WaitAtFire | the same five | moved to the fire | fire marker | yes, 07990E | Fragment_35 after MoveTo | sound; deleted by A5 |
| MQ01 | LeaderLeaves | Cuts-the-Old-Knot | -3900,1420 | water's edge -4080,2000 | yes, 07990E (211) | Fragment_40, player at the fire | sound |
| MQ01 | CuttersLeave | Root-Cutter 1, 2 | -3400,1600 | water's edge | yes, 07990E | `Choose`, player in the shed or huts zone | sound |
| MQ01 | SalSeiFollows | Sal-Sei | shed marker -3450,1650 | player, to the shore -4050,650 | yes, 07990E (270) | `Choose` | sound |
| MQ01 | DeeshDuunFollows | Deesh-Duun | huts marker -4500,1450 | player, to the shore | NO: off navmesh, nearest 07991B | `Choose` | FAULTY (B12); no stall |
| MQ04 | PaysLateNight | Pays-Late | 93650,-12850 | cut-root mark 92760,-13700 | yes, 0C7102 (214); builder names deleted meshes | clock 20:00 while stage 10..90; not evaluated by script | sound in effect; unseen start is harmless (he is meant to be there at night); B11 |
| MQ05 | KaskaGoPost | Kaska-Meen | his post | his post | same spot | always | FAULTY: does nothing (B15) |
| MQ05 | EiTujaGoPost | Ei-Tuja | his post | his post | same spot | always | FAULTY: does nothing (B15) |
| BC01 | PatronAtLanding | Never-Sold | House interior 15635D (no navmesh) | landing 128900,-46500 | NO: interior with no navmesh, then several islands | stage 10, set in her house in front of the player | FAULTY (B5) |
| BC01 | DebtorFollow | Rows-For-Another | 128880,-46230 | player, to the channel zone 130900,-45250 | yes, 0ACD06 (292) | stage 40 by her own line, never evaluated by script | FAULTY: template-type (B4) |
| BC02 | SpeakerFollow | Says-It-Plain | 140850,-63800 | player, to the gate 139631,-63604 | yes, 0ACC91 (73) | stage 31 by his line | FAULTY: template-type (B4) |
| BC02 | KillerFollow | Hides-In-Reeds | 140931,-63454 | the gate | yes, 0ACC91 (120) | stage 32 | FAULTY: template-type (B4) |
| BC02 | MotherFollow | Keeps-The-Old-Count | 140731,-63854 | the gate | yes, 0ACC91 (52) | stage 33 | FAULTY: template-type (B4) |
| TG01 | ThiefDay | Keeps-What-Floats | bed or bench | day marker 50069,-7317 | yes, 0A7785 (78) | schedule 6:00, 12 h | sound |
| TG01 | ThiefEvening | Keeps-What-Floats | day marker | bench 50964,-6408 | yes, 0A7785 | schedule 18:00, 5 h | sound |
| TG01 | ThiefSleep | Keeps-What-Floats | bench | bed 49856,-6784 | yes, 0A7785 (94) | schedule 23:00, 7 h | sound; that he lies on the bedroll is unwalked |
| TG01 | FriendBench | Sits-By-The-Water | 51060,-6450 | bench | yes, 0A7785 | always | sound |
| BlockTest | WalkPackage | Dock Walker | 07EEF8 | door marker | yes (owner walked it) | Fragment_60, beside the player | sound (the proof) |

LQ25, LQ30, MQ03, BC03 and TG02 put no package on anyone. The three follow routes that are sound in geometry still
have no script evaluation; a follow package started by the person's own line starts when the dialogue closes (vanilla
shape), so none is needed. No follow or travel in the slice needs to cross an island except B5 and B12.

---------------------------------------------------------------------------------------------------------------------

## D. Read-back gaps: what passed while the march was broken, and the check to add

The seven read-backs (MainQuestCheck, MQCheck, ChainbreakersCheck, NightReedCheck, LocalQuestsCheck, BlockTestCheck,
PlaceCheck) compare the built records with what the builder meant: "alias X carries package Y gated on stage N"
(ChainbreakersCheck.cs:47-52), "zone Z: prereq -> stage" (:40-45). They are the builder's intent read twice; none asks
whether the thing can happen. Add one check program, `plugin.sh questcheck`, generic over every quest of ours in the
ESP (no per-quest tables), failing the build:

| # | Check | Would have caught |
|---|---|---|
| 1 | **Route on one island:** for every alias package with a location or a follow target, breadth-first over the winning navmesh from the person's placed spot (or the marker a fragment last moves them to) to the destination (for a follow: every zone of the quest whose prerequisite is the package's stage). Fail on a deleted mesh, a start more than 150 off navmesh, or NOT CONNECTED | B5, B11, B12 |
| 2 | **No unseen start:** for every alias package whose conditions first turn true at stage S, find S's setters; fail when a setter is in another cell than the person (a different interior, or an exterior more than 2 cells off) unless the package is listed "unseen by design" with a reason, or S's fragment gates on `Is3DLoaded` | B1, B5 |
| 3 | **Package shape:** every alias package is `Type: Package` with a template link, and its template is one of the kit's two (Travel 016FAA, Follow 019B2C) or a schedule sandbox or sleep | B4 |
| 4 | **Every stage has a reachable setter:** build the stage graph from INFO fragments (the .pex's SetStage calls), zones, alias scripts and fragments; fail a stage with no setter, a setter whose prerequisite stage has none, a death setter on an Essential alias, and a non-ending stage with no way out | B7, B9, the 94s |
| 5 | **Start order:** every condition a builder says it adds is in the ESP (LQ25's MQ05 gate); a builder's "left out until" branch is a failure, not a printed note | B3 |
| 6 | **Endings clean up:** every quest is RunOnce; every completing stage's fragment (from the .pex) disables every zone of the quest and calls `Stop()`; no zone of a finished quest is left with a done prerequisite | B2, B14 |
| 7 | **Zones:** no two zones of a quest overlap when one's stage is the other's prerequisite; a zone's box does not contain the spot of the setter of its prerequisite (the player would already be inside) | B13 |
| 8 | **Objectives:** every objective shown by a fragment has a target alias, and the alias's ref is enabled at that stage (its enable parent's state followed through the fragments) | B8 |
| 9 | **One of each person:** no two enabled refs with the same displayed name share a loaded area or a door pair at any stage (enable parents followed through the fragments) | B6 |

`inspect navpath` should become the library call behind checks 1 and 2 (and stop dying on a deleted mesh).

---------------------------------------------------------------------------------------------------------------------

## E. One quest kit

Today four builders carry their own helpers with different behaviour:

| Helper | QuestKit.cs | MainQuest.cs | LocalQuests.cs (+Chainbreakers) | NightReed.cs |
|---|---|---|---|---|
| Base (template flags) | looks + AIData + AIPackages + Factions + Script + DefPackList (:104) | looks only, own AIData, no packages (:82) | as QuestKit (:71) | looks only, own AIData (local) |
| Travel | owner quest set, radius 64 (:196) | owner quest cleared, radius given (:141) | `Pack`: any vanilla package by editor id, owner set (Chainbreakers.cs:107) | `Pack`: owner cleared, schedule |
| Follow | none | copy of WERoad02Follow, Package type (:150) | `Pack("FollowPlayer")`: the template itself | none |
| Zone | :158 | :115 (with enable parent) | :111 | inline |
| Forced alias | takes the ref | takes a FormKey | takes a FormKey | takes a FormKey |
| Stages | from the record, all with text | `NewQuest` with a hidden list | `NewQuest` with a stage list | `Stages` with text in code |
| Objectives | no target | target added by hand | no target | no target |
| Quest flags | RunOnce set by caller | none | StartGameEnabled | StartGameEnabled / none |
| Topic | prompt + INFOs, bands by `Banded` | variants from JSON, `Under` for choices | `TopicV` | lines from a TSV |
| Snap | named mesh, last copy with data | `Snapper.At(mesh)` | `Snapper.At(cell)` | `Snapper.At(mesh)` twice |
| Conditions C/Stage/Has/Speech/IsId | static | 6 local + imports NightReed's | own | own |

**The one kit** (QuestKit.cs grows to hold it; every builder constructs one per quest):
- `Quest(type, startGameEnabled)`: always RunOnce; the empty start-up stage; refuses a second call.
- `Stage(n, journal or Hidden)`, `Ending(n, journal)`: `Ending` records the stage as completing; the kit writes the
  fragment table, and a generated Papyrus include per quest holding the guard variable and `EndQuest()` (complete the
  shown objectives, disable every zone the kit made for this quest, IncSideQuests for a Side Quest, `Stop()`).
- `Objective(stage, text, params targetAlias)`: at least one target, checked.
- `Person(id, name, template, level, life)`: one template-flag set (looks, AI data, packages from the template unless
  `Packages.None` is asked); `life` is Mortal, Protected or Essential and lands on the alias; fixed level always.
- `Alias(ref, flags)`; `DeathSets(alias, prereq, stage)` throws on Essential; `AcquireSets`, `ActivateSets`.
- `Zone(id, at, half, prereq, stage, parent?)`: records the box; throws on the overlap rule (D7).
- `Travel(id, alias, toMarker, radius, fromStage, untilStage, startsSeen)`: the DA06 copy, owner quest set, the two stage
  conditions; `startsSeen` must be given: `Seen` registers the alias for the generated `StartWalk_<stage>()` function
  (the Is3DLoaded loop and `EvaluatePackage`), `UnseenByDesign(reason)` is the only way to skip it.
- `Follow(id, alias, atStage)`: the WERoad02Follow copy, owner quest set, target the player; throws unless a zone with
  that prerequisite exists on the alias's island.
- `Schedule(id, alias, kind, marker, radius, hour, minutes)`: the Gleda sandbox and sleep copies.
- `Snap(x, y)` and `Snap(cell, x, y)`: winning undeleted navmesh under the point; returns mesh and spot.
- `Topic`, `Choice` (the question's INFO linking to its answers), `Banded`, `AfterHello`: one implementation reading
  one line store.
- `Finish()`: runs D's checks 1, 3, 5, 7, 8 in the builder, so a wrong block fails the seed, not the walk.

**Delete:** MainQuest.cs `Ctx.Base/Marker/Actor/Zone/Interior/Travel/Follow`, `Glob/Stage/Done/Or/Not/SpeechBelow`,
`NewQuest`, `Topic`; LocalQuests.cs `Snapper`, `Kit`, `Script/Obj/Alias/Int/C/StageIs/IsId/IsRef/Rank`, `NewQuest`,
`Forced`, `AliasScript`, `OnDeath`, `Topic/TopicV`, `Fragments`; Chainbreakers.cs `Interior`, `Pack`, `Or/Hour/Speech/Has`;
NightReed.cs `Snapper`, `C/OnPlayer/StageLt/StageIs/Speech/Has/IsId/Dead/Script/Obj/Alias/Int`, local `Base/Marker/Actor/Pack`,
`Topic`, `Stages`, `Forced`, `AliasScript`, `OnDeath`; BlockTest.cs's copies when the block test is removed. Form ids
must not move: keep each builder's allocation order and port one builder per commit, round trip clean after each.

---------------------------------------------------------------------------------------------------------------------

## F. Recipe text

### quests-on-a-world.md section 4, replace the "Walking" bullet with

- **Walking:** nobody walks from one navmesh to another (the world's navmeshes carry no edge links; `plugin.sh inspect
  navstat`). Every walk a quest asks for starts and ends on one navmesh, proved with `plugin.sh inspect navpath` from
  the person's spot to the destination; a follower's destination is the zone that ends the escort. A route that would
  cross to another navmesh is redesigned: move the destination onto the walker's navmesh, or move the scene to where
  the walk can end. A person is moved between navmeshes only by a stage's fragment, and only when the player cannot
  see either spot.
- **A walk starts in front of the player.** A package that makes someone walk is gated on a hidden stage that is set
  only once that person's 3D is loaded (the kit's `Travel(..., Seen)`), and that stage's fragment calls
  `EvaluatePackage` on each walker. A package that may start unseen (a schedule, a night post) says so with its reason.
- **A guide never ends in nothing.** Where people lead the player, their walk ends inside the zone, or within the
  distance test, that sets the next stage. The player is never asked to reach a place nobody has walked them to.
- **The navmesh named is the one in the game.** A spot is taken from the winning navmesh under it; a navmesh a later
  plugin deleted is not there.
- **One of each person.** Where two refs stand for one person (inside and outside a door), the fragment that enables
  one disables the other, when the player can see neither change.

### quests-on-a-world.md section 5, replace the table rows named and add the last four

| Needed | Proven way to do it |
|---|---|
| people who lead the player somewhere | a Travel package on each alias to a marker on their own navmesh, gated on a hidden stage set when their 3D is loaded; the walk ends in the zone that sets the next stage |
| an escort reaching a place | the kit's Follow package (a copy of a vanilla follow package, never of a template), gated on the stage the person's own line sets; a zone the player enters at the destination, on the follower's navmesh, ends it |
| a person at a place by the clock | a schedule package on the alias to a marker on their navmesh; it may start unseen |
| a person who must be somewhere else for the next step | a fragment's MoveTo to a marker while the player sees neither spot; never a package across navmeshes |
| a quest that is over | the ending's fragment completes the shown objectives, disables every zone of the quest, counts the side quest, and stops the quest; the quest is Run Once |
| a zone | fires when the player walks in, once its prerequisite stage is done: it is placed where the player is not standing when that stage is set, and it does not overlap the zone before it |
| a person whose death moves the quest | Protected on the alias and a death trigger; a person who must live is Essential and has no death trigger |
| a thing the quest needs back from the player | an alias flagged Quest Object, created in its container by the alias, cleared by the ending |

Replace the "Engine rules every quest keeps" bullet with:
- **Engine rules every quest keeps:** every quest is Run Once; aliases are forced references to persistent refs, never
  find-matching; every stage two triggers can set guards itself with a variable read and set with no call between;
  every objective has a target alias whose ref is enabled at that stage; a quest shows in the journal only with an
  objective; side quests count on the Stats page through their ending; every ending stops the quest and disables its
  zones; every stage has a setter the player can reach and every stage but an ending has a way out; save and reload
  mid-quest leaves state intact.
- **Code:** one builder per line on the one quest kit; a builder never copies a kit helper or builds a package, zone,
  alias, objective or ending by hand; a condition that needs another builder's quest is added in a finish step after
  both exist and is never left out silently; called in a fixed order so form ids never move.

### quests-on-a-world.md section 8, add after "Models exist"

- **Quest check** (`plugin.sh questcheck`), over every quest in the built plugin: each package's route on one winning
  navmesh; no walk that can start unseen unless named so; packages of the kit's shapes only; a reachable setter for
  every stage and a way out of every stage but an ending; no death trigger on an Essential alias; every promised
  condition present; every quest Run Once and every ending stopping it and disabling its zones; no overlapping
  consecutive zones; a target on every objective; one of each person at every stage. 0 failures before deploy.

### blocks.md, replace these rows

| Block | Record shape | Papyrus shape | Precedent |
|---|---|---|---|
| **TR-zone**: entering an area | ACTI trigger box placed as REFR with the vanilla `defaultSetStageTrigScript` (quest, stage, prerequisite stage). It fires when the player walks in after the prerequisite is done, so it stands where the player is not when that stage is set, clear of the zone before it; the quest's ending disables it | none of ours | 327 refs carry it |
| **E-package**: give an actor new behaviour | alias package list: the kit's Travel (to a marker on the actor's navmesh), Follow (the player), or a schedule; each a copy of a vanilla package of type Package, owner quest set, conditions on the stage. A walk is gated on a hidden stage set once the walker's 3D is loaded | that stage's fragment: `Alias.GetActorRef().EvaluatePackage()` per walker; a follow or schedule needs none | 4,125 alias packages in 365 quests, none template-type |
| **E-stage** (the ending) | the completing stage holds a log entry with text and the Complete Quest flag; the quest is Run Once | the guard, the last objective completed, the quest's zones disabled, `IncSideQuests()` for a side quest, `Stop()` | Skyrim.esm's completing side quests |

In "Where the argument fails on this engine", replace the AI-package row and add two:

| Failure | Why it breaks | Guard |
|---|---|---|
| A package starting unseen | conditions that turn true while the actor's cell is not loaded make the actor do the whole trip unloaded, and the player finds them at the far end | Rule of E-package: a walk's stage is set only when the walker's 3D is loaded, and its fragment evaluates the package; the quest check fails a walk whose stage is set from another cell |
| A walk across navmeshes | no edge links: the actor stands at the edge of its own navmesh for ever | Rule of E-package: start and destination on one winning navmesh, proved by navpath in the build |
| A finished quest set going again | a zone left enabled with its prerequisite done calls SetStage on the stopped quest, which starts it | Rule of E-stage: Run Once, and the ending disables the quest's zones |

---------------------------------------------------------------------------------------------------------------------

## Recommendations

1. Re-host MQ01's camp on the pier's own island (A5) before any other MQ01 fix: it removes stage 35, the camp zone,
   WaitAtFire, B12 and B13, and makes B1's fix one package. Evidence: grid, surface, refs and navpath in A5. MQ03's
   camp-at-dawn things (sap, fish-trap, picks, the Reed's two on the shore; MainQuest.cs:542-550) move with it.
2. Do B2's Run Once and ending clean-up before the owner walks any ending: it is four lines in the kit and the worst
   case is a player stripped of everything.
3. Build D's quest check before porting builders to the one kit; it is the regression net for the port.
4. Leave edge links alone (A4) unless the owner rules navmesh edits in; nothing in the slice needs them once A5 is done.
5. `inspect navstat` should print link entries, not navmeshes with links, and the docs should say 5 of 17,591, not 0.

Covered: tools/ArgoniaPlugin (Generate, MainQuest, MQ04, MQ05, QuestKit, LocalQuests, Chainbreakers, NightReed, Inspect,
plugin.sh, Program; BlockTest, the *Check.cs and PlaceCheck by grep), papyrus/ARG_QF_*.psc and three TIFs,
plugin/Argonia/Packages (all 19) and Quests (flags, objectives, targets), DialogTopics/ARG_LQ25_TheBeast, docs/design
(blocks.md, quests-on-a-world.md), docs/phases/4-first-act-built.md, story/data/db quest_objective (MQ03); the load
order's navmeshes, NAVI, refs and land for cells -2..2, -3..1 of BlackMarsh.
Skipped: dialogue text, Talk.cs and the writing skills (the second reviewer's); docs/phases/3-building-blocks.md and
story/data/quest_lines (not needed for the findings); CleanUp.cs, Heights.cs, Seq.cs beyond the build's own output;
running the seven read-backs (the lead reports them passing; D rests on their code); TG02's and MQ03's water spots and
the Chapter's interior (no package or route in them); the game itself.

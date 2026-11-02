# Lane 1.x-r4-play: four play fixes (owner play test 3, findings 2, 34, 15, 33)

## Finding 2: saves load in first person
Cause: infra/gpu-box/region_saves.py `new_game` (the --fresh path) never set the camera; only base_save.py pressed F,
and region_saves saved straight after the moveto. Fix: `tools/bridge.py ensure_third_person` (reads IsPC1stPerson, toggles
F until it reads 0); called by base_save.py, by region_saves `new_game`, and before every region save (also the
non-fresh path), which records the failure instead of saving first person. L2: tools/tests/test_bridge.py.

## Finding 34: gold
data/quarantine/start.json `player.kit` gains `item.gold` x 5000. items_records: `kit_edid` -> Gold001, `kit_entries` ->
00000F:Skyrim.esm (the Player override carries it in a real new game), `kit_records` writes nothing for it. base_save.py and
region_saves.py loop the kit, so the console additem gives it. L2: test_items_records.py `test_kit_is_weapons_...`.
The Claywater save is the claywater lane's (not touched).

## Finding 15: camera when hit
Cause: Precision (72347) hit-reaction camera shake, MCM/Config/Precision/settings.ini [Hitstop] bEnableHitstopCameraShake=1
(strength 6 NPC / 4 other, 0.3 s) and [Recoil] bEnableRecoilCameraShake=1 (strength 10, 0.4 s). No other stack mod
(TDM, TK Dodge, Engine Fixes, SSE Display Tweaks grep) has a hit camera setting. Laid: both = 0 via the precision
manifest `ini` (data/dependencies.json, applied by stack.py apply_ini). The hitstop slowdown and recoil animation stay.
Not proven as THE cause in game (the mod's shake is the only hit-triggered camera mover; ragdoll/hit-impulse untouched).
If the still shows a dip after this, next suspect is the ragdoll camera follow ([HitImpulse]/bUseRagdollCollisionWhenAllowed).
L1: test_stack_combat.py `test_precision_camera_shake_is_off_when_laid`.

## Finding 33: FreeClimb on trees
No setting filters trees: FreeClimb never reads material, keyword or form for trees (docs/research/2026-11-01/climb-anything.md
§1, Plugin.cpp:484-492; src/UserSettings.cpp clamps). A tree climbs when its trunk body is layer 9 (Trees, fixed,
simple-contact) or layer 1 (Static); it is refused only when the layer is 15/none (which also has no collision, so the
player walks through it). The owner ruled 2026-11-01 that trees climb ("climb anything big enough"), and 2026-10-31 that
the mechanic (uneven surfaces, overhangs, limb clipping at rest) is the modder's. So NOTHING CHANGED: making trees
unclimbable would contradict the 11-01 ruling and could only be done by giving them no collision. PLANNER CALL: if the
owner now wants trees off, the only route is a fork of FreeClimb (Plugin.cpp:486-492) or tree meshes without trunk
collision; attach-angle MaxNormalZ (0.20-0.75) cannot exclude them. Guarded by test_freeclimb_has_no_tree_filter_to_lay.

## Owed in game (checks.md, two rows)
One batch: load a region save (third person visible, bridge inventory shows 5,000 gold), take a hit, still of the camera.
Region saves must be remade (--fresh) to carry the camera and gold. Precision's ini is laid at the next stack deploy.

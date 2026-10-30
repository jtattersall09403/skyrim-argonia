# Lane game-13: terrain LOD made then withdrawn (owner ruling), DSC verdict, all.yaml 10/30, memclimb, shader cards, stream latency (2026-10-30, ~12:50 to 17:00 UTC)

## Done (commits f120cbc, 024462e, 8312af2, f74e2f5; child 209b97d)
- **run_batch.py refuses to start while an LOD tool runs** (xLODGen, TexGen, DynDOLOD, LODGen, Texconv; x64 names too), naming it; test added (9 passed). The first live run exposed that `Get-Process -Name` exits 1 with no match; the probe now ends `'LOD-none'; exit 0`.
- **deploy skips an unchanged SKSE build** (child, 209b97d): stamp `HEAD:skse + preset` beside the DLLs; tools/skse_stamp.py, 6 tests. Unproven live: the first deploy after it should build and write the stamp, the second skip.
- **LOD (xLODGen, before the owner ruling):** g12-lod4 finished terrain at 26:30 (meshes ~4 min at 12:46-12:50; textures 22:58, 256 px diffuse+normal, levels 4/8/16/32, 14,545 files, 346 MB) but sat idle: the terrain beta ends with "LOD generation done.", not "LOD Generator: finished". lod.ps1 now matches both (8312af2). Collect: 20,600 files, 594 MB. Vantage still "with" taken; the reader saw distant terrain shape where "without" has fog, no holes, no Nordic element, but too fogged and low to judge colour or water, and a hard flat edge at y≈480 to check.
- **Owner ruling (CK LOD only) applied on the machine:** 20,598 xLODGen/DynDOLOD files taken out of Data (hard links matched by length and time) and the Argonia LOD (generated) mod emptied (20,600 files). The stage still lists the empty LOD mod; LODSettings\ARG_Province.lod went with it (the CK lane needs it back: infra/gpu-box/lodsettings.py).
- **CK LOD switches** (strings in the real CreationKit.exe, ASCII and UTF-16): `-GenerateLips`, `-GenerateSEQ`, `-GenerateSingleLip` (and `-generated`). **No LOD switch**: CK LOD is GUI-only (World > World LOD), as ck-lod-plan.md's draft `-Step cklod` assumes.
- **DSC verdict on B2: not viable on this stack** (f74e2f5, combat-mod-28567.md §1). Nemesis hung at 0 CPU inside `stack.py combat B2` again; with Nemesis set aside, Pandora parsed "FNIS Mod 1 : BBDarkSoulsCombat" but pandora-check found BB_DSC_ForwardRoll_Fast, BB_DSC_Backstep_Med, BB_DSC_RightRoll_Fat_MAG missing from the behaviours. For the 1.7 packet.
- **Combat A restored: 22,573 checked, 0 bad, 0 unrecorded, VERIFY OK.**
- **memclimb (6 loads each, game alone; skse-stale5's build overlapped its last minutes, which moves time, not private MB):** A base-save load **+20 MB/load**; B holding cell then Claywater road **+58 MB/loop**; C interior reload **-1 (flat)**. In the batch, journeys grow ~215-530 MB per item (lf83-endings +1,400); peak 6,745 MB; relaunch at 6,000 works.
- **Shader cards proven:** Sunshine apps.json lists "Skyrim", "Argonia (shaders on)", "Argonia (shaders off)". on: game up, CS v1.9.1 log written this launch, DLL in Data. off: game up, no CS log this launch, DLL set aside. Note: `stack.ps1 play-modded` never returns while the game runs (the card's -Wait is intended).
- **Stream latency (e2e.sh webrtc, headless Chrome on the build VM, emulated 4g; 1 session):** rtt 1/4 ms, jitter 8.5/20.4 ms, 0 loss, 24 fps, decode 0.4 ms; **press-to-screen keyboard 35.6/83.9 ms (n 4), touch 49.1/51.1 ms (n 10)** (median/p95). Same-region VM, not a phone: a real device/network figure is still owed for 0.2 §d.

## The game-12 batch alone (out/batch/game-12/20261030T133637): 3/12 in 905 s
No LOD tool ran. Reds diagnosed by the planner's agents (docs/research/2026-10-30/diag-*.md); none a game-rule bug.

## all.yaml (out/batch/all/20261030T151243): 10/30 passed in 3,186 s, deploy 486 s before it
Launch 241 s, scene apply 197 s, steps 2,429 s; 6 launches. Crash logs (in the SKSE folder): crash-2026-10-30-15-22-42.log (fight-roll-burden), -15-37-23 (smoke), -16-00-58 (world-sample).

| item | result | s | MB delta | failed at: reason |
|---|---|---|---|---|
| attributes | PASS | 82.6 | 531.0 |  |
| claywater-look | FAIL | 151.9 | 362.0 | station-house-inside: console `player.GetInWorldspace ARG_Province` printed = 'GetInWorldspace >> 1.00', wanted conta |
| claywater-walk | PASS | 115.8 | 758.0 |  |
| combat-trial-a | FAIL | 31.6 | 241.0 | sheet-and-perk-lock: BridgeError: console: the console refused `player.hasperk TKDodgeAddon.esp/0x809`: Syntax Error |
| dialogue-intercept | FAIL | 22.5 | 192.0 | closed: core ViewState dialogue value = None, wanted eq '' |
| fight-archetype | FAIL | 24.3 | 239.0 | record-values: BridgeError: console: the console refused `1000088C.GetLevel`: Script command "1000088C.GetLeve |
| fight-damage-builds | FAIL | 29.4 | -1812.0 | pinned-skills: BridgeError: av: no actor value OneHanded |
| fight-lock-on | FAIL | 67.5 | 155.0 | beyond-range: tdm-target locked = True, wanted eq False |
| fight-roll-burden | CRASH | 11.2 | None | game down: SkyrimSE is not running; crash log crash-2026-10-30-15-22-42.log:
| quarantine | PASS | 760.2 | None |  |
| quest-board | FAIL | 57.2 | 647.0 | strike: BridgeError: pad: 3060 ms is over the 3000 ms input cap |
| smoke | CRASH | 18.6 | None | game down: SkyrimSE is not running; crash log crash-2026-10-30-15-37-23.log:
| w3-crime | FAIL | 80.1 | None | strike: console `player.GetCrimeGoldViolent ARG_Faction_ClaywaterStation` printed = 'Actor violent Crim |
| first-place | FAIL | 121.8 | 383.0 | livia-landing-terms: core KnowsTopic topic.claywater-landing-terms value = False, wanted eq True |
| grow-at-rest | FAIL | 23.0 | 318.0 | setup: BridgeError: av: no actor value OneHanded |
| lf83-components | FAIL | 57.0 | 243.0 | hear-station-open: core ViewState dialogue value.body.speaker.id = None, wanted eq 'npc.imperial-fringe.claywater- |
| lf83-endings | PASS | 138.6 | 1400.0 |  |
| livia-sleep | PASS | 81.3 | -2246.0 |  |
| w3-interior-sun | PASS | 85.7 | 358.0 |  |
| w3-weather-stills | FAIL | 19.1 | 245.0 | mist-06: BridgeError: console: the console refused `fw 6`: Invalid weather '6' for parameter Weather ID. |
| water-swim | PASS | 78.1 | 609.0 |  |
| ui-sweep | FAIL | 124.3 | 438.0 | favorites: no menu event matching 'FavoritesMenu' since the step began (0 menu events) |
| croc-den | PASS | 216.9 | -1653.0 |  |
| rest-is-the-only-save | PASS | 89.7 | 308.0 |  |
| ui-probe | FAIL | 71.6 | 268.0 | talk-livia: core ViewState dialogue value.body.speaker.id = None, wanted eq 'npc.imperial-fringe.claywater- |
| world-sample | CRASH | 71.2 | None | game down: SkyrimSE is not running; crash log crash-2026-10-30-16-00-58.log:
| cosave | PASS | 106.7 | None |  |
| die-and-recover | FAIL | 42.6 | 333.0 | rest: core WakePoint value = '', wanted ne '' |
| menus-quit | FAIL | 26.4 | 135.0 | tween-stays: no menu event matching 'TweenMenu' since the step began (1 menu events) |
| suspend-save | FAIL | 48.3 | 252.0 | menus-write-nothing: 5 menu events matching '"opening": false' since the step began: {'menu': 'TweenMenu', 'opening' |

- **Step saves do not work:** after 30 items the machine holds 0 argj-*.ess (searched C:\argonia and Documents), yet out/resume/*.json records them, so the console `save argj-…` is silently refused. Set `step_saves` default false in run_journey.py (fix-batch-reds owns the file; not edited here) or save through the bridge.
- Many reds are authoring (console grammar, `av OneHanded`, `fw 6`, hasperk form): fd9559a's linter covers part. fix-batch-reds owns the rest.

## Not closed
- decision 0017 1.2 §0: ui-probe failed at talk-livia before the frame-time steps; no numbers.
- PROGRESS rows and Outcomes: not edited; no chunk item closes on this batch alone.

## Next lane (in order)
1. When fix-batch-reds commits: one `make deploy` from a clean worktree (`git -C <wt> fetch && checkout --detach origin/main`; note 087959c sat on local main unpushed), `python3 tools/fetch_vocab.py` with the game up, then `run_batch.py --dry` and only the reds.
2. CK LOD: lay LODSettings\ARG_Province.lod again, build lod.ps1 `-Step cklod` from ck-lod-plan.md (GUI only, no switch), alone on the machine.
3. A real-device stream latency for 0.2 §d.

## Machine state
argonia-play stopped at the end of this lane. Combat A laid, verify 0 bad. HEAD 087959c deployed. Data has no xLODGen/DynDOLOD files.

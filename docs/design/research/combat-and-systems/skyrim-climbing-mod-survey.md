<!-- imported unchanged from elder-souls-argonia docs/research/combat-and-systems/skyrim-climbing-mod-survey.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Skyrim climbing mod survey (clip sourcing for the BotW motion set)

Date 2026-10-20. Read-only research. Nexus pages return HTTP 403 to page fetches, so the facts on 97253, 132292 and 193552
are from Nexus API reads on that date; the rest come from search summaries, third-party mirrors and GitHub. Licence reading is waived for the
private build (0152 §2); credits still land with every download.

## Reconciliation block

- Live docs: `docs/research/combat-and-systems/botw-climbing-system.md` §10 (mod audit table, lines 133-149) and §12 (motion list);
  `swim-climb-boat-implementation.md:306,356`; `world/90-asset-strategy.md` §74.3 (clip table, per §10 recommendation).
- Confirms: EVGAT (63232) has no wall loop, lateral, hang or ledge-shimmy; its ladders are timed one-shots (Short 5 s, Tall 9 s,
  Slide 4.5 s per ggmods mirror). SkyParkour v3 and SkyClimb ship no wall loops. SkyClimb has no clips of its own (README: "uses EVG Traversal's animations").
- Corrects: §10 last row ("wall climb loop, lateral loop, hang idle ... not found in any listed mod") and the
  section's "blocker" paragraph. **FreeClimb (Nexus 193552) was missed** and ships up/down/left/right/hang clips plus drop, ledge catch, mantle, hops.
- Edit one doc: `botw-climbing-system.md` §10 (add the FreeClimb row, delete the "Not found" row and rewrite the consequence
  paragraph); then 90 §74.3 as §10 already recommends. No new file.

## Findings, the two the owner named first

### SkyClimb, Nexus 97253 (Sokco; fork 124203 "1.6.1170 Fix" by theRealJohnDoe; Tsptds/SkyClimb-1170 on GitHub)
- Form: SKSE plugin (code). Requires EVGAT, powerofthree's Papyrus Extender, SKSE. Evidence: GitHub README
  "SkyClimb uses EVG Traversal's animations"; Nexus summary "procedural, tests for ledges anywhere".
- Clips shipped: **none**. Ledge mantles only (EVGAT Ledge/Medium Ledge, v1.1 added vaults). No loop, hang, shimmy, ladder. No loose HKX, no DAR/OAR folders.
- Verified (Nexus API): code only, uses EVGAT clips. Add-ons: 131489 sheathed-only, 93346 stamina cost, 109022 OAR conditions.

### SkyParkour v3 (SPPF), Nexus 132292 (tsptds, with JellyfishInLoop; v3.6.5 seen)
- Form: SKSE plugin plus built-in clips; v3.0 dropped the OAR requirement, v3.1 requires Nemesis or Pandora (behaviour injected).
  JellyFishInLoop animations (153098, now obsolete) are integrated since v3. Modder article 10726 ("V3 Modder Resources"): clips must end
  with `animmotion` values per state (example medium climb `1.2 animmotion 0 55 153`), `SkyParkour_Stop` annotation at the end, `SkyParkour_Fail` ends `0 0 0`.
- Clips: root-motion **one-shots** only: ClimbLow/Medium/High/Highest, steps, vault, Grab (midair ledge catch), Fail, water exit, crouch slide, first-person set. No loop, hang idle, shimmy, climb-down, ladder.
- Verified (Nexus API, v3.6.5, Tsptds and JellyfishInLoop): root-motion one-shots. Indirect signal: mod 147794 re-hosts `EVG_LedgeCatch.hkx` "by explicit permission of tsptds" and says
  users need the author's permission, so treat SkyParkour assets as **ask first**. Others (Jelly's patch 186110) credit "TSPTDS for SkyParkour".

## Findings, new

### FreeClimb, Nexus 193552 (Epsilona11; v0.5.0; GitHub Eelta/FreeClimb, GPL-3.0-only code)
- Form: SKSE64 DLL **plus 25 loose HKX** in `Data/meshes/actors/character/animations/FreeClimb/` with `pack.json`, `skeleton.json`, `configs/*.json`.
  Own 99-track HKX format played by the DLL (not DAR/OAR, not behaviour-injected). Override per slot via MO2; converter tool imports Skyrim SE humanoid HKX.
  Repo tree: `runtime/meshes/actors/character/animations/FreeClimb/` (raw.githubusercontent.com/Eelta/FreeClimb/main/...).
- Slots (pack.json / configs): `hang`, `up`, `down`, `left`, `right`, `reach`, `hopUp/hopLeft/hopRight`, `contextHopLeft/Right`,
  `contextMantle` (height 133.6 uu), `ledgeCatch`, `jumpCatch`, `drop`, `dropBack`, `backFlipOut`, `kickUp/Left/Right`, `runUp/runLeft/runRight/runDiagonalLeft/Right` (wall run).
- Loop evidence (INFERRED, not played): `up` and `down` configs carry stride 90.34 uu with travel (0,0,+/-90.34), `left`/`right` stride 42.27 with travel
  (-/+42.27,0,0), and per-frame foot/hand contact arrays: stride-per-cycle data of cyclic clips. `hang`: stride 0, all four contacts 1.0 (static hold). Nexus changelog: "default climbing and wall-idle hand poses".
  README: WASD along the wall, release keys = rest against the wall, S+Space push off, climbing speeds set per direction in the MCM.
- Missing: ladder loop, ledge shimmy as such (left/right are wall-lateral, use as shimmy only if the pose is a hang), climbTired, climbSlip, pole.
- Animations are **not its own**: `docs/MIXAMO-LICENSE.md` "27 Adobe Mixamo animations, retargeted"; `docs/THREEPEAT-LICENSE.md` Threepeat Games
  BracedIdle, BracedJumpLeftV5, BracedJumpRight, BracedIdleMantleV7final ("free as in freedom for commercial use in your projects"). Audio Kenney CC0.
- Reuse: code GPL-3.0-only (do not copy code into the game). Clips: Adobe terms govern; "must not be repackaged as a standalone animation library, stock asset or template"; Adobe FAQ lists games as permitted. Credit: Mixamo, Threepeat, Epsilona11.
  Verified (Nexus API, v0.5.0, updated 2026-10-10): free climbing in any direction with corners, hang, directional leap catches, drop and release, re-grab while falling, automatic mantling, plus wall running and overhang traversal (not used, 0152). **Best route: go to the sources (Mixamo, Threepeat) directly** and retarget; the same clips, cleaner licence, no Skyrim runtime.

### EVG Animated Traversal, Nexus 63232 (Everglaid; v2.1, updated 2026-02-14; needs SKSE, Address Library, OAR, Animation Motion Revolution)
- Form: OAR folders plus AMR-driven root motion (v2.0b+ requires OAR). Quoted list (ggmods mirror): Vault 2.2 s, Raider Roll 3.5, Duck 2.2,
  **Squeeze "Shimmy through a tight spot" 2.5**, Deep Walk 3; **Ledge 2.5, Medium Ledge 2.25, Ledge Catch 1.5, Short Ladder "Basic climb up a short vanilla ladder" 5, Tall Ladder 9, Ladder Slide "Souls-style slide down" 4.5**;
  Raider Drop 4.0, Wall Drop 4.25, Wall Drop Far 4.5, Failed Ledge 2.0. All timed one-shots: no ladder loop, no climb-down, no hang.
- Permissions: ggmods mirror "No permissions have been set" (unreliable). Add-on authors call it open and ask credit for Everglaid (Maleficus 70724). Verify on the page.

### Ladders
| Mod | Id, author | What it is | Clips |
|---|---|---|---|
| EVGAT Dynamic Climb-able Ladder Doors | 108900, SeaSparrow (v1.3.0 2025-06-15) | BOS plus EVGAT: turns door-ladders into climbables; credits Everglaid, Powerofthree | none of its own; uses EVGAT one-shots; **climb-down removed** pending a door-activation fix |
| Bells of Skyrim patch | 109059 | removes Windhelm bell ladder | none |
| Climbable Ladders SE | 25999, PhysicsFish | modder resource; player fades out | **no animations** |
| LvxMagicks Ropes and Ladders | 181961 | deployable ropes, rope ladders, grapples; "climb up from below or descend from the top" via prompt, ESL plugins | clip form UNKNOWN (page 403); check requirements for EVGAT/own HKX before counting it |
| Immersive Interactions | 47670 | removed ladder "open" anim because of 108900 | none |
No "Ladders of Skyrim" or "Immersive Ladders" mod exists in the results. **No Skyrim mod ships a continuous ladder up/down loop with mount/dismount.**

### Other
| Mod | Id, author | Finding |
|---|---|---|
| Dynamic EVGAT SkyClimb and Parkour animations | 109022, RavenKZP | OAR conditions on sneak level (vault 30, climb 50, parkour fence 60, wall 80); reuses clips; **permissions open: asset use with credit, convert to other games with credit, donation points ok** |
| Parkour in Skyrim (EVGAT addon) | 99466, JL10123 | faster 1.4 s EVGAT variants plus sprint "special" and vault clips (Nemesis run); credits Everglaid, Sokco, dTry, tktk (Blender rig); open per 109022 |
| EVG CLAMBER | 114753 (LE 122221), Everglaid, miken1ke, Ersh | slope movement only (OAR) |
| Fluid Motion - Pathfinding and Animation Overhaul | 194680 | NPC/player obstacle and ledge climb-over via retargeting; one-shot style; clips unread |
| Free Run LE | LE 122401 / 122421 | height-measured climbs, vaults, ledge grabs, failure clip; LE; one-shots |
| VR Climbing | 168553 | VR hand-driven, no clips |
| Simply Climb / V2 | 26488 (LE 88289) / 170550 | no animation, character floats |
| Rope climbing | none found | no mod |
No DAR/OAR climb animation replacer for wall hang or shimmy was found. r/skyrimmods threads did not surface in search.

## Table: BotW motion rows against sources

| Row | Source | Form |
|---|---|---|
| wall up, down, left, right (with corners) | FreeClimb `up`, `down`, `left`, `right` | loose HKX, 99-track |
| hang (climb idle, ledge hang) | FreeClimb `hang` | loose HKX |
| leap catch up and sideways | FreeClimb `reach`, `hop*`, `jumpCatch` | loose HKX |
| drop, release, re-grab | FreeClimb `drop`, `dropBack` | loose HKX |
| mantle (auto) | FreeClimb `contextMantle` | loose HKX |
| mantle tiers, ledge catch, slip, water exit, ladder one-shots | EVGAT Ledge, Medium Ledge, Ledge Catch, Failed Ledge, ladders; SkyParkour Climb tiers, Grab, Fail, water exit | OAR / plugin one-shots |
| scramble (45-70 deg) | CLAMBER | OAR slope movement |
| ladder loop with mount and dismount | none: retime FreeClimb `up`/`down` to a rung pitch, EVGAT mount and dismount | retime route |
| tired, pole climb, rest | none | gap |

## Verdict

The continuous BotW set comes from one mod, FreeClimb, as loose HKX on the Skyrim rig (Mixamo and Threepeat content; its GPL-3.0 code is not taken).
EVGAT and SkyParkour supply the one-shots; CLAMBER the scramble. No Skyrim mod ships a ladder loop: the ladder is FreeClimb's climb loops retimed to a
rung pitch with EVGAT mount and dismount, never a one-shot cut into a loop. Wall running and overhang traversal stay in the vault. Confirm each loop
by opening the HKX and its duration at ingest.

## Sources

- Nexus API reads, 2026-10-20: mods 97253 (SkyClimb), 132292 (SkyParkour v3), 193552 (FreeClimb)
- https://www.nexusmods.com/skyrimspecialedition/mods/63232 (EVGAT)
- https://ggmods.com/game/the-elder-scrolls-v-skyrim-special-edition/mod/284/ (EVGAT list mirror)
- https://www.nexusmods.com/skyrimspecialedition/mods/132292 (SkyParkour v3)
- https://www.nexusmods.com/skyrimspecialedition/articles/10726 (V3 modder resources)
- https://www.nexusmods.com/skyrimspecialedition/mods/153098 , /186110 , /147794 (Jelly animations, slide patch, low ledge restore)
- https://www.nexusmods.com/skyrimspecialedition/mods/97253 , /124203 ; https://github.com/Sokco/SkyClimb/blob/main/README.md
- https://www.nexusmods.com/skyrimspecialedition/mods/193552 (FreeClimb); https://github.com/Eelta/FreeClimb (README.md, docs/MIXAMO-LICENSE.md, docs/THREEPEAT-LICENSE.md, docs/AUDIO-LICENSE.md, runtime/.../FreeClimb/configs/*.json, pack.json)
- https://www.nexusmods.com/skyrimspecialedition/mods/108900 , /109059 , /25999 , /181961 , /47670
- https://www.nexusmods.com/skyrimspecialedition/mods/109022 , /99466 , /70724 , /114753 , /194680 , /168553 , /26488 , /170550
- https://www.nexusmods.com/skyrim/mods/122401 (Free Run LE)
- https://schaken-mods.com/forums/topic/173235-evgat-dynamic-climb-able-ladder-doors/
- https://note.com/aemono369/n/n19065c3e295e (Japanese movement-mod roundup)

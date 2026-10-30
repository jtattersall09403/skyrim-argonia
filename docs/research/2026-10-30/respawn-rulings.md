# Respawn, rest, clearable places and the vastei pile (2026-10-30)

Owner ruling 2026-10-30 (owner brief row of that date). Old repo: jtattersall09403/elder-souls-argonia, shallow
clone in `$ARGONIA_PRIVATE/old-repo`; it gives goals, never machinery (0026).

## 1. The old rulings

| Ruling | Old source |
|---|---|
| **Respawn on rest** (owner, 2026-08-28): generic enemies (creatures, wildlife, dungeon denizens) respawn when the player rests; named NPCs, minibosses, bosses and quest actors never; a completed dungeon's generic population stops respawning (completion authored per dungeon); waking from death counts as a rest; respawned creatures carry template drops only; placed treasure never respawns. Data shape: a per-actor class `onRest \| never \| untilCleared`. Superseded an earlier "no repopulation on rest" default. | `docs/decisions/0031-workstream-s-round1-shape.md:39-50`; `docs/world/76-stats-progression.md:86-87, 1321-1329` (§126) |
| Rest saves, banks one level, opens the sitting, restores pools, respawns; camp anywhere calm in the wild, never in a dungeon, combat or settlement. | 76 §126 (`:1305-1318`); `docs/decisions/0144-…md:15`; `docs/phases/2-slice/2.8-progression.md:32, 101` |
| Death: wake at the last rest; nothing lost but carried vastei, left as one pile where you died; a second death replaces it; take it back within 2 m. | 76 §126 (`:1316-1319`), `:575-581`; `docs/phases/2-slice/2.7-loops/death-and-wake.md:1-8` |
| Grinding respawned enemies after a rest is chosen play: no repeat-target damping. | `docs/decisions/0037-workstream-s-round4-qa-rulings.md:20-23`; 76 `:496` |
| Every hostile record carries a respawn class; places carry a hostile-or-clearable share (55 % target, 50 % floor). | `docs/phases/2-slice/2.7-combat-and-encounters.md:127, 152`; `docs/decisions/0041-phase11-settlement-decisions.md:76, 145`; `docs/world/97-placement-principles.md:197` (A10) |
| Bonfires: none. Rest is a camp (or a bed); the old project never had a bonfire object. | grep of the old repo: no bonfire ruling |

**What 2026-10-30 changes:** the old `untilCleared` (respawn on rest until the place is cleared) is replaced: an
enemy homed in a clearable place **never** respawns, after rest or death. Everything else stands.

## 2. The native Skyrim way

- **The actor's flag.** NPC_ ACBS `Respawn`: when the engine resets a cell, a dead actor with the flag comes back;
  one without stays dead. Our `onRest` class compiles to exactly that flag (`place_build.respawns`,
  `combat_records.archetype_records`); `never` leaves it off.
- **The engine's reset.** A cell resets after `iHoursToRespawnCell` (cleared: `iHoursToRespawnCellCleared`) unvisited.
  1.5 put both out of reach (`world/db/game_setting.jsonl` rows 16-17), so only our rest resets cells. Papyrus/engine
  `Cell::Reset` (CommonLib `TESObjectCELL` reset / `ObjectReference::Reset` per actor) is the engine's own reset; a
  rest asks it of each cell that holds a respawning actor, and the Respawn flag decides who returns.
- **Clearable places.** ECZN flag `Never Resets` plus the LCTN `cleared` state: a clearable place's encounter zone
  is Never Resets, so even a reset leaves its dead dead. With every actor there `never`, the flag is a second
  guard, not the mechanism.
- **Treasure.** Placed containers are never reset by our rest (we reset actors, not cells' containers), so
  placed treasure never respawns.

## 3. In data (this change)

- `npc_statblock.respawn` and `creature_statblock.respawn` now reference `core_respawn_class` (FK).
- `build_person.respawn` (a second copy of the same fact) is gone; the NPC_ flag is derived from the statblock.
- 42 rows set to `never`: the 41 actors homed in clearable places (the Broke Column, Teeth of Sithis, the Naga
  highway camp, Voriplasm Vault, Jungle Root Hollow; 12 of them were `untilCleared`) and the Claywater crocodile
  (owner: never respawns). The ambush deserter and the bog dogs stay `onRest`; townsfolk stay `never`.
- Named check `respawn-clearable` (gate) and `tools/argonia_world/tests/test_respawn.py` (L1).
- `untilCleared` stays in `core_respawn_class` (unused) because `core_tables.py` compiles it into ArgoniaCore's
  C++ table; retiring it is a regenerate of that table, folded into the 1.5 runtime addition.

## 4. The vastei pile visual

Candidates (all base records referenced by path or FormKey, never shipped; 0003), ranked by look and fit for "a
pile you walk to and take":

| # | Candidate | Look | Fit | Verdict |
|---|---|---|---|---|
| 1 | `DefaultAshPileGhost` 101048:Skyrim.esm, `effects/ashpileghost01.nif`, + ARTO `SoulTrapTargetEffects` 0506D6:Skyrim.esm (violet wisps) | soft pale glowing heap with soul wisps | the engine's own loot pile: already a pile the player activates | **picked** |
| 2 | `DLC01DefaultAshPileSoul` 00A905:Dawnguard.esm (Soul Cairn ghost pile) | similar, cooler | a Dawnguard master for one mesh | reserve |
| 3 | `SoulGemPetty` mesh (the current stand-in) + effect shader | small crystal | reads as an item, not a pile | replaced |
| 4 | `FXGlowFillRound*` 02EB0D-11:Skyrim.esm glow statics | a lit orb | no collision; no pile | add-on only |
| 5 | `DefaultAshPile1` 00001B:Skyrim.esm, `effects/ashpile01.nif` | grey ash | reads as a corpse's remains, dull | no |
| 6 | Dragon soul absorb (Dragonborn FX) | big streaming light | the Dragonborn myth is Nordic (0012) | no |
| 7 | Atronach Forge | a large altar | furniture, not a pile; Nordic ruin setting | no |

Nordic check (0012): ghost ash and the Soul Trap art are magic FX shared across TES, no ornament. Set in
`tools/argonia_world/life_records.py` (`VASTEI_MODEL`, `VASTEI_FX_ART`), verdict in `data/immersion/verdicts.jsonl`.
**Still:** the build VM holds no extracted vanilla meshes, so no cheap off-game render; proposed for game-14's
next slot as a still at `die-and-recover` (the pile where the player fell), which also proves it activates.

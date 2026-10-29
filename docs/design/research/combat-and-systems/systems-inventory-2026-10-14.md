<!-- imported unchanged from elder-souls-argonia docs/research/combat-and-systems/systems-inventory-2026-10-14.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Systems inventory (code, not docs) — 2026-10-14
Method: directory listings, README heads, name greps, registry entry counts. Test coverage = a co-located *.test.ts exists by name; tests were not run.

## Gameplay/runtime systems
- Player movement + modes: packages/game-core/src/physics/PlayerMovementController.ts:16 (interface), :91 `MovementMode = "grounded" | "swim"`. Adapter in packages/character/src/EcctrlAdapter.ts. Working (grounded + swim). Tests: physics/*.test.ts, locomotion/swim.test.ts, character/EcctrlAdapter.swim.test.ts. Swim/climb/burden/boat speeds are 0 placeholders (physics/capabilityProfiles.ts:19,38,40: "land with Phases 9+").
- Climbing: no runtime (only grep hits in boundary/walls, fx). Contract/none.
- Boats / buoyancy: water/buoyancy.ts, water/buoyantBody.ts, water/rigidBody.ts. Thin-to-working physics. Tests: water/buoyancy.test.ts, buoyantBody.test.ts. No boat controller found.
- Combat: packages/game-core/src/combat/ (resolveHit.ts, fighter.ts, weapon.ts, bowShot.ts, arrowFlight.ts, poise.ts, blockReaction.ts, backstab.ts, statusEffects.ts, armourMitigation.ts). Working; per combat/README.md one resolveHit path for melee and arrows. Tests: 22 files in combat/.
- Parry/block: combat/blockReaction.ts, equipment/guard.ts. Working (test blockReaction.test.ts, equipment/guard.shields.test.ts).
- Lock-on: anim/lockOn.ts. Thin (test lockOn.test.ts).
- Bow: combat/bowShot.ts, solveBowAim.ts, arrowFlight.ts; packages/character/src/FirstPersonBow.tsx. Working (bowAimRegression.test.ts).
- Enemies AI: ai/enemyAi.ts, ai/enemyBow.ts, ai/weaponTactics.ts; actors/enemyArchetypes.ts. Working (3 tests).
- Perception: perception/detection.ts (`perceive`, `stepAwareness`), perception/noise.ts. Working rules (detection.test.ts). Not proven wired into enemyAi by this inventory.
- Inventory: packages/game-core/src/inventory/ (inventory.ts, store.ts, registry.ts, view.ts, itemStats.ts). Working data/store; UI at apps/combat-sandbox/src/ui/inventory/InventoryScreen.tsx, PaperDoll.tsx, useInventoryCursor.ts. Tests: inventory.test.ts.
- Equipment: packages/game-core/src/equipment/ (armour.ts, arsenal.ts, defineWeapon.ts, weaponRecords.test.ts, movesets/). Working for weapons/armour; tests: 10 files.
- Items registry: world/sources/registries/items.json — 18 entries (schema-keyed `entries`). Weapon/armour tables also in equipment/generated and arsenal blueprints.
- Stats/progression: packages/game-core/src/stats/ (index.ts, derived.ts, progression.ts, ladder.ts, checks.ts, modifiers.ts, crafting.ts; sim/ for simulation). Working pure functions; stats.test.ts, equivalence.test.ts, records.test.ts, sim/invariants.test.ts. Data: stats/data/{attributes,classes,skills,curves,economy,magic,races,rules-argonia,rules-morrowind,builds,gear,enemies}.json.
- Magic/spells: stats/data/magic.json (tiers, damage, skillGate) and stats/derived.ts only. Data-only; no spell runtime, no effects engine found by name. Contract/data only.
- NPC schema + registry: world/sources/registries/npcs.json — 732 entries. Schema under packages/world-schema/schemas/ (npc family via families.json). Data present; runtime NPC actor = packages/character (PlayerBody/SkyrimFighter) and actors/races.ts. Gate: world-schema/test_world_schema.py.
- Factions registry: world/sources/registries/factions.json — 111 entries. Data only; no faction runtime found.
- Dialogue: no dialogue runtime found. text-catalogue holds keyed strings (packages/text-catalogue/src/catalogue.ts). Contract/none.
- Quests: data only — world/sources/quests/ (13 json incl. quests-main.json, lines.json, local-*.json) and world/sources/registries/quests.json (731 entries). No quest engine found under packages/game-core/src.
- Crime / bounty: none found (grep hits only in travel/travelServices.ts and studio travel state). Missing.
- Economy / barter / merchants: stats/data/economy.json (potions bought/sold tables, line 1 designRef §124); stats/sim/campaign.ts. Data + sim only. No merchant runtime.
- Save/load: none found by name. Missing.
- World time / clock: packages/world-time/src/{clock.ts, calendar.ts, ephemeris.ts, season.ts}. Working (worldTime.test.ts, starCatalogue.test.ts).
- Weather: packages/world-weather/src/{states.ts, synoptic.ts, express.ts}. Working (weather.test.ts).
- Audio: packages/audio/src/{manager.ts, backend.ts, threeBackend.ts, fakeBackend.ts, events.ts, buses.ts, ambience.ts, surfaces.ts}. Working manager with fake and three backends; ~6 tests. Consumed by apps/combat-sandbox/src/components/useSandboxAudio.ts.
- Text catalogue: packages/text-catalogue/src/{catalogue.ts, entries.ts, stats-text.ts, generated/}. Working; catalogue.test.ts.
- Interior load / doors / swing doors / windows: packages/game-core/src/interior/ (interiorLoader.ts, bundle.ts, doors.ts, doorTransition.ts, swingDoors.ts, interiorWindows.json, interiorSockets.ts). Working; interior.test.ts, swingDoors.test.ts, interiorSockets.test.ts. Studio mount: apps/world-studio/src/character/InteriorDoors.tsx.
- Sockets vocabulary: world/sources/vocab/socket-vocabulary.json (422 lines); placed sockets via game-core/src/settlement/sockets.ts; travel sockets apps/world-studio/src/travel/TravelSockets.tsx. Working; sockets.test.ts.
- Navmesh / NavService: no NavService. Settlement walkability index in settlement/settlementIndex.ts (test settlementIndex.test.ts). Partial; no navmesh found.
- HUD / UI: game-core/src/hud/minimap.ts (test); apps/world-studio/src/hud/HudChrome.tsx; apps/world-studio/src/map/; apps/combat-sandbox/src/components/Hud.tsx; combat-sandbox/src/ui/CharacterPicker.tsx. Thin/working in studio and sandbox only.
- Map: apps/world-studio/src/map/ (3 tests). App-private to studio.
- Character creation: apps/combat-sandbox/src/ui/CharacterPicker.tsx (+ characterPickerGrid.test.ts); game-core/src/actors/appearance.ts, races.ts. Sandbox-private; no creation flow in apps/game.
- apps/game stub: apps/game/src/main.ts (3 lines; logs sea level; "Real composition begins at Phase 7"). Contract/none.
- Settlement runtime: packages/game-core/src/settlement/ (SettlementLayer.tsx, pools.ts, runColliders.ts, tether.ts, sockets.ts, ~36 test files). Working renderer; studio-mounted.
- Rest/sleep, lockpicking, loot/containers, encounters: no dedicated runtime. lockpick appears only in inventory/registry.ts and store.ts (likely item/key id). Missing or unverified.
- Scheduling / FrameWorkQueue: packages/game-core/src/scheduling/frameWork.ts (+ frameWork.test.ts, frameWorkContext.tsx). Working.
- Streaming / chunks: packages/game-core/src/terrain/chunkStore.ts, streamRefocus.ts, heightfield.ts (+ tests). Working; settlement/farCells.ts.
- Interaction: packages/game-core/src/interaction/arbiter.ts (interaction.test.ts). Working.
- Camera: packages/game-core/src/camera/ (followCamera.ts, cameraCollision.ts, bowCamera.ts). Working.

## apps/ (4)
- apps/combat-sandbox — React/Vite combat test bed (arena, HUD, inventory UI, character picker).
- apps/game — 3-line shell that logs sea level; placeholder.
- apps/stats-lab — Vite app for stats tuning/inspection (src present).
- apps/world-studio — Vite world authoring/preview studio (terrain, settlements, water, weather, interiors, travel, map).

## packages/ (10)
- audio — audio manager, backends, events, manifests (world module 57).
- basis-transcoder — plugin wrapper for Basis texture transcoding (plugin.mjs only).
- character — player/NPC actor: EcctrlAdapter, SkyrimFighter, bows, armour attachments.
- character-assets — asset files and verify.mjs for character GLB assets.
- contracts — shared constants and interfaces (src/index.ts; SEA_LEVEL_Y).
- game-core — shared runtime: combat, stats, inventory, AI, physics, water, settlement, interior, render, fx.
- text-catalogue — keyed player-visible text table.
- world-schema — JSON Schemas per record family + Python integrity gate.
- world-time — clock, calendar, ephemeris, season.
- world-weather — synoptic weather states and express helpers.

## world/sources/ top-level (18)
- anchors — settlement anchor points (settlement-anchors.json).
- assets — asset registries (registry-*.jsonl) and architecture regions.
- blueprints — settlement/building design + layout files.
- catalogue — place and design-group catalogues (places-*.json, interior-recipes.json).
- climate — weather states.
- demographics — population priors.
- flora — vegetation palettes, groundcover, patches.
- hydrology — water bodies, graph, routing corrections.
- lore — world lore markdown.
- placement — accepted places, micrositing, settlement form stats.
- quests — quest and line data (13 json).
- regions — authored region overrides.
- registries — id-linked vocabularies: creatures 31, deeds 304, factions 111, items 18, npcs 732, quests 731, rumour-pools.
- routes — roads, stations, travel services, water crossings.
- settlements — settlement warnings.
- sites — candidate sites, dossiers, macro-plot.
- sky — star catalogue.
- terrain — freeze, patches, water corrections.
- vocab — socket-vocabulary.json, ground-paint.json.

Covered: apps/* (top level + game/src, combat-sandbox/src, world-studio/src dirs), packages/* (top level), packages/game-core/src/* (all 37 folders), packages/game-core/src/stats/data, world/sources/* (top level), world/sources/registries and quests (counted).
Skipped: apps/*/dist, node_modules, generated/ folders (not read); packages/world-schema/schemas contents (not opened); tests not run.

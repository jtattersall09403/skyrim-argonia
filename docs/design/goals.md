# Goals by system

The end goals of each system in [PLAN §4](../PLAN.md), as the imported designs state them. Goals only: how the old code did it is not here. Sources are imported design docs (`world/`, `quests/`, `old-decisions/`; old numbers are the old repo's, not this one's) or this repo's decisions. Where a doc is the goal statement, read it.

## World and land

### Worldspace terrain + apron
- Province-scale Black Marsh, an unconquered hydrological heart ringed by a ruled fringe: [20 §11](world/20-province-design.md).
- Beyond the border the Tamriel map continues 1:1 and the sea covers the rest: [0067](old-decisions/0067-the-apron-is-the-tamriel-map-at-one-to-one.md).
- Terrain and water are solved together; hydrology is the primary generator: [50 §33](world/50-hydrology-climate.md).

### Rivers, lakes, waterfalls, sea
- One authoritative water model, bodies with semantics: [60 §38, §40](world/60-water-traversal.md).
- Waterfalls are Skyrim's own FX kit, stacked Bethesda's way: [0064](old-decisions/0064-waterfalls-are-the-vanilla-kit.md).
- Floods are world state with a seasonal rhythm: [50 §36](world/50-hydrology-climate.md).

### Navmesh
- Every person's walk on the place's path network is proved, not assumed: [72 §114-115](world/72-navigation-ai.md).
- The build owes walkable networks; rich AI is capped: [72 §113](world/72-navigation-ai.md).
- People are placed when unseen, walk when seen: [0138](old-decisions/0138-people-and-creatures-live-by-the-place-record-and-the-lamp-clock.md).

### LOD, distant terrain, the map image
- Derived files are made on the player's machine, never shipped: [0014](../decisions/0014-derived-files-are-made-on-the-players-machine.md).
- Distance carries the province's air: haze and aerial perspective: [55 §97](world/55-light-sky-time.md).
- The far land is the Tamriel map continued: [0067](old-decisions/0067-the-apron-is-the-tamriel-map-at-one-to-one.md).

### Regions, weather, climate, sky
- Light is data: sun, moons, stars, haze and weather come from the climate fields: [55 §93](world/55-light-sky-time.md).
- A 365-day calendar, 28-night lunar cycle, era 4E 201: [55 §94](world/55-light-sky-time.md).
- One province weather timeline, expressed regionally: [0032](old-decisions/0032-phase8c-weather-implementation-shape.md).
- A region taxonomy for the province: [20 §16](world/20-province-design.md).

### Roads, routes, the route graph
- Routes follow hydrology: slope, dry ground, flood frequency, bridges: [50 §37](world/50-hydrology-climate.md).
- Roads reach places by the approach rule: [quests/20 §12](quests/20-world-provisions.md).

### Places, interiors, doors
- Every location has a causal reason to exist: [00-core rule 1](world/00-core.md).
- Placement principles are binding, macro to micro: [97](world/97-placement-principles.md).
- A plugin's own load door binds a shell to an interior: [0114](old-decisions/0114-the-plugin-data-is-the-interior-manifest.md).
- Interiors are promised with their places: [70 §48](world/70-dungeons-interiors.md).

### Vegetation
- A first-class system with four render tiers: [65 §109-110](world/65-vegetation-scatter.md).
- Deterministic scatter, wind and constraints: [65 §111](world/65-vegetation-scatter.md).
- Tropical Skyrim and Black Marsh mods before vanilla: [90 §74.1a-b](world/90-asset-strategy.md).

## Tools and state

### The studio, scenes, the two runners
- The studio plays the game; no modes or switches for game actions: [0149](old-decisions/0149-the-studio-plays-the-game-no-modes-flags-or-switches-for-game-actions.md).
- Journeys are staged scenes, looped until they pass: [0155](old-decisions/0155-journeys-are-staged-scenes.md).
- Each block is tested at its cheapest level, composed once: [0156](old-decisions/0156-test-each-building-block-at-its-cheapest-level-compose-once.md).

### Game state, co-save, message schema, menu router
- One composition seam joins every system: [2.1 brief](phases/2-slice/2.1-composition-seam.md).
- Each system saves itself as it lands: [0158 §3](old-decisions/0158-boats-and-sound-before-the-save-loop.md).
- Every entity has one home table: [98](world/98-data-model.md).

### Where each rule lives
- Everything is built natively the Skyrim way: [0026](../decisions/0026-everything-is-built-natively-the-skyrim-way.md).
- Numbers live in one place: [76 §129](world/76-stats-progression.md).

## People and the living world

### NPCs, whole-body templates, schedules, factions
- Every person named and visually unique; places live by their record: [0138](old-decisions/0138-people-and-creatures-live-by-the-place-record-and-the-lamp-clock.md).
- One village clock: rise, work, meal, lamps, bed: [72 "The day"](world/72-navigation-ai.md).
- Race shares follow the demographic priors: [92 §84](world/92-demographics.md).
- Factions have a registry and advancement rules: [quests/40 §27-28](quests/40-factions.md).

### Fixed danger D0-D5, roaming bands, respawn on rest
- The world never receives the player's level: [0004](old-decisions/0004-fixed-difficulty-constraint.md), [00-core rule 2](world/00-core.md).
- An absolute ladder D0-D5 for creatures, loot and traps: [76 §128](world/76-stats-progression.md).
- Hostile places attack on sight; roaming bands follow region danger: [0142](old-decisions/0142-combat-is-met-everywhere-hostile-places-roaming-bands-and-answered-violence.md).
- Access opens through capability and knowledge, never softening: [20 §12.4](world/20-province-design.md).

## Character

### Attributes, 27 skills, formulas
- Seven attributes, Morrowind's jobs and coefficients, no dice: [76 §117](world/76-stats-progression.md).
- Morrowind's 27 skills, three substitutions: [76 §118](world/76-stats-progression.md).
- One stat schema compiled for every actor: [0144](old-decisions/0144-progression-ships-whole-one-stat-schema-compiled-for-every-actor.md).

### Races, birthsigns, classes, effect stack, perks
- The character in one screen: [76 §116](world/76-stats-progression.md).
- Races and birthsigns are permanent packages on one effects stack: [76 §127](world/76-stats-progression.md).
- Creation: race, birthsign chosen directly, class: [76 §119](world/76-stats-progression.md).

### Skill use, vastei, levels at rest, the sitting
- Skills grow by use; vastei buys attributes: [76 §120](world/76-stats-progression.md).
- Early levels come fast, never ages between later ones: [0147](old-decisions/0147-early-levels-come-fast.md).
- Levels are taken at the level sitting: [76 §120.4](world/76-stats-progression.md).

### Death pile, wake at last rest, rest = only save
- Healing is potions; death and respawn follow Morrowind's weight: [76 §126](world/76-stats-progression.md).
- Progression ships whole: [0144](old-decisions/0144-progression-ships-whole-one-stat-schema-compiled-for-every-actor.md).

## Story and text

### Dialogue: topics, hyperlinks, disposition, persuasion
- Morrowind-shaped topics, layered from culture to the person: [0139](old-decisions/0139-cultures-down-to-the-person-facts-once-opinions-each.md).
- Anyone may explain in their own words: [0143](old-decisions/0143-anyone-may-explain-restatement-is-near-verbatim-only.md).
- Disposition changes the talk; essential topics are never gated: [0145](old-decisions/0145-disposition-changes-the-talk-essential-topics-never-gated.md).

### Quests as data, conditions
- Quests ship as data over one world record: [0153](old-decisions/0153-quests-ship-as-data-over-one-world-record.md).
- One typed condition and action vocabulary: [quests/85](quests/85-condition-vocabulary.md).
- Quest-ready location packets: [quests/20 §13](quests/20-world-provisions.md).

### Writing quests, dialogue and text
- Content is written from one source of truth: [0024](../decisions/0024-content-is-written-from-one-source-of-truth.md).
- Lore layers, voice, twist discipline: [quests/60 §45-48](quests/60-writing-and-lore.md).
- Lore extrapolation fills the 4E 201 gaps: [45](world/45-lore-extrapolation.md).

### Investigation support and the detectives' faction
- [0025](../decisions/0025-a-detectives-faction.md) states the faction's goal.
- Evidence and knowledge predicates: [quests/85 A3](quests/85-condition-vocabulary.md).
- Main quest, *The Eye and the Root*: [quests/30](quests/30-main-quest.md).

### Journal, directions, no markers
- Directions, not markers, until the player has been there: [0137](old-decisions/0137-directions-not-markers-until-discovered.md).
- Directions are written against the real road and river network: [0137](old-decisions/0137-directions-not-markers-until-discovered.md).
- Journal text follows the style guide: [quests/60 §45e](quests/60-writing-and-lore.md).

### World map, local map
- Nothing points at an undiscovered place: [0137](old-decisions/0137-directions-not-markers-until-discovered.md).
- The map image is a derived file: [0014](../decisions/0014-derived-files-are-made-on-the-players-machine.md).

### Our own UI and HUD, Pelagiad, the UI map, transitions
- One coherent Argonian UI approach, chosen with the owner: [0017](../decisions/0017-one-coherent-argonian-ui-approach-chosen-with-the-owner.md).

## Items and systems

### Weapon classes, armour slots, condition
- Weapon classes follow Morrowind: [0016](../decisions/0016-weapon-classes-follow-morrowind.md).
- Blocking, condition, and what skill never touches: [76 §121.6](world/76-stats-progression.md).

### Economy, barter, training, services, travel
- One price contract: coin, goods or a favour: [0141](old-decisions/0141-one-price-contract-coin-goods-or-a-favour.md).
- Crafting, economy, services and crime: [76 §124](world/76-stats-progression.md).

### Magic
- Skyrim hands, one effect-family system, folk sellers: [0146](old-decisions/0146-magic-ships-whole-skyrim-hands-one-effect-family-system-folk-sellers.md).
- Spell sellers carry a sheet-sized stock: [0148](old-decisions/0148-spell-sellers-carry-a-sheet-not-the-catalogue.md).
- Design: [76 §123](world/76-stats-progression.md).

### Crafting
- The whole engine ships, thin content: [0150](old-decisions/0150-crafting-ships-whole-the-slice-climbs-its-first-rungs.md).
- Recipes, materials, ingredients and enchant tiers all ship: [0150](old-decisions/0150-crafting-ships-whole-the-slice-climbs-its-first-rungs.md).
- Design: [76 §124](world/76-stats-progression.md).

### Stealth, crime, Owing, locks, pickpocket
- Per-observer detection; pickpocketing is the one gamble: [0151](old-decisions/0151-stealth-crime-and-locks-ship-whole-pickpocket-is-the-one-gamble.md).
- Awareness is unaware, suspicious or engaged: [0092](old-decisions/0092-stealth-is-a-detection-service-the-runtime-feeds.md).

## Combat and traversal

### Combat: DS1's system
- DS1 Remastered is the oracle; each behaviour maps to a tuned mod or our build: [0004](../decisions/0004-ds1-remastered-is-the-combat-oracle.md), [0019](../decisions/0019-combat-maps-each-ds1-behaviour-to-a-tuned-mod-or-our-own-ds1-build.md).
- Damage, stamina, poise, defence: [76 §121](world/76-stats-progression.md).

### Wiring the mods to our stats
- The sheet is the one source of numbers: [76 §116, §129](world/76-stats-progression.md).

### Movesets
- Chosen for DS1 fidelity: [0019](../decisions/0019-combat-maps-each-ds1-behaviour-to-a-tuned-mod-or-our-own-ds1-build.md).
- Fighting is met everywhere, not only in set pieces: [0142](old-decisions/0142-combat-is-met-everywhere-hostile-places-roaming-bands-and-answered-violence.md).

### Enemy AI, bosses
- Enemies resolve to fixed numbers on the ladder: [76 §128](world/76-stats-progression.md).
- Encounter placement follows ecology and motive: [70 §50](world/70-dungeons-interiors.md), [74](world/74-ecology.md).

### Ranged and thrown
- Recoverable arrows; projectile response by material: [75 §55](world/75-combat-compatibility.md).
- Damage and aim: [76 §121.1](world/76-stats-progression.md).

### Climbing, ladders
- Breath of the Wild's climb, province-wide, derived from rules: [0152](old-decisions/0152-climbing-is-a-province-wide-system-swim-is-closed-ladders-and-water-stealth-join.md).
- Climb semantics for surfaces: [60 §46](world/60-water-traversal.md), [76 §122.1](world/76-stats-progression.md).

### Swimming, diving, breath
- Swimming modes; underwater is a complete exploration layer: [60 §43-44](world/60-water-traversal.md).
- Creatures swim too: [75 §57](world/75-combat-compatibility.md).

### Boats
- Boats sail like The Wind Waker; dugout and sea hull first: [0159](old-decisions/0159-boats-are-wind-waker-sailing-dugout-and-sea-hull-first.md).
- Boats are the primary vehicle: [60 §45](world/60-water-traversal.md).

### Marsh specials
- The marsh does what the lore says: [0157](old-decisions/0157-the-marsh-does-what-the-lore-says.md).
- One hazard-volume record serves every stand-here-and-it-lands fact: [0157 §2](old-decisions/0157-the-marsh-does-what-the-lore-says.md).
- Creatures do what the lore says (the wamasu spits shock): [0157 §1](old-decisions/0157-the-marsh-does-what-the-lore-says.md).

### Ragdolls
- Nice to have; no old goal beyond [PLAN §4](../PLAN.md).

## Look, sound and release

### Graphics
- Light and atmosphere carry place: [55 §93, §96-97](world/55-light-sky-time.md).

### Music, ambience, UI sound
- Sound is a first-class world system: [57 §105](world/57-audio-soundscape.md).

### Vanilla quarantine
- No vanilla system, asset or word reaches the player unreviewed: [0012](../decisions/0012-vanilla-skyrim-is-quarantined.md).
- Base-Skyrim assets come from Tropical Skyrim first: [90 §74.1a](world/90-asset-strategy.md).

### Immersion inventory and gate
- No Nordic element survives: [0006](../decisions/0006-black-marsh-immersion-no-nordic-element-survives.md).

### Main menu, loading, settings, controls
- Shell screens follow the one UI approach: [0017](../decisions/0017-one-coherent-argonian-ui-approach-chosen-with-the-owner.md).

### Character creation, the opening
- Creation steps: [76 §119](world/76-stats-progression.md).
- A new player knows nothing: [quests/60 §45d](quests/60-writing-and-lore.md).

### Install, pin, distribute
- One pinned runtime; nothing shipped that players do not own: [0002](../decisions/0002-one-pinned-skyrim-runtime.md), [0003](../decisions/0003-nothing-shipped-that-players-do-not-own.md).

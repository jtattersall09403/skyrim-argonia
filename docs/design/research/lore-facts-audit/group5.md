<!-- imported unchanged from elder-souls-argonia docs/research/lore-facts-audit/group5.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Group 5 audit: religion (18) and peoples (12) facts, world/sources/lore/loading-facts.json

Evidence base: races roster = 10 bodies, Argonian the only Black Marsh body (packages/game-core/src/actors/generated/races.json; decision 0096). factions.json has faction.nisswo, shadowscales, naga-kur, tribeless-naga, root-whisper, sul-xan (world/sources/registries/factions.json entries). traps.json kinds = fire, frost, shock, lifeforce, poison, paralysis, silence (Morrowind spells only; no xanmeer-specific kind). detection.json has per-profile sightM/hearing/scent (world/sources/registries/detection.json:187). 4.5 table (docs/phases/4-buildout/4.5-systems-depth.md:13-26) holds: rite stat drains, sap-draught/spore-call, Hist communion powers, dream and vision harness, trap kinds beyond slice, pilgrimage chains.

| id | derivation | exists / planned (file:line) | status | value | effort | timing |
|---|---|---|---|---|---|---|
| revere-hist | Hist as the faith: Argonian race power/dialogue rule (no Tamrielic shrines for Argonians; assimilated ones may use them); Hist shrines as blessing sites (Hist-tree blessing instead of Divine shrine) | shrine blessings priced by standing, 2.6 (phases/2-slice/2.6-trade-and-services.md:39); checklist "shrine blessings: one temp buff, priced by faith" (research/combat-and-systems/slice-systems-checklist.md:118); Hist communion = 4.5 (2.9-magic.md:240; 4.5:23). No race-keyed faith rule found | PLANNED (blessing), GAP (faith key = Hist for Argonians) | M | S | seam-now: blessing record needs a `faith` key |
| clutch-of-nisswo | Nisswo faction, wandering priests as truth-gatherers; NI quests | faction.nisswo (factions.json); NI01-NI09 (quests/40-factions.md:288-319); Nisswo spell-sellers (world/76-stats-progression.md:1120); culture sheet (dialogue/cultures/factions/nisswo.json) | EXISTS (faction, sheets), PLANNED (quests, 4.3/4.5) | M | - | later |
| nisswo-nothing-speaker | Jel etymology; Nisswo as a role/title in dialogue and rank names | nisswo.json culture sheet; glossary quests/57-glossary.md | EXISTS (flavour) | L | - | - |
| nisswo-kings | Xul-Thuxis (Deepmire) pre-Duskfall priest-king site; blood-sacrifice ruin; lore books | Xul-Thuxis in research/phase16/16g-review/naga-kur-deeps.md, teeth-of-sithis.json culture sheet; no quest tie | PARTIAL (place lore), GAP (book/quest) | L | S | later (book + 4.3 line) |
| raj-sithis | Sithis doctrine: Changer; Nisswo sermon topics; dialogue rule that Nisswo frame all change as divine | nisswo.json (Daedric heresy line :126); NI quests | EXISTS (flavour) | L | - | dialogue only |
| teeth-of-sithis | Temple place with sanctuary stance at Nisswo rank 1, casts back at player | TeethofSithisInt01 fill, hostility flips (2.11-quests-journal-map.md:32), 2.9 cast-back (2.9-magic.md:8,234), NI05 (40-factions.md:315) | EXISTS / PLANNED | H | - | slice (already in) |
| shunatei | Named grief/stasis mechanic: "holding on" as a quest theme (NI06 A Change Refused); a dialogue concept; optionally a spell/disease flavour | culture-registers.md, quests/30-main-quest.md, 36-cast-roster.md use the word; NI06 | EXISTS (theme) | L | - | dialogue only |
| duskfall-defined | Duskfall history book / relics (DQ artifact quests); era-dated lines | quests/50-side-quests.md:116-121; 99-sources; style-guide | EXISTS (themes) | L | - | - |
| jaraleet | Hist communion by sap: sap-speaker NPCs, communion spell/power, vision scene; sap-draught | communion = 4.5 (4.5:13,23); hist-and-sap dossier; sap-poisoning marks (gold tongue) on cast (30-main-quest.md:187) | PLANNED (4.5) | H | M | later; seam-now: effect family slot |
| duskfall-sithis-shift | Cyclical-time worldview: dialogue register (death as cycle, season/calendar names Hist-Deek etc.); calendar in-world names | no "cyclical" rule in culture-registers.md (grep empty); calendar months exist in world-time per hist dossier | GAP (dialogue register line only) | L | S | later |
| dream-wallow | Vision scene: isolation + herb, objects manifest; main-quest sap-dreams ("fog-dressed reuse of interiors", 30-main-quest.md:156-160); Naga-Kur rite; reusable "wallow" player power/herb | dream and vision harness = 4.5 (4.5:20); MQ dreams (30-main-quest.md:156); LD63 rite quest (quests/index/standalone.md:73); naga-kur.json:58; no engine support | PLANNED (4.5) | H | M | later; seam-now: staged-scene stage kind |
| naga-kur-kaju | Rite/trial: kill a chief-chosen dream-beast alone inside the wallow; boss/trial arena, starblossom fumes | type-recipes.json:11666,11742 ("kaju-kill"); sithis dossier :121; no kaju creature row found | PARTIAL (place props), GAP (creature + trial) | M | M | later (4.5 boss + dream harness) |
| atak-and-kota | Adzi-Kostleel creation myth: book/dialogue; Atakota emblem | tribes.md only | dialogue/book only | L | S | later |
| shadowscales | Assassin order: faction with ranks Watcher to Writ-Keeper; Empty Cradle quest; birth-offered recruits; cowl relic | faction.shadowscales; "31. The Empty Cradle" (40-factions.md:175-186); MQ23 manhunt (30-main-quest.md:272); DQ05 | PLANNED (factions line) | H | L | later |
| ku-vastei | "Necessary change" title: Shadowscale rank/honorific, contract dialogue | culture sheet register; 40-factions.md:426 | EXISTS (flavour) | L | - | - |
| shadowscales-4e201 | Last Shadowscale dying in 4E 201: quest clock / NPC cameo | 40-factions.md:179 (canon dates quoted) | PLANNED | M | - | later |
| no-daedra-words | Language rule: Argonians never name Daedra; dialogue lint (Argonian-register lines may not use "Daedra" and use "the Outside"/Oblivion-circumlocution); Daedra-cult NPCs break the rule as a tell | style-guide.md:142-166 covers Jel loanwords; no rule on Daedra words (grep of cultures/ finds only nisswo.json:126 "Daedric heresy") | GAP | M | S | seam-now (text lint rule, cheap before the slice dialogue freezes) |
| kingdom-of-argonia | Scalded Throne place + empty-throne motif | Helstrom hall (30-main-quest.md:162; place.hist-heartland.helstrom.json); 4.3 narrative lines | PLANNED | M | - | Part 4 |
| men-of-the-marsh | Horwalli, Yespest, Kothringi as ruin/grave/NPC lore; Horwalli-Yespest sites | lost-peoples dossier; catalogue places-naga-kur-deeps/pirate-freeholds mention Horwalli; type-recipes.json | EXISTS (place lore) | L | - | - |
| kothringi-lustrous | Silver-skinned NPC race: no body (roster has no Kothringi); realistic = ruins/graves and the "last Kothringi" chimes NPC (36-cast-roster.md:605) | cast roster :605; htbm Kothringi hut variant (world/90-asset-strategy.md:265); Kothringi remains (world/60-water-traversal.md:339) | PARTIAL (hut kit, cast) | L | S (silver skin tint on an existing body = retexture, forbidden) | later |
| kothringi-sailors | Kothringi tidal canoe as the shallow-draft boat class (swamp+coast) | research/lore/marsh-watercraft-and-argonian-boats.md:29 ("one named native type"); boat classes reed canoe/dugout/skiff (2.15-boats.md:83) | PLANNED (2.15) | M | S | slice-now: name the canoe class `kothringi` in the 2.15 boat-class rows |
| crimson-ship | Flu ship: lost-ship wreck quest/rumour, ghost-ship set piece | cast roster :605 ref; history-timeline; wrecks-v1 interior kit exists (world/sources/placement/kit-interiors/wrecks-v1.interiors.json) | PARTIAL (lore + wreck kit) | M | M | later (4.3 line) |
| lilmothiit-fox-folk | Extinct Khajiit-like people: drowned ruins, remains; no race body (Khajiit body could not be reskinned without art) | world/70-dungeons-interiors.md:30; 30-lore-systems.md:161-165; 60-water-traversal.md:339 | PLANNED (site types) | L | - | later |
| lilmothiit-founders | Lilmoth/Blackrose foundations under later town | 30-lore-systems.md:165 | EXISTS (place lore) | L | - | - |
| orma | Blind people: (a) perception rule: sightM 0, hearing/touch up, as a detection profile (b) Hand-Read Halls tactile ruin, LF09 blind-architecture dungeon (c) lit-less hall mechanic: no light wells, sound layouts | places-imperial-fringe.json:13102 (Hand-Read Halls, DQ08, LF09), index LF09; detection.json sightM per profile (:187) so an Orma profile is a data row; no race/body (assets) | PARTIAL (place + quest planned) | M | S (profile), M (dungeon) | slice-now: none; seam-now: profile rows must not assume sight>0 |
| naga | Naga as hostile band race and NPC (huge mouths, 7-8 ft): Naga-Kur camp, tribeless Naga | faction.naga-kur, tribeless-naga; Naga highway camp band D4 (2.7-combat-and-encounters.md:30); no distinct body (uses argonian) | EXISTS (faction/bands) | M | - | - |
| lukiul-outsiders | Argonians who left are outsiders: standing rule for marsh vs port Argonians; An-Xileel slur | culture-registers.md:191; glossary :39; world.md:22 (writer brief); dialogue lines in 2 places | EXISTS (flavour) | L | - | dialogue only |
| barsaebic-ayleids | Ayleid exiles at Silyanorn/Stormhold: ayleid ruin kit, Stormhold place | world/90-asset-strategy.md, 70-dungeons-interiors.md; ayleidcc traps in kits; place-purpose doc | PLANNED/EXISTS (place/kit) | L | - | Part 4 |
| ayleids-ancient-xanmeers | Lore hook: Ayleid scholars' doubt; a Barsaebic survey journal found in a xanmeer (document row) | documents.json home exists; no entry | GAP (book) | L | S | later |
| xanmeers | Stepped pyramid dungeons: maze interiors with traps, puzzles, flooded lower levels, hist summit chamber. Our traps are Morrowind spell traps only; xanmeer needs mechanical traps (swinging blade, pressure plate) and a lever/puzzle language | xanmeer-interior-v1 kit (kit-interiors/xanmeer-interior-v1.interiors.json) with Ayleid-CC trap props at :747-756 (swinging blade); lever gates (98-data-model.md:65); trap kinds beyond slice = 4.5 (4.5:12); xanmeer exterior (97-placement:870); Glenbridge/Teeth places | PARTIAL (kit, lever gate, locks); GAP (mechanical trap kinds) | H | M | seam-now: traps.json trigger vocabulary (see below) |

## Common threads

1. Faith as an effect/service: Hist-faith blessing (revere-hist), shrine priced by standing (2.6), sap-draught/communion (jaraleet), Nisswo spell-selling. One effect-stack entry + a `faith` key on blessing rows serves all.
2. Dream/vision harness (4.5 staged scenes): dream-wallow, naga-kur-kaju, MQ sap-dreams, jaraleet visions, LD63 rite. One system, five uses.
3. Sense-rule profiles: orma, plus Naga/creature profiles, all rows in detection.json (data, not code).
4. Factions already registered: nisswo, shadowscales, naga-kur carry the religion facts. Only content (4.3) missing.
5. Peoples as lost-culture dressing, not playable: kothringi, lilmothiit, horwalli, yespest, orma, ayleids: ruins, graves, wrecks, documents.json rows, never new bodies (no art). Roster has one Black Marsh body.
6. Dialogue register only: nisswo-nothing-speaker, raj-sithis, shunatei, duskfall, cyclical time, ku-vastei, lukiul, atak-and-kota, no-daedra-words.
7. Boats: Kothringi tidal canoe feeds 2.15 boat classes.
8. Trapped interiors: xanmeers, Hand-Read Halls, Ayleid ruins (ayleid trap props in kits).

## Seam-now candidates

- traps.json entries[].trigger: today only `open`. Add vocabulary room for `step` (pressure plate), `lever`, `timer`, and an entry `kind` field (spell | mechanical) with `effectId` still optional (`mechanical` rows use `damage` + prop id) so xanmeer traps (swinging blade props exist in the kit) arrive as data rows; locks.json `trap` stays the link.
- Shrine/blessing record (2.6): include `faith` (divine | hist | sithis | none) and a `forRaces`/`excludedFor` gate so Argonians use Hist shrines; priced by standing is already ruled.
- detection.json profile rows: keep sight a per-profile number that can be 0 (Orma); ensure the player-facing "notices you" logic does not divide by or require sight.
- Staged-scene stage kinds (journey.ts: at, hour, place, cell, near, owing, stance): reserve a `vision`/`dream` kind (4.5) so dream-wallow and MQ dreams are not retrofitted.
- 2.15 boat class id `kothringi-canoe` (shallow-draft, swamp+coast) in the class rows.
- Dialogue lint (docs/standards/text/style-guide.md Jel section): rule that Argonian-register lines avoid the word Daedra (no-daedra-words); cheap now, costly after the slice corpus is written.

## Most valuable gaps

1. Xanmeer mechanical traps and puzzle language (H/M).
2. Hist-sap communion / dream-wallow vision harness (H/M, already 4.5) with the kaju trial as its first user.
3. Hist-faith shrine blessing for Argonians (M/S).
4. no-daedra-words lint (M/S).
5. Orma sight-0 profile + Hand-Read Halls (M).

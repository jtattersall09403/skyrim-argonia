<!-- imported unchanged from elder-souls-argonia docs/research/lore-facts-audit/group2.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Fact audit group 2: topics hist + history (39 facts)

Era note (0002): game is 4E 201. Every `history` fact is past (Umbriel 4E 48 is 153 yrs back); they support rumours, documents, ruins, memorials and quest backstory, not live systems.

Key evidence (file:line)
- hist-and-sap dossier: world/sources/lore/topics/hist-and-sap.md (sap, rubber, plasm, communion, lukiul, eggs sections).
- Allegiance track already designs sap-draught, rites as corprus-style stat drain, spore-call, gold tongue/bark scale as flavour only: docs/quests/30-main-quest.md:481-499 (24b.1); docs/decisions/0028-allegiance-reward-tracks.md:49; deferred to 4.5: docs/phases/4-buildout/4.5-systems-depth.md (allegiance row "sap-draught and spore-call"; "Hist communion powers"; "creature specials: wamasu shock the water"; "disease, toxin and insect counterplay"; "weapon poisons and oils").
- item.hist-sap exists with fortify-health 11.3/34s + fortify-willpower: world/sources/registries/items.json (id item.hist-sap, subkind potion); in loot-rules.json:292,361,1581. item.spore-cloud-scroll (spellId sleep), item.mnemic-egg (quest), item.wamasu-bone ("holds a charge for years"; harvest.wamasu in creature-harvest.json:429-442), item.spriggan-sap (only rareFortify, 2.9b-loops/records.md:21).
- 2.9b recipe gate takes misc or ingredient inputs, tiers 1..8: docs/phases/2-slice/2.9b-crafting.md:~83; stations in upriver-hist-village (2.9b-loops/stations.md:12-15).
- Effect stack has resistShock: packages/game-core/src/stats/effects.ts:33; one disease with staged timed entry: docs/phases/2-slice/2.9-magic.md:84-86.
- Calendar with Jel names built: packages/world-time/src/calendar.ts:23-25 (Hist-Deek/Dooka/Tsoko, Egg, Egg-Basket); each month = birthsign (docs/world/98-data-model.md:86).
- Hist-tree "drink sap" ruled later: docs/research/combat-and-systems/slice-systems-checklist.md:153.
- Hist as spatial layer (egg pools, sap-speaker residence, rootworm): docs/world/30-lore-systems.md:65-125; licensed sap-tapping camp exists: docs/phases/P-polish/backlog.md:91.

## Table

Asset note: we never make art. Hist sap vial mesh exists (sleepingtreesap01 via items.json assetAvailability); wamasu bone, mnemic egg (King of the Murkmire egg meshes), guar/hatchery, xanmeer kits exist per records. No rubber mesh known; reuse a vial/ingot/leather-strip mesh with a new record.

| id | derivation | exists / planned (file:line) | status | value | effort | timing |
|---|---|---|---|---|---|---|
| fact.hist-spore-trees | Hist tree as place feature: interactable root-tree prop in every Hist village; dialogue | Hist as layer 30-lore-systems.md:65-125; upriver-hist-village placed; item.hist-sap | EXISTS (places) | M | S | later |
| fact.people-of-the-root | Sap-licking rite as interaction verb at a Hist; self-name in dialogue ("saxhleel") | verb ruled later, checklist:153; 24b.1 sap-draught | PLANNED (4.5 allegiance / Hist sites) | M | M | later |
| fact.hist-older-than-men | Dialogue/book topic only | glossary 57; hist dossier | dialogue/flavour only (partly EXISTS in topics) | L | S | later |
| fact.hist-one-mind | Root-network system: Hist-state shared across sites (kill/harm one Hist, all react); fast-travel via roots (rootworm) | rootworm travel 2.6 / 30-lore-systems.md:52-57; no shared Hist-state record | PARTIAL (travel planned, shared state GAP) | M | M | seam-now (a world-state flag `histState` per Hist node, see below) |
| fact.hist-roots-reach | Rootworm route network, root-transit between Hist; lore for far-off Hist (Cyrodiil etc.) | rootworm in 74-ecology.md:121; 2.6 talk-pay-arrive; HistNodeBlueprint.rootTransitLinks 30-lore-systems.md:120 | PLANNED | M | S | later |
| fact.hist-growth-names | Calendar months and Hist maturity labels; place name/age of Hist (Deek/Dooka/Tsoko) on Hist node record; Root Talk in Hist-Tsoko | EXISTS calendar.ts:23-25; Root Talk month 20-world-provisions.md:~212 | EXISTS | L | S | slice-now already (add `maturity` field to Hist node record, later) |
| fact.hist-hatching-pools | Egg-pool place feature: hatchery with egg-tender service, clutch tending quest/job, guar warms hatchery | egg pools in HistNodeBlueprint 30-lore-systems.md:118; egg-tender glossary 57:36; MQ19, MQ01; no tending activity | PARTIAL (place feature planned, no mechanic) | M | M | later (dialogue + one quest line) |
| fact.hist-egg-bond | Stakes mechanic: severing Hist link kills clutch; main-quest causal chain (MQ21 mnemic egg); timer/world-state change after cult interference | dossier "silence vs severance" hist-and-sap.md; MQ21 30-main-quest.md:270 | PLANNED (quest) | H | M | later (quest); data: rely on quest world-flags |
| fact.hist-sap-visions | Vision/dream harness: lick sap -> staged vision scene; reveals past state of a place | "dream and vision harness" 4.5 row; 30-lore-systems.md:93; 2.11 staged scenes | PLANNED (4.5) | H | L | later; seam: staged-scene record may carry `trigger: sap` (2.11) |
| fact.sap-poisoning | Staged condition: repeated sap doses accumulate; stage-1 gold tongue, stage-2 bark scale (+armour/-agility?), hallucination; NPC dialogue reacts (Opens-the-Last-Door, Miril-Tei) | cosmetics flavour-only 0028:49; cast 36-cast-roster.md:153,404; staged diseased entry 2.9-magic.md:84; "disease, toxin counterplay" 4.5 | PARTIAL (dialogue exists, mechanic GAP) | M | M | seam-now (dose counter reuses staged timed entry) |
| fact.hist-sap-rubber | Crafting material `item.hist-sap-rubber` (smith/alchemy recipe: hist sap + ... -> rubber), insulated gear: gloves/boots/prod with resistShock; telescoping wamasu prod = weapon that stuns/harvests wamasu; enchant-free shock protection; wamasu-bone charge-holder for shock enchant | No rubber/prod record (items.json); resistShock effect exists effects.ts:33; recipes gate misc inputs 2.9b; wamasu shock water only in 4.5 row; wamasu-bone exists | GAP | H (ties wamasu, crafting, swim) | M | seam-now (see candidates 1,2) |
| fact.amber-plasm | Corrupt sap item `item.amber-plasm` (looks like hist-sap, mad-Hist drop): cult growth buff w/ madness (Str/End up, Will/Pers down), ingredient with deceptive description; identify-by-skill | Tier-2 rite stat model 24b.1; hist-sap item has no plasm twin; voriplasm creature in 74-ecology.md | PARTIAL (cult model, no item) | M | S | later (one item row + alchemy effects) |
| fact.hist-ehlnofey-war | Book / ruin lore; sunk lands -> flooded ruins (xanmeer, drowned kit) | xanmeer ruins placed; documents.json | dialogue/flavour only | L | S | later |
| fact.sap-is-soul | Souls = sap: death returns soul to tree (soul-trap rule: Argonian "sap soul" returns to Hist, not trappable?); Soultrap exception for marsh Argonians; funeral rite at Hist | 76-stats-progression.md:550 mentions; magic soultrap src/soultrap.ts (creature souls) | PARTIAL (stated, rule unverified) | M | S | seam-now (soul-trap `trappable` flag on person species/race) |
| fact.hist-whispers | Passive: near Hist gives whispers/hints (ambient audio, subtitle, minor regen/Willpower aura), marsh-born only; Hist as safe "rest" spot | hist communion = 4.5 (2.9-magic.md:240); 2.14 sound has Hist ambient? (not checked) | PLANNED (4.5) | M | M | seam-now (character `marshBorn` flag), else later |
| fact.hist-magic-spores | Spore-call ability (cloud, incapacitate); spore-cloud scroll | scroll EXISTS (items.json item.spore-cloud-scroll, sleep spell); spore-call ability PLANNED 24b.1 tier 3 + 4.5 | PARTIAL | H | M | later; spore effect = sleep/paralyse (2.9 effect family exists) |
| fact.hist-bond-not-bondage | Tone/dialogue; reputation with tree-minders; Hist-care actions (water, clearing blight) as quest options | Root Talk track 24b.3 | dialogue/flavour only (quests PLANNED) | L | S | later |
| fact.hist-realm-sank | Sunken ruins as swim/dive targets; drowned landmarks | swim/dive 2.12; xanmeer kits | dialogue/flavour only (+ environment, EXISTS) | L | S | later |
| fact.barsaebic-refuge | Ayleid ruin sites (Stormhold/Gideon region); ruin kit | ayleidkit ids; 30-lore-systems.md:167; quests index local-imperial-fringe/standalone | EXISTS (kit/places) | L | S | later |
| fact.bramman-1033 | Hidden navigable river (Bramman's river) + pirate rumour; boat route | 20-world-provisions.md:206; rumour-pools has Bramman; quests Bramman | PLANNED (quest/rumour exists) | M | S | later (boats 2.15 allows) |
| fact.battle-of-argonia | Rumour/book; battlefield remnant ruin; glossary entry | 57-glossary.md only | PARTIAL (glossary only) | L | S | later |
| fact.great-burn-1e2828 | Burn country as terrain: charred peat, peat fire-scar region, smouldering underground hazards (fire/smoke ground volume), burned-region ecology; White Rose Prison in burn country; helstrom | 74-ecology.md:160 (extinct croc); 20-world-provisions.md White Rose; fire spread CUT 0042 §2; hazard volumes in 4.5 creature specials | PARTIAL (places + dialogue; hazard GAP) | M | M | later (damage-volume generalisation in 4.5) |
| fact.great-burn-losses | Extinct species lore; vanished tribes -> ruin/memorial; ecology rule "species list excludes X" | 74-ecology.md:160 | EXISTS (ecology) | L | S | later |
| fact.war-ends-1e2836 | Dialogue/rumour only (Imperial vs Argonian reading) | glossary / rumours | dialogue/flavour only | L | S | later |
| fact.knahaten-flu | Rumour/ruin; DQ01 Flu That Prays quest; flu-shrine; disease lore | DQ01 50-side-quests.md:112; rumour-pools; documents.json | PLANNED | L | S | later |
| fact.half-swim-sniffles | Argonian racial disease resistance (+disease resist, immune Knahaten); NPC dialogue | racial disease resist 76-stats-progression.md:81 (race modifier §127) | EXISTS (racial) | L | S | slice-now already |
| fact.flu-last-case | Rumour/document; Kothringi vanished boat -> derelict boat quest | boats 2.15; Kothringi in 30-lore-systems.md:161 | dialogue/flavour only | L | S | later |
| fact.flu-blame | Prejudice theme: outsider NPCs suspicious; dialogue reaction/rumour topic | racism handled via faction/Owing? (not verified) | dialogue/flavour only | L | S | later |
| fact.liberation-war-2e572 | Rumour/book; Shellback faction memory; veteran NPC | npcs.json mentions (Heita/Liberation) | dialogue/flavour only (EXISTS in npcs) | L | S | later |
| fact.heita-meen | Named historical person; statue/grave; NPC dialogue | npcs.json | dialogue/flavour only | L | S | later |
| fact.ebonheart-pact | Document/book; Pact insignia on ruins/faction relations | documents.json | EXISTS (document) | L | S | later |
| fact.tiber-septim | Dialogue/book only | foreign-powers dossier | dialogue/flavour only | L | S | later |
| fact.arnesian-war-3e396 | Dres border ruin/rumour; slave revolt memory; Dres slavery dialogue | none | dialogue/flavour only (GAP in rumours) | L | S | later |
| fact.oblivion-crisis-argonians | Veteran NPCs ("charged the gates"); memorial; book | documents.json mentions Dagon | dialogue/flavour only | L | S | later |
| fact.fourth-era-secession | Political frame (Argonia independent); dialogue/book | main quest 30 background | EXISTS (frame) | L | S | slice-now already |
| fact.accession-war | Rumour about invasion of Morrowind; Redoran refugees; faction relations | rumour-pools.json; factions.json | EXISTS (rumours/factions) | L | S | later |
| fact.umbriel-4e48 | Umbriel memorial (Deepmire), Umbriel Witness Society quests, undead remnants, rogue Hist lore; MQ09/13 | 20-world-provisions.md:203,219; quests index; deeds.json; rumours | PLANNED / EXISTS (quest data) | M | S | later |
| fact.umbriel-ends | Umbriel as wreck-site (settled in bog under trees): D5 destination | Deepmire plus Umbriel memorial 20-world-provisions.md:203 | PLANNED | M | M | later (Part 4) |
| fact.lilmoth-slaughter | Ruined/half-sunken Lilmoth district; Pusbottom; undead in prison | MQ13 30-main-quest.md:262; LQ08/LQ09; Lilmoth docs (9 in documents.json) | EXISTS / PLANNED | M | S | later |

## Common threads

1. Sap as substance (people-of-the-root, visions, sap-poisoning, sap-is-soul, amber-plasm, hist-sap-rubber): one `item.hist-sap` family. Today one item (potion, fortify) exists. Missing: dose/addiction state, a corrupted twin, a processed material (rubber), and a lick-at-the-tree verb. One shared shape: sap/plasm/rubber items + a cumulative dose counter on the staged timed effect (same mechanism as the one disease).
2. Wamasu + electricity (hist-sap-rubber): rubber-insulated prod/gloves/boots = `resistShock` gear, wamasu-bone charge, wamasu shock-water volume (4.5 row), swim hazard (2.12). The shock-water rule must read the player's `resistShock` so insulated gear matters; otherwise prod is decorative.
3. Hist communion (visions, whispers, spores, one-mind, bond): 4.5 "Hist communion powers" + "dream and vision harness". Gate is marsh-born vs lukiul (dossier). Needs one boolean on the character record.
4. Egg/hatchery (hatching-pools, egg-bond): place feature + quest stakes; no mechanic needed beyond world flags.
5. Disease/resistance (half-swim, flu, knahaten): racial resist exists; flu = lore/quest; disease system exists (one disease).
6. History as documents/rumours (all history facts bar Great Burn): rumour-pools.json, documents.json already cover Knahaten, Umbriel, Bramman, Ebonheart, Dagon, Accession, Lilmoth. Missing in rumours/documents: Great Burn, Battle of Argonia, Heita-Meen/Liberation War (only npcs.json), Arnesian War, Tiber Septim. Pure authoring, no system.
7. Burn country (great-burn): terrain/ecology exist as lore; peat-fire hazard not planned (fire spread CUT 0042 §2).

## Seam-now candidates

1. Recipe/material shape for rubber: `item.hist-sap-rubber` (kind misc or ingredient, subkind material) + a 2.9b recipe row (input item.hist-sap + a second ingredient, station alchemy or workbench). No code: the 2.9b gate already takes misc/ingredient inputs (2.9b-crafting.md deliverable "recipe gate takes misc or ingredient inputs"). Cost now: two rows. Retrofit cost: low, but cheapest while the recipes table is being authored.
2. `resistShock` on equipment records: confirm gear records can carry a stat effect `resistShock` (effects.ts:33). Insulated glove/boot/prod = item rows with an effect; the wamasu shock-water damage volume (4.5) must be authored as `damageType: shock` volume that reads `resistShock`. Seam: the damage-volume record's damage type and resist link, which belongs to 2.7 creature specials.
3. Sap dose counter: reuse the staged timed entry that `diseased` uses (2.9-magic.md:84-86); allow `source: "sap"` and stage-indexed text, so gold tongue/bark scale are stage labels shown in dialogue conditions (flavour, per 0028). Seam: timed-entry `source` union (packages/game-core/src/stats/timed.ts) plus a dialogue condition on the stage.
4. `marshBorn` (or `hist` id) field on the character/person record: gates whispers/spore/communion; MQ01 creation barge (30-main-quest.md:250) already decides. Seam: character record in docs/world/98-data-model.md and person compiled sheet; cost to retrofit later is high once saves exist (save family versioning).
5. Soul-trap `trappable` flag on species/race (sap-is-soul): one boolean on creature/person sheets, read by `packages/magic/src/soultrap.ts`.
6. `Hist` node record (`HistNodeBlueprint`, 30-lore-systems.md:110-125): add `maturity` (deek/dooka/tsoko), `state` (healthy/severed/rogue/silent), and `eggPools` ids; the one-mind and egg-bond hang off `state` and quest world flags. Check it is a record in 98-data-model before Part 4 packets multiply Hist nodes.

## Most valuable gaps
- hist-sap-rubber (H): wamasu prod/insulated gear; links crafting, swim, wamasu.
- sap-poisoning (M): dose/stage mechanic.
- hist-egg-bond (H as quest stakes), hist-sap-visions (H, 4.5).
- Authoring gaps: rumours/documents for Great Burn, Battle of Argonia, Arnesian War, Heita-Meen.

## Not verified
- Whether 2.14 sound or any slice place already plays Hist whispers.
- Whether character record has a marsh-born field (grep of 76/98/2.8 found none).
- Whether MQ01 creation sets a Hist/home.

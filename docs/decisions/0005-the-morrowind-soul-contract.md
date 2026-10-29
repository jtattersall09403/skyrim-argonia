# 0005: The Morrowind soul contract

**Status:** decided 2026-10-27 (owner's must-haves, [owner-brief](../owner-brief.md) §1.2). Each clause is a
testable acceptance condition. Each clause's first rung is built in Part 1 ([the core loop](../phases/1-core-loop/README.md)) and made whole in Part 2 ([the slice](../phases/2-slice/README.md)); character creation is 3.2.

## The contract

A player who knows Morrowind must recognise it within the first ten minutes, and must never see a Skyrim
system where Morrowind's belongs. Specifically:

| # | Clause | Must be true in game | Tier | Built from |
|---|---|---|---|---|
| C1 | **Dialogue** | NPC talk is a window with the NPC's text, **hyperlinked keywords** in it, and a **topic list** that grows as the player learns topics; topics learned from one NPC can be asked of others; answers depend on **disposition (0–100)**, faction, rank, race, place and quest state; **persuasion** (admire, intimidate, taunt, bribe) moves disposition with Argonia's no-dice thresholds; greetings and essential topics never gated (old 0145). Writing follows the old repo's Morrowind style guide and exemplar corpus | S2 + S3 | ArgoniaCore topic store + condition evaluator; PrismaUI dialogue view; records generated from the old dialogue data |
| C2 | **Attributes and stats** | Seven attributes (Strength, Intelligence, Willpower, Agility, Speed, Endurance, Personality; Morrowind minus Luck) and **27 skills** with major/minor/misc classes, specialisation, favoured attributes, races and 13 birthsigns; Argonia's formulas (old `76-stats-progression.md` §116–129: score = (skill + attr/5)/1.2, k(s) curve, health/stamina/magicka formulas, burden tiers, mitigation) | S2 | Custom Skills Framework for new skills; attributes in reserved actor values; ArgoniaCore formula hooks |
| C3 | **Levelling: rest and vastei** | Skills rise by use; levels bank and are taken **only when resting**; at the **level sitting** vastei is spent on attributes with the old cost curve; **death drops carried vastei as one recoverable pile** at the death spot (dying again replaces it); waking at the last rest; rest is the only save; generic enemies respawn on rest | S1 + S2 + S3 | Sleep to Gain Experience pattern, Respawn – Soulslike pattern, our PrismaUI sitting screen |
| C4 | **Perks** (owner open to merging) | **No Skyrim perk trees or constellation menu reach the player.** Perks survive only as an invisible engine layer (perk entry points are Skyrim's cheapest formula hooks) granted by our system. Decided after the perk audit in 2.1; the owner may instead choose to expose a Morrowind-flavoured perk layer (owner call O-4) | S1 | Perk audit; our perk records |
| C5 | **Weapon and item classes** | Morrowind classes: short blade, long blade, axe, blunt, spear, marksman (bow, crossbow, thrown; decision 0016), hand-to-hand; armour light/medium/heavy; each weapon class trains its own skill | S1 + S2 | Keywords; spear and throwing mods; CSF skill redirect hook |
| C6 | **Separate armour pieces** (nice to have) | Helm, cuirass, left/right pauldron, greaves, boots, left/right gauntlet, shield in separate slots, with Morrowind's weighted armour rating | S1 + S2 | Free biped slots; sourced split meshes only if they exist; otherwise paired pieces (owner accepts "nice to have") |
| C7 | **No markers; directions** | No quest markers on the map or compass, ever; quest givers and locals give **directions written into the journal**; map markers appear only once a place has been reached on foot (old 0137) | S1 + S2 | Wayfinder pattern, No Google Maps plugin, our direction generator against the route graph |
| C8 | **Journal** | A Morrowind-style book journal: dated entries, quest index, and a **topics index** with what each NPC said | S3 | PrismaUI journal view over ArgoniaCore's logs |
| C9 | **Map** | A Morrowind-style paper world map and a local map; no player-position marker unless granted by an in-world act | S1 + S3 | Flat World Map Framework with our own map art (UI exception); PrismaUI local map |
| C10 | **UI** (our own original views, decision 0017) | Morrowind made today, one coherent Argonian design system chosen and refined with the owner (1.2 §0, 1.2; the old palette a starting point), **Pelagiad** font everywhere including vanilla menus, Morrowind-shaped windows (stats, magic, inventory with paperdoll, map) open together, draggable, resizable and remembered on desktop | S1 + S3 | Our font library + fontconfig (0014 §7); PrismaUI views for stats, magic, inventory with paperdoll; other menus per 0014 §7 |
| C11 | **HUD** (our own original, decision 0017) | A custom HUD: souls-style bars (health, stamina, magicka) that grow with stats, sneak eye, equipped-hands plaque, effect stack, vastei plaque; no Skyrim compass | S1 + S3 | TrueHUD/Infinity UI or PrismaUI HUD |
| C12 | **Character creation** | Morrowind's flow: name, race, class (pick, generate by questions, or custom), birthsign, review; no Skyrim race menu as the player sees it | S3 | PrismaUI chargen over the vanilla face sliders (RaceMenu as a dependency only if 0.2 or 3.2 need it) |
| C13 | **Economy, training, travel** | Barter without haggle per the old one-price contract; finite merchant purses restocking every 48 h; trainers capped by the governing attribute (the old design; Morrowind's trainer-own-skill cap is an
  optional addition the owner may approve); Morrowind travel services (boats, ferries, rootworms) instead of carriages; no free fast travel | S1 (+S2 for exact barter) | Data, Papyrus, optional price hook |
| C14 | **Fixed danger** | No level scaling anywhere: fixed encounter zones, placed actors from the D0–D5 bands, fixed loot (old 0004) | S1 | Encounter zones min=max; no levelled lists for hostiles or loot |
| C15 | **Magic, crafting, stealth, crime** | The old repo's designs (casting never fails, spellmaking, enchanting, alchemy always succeeds, smithing tiers, per-observer stealth, the Owing ledger) | S1 + S2 | See 2.9–2.11 |

## Rules

- A clause is met only when it passes in game on the GPU box (testing level L4) and the owner has seen it
  in an owner check-in. A clause cannot be met in a mock or the browser-side UI harness alone.
- If a clause cannot be met at S1/S2, it goes to S3; if it cannot be met at S3, the owner decides the
  compromise. Nothing is silently dropped.

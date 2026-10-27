# P4: Morrowind's soul

**Goal.** Every clause of the Morrowind soul contract ([0005](../decisions/0005-the-morrowind-soul-contract.md),
C1–C15) passes in game, built to the old project's designs, with the owner having played it.

**Starting state.** P2 exit gate passed (pipeline, bridge, view harness, installer). P3 runs alongside; checks
that need the world use the S4 sample block until P3's places land.

**Read first.** Decision 0005 in full; [skyrim-morrowind-soul](../research/2026-10-27/skyrim-morrowind-soul.md)
in full; [audit-systems](../research/2026-10-27/audit-systems.md); imported design docs:
`docs/design/world/76-stats-progression.md` (the spec, ~1,640 lines; §102, §116–129 are binding unless a
decision here changes them), `docs/design/quests/` (00-overview, 20-world-provisions, 30-main-quest,
40-factions, 85-condition-vocabulary), `docs/design/standards/text/` (style guide), the dialogue README and
culture sheets; old decisions 0004, 0007, 0028, 0030, 0031, 0033, 0035, 0037, 0039, 0042, 0091, 0092, 0096,
0137–0139, 0141–0148, 0150, 0151, 0153 (see [inherited-rulings.md](../inherited-rulings.md)).

**Where state lives.** ArgoniaCore (SKSE) owns all new state (attributes, vastei, pending level, learned topics,
dispositions, Owing ledger, knowledge facts, journal log, discovered places) in the SKSE co-save, with a pure
C++ `core/` library holding the rules (unit-tested on Linux, L2). Papyrus is used for quest fragments and glue.
PrismaUI views read and write state through the typed message schema (P2-WP2.8).

## Work packages

### WP4.1 Attributes, skills and the stat formulas (C2)
- **Attributes:** Strength, Intelligence, Willpower, Agility, Speed, Endurance, Personality (no Luck), stored in
  reserved actor values. Choose between obsolete AVs and `Variable01`–`10` by checking which vanilla and
  dependency scripts read each (record the audit); fall back to co-save values with mirrored globals for
  conditions.
- **27 skills** (Morrowind's, Armorer → Smithing). Reuse vanilla skill AVs where the meaning matches; add the
  rest with Custom Skills Framework; hide One-handed, Two-handed and Pickpocket from the player:

  | Morrowind skill | Implementation | | Morrowind skill | Implementation |
  |---|---|---|---|---|
  | Block | vanilla Block | | Alchemy | vanilla Alchemy |
  | Smithing (Armorer) | vanilla Smithing | | Alteration | vanilla |
  | Heavy Armor | vanilla | | Conjuration | vanilla |
  | Light Armor | vanilla | | Destruction | vanilla |
  | Medium Armor | CSF | | Illusion | vanilla |
  | Blunt Weapon | CSF | | Restoration | vanilla |
  | Long Blade | CSF | | Mysticism | CSF |
  | Axe | CSF | | Enchant | vanilla Enchanting |
  | Spear | CSF | | Security | vanilla Lockpicking (renamed) |
  | Short Blade | CSF | | Sneak | vanilla (includes pickpocket, as Morrowind) |
  | Marksman | vanilla Archery (renamed; bows, crossbows, thrown) | | Speechcraft | vanilla Speech |
  | Hand-to-hand | CSF | | Mercantile | CSF |
  | Athletics | CSF | | Acrobatics | CSF |
  | Unarmored | CSF | | | |

- **Formulas** from 76 (exact text there wins): score = (skill + attribute/5)/1.2; k(s) = 1 − (1 − s/100)^1.6;
  max health = (Str + End)/2 + level × End/10, retroactive; stamina max = 60 + 0.8 × End up to End 50, +4 per
  point above; stamina regen 12 + 0.24 × Agi per second after a 1.05 s delay; magicka = 20 + 3 × Int; carry
  capacity 30 + 3 × Str kg with burden tiers by carried/capacity (fast < 0.2, mid < 0.35, fat < 1, overloaded);
  armour mitigation AR/(AR + 135.6 + 0.6 × damage); light/medium/heavy ×0.75/0.9/1.0; material ladder steel 1.0
  to daedric 4.4; Speed drives movement (SpeedMult); no wield requirements, soft requirements (stamina ×(1 +
  0.07d)); difficulty knob scales enemy damage only (0.7/1.0/1.35).
- One StatEffect stack (field, op, magnitude, source) for races, signs, disease, potions, spells, enchants,
  mapped onto Skyrim magic effects where they exist and ArgoniaCore modifiers where not.
- Burden tiers also select the roll tier for combat (P5).
- **Acceptance:** L2 tests port the old `balance.test.ts` cases and the ladder table (`ladder-table.md`) and
  pass; L4 scenario reads every derived value for 5 test characters and matches the formulas.

### WP4.2 Skill use, vastei, levels at rest, the sitting (C3)
- Skills grow by use "in anger" with the old worthiness anti-grind rules (76 §120.2); **vastei** accrues per
  qualifying use (= 4 × worthiness × (1 + effSkill/50)); trainers and skill books grant ranks and **no** vastei;
  quest rewards and looting never grant vastei.
- 10 major/minor ranks → one pending level (early levels faster per old 0147: ranks per level ramp 1, 2 … 8 —
  check 0147's exact curve); misc ranks or ranks in a skill at 100 count 1:3; no practice discount, no
  repeat-target damping (old 0037); level 2 in 15–30 minutes, level 10 in about 4–6 hours, no cap.
- Levels are taken only when resting: the **sitting view** (PrismaUI) spends vastei on attributes at cost
  40(1 + lvl/10)^1.3 × (1 + attr/50)^2 × (1 + 0.5(n − 1)), max 5 points per attribute per sitting; health
  recomputes; Endurance bought at the sitting.
- Vanilla level-up and XP are suppressed (Skill Uncapper/Experience patterns as references; Sleep to Gain
  Experience's banking pattern, source on GitHub).
- **Acceptance:** L2 tests for every formula; L4 scenario: play 15 minutes of scripted skill uses → pending
  level → rest → sitting opens → spend → values change.

### WP4.3 The perk audit (C4, owner call O-4)
- Enumerate every PERK and skill tree in the load order; classify each: (a) a mechanic we need as a hidden engine
  ability (sneak multipliers by weapon band, armour bonuses, etc.: implement our rules through perk entry
  points where that is the cheapest hook), (b) a player-facing choice to remove, (c) Nordic text or icons.
- Hide the perk/constellation menu entirely; our stats screen replaces it.
- Present the audit and the recommendation (invisible engine layer only) to the owner as O-4; if the owner
  prefers a visible Morrowind-flavoured perk layer merged with vastei, design it as a P4 addendum.
- **Acceptance:** no perk menu reachable; every vanilla perk has a verdict in the immersion inventory.

### WP4.4 Rest, saving, death, respawn (C3)
- Rest: camp anywhere calm in the wild; never in a dungeon, in combat, while hunted, or inside a settlement
  (towns: wait only); beds by tier (camp < rented < owned): rented gives a "rested" entry ×1.05 skill XP for 8
  game hours, owned ×1.08; a camp gives only the sitting.
- **Rest is the only save**: manual saves, quicksave and autosaves are hidden from the player; rest writes the
  save; a hidden suspend-save on quit protects against stream drops and crashes (old 2.13 intent).
- **Death:** intercept death (Respawn – Soulslike pattern, permissive licence; bleedout interception), wake at
  the last rest with the world persisting; skills, levels, items and gold kept; carried vastei drops as **one**
  pile at the death spot (a second death replaces it); within 2 m a prompt "Take Vastei (N)" takes it all back;
  the pile shows as a gold ring with a halo and rising wisps (old `deathPileMarker` design, built from vanilla
  effect shaders).
- **Respawn on rest:** generic enemies respawn on rest; named actors, bosses and placed treasure never; a cleared
  dungeon stops respawning (old 0031).
- **Acceptance:** L4 scenarios for each rule; save/load round trip keeps every co-save value.

### WP4.5 Races, birthsigns, classes, character creation (C12)
- Races: Skyrim's ten with Morrowind-style packages (old 0096: one race record keyed by the roster with
  Morrowind's packages); Argonians breathe water; sex is an axis (old 0054).
- Birthsigns: the 13 replace the standing stones (stones removed from the world).
- Classes: the old presets plus custom and the question-generated class (Morrowind's questions rewritten for
  Black Marsh); 5 major, 5 minor, specialisation, 2 favoured attributes.
- Chargen flow (PrismaUI): name → race (vanilla face sliders behind our frame) → class → birthsign → review;
  placed inside the opening (P7) as Morrowind's census scene is.
- **Acceptance:** L3 harness tests for each step; L4 new-game scenario reaches the opening with the chosen sheet.

### WP4.6 Dialogue runtime (C1)
- Production version of G5: intercept vanilla dialogue for every Argonia NPC; the dialogue view with greeting,
  hyperlinked keywords, a growing topic list, services (barter, training, travel, spells, repair, spellmaking,
  enchanting) opened from the window as Morrowind does, persuasion (admire, intimidate, taunt, bribe 10/100/1000)
  with the old no-dice thresholds, Goodbye.
- **Condition evaluator** covering the whole old condition vocabulary (`85-condition-vocabulary.md`: ~50
  predicates, ~40 actions), including the ones Skyrim lacks: knowsTopic, topicHeardFrom, witnessed,
  evidenceState, custody, rumourActive, firstTime, daysSince, owingAtLeast, placeStanceIs, histStepAtLeast,
  speakerCulture, settlementStanding, seenBy, successorActive, localVariantActive. Native Skyrim conditions are
  used where they exist (GetStage, GetItemCount, GetFactionRank, GetInCurrentLocation, GetCurrentTime, GetDead,
  GetDetected, GetIsCurrentWeather…).
- **Disposition** 0–100 per NPC: base from race, faction (half of reputation), Personality, Speechcraft; changes
  the talk but never gates greetings or essential topics; floor 0; daily recovery (old 0145).
- Barks and idle chatter as subtitles, from the old bark lines; no vanilla Nordic barks (decision 0012).
- **Acceptance:** L2 tests per predicate and action; L3 view tests; L4 scenarios: topic learned from A asked of
  B; disposition variants; persuasion moves disposition; services open; an essential topic at disposition 0.

### WP4.7 Dialogue and text content
- Flatten the imported dialogue (14 place files, 1,471 lines for ~89 people; 569 pool lines; 317 topics; 551
  facts; 96 glossary entries; the culture-sheet hierarchy province > region > people > faction > office >
  settlement > group > household) into ArgoniaCore's runtime data, preserving low/high disposition variants and
  "facts once, opinions per person" (old 0139), "anyone may explain; restatement near-verbatim only" (0143), no
  two identical sentences.
- Text catalogue: every player-visible string from one keyed catalogue (journal, books, signs, place names,
  item names, spell names, loading facts, hydrology names), checked by the prose linter and the `text-review`
  skill against the style guide; the Morrowind exemplar corpus guides new writing.
- Dialogue writing (new lines for new NPCs) runs the `dialogue-write` skill on **Sonnet** (old owner ruling),
  with voice-reader panels and corpus reads.
- **Acceptance:** every imported line reachable in game for its speaker (L1 data check plus 20 sampled L4 talks);
  linter green.

### WP4.8 Quests as data, directions, no markers (C7)
- Quest generator: stage graphs (stages 10, 20…, onEnter actions, objectives, successors, fail-forward,
  endings) → QUST records with stages, log entries, objectives and aliases, plus generated Papyrus stage
  fragments; non-native conditions and actions call ArgoniaCore; tier protection (main > faction > side, old
  0030); nobody is unkillable (old 0138), so every quest has a fail-forward for a dead NPC.
- Import the 38 staged quests now; the rest are authored in P9.
- **Directions generator:** quest givers' directions are written into the journal from the P3 route graph
  ("follow the road west past the broken column, then take the left fork to the river"), checked by a validator
  that walks the described route in data (old 0153).
- **No markers:** quest targets have no map or compass markers (No Google Maps plugin; objective target data
  omitted; compass removed in WP4.10); map markers for places appear only after the player reaches them on foot
  (old 0137); grantable markers only through in-world acts (a guide marks your map).
- **Acceptance:** each imported quest runs start to end in an L4 scenario; the direction validator passes for
  every direction text.

### WP4.9 Journal, world map, local map (C8, C9)
- Journal view (PrismaUI book): dated entries, quest index, topics index (every learned topic, what each NPC
  said, from ArgoniaCore's dialogue log), directions; a Black Marsh book look with ribbons and filters (old 2.2).
- World map: Flat World Map Framework with the P3 painted map image; discovered markers only; no player-position
  marker unless granted.
- Local map: a PrismaUI paper-style local map from our own data (cell geometry outline, buildings, roads),
  replacing Skyrim's local map.
- **Acceptance:** L3 tests; L4 scenarios open each and read state.

### WP4.10 UI skin, Pelagiad, HUD (C10, C11)
- **Pelagiad everywhere:** replace the vanilla font set through `fontconfig.txt` and font SWFs (the standard
  font-replacer method), verifying every vanilla menu in the stack renders Pelagiad (screenshot sweep).
- Vanilla menus kept (inventory, container, barter, magic, crafting, lockpicking if kept, tween/system menus) are
  restyled through SkyUI 6/Infinity UI SWF skins to the palette; screens that Morrowind shapes differently
  (stats/character sheet, magic list with schools, spellmaking, enchanting where different) become PrismaUI views.
  Choose per screen by reuse order (0010) and record it.
- HUD: souls-style bars top-left that grow with stats (health, stamina, magicka, breath), sneak eye (four states:
  hidden/caution/danger/detected), equipped-hands plaque bottom-left, effect stack bottom-right, vastei plaque,
  toast queue, place-discovered banner, floating prompt with input glyph; no compass; boss bars via TrueHUD
  restyled. Gamepad and keyboard prompts both.
- **Acceptance:** screenshot sweep of every menu and HUD state at 1080p and 720p; reader panel against the old
  ui-lab references (`apps/ui-lab` shots in the old repo) and the Nordic-tells checklist.

### WP4.11 Items, weapon classes, armour pieces, condition (C5, C6)
- Import the 508 items (class × material, soft requirements, tempering grades) into WEAP/ARMO/ARMA/MISC/BOOK
  records; weapon class keywords drive the skill used (CSF redirect hook from vanilla One/Two-handed XP).
- Spears and throwing weapons through dependency mods (Animated Armoury/Armory Extended pattern, Throwable
  Weapons SKSE); crossbows vanilla; Argonian weapon packs (P2 manifest).
- Armour slots: helm 30, cuirass 32, pauldrons 57 (+46/47/59 for the second side), greaves 49 or 53, boots 37,
  gauntlets 33 (+58/59), shield 39; body meshes must not include arms/legs where those slots are separate.
  Separate left/right meshes only where a sourced mod ships them; otherwise paired pieces in separate slots
  (O-9). Morrowind's weighted armour rating by slot as an S2 hook.
- **Condition 0–100** (Skyrim has no durability): ArgoniaCore tracks condition per item instance; a weapon at 0
  is unusable; repair by Smithing and repair services; full damage above 0 (76 §128.2).
- Off hand holds a shield, a weapon or a light (old 0091, native); quick belt via favourites/hotkeys restyled.
- **Acceptance:** L4 scenarios: each class trains its own skill; slots stack correctly; condition decays and
  repairs.

### WP4.12 Economy, training, services (C13)
- Barter without haggle: buy = base × clamp(1.35 − advantage/200, 0.8, 1.35), sell clamp(0.55 + adv/200, 0.55,
  0.95) with Morrowind's pcTerm advantage (S2 price hook; game settings as the S1 approximation if the hook
  fails); finite purses by trade class (general 750, smith 1,000, …, rich 9,375) × place tier (city 1, town
  0.75, village 0.5), refill every 48 h; one price contract: coin, goods or a favour (old 0141).
- Training: 10 × skill gold per rank, trainer's own skill as the cap and the governing attribute as a cap;
  `iTrainingNumAllowedPerLevel` set to match the old design; skill books +1 rank each (5 per skill).
- Services: repair, enchant, spellmaking, recharge, cure, guides, ferries, tolls; spells 2 gold per magicka.
- **Acceptance:** L2 price tests; L4 barter scenario reads prices for 3 merchants at 2 dispositions.

### WP4.13 Travel services, no fast travel (C13)
- 23 services (ferry, boat, canoe, rootworm) from `travel-services.json` as dialogue services: flat fare,
  arrival instantly with time passing over the defined graph (MoveTo pattern of vanilla carriages); the rootworm
  "Underground Express" as a scripted service; no generic fast travel (`EnableFastTravel(false)`), map travel
  disabled.
- **Acceptance:** each service in an L4 scenario.

### WP4.14 Fixed danger, encounters, respawn (C14)
- Encounter zones with min = max per place danger band (D0 safe … D5 deep core); actors compiled from the 76
  §128 ladder (D1 health 18–28 … D5 96–205; "blows that kill you" 6/4/3.5/3/3) for every actor through one stat
  schema (old 0144); the 217 hostile records and loadouts; no levelled lists for hostiles or loot; fixed placed
  loot from `lootTable`.
- Roaming bands from the per-region table (old 0142; 0.83–1.06 per km was the old measured density); hostile
  places attack on sight; violence answered by the victim's kin; generic respawn on rest (WP4.4).
- **Acceptance:** L1 compile tests; L4 scenario samples 50 encounters for band-correct stats.

### WP4.15 Magic (C15)
- Casting never fails; a spell is castable iff 2 × school + Willpower/5 ≥ cost (working spells ~60% of the limit,
  the 50-point reliable line); magnitude scales 0.75–1.25 with skill; spell damage bypasses armour; Willpower/4 %
  innate resist; cost reduction capped at 75%; spells in hands (Skyrim native) with hold-charge and dual-cast
  ×2.2 magnitude ×2.8 cost; stream spells; casts interrupted by poise break (P5); powers once a day; Hist
  communion powers race-neutral (old 0042) on the power slot freed by shouts (decision 0012).
- Import 300 effects and 876 spells (old packages/magic) with Morrowind names, mapped onto MGEF archetypes;
  Mysticism effects (detect, soul trap, dispel, telekinesis, absorb) as far as Skyrim supports them.
- **Spellmaking** (up to 8 effects, fee 7 × cost) as a PrismaUI service screen over SKSE spell creation;
  enchanting points = (Enchant + Int/5)/3, constant effects tiered by soul size, disenchant teaches the effect.
- Levitation: try an S2 implementation (flying controller); if not feasible within its time box, drop it and
  record the loss (Morrowind had it; the old design copied its speed from OpenMW).
- Spell sellers carry a sheet, never the catalogue (old 0148); folk sellers, no guilds.
- **Acceptance:** L2 castability and magnitude tests; L4 casting scenarios including dual-cast and a spellmade
  spell.

### WP4.16 Crafting
- Alchemy always succeeds; effects revealed at skill 15/30/45/60; potions are the healing economy (no estus);
  weapon poisons and oils coat the next hit; smithing = repair + temper (3 grades, +8% at 25/55/80) + forge
  (tier 1 + floor(skill/14)); 7 stations, 154 recipes, 8 material tiers; resource nodes; fortify-crafting
  loop allowed but scarce (old 0150).
- **Acceptance:** L4 scenario per station.

### WP4.17 Stealth, crime, locks, the Owing (C15)
- Per-observer detection (Skyrim's detection tuned toward the old model: light, gait noise, armour weight, view
  cone, line of sight, Sneak + Agility/5 vs spot) with the four-state eye; search then give up; alarm radius;
  submerged players break sight.
- Sneak blows multiply by weapon band (dagger ×3–15, bow ×2–8) and **never auto-kill** (sneak killmoves off).
- Crime exists only when seen; the **Owing** ledger per region replaces bounty/jail: pay gold, serve custody
  (advances the clock, costs pending skill progress), or resist; trespass zones with hours; locals challenge
  where there is no watch (old 0039/0151).
- Locks are a threshold, (Security + Agility/5) × tool ≥ lock level (S2 hook replacing the lockpicking minigame,
  as Morrowind had none); traps as data; pickpocket is the one seeded gamble.
- **Acceptance:** L4 scenarios for detection states, a sneak blow, each Owing path, a lock threshold.

### WP4.18 Factions and reputation
- 32 factions with ranks as reputation ceilings (associate 0, member 10, senior 40…), reputation −100 to 100,
  crime against a member lowers standing with all; allegiance rites as permanent packages (old 0028); no
  followers.
- **Acceptance:** L4 scenario joins, rises and is expelled.

### WP4.19 People's lives: schedules and the lamp clock
- Day blocks → AI packages with hour windows (rise 05:30, work 06:30, meal 12–13, home 17:30 when lamps light,
  bed 22:00, per-person jitter, role exceptions, predator hunt blocks); shops lock; NPCs walk the path network.
- **Acceptance:** 24-hour time-skip scenario in Greenspring: each NPC is where its schedule says at 6 sampled times.

### WP4.20 Owner packets
Three packets as each group lands: (1) chargen, stats, levelling, death; (2) dialogue, quests, journal, map, UI,
HUD; (3) economy, travel, magic, crafting, stealth, factions, people. Each: what to try, where (save provided),
how to reply; blockers vs polish per the rules in ways-of-working.

## Exit gate
C1–C15 each pass their acceptance and have been seen by the owner; the soul packets have no open blocker; the
immersion inventory has verdicts for every vanilla system P4 replaced or hid.

## Risks and fallbacks
- **Intercepting vanilla dialogue** for every NPC is fragile: keep a vanilla-menu path that still works (Skywind
  style) behind the view, so a broken view never strands a quest.
- **AV conflicts** with dependency scripts: the AV audit in WP4.1; co-save values as the fallback.
- **Scope**: P4 is the biggest phase; ship it in the three packet groups, never as one batch.

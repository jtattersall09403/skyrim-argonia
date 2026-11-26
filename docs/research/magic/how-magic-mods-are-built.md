# How magic mods are built, what each technique costs, and what already exists (for owner issue #104)

Written 2026-11-26. Part of the research for a more Argonian, lore-friendly magic flavour. This part answers: how modders
build magic, what each technique costs us, and what we could take. The design question (what Argonian magic should be)
belongs to the other parts.

## 0. Live docs, and what this page supersedes

- [lane-1.12-magic.md](../mods/lane-1.12-magic.md) is the live record of Magic Expanded (Nexus 133435) in our stack:
  152 SPEL, 191 MGEF, 140 tomes; 12 Nordic-flavoured effects renamed at data load by `mod_form` rows; its tomes never
  reach Black Marsh (no spell-selling trade class). **Confirmed** (read, not re-measured). It matters here because it
  already proves the cheapest technique below (rename and re-describe by code, at data load, with no edit of the
  author's plugin) and shows the gap that every spell-tome technique meets: spells must be put in a seller's hands.
- [lane-1.12-magicpane.md](../mods/lane-1.12-magicpane.md) is the live record of our magic pane (six schools, powers
  in the voice slot) and of `trade_class_mod_stock` (13 Magic Expanded tomes for `trade-class.general`, added to each
  trader's merchant chest at data load). **Confirmed**; it is the existing route for "who sells what".
  **Supersede nothing**; the one doc the writer of the #104 proposal should edit is the lane-1.12-magic.md "Reach in
  Black Marsh" section (or its successor design doc), not a new file.
- [morrowind-level-scripting.md](../morrowind-level-scripting.md) says nothing on spell data (it covers quest
  scripting); only its note that GetPCIsRace is missing from the allowed conditions (lines 145, 189-191) touches
  racial conditions, and that is about dialogue lines, not spell conditions.
- `mods/dependencies.json` rows already installed that bear on magic: `magic-expanded`, `magistrate-levitate`,
  `spid` (7.3.3, MIT), `po3-papyrus-extender`, `po3-tweaks`, `skyui`, `mcm-helper`, `sleeping-hist-tree`. No
  Mysticism, Odin, Apocalypse, Triumvirate, Ordinator or KID row exists.
- How permissions are recorded (`mods/sourcing-register.json`): a row with `licence`, `linked_or_forked_by` and a
  `notes` line that starts "permission:". The rule used for Magic Expanded is the one to copy: **a mod the player
  downloads and we only reference needs no grant; copying its records, scripts or assets needs the author's
  permission** (register row for Nexus 133435; decision 0003 clause 4).

**Method limits (honest):** nexusmods.com returned HTTP 403 to every fetch, as did ck.uesp.net and web.archive.org.
The Nexus API (key from `tooling/nexus_search.py`) returns name, author, version, downloads, description text and
files, but **no Permissions-tab field** (GraphQL type `Mod` has none; v1 JSON has none). So permission status below
is "UNREAD, owner or a browser must open the Permissions tab" unless a licence is in our register or the description
itself says something. Record-structure statements in sections 1 and 3 are from UESP page titles and snippets seen
in search, from Nexus author descriptions (cited by id), and from general knowledge of the Creation Kit; where I did
not see a source I say "from knowledge". Vanilla magicka costs are not quoted because Skyrim.esm is not on this
machine; section 4 says how to measure them (xEdit on the play machine).

## 1. The anatomy of a spell in Skyrim's data

**Chain of records** (UESP CK "Magic Effect" and "Effect Item" pages; Tes5Mod MGEF/EFSH format pages):
SPEL (the spell: name, cost, type, casting type, delivery, charge time, equip slot, perk, keywords, list of effects)
-> EffectItem rows (magnitude, area, duration per effect; the CK says casting type and delivery are set by the
parent object and restrict which magic effects can be chosen) -> MGEF (the effect: archetype, actor value, flags,
art, light, shaders, sounds, projectile, explosion, impact data, conditions, keywords, optional Papyrus script).

**Archetypes** (MGEF "Archetype" field; from knowledge, the CK page itself was not reachable): Value Modifier (changes an
actor value every second, or once and back when "Tapering"/recover flags are set; UESP: "if checked, Value Modifier and
Peak Value Modifier archetypes will modify their actor value once at the start, then modify it back once the Effect
expires"), Peak Value Modifier (a value bump held for the duration), Script (UESP: archetypes occur "in addition to
any scripted effects that may result from the Papyrus Script on the MagicEffect" - a script runs on start, tick and
finish), Dual Value Modifier, Absorb, Summon Creature, Cloak (a repeating area effect around the caster), Light,
Paralysis, Invisibility, Demoralize/Frenzy/Calm/Rally (Illusion), Cure, Reanimate, Bound Weapon, Telekinesis, Detect
Life, Darkness, Night Eye, Slow Time, Banish, Disarm, Stagger, Guide, Soul Trap, Turn Undead (UESP talk: hard-coded to
fail unless the target has the ActorTypeUndead keyword), Spawn Hazard, Vampire Lord, Werewolf, Grab Actor, Enhance
Weapon. The point: **almost all behaviours Argonian-flavoured magic needs (poison
damage, resist, regenerate, water breathing, summon beast, fear, calm, bound weapon, light, paralysis, drain) are stock
archetypes; only novel mechanics (transform, teleport variants, "react to sap") need a Script archetype.**

**Delivery** (Self, Touch, Aimed, Target Actor, Target Location) and **casting type** (Constant Effect = ability that
never ends, Fire and Forget, Concentration) are chosen on the SPEL; a spell with type "Lesser Power" or "Greater Power" is
a power (voice slot, cooldown), type "Ability" is always-on, "Voice" is a shout. **Projectile** (PROJ: model, speed,
gravity, explosion, trail light, sounds), **Explosion** (EXPL: radius, damage, impact data, art), **Hazard** (HAZD: a
placed area that applies a spell on a timer; vanilla uses it for fire pools and traps), **Impact Data Set** (IPDS:
decal and sound per surface), **Art Object** (ARTO: cast, hit and enchant visuals; nif with a node), **Effect Shader**
(EFSH: a shader laid on the hit actor or object), **Light** (LIGH), **Sound** (SNDR descriptors). **Keywords** classify
(MagicSchoolFire, MagicDamageFrost, MagicCloak ...) and drive perks and AI; **perks** (PERK) scale by keyword
condition; **conditions** on the SPEL's effect row or on the MGEF gate whether it applies (section 3.5).
**Spell tome** = BOOK record with "Teaches Spell" (no script; also works for powers, see 3.4);
**spell vendors and loot** = leveled lists (LVLI, vanilla `LItemSpellTomes*`) and vendor-faction chests; **NPC use** =
the actor's spell list plus its combat style (CSTY) and AI.

**Record-only changes** (no script, no plugin DLL), from knowledge and lane-1.12-magic.md:
- every field above on a new SPEL/MGEF/PROJ/EXPL/HAZD/ARTO/EFSH/LIGH/PERK/BOOK/LVLI record, and overrides of the
  vanilla records;
- renames and descriptions (FULL, DESC); keywords; spell cost and magnitude edits;
- tomes teaching spells and powers; vendor stock via leveled lists or merchant chests;
- race ability lists (RACE record spell list), perks, standing-stone-like abilities if carried by a spell;
- potions, poisons, ingredients, scrolls and staves (ALCH, INGR, SCRL, WEAP+ENCH).
**Needs a script (or SKSE/SPID):** adding a spell to the player or to leveled lists at run time without editing
records, "grant a power when I touch this activator", spell effects that do things no archetype does (Script archetype),
research/experience systems, forms (Triumvirate's Horned Lord transform uses a script; Phenderix Elements forms).

### 1.1 What a recolour really takes

Visible colour comes from four places; each has a different cost:
1. **EffectShader (EFSH) records.** UESP CK "EffectShader" (search snippet): fill and edge sections have a **colour used only when no texture is
   selected**; a selected texture scrolls over U/V; **particle colour keys** set tint and alpha at a time (first key time
   above 0 means the raw texture colour at start; last key below 1.0 returns to raw colour). Changing these is
   **record-only and per-record**: a new EFSH plus a changed MGEF reference. This recolours the shader laid on a hit
   actor, the hand glow's *shader* (not its nif) and the particle layer where the shader owns it.
2. **Light (LIGH) records** and the MGEF "light" field: colour, radius, fade. Record-only; this is what lights a
   marsh with green instead of orange when a spell is cast.
3. **Gradient and greyscale textures** referenced by effect nifs. Nexus forum guidance seen in search: in NifSkope, on
   the BSEffectShaderProperty, "change the Greyscale Texture, which is the gradient affecting the spell's color; the
   gradients are in the effects/gradients folder and must be extracted from the meshes archive". **Caveat the same
   thread states: editing a shared texture or nif changes every spell that uses it**; a custom spell can still link default
   textures. So a recolour by file = a **new** nif copy plus a new dds, and the SPEL/MGEF/PROJ point at the copy.
4. **Particle (.nif particle systems and PSYS-like blocks)** use per-nif colour fields: needs NifSkope or a script.

Our rule (decision 0003 clause 2, "any Bethesda file ... converted or not"): nothing derived from a game file may sit in the
repo or release. A recolour of (3) and (4) therefore has to run **on the player's machine at install time** on
files the player owns, writing into an output folder the installer lays (as the project already does for flat images:
`docs/research/new-art/nature-and-vessels.md:28` "recolour sick-Hist variants by texture swap"; `...:122` KoTM leaves
recoloured via `recolour.json`, owner call L15). That is a code-only job: open dds (BC7/BC1) from the BSA, shift hue in
HSV with a fixed matrix, write a new dds; for a nif, rewrite the greyscale-texture path string and (optionally) the
vertex-colour/emissive colour field, saved as a new nif under our own path. Cost per effect: small once the pipeline exists;
the pipeline is the work (nif edit in code needs a library, e.g. pyffi/nifly; not tested here). **(1) and (2) need no
file at all and are the first stop; (3) and (4) only where the colour is baked into a gradient or the mesh.** UNPROVEN
in this repo: no recolour of a spell effect has been done; the hue shift of a greyscale gradient (a ramp) is not
the same as hue-shifting a coloured flame texture, so test one cast in game first.

## 2. Survey of spell packs (what each teaches)

Numbers are from the Nexus API on 2026-11-26 (`tooling/nexus_search.py`, v1 description text); downloads are
Nexus unique downloads where shown; "perm." is the Permissions tab, UNREAD unless stated.

| Mod (Nexus SSE id, author) | Size and structure | Distribution | Scripts | VFX | Perm. | 1.6.x |
|---|---|---|---|---|---|---|
| **Apocalypse** 1090, Enai Siaion v10.3.0 (2026-08) | 175 spells, 53 MB; Master tier gated by College ritual quests; MCM; add-ons: Waterstride (72243, Velgath, 3 KB), More Apocalypse (18578, 20 spells), patches for Vokrii, Ordinator | tomes in leveled lists/vendors; NPCs deliberately **not** modified ("would cause unacceptable compatibility issues"); NPC use via oyvveg's SPID mod 58017 | "Low script load, no save bloat" (author) | custom, high quality | UNREAD | updated 2026-08, current |
| **Odin** 46000, Enai Siaion v3.2.0 | rebalances vanilla spells, makes scrolls and staves viable, 125 new spells; 31 MB | tomes, Winterhold-college vendors (patch 55919) | low (author) | partly reused, partly new | UNREAD | current |
| **Mysticism** 27839, Simon Magus v2.5.0 (2026-08) | complete overhaul: balance of vanilla + new archetypes (Mark/Recall, waterwalk, open lock, Burden, Corrode Armor, Weakness to Fire, Master destruction), 11 MB | tomes; Triumvirate/Apocalypse patches exist | moderate | mostly reused | UNREAD | current |
| **Arcanum** 23488, Kosorsomesaykosm v4.0.1 (2021) | >200 spells; ~510 MB; rituals, glyphs, blood magic, zombies/necro; "many require rituals or setup"; Patreon walkthrough | tomes/vendors | **heavy** (script-driven rituals; Borgut1337 id 93437 optimises its scripts) | very high, all custom | UNREAD | works on 1.6 per community; old |
| **Triumvirate** 39170, Enai Siaion v1.8.0 (2022-04) | **75 spells in 5 archetypes (druid, shadow mage, warlock, cleric, shaman)**; 47 MB; Horned Lord form (Force of Nature), Night Gate portals, Obedience; patches: Adamant, Mysticism | "available immersively through vendors" | "Lightweight scripts, no save bloat" | mixed | UNREAD | works; old file but widely used (1.41M DL) |
| **Natura** 77826, Darenii v4.0.5 (2024-03) | nature pack "balanced around vanilla"; 100 MB; novice stone/water/wind sprays and runes (8 dps), summons (Frostbite, Albino spiders); Hive staff; Spriggan add-on | tomes; **SPID** for NPCs (Forsworn files) | moderate | new | UNREAD | current |
| **Venomancy** 146585, Surge101ex (2025-07) | 40 Destruction/Restoration + 77 Conjuration + 11 Alteration + 8 Restoration spells, two perk trees, shouts, bosses; Destruction **or** Restoration version | tomes in leveled lists via script; built-in SkyPatcher | script + perk | custom | UNREAD | current |
| **Poison Spells** 25497, Jay093 v0.4 (2019); **Plague** 62807, Darenii v1.4 | poison as an element (35 MB, perk-gated); Plague = 4 poison spells for Mysticism; SPID file for witches | tomes | low | new | UNREAD | old |
| **Elemental Destruction Magic Redux** 37211, reaperix (revised by another author with reaperix's permission, per its description) v1.2.0 (2022) | adds **earth, water, wind** destruction and conjuration; 16 MB, ESL flagged; tomes put in leveled lists by a one-time script; vendor gating by skill | script at game start | low | new | UNREAD | works; water hand VFX replacer 56657 |
| **Forgotten Magic Redone SE** 12711, 3jiou/Sward66 v1.0 | spells gain experience and unlock new effects; paladin spells; SKSE+SkyUI; 9 MB; "Cast Spells as Lesser Powers" patch | tomes | **heavy** (per-spell experience) | custom | UNREAD | 2022; works |
| **Shadow Spell Package** 13299, Teneb Kel 5.02SE (2018) | shadow-themed (drains, DoT, debuffs) with perks; needs Dawnguard + SKSE; leveled lists populated by script "so compatible with everything around"; resources borrowed from Apocalypse | script into leveled lists | medium (ticking dots) | borrowed | UNREAD | old; tweaks 78296 |
| **Phenderix Elements** 78034 | 11 toggleable elemental forms + spell-learning by using your own spells; 2026-03 | learned by use | script heavy | custom | UNREAD | current |
| **Spell Research** 20983, IronDusk33 v2.2.3 (2023) + Spellforge 46482, Arctal (2024) | research theses, tome/scroll crafting from any spell mod; Spellforge = a placeable crafting station that replaces tome buying and filters by school | replaces tomes | script | few | UNREAD | current |
| **Wintersun** 22506, Enai Siaion v3.3.0 (2026-09) | religion: pray at shrines, **choose a deity "based on your race"**, tenets, blessings, follower abilities; 52 MB; "Lightweight scripts"; Tribunal Integration 63012 adds Morrowind's gods (UNREAD whether Argonian deities exist) | shrines | light | reused | UNREAD | current |
| **Thunderchild** 1460, Enai Siaion v4.11SSE (2017) | **29 shouts** as a parallel system, Words unlocked by buffs; MCM; 42 MB | shrine/words | script (the author warns of script delays) | custom | UNREAD | works, old |
| **Imperious** 1315 (v7.28.0), **Morningstar** 22298, **Freyr** 88043 (standing stones as race bonuses) / **Aetherius** 26686 (v ..2026-07, Simon Magus) / **Mundus** 33411 / **Heritage** 129813, Sami (2025-10) / **Amazing Race Tweaks - Argonian** 94048, Sp0ckrates (2023) / **Argonian Upgrades** 48524, WinsomeMinotaur (2021) | racial powers. Argonian content verified in the descriptions: Imperious "Histborn: below 20% health/magicka/stamina you regenerate half the difference per second"; Aetherius "Histskin: poison and disease resist +50%, potions last 50% longer"; Heritage "Histskin: regenerate an extra 1% max health per second"; Freyr: Argonian Thief "Chameleon: 25% harder to detect standing still", Warrior "Histskin +2% max health regen/s", Apprentice "Regrow Limbs: 5% regen below 25%"; ART: Shadowscale power, improved Histskin, Hist Assist (cheaper Restoration); Argonian Upgrades: level-scaled heat vision, venom, claw damage, poison resist, **"uses no scripts"** | SPEL on the RACE record; Imperious "NPCs can use them too" | none to light | none | UNREAD | current; Imperious/Aetherius/Heritage edit race records ("only one mod can modify race records at a time", Imperious text) |
| **Sacrilege / Sacrosanct / Growl** 42408, 3928, 31245 | themed power sets for vampires and werebeasts; same author family | perk-like abilities | medium | custom | UNREAD | current |
| **Apothecary** 52130, Simon Magus v1.3.9 (2024) | alchemy overhaul; poisons replicate Illusion's influence effects; 106 KB (records only), "Weakness to Poison" boosts poisons | ingredients/vendors | **record-only** | none | UNREAD | current |
| **Skyrim Scroll Crafting** 152, Scroll Scribe 110190, Agent of Mora 21640 | scroll/tome crafting | crafting | script | none | UNREAD | works |
| **Spells as Lesser Powers** 2697 (NOUARX), Cast Spells As Lesser Powers 65398 (AndrealletiusVIII), Candlelight and other minor spells as lesser powers 19603 | tomes teach spells as lesser powers (the power slot) | tomes | record-only/ light | none | UNREAD | works |

**Argonian-themed magic: none found as a pack.** Searched the Nexus API (both Skyrim domains) for: Argonian spell,
Argonian magic, Argonian racial, Argonian abilities, Hist, Histskin, Hist sap, Hist tree, Shadowscale, Black Marsh, swamp, spore,
venom, voodoo, witch doctor, shaman, druid, nature magic/spells, water spells, poison spells, Sithis, totem, ritual,
blessing, shrine, Beyond Skyrim. Found only (a) racial-power rewrites (the Argonian rows above), (b) Hist **objects**
(Skyfall's Sleeping Hist Tree Overhaul 116792, Roots of the Sleeping Tree 62422), (c) Shadowscale **armour**
(79717, 43720), (d) generic nature/poison/water packs that do not use the Argonian theme. A voodoo/witch-doctor pack
exists only for LE (`skyrim:73368` BigBizkit's Ultimate Voodoo and Witch Doctor Arsenal; SE port 181332 "unofficial",
7 endorsements). No Beyond Skyrim Black Marsh content has been released as a Skyrim mod (Beyond Skyrim: Bruma is the
released province; Bruma spells search turned up only an LE Morrowind spell, `skyrim:71124`). **So "Argonian magic"
is ours to compose from stock archetypes plus nature/poison/water packs; nothing can be taken whole.**

**What the packs teach on scope, structure and balance:**
- **Scope.** The three classic packs sit at 75-200 spells; the heavy hitters (Arcanum) take ~500 MB and script rituals;
  users keep the light ones. Enai Siaion's packs boast "no save bloat" and cite script load as the main complaint
  in comments (Imperious and Thunderchild pages warn of script-delayed starts). **Lesson:** a small themed set of
  record-only spells beats a big scripted one for our soulslike stack.
- **Structure per school and level.** All the packs use vanilla's five levels (novice, apprentice, adept, expert,
  master) and gate **Master** tier behind a quest (Apocalypse/Odin: College Ritual quest). Triumvirate organises by
  archetype rather than school: each archetype spans several schools. **Lesson for #104:** Argonian "archetype" can ride the
  same keyword.
- **Balance.** Natura quotes "balanced around vanilla spells" with novice DoTs of ~8 dps (verified in its description);
  Arcanum and Odin each give tier-specific "dps per magicka" curves in their descriptions. Mod spells that do 2-3x
  vanilla break fights; community patch lists include "Triumvirate (Balanced)" (65427) and "Semi-Phenomenal Triumvirate"
  (143682) because the original is considered strong.
- **Distribution.** Tomes via leveled lists + vendors (script-added in Elemental Destruction, Shadow Spell Package,
  Venomancy; **SPID/KID/SkyPatcher is now the norm** and the safer method); **NPCs** get spells via SPID
  distribution files (Natura, Plague, oyvveg's Apocalypse/Odin/Mysticism NPC packs ids 58017, 46877, 53682).
  "NPC Spell Variance" KID files (133035 Triumvirate, 132929 Mysticism, 134661 Arcanum, 165405 Shadow) show a standard way to give actors keyword-based spell lists.
- **Perk integration.** Ordinator-grants-spells (52674) and "Ascension" (Darenii's Natura aspect) show that
  a perk can hand the player a spell record-only (perk entry "Add spell/ability"). Mysticism-era mods
  assume the Ordinator/Vokrii perk overhauls; we run none (no row in dependencies.json), so vanilla perk trees are our base.
- **Parallel systems.** Wintersun (religion) and Thunderchild (shouts) are the two big "magic-adjacent" systems; both are scripted and
  quest/MCM heavy. They show that a parallel progression works but costs scripts and MCM; neither is Argonian.

## 3. The cheap techniques, ranked (feel per unit work)

1. **Rename and re-describe existing spells, tomes and effects** (FULL/DESC only). Proven in this repo (lane
   1.12: `mod_form` rows, 11 renamed, 3 described, applied at data load by ArgoniaCore, no master on the plugin).
   Per item: seconds each in data; the cost is the writing and the consistency pass. Risk: low; Wind UI / our
   pane read the new strings (the pane was built, lane-1.12-magicpane.md). Limits: reading a name does not change what a
   spell does; "Marsh Squall" is a snowstorm with a new label until its shader/colour changes.
2. **Change who sells, teaches and rewards spells** (stock rows, tomes as quest rewards, trainers, shrines as sources).
   Record-only for tomes and chests; our existing `trade_class_mod_stock` route is the place. Per spell: one row.
   Gap already stated in lane-1.12-magic.md: a spell trade class must exist, and merchant chests in BM&V need it.
   High impact: a player meets Argonian magic **where Argonians are**. The Hist-grown shrine/grove is one record-only
   place a tome can lie.
3. **Recolour by record (EFSH colour keys, LIGH colours, MGEF light field)** so the cast reads green, amber, moss or
   sap rather than Nordic frost-blue. Record-only, one new EFSH per colour family (not per spell); per section 1.1 the
   cost jumps only where colour is baked into a gradient/nif. Impact: high (colour is the first thing seen);
   risk: low-medium (a shader record can look wrong in mixed lighting; one test cast per family).
4. **Themed sets with a shared keyword plus a small perk or ability.** Add a keyword (MagicHistMagic) to each
   Argonian-flavoured spell and one PERK that adds "while an Argonian spell is active, X" (perk entries and
   keyword conditions are record-only; the Ordinator-grants-spells mod 52674 proves perks may add abilities). Per set: a
   keyword + 1-3 perk entries. Risk: perks interact with any perk overhaul (we run none yet).
5. **Racial power rewrite on the Argonian RACE record or by SPID** (vanilla Histskin: a Greater Power once a day,
   10x health regen for 60 s, UESP Skyrim:Histskin). Rewriting Histskin and adding two or three abilities
   (water breathing is vanilla; poison/disease resist and amphibious swim speed are record-only; Argonian Upgrades 48524
   proves a **no-script** version). SPID can add an ability or spell to every actor of race Argonian without editing the
   race record (SPID is installed; our row `spid`). Risk: other mods edit race records; we are the only plugin editing it.
6. **A parallel power slot from stock mechanics.**
   - **Lesser/greater powers**: any spell with type Power appears in the voice slot; BOOK "teaches spell" works for
     powers (the lesser-power tome mods 2697 and 19603 show tomes teaching powers record-only; our magic pane already lists powers).
   - **Activator-granted**: vanilla standing stones, shrine blessings, the Black Book powers and the Dawnguard
     vampire / werewolf trees are an ACTI (or quest stage) with a **tiny Papyrus script** that adds a spell/perk on
     activate (from knowledge; not measured here). One generic script ("on activate, add property spell X") is
     reusable for every Hist-tree or shrine in the world (CLAUDE.md allows Papyrus only for generic scripts). Our own
     SKSE plugin can add an equivalent at no script cost. **Record-only alternative: tome or consumable** (item below),
     since a BOOK teaches without a script.
   - **Dragon shouts / word walls** use a script plus a SHOU record; not reusable without the script; skip.
   - **Vampire/werewolf trees**: custom perk trees (Dawnguard) are a skill-tree record plus a script to grant points;
     the Sacrosanct/Growl family shows an Enai Siaion approach (abilities and powers, no tree). A small blessing system
     = a handful of SPEL abilities + one activator script.
7. **Consumable-driven magic.** A Hist sap potion (ALCH) with a Fortify/Regen effect and a custom colour **is record-only**,
   needs a recipe (ingredient or vendor stock) and stock rows. Poisons (ALCH with a poison flag), scrolls (SCRL) and
   staves (WEAP + ENCH) are the same. Apothecary 52130 (106 KB, "record-only") is the existing model for poison and potion
   balance. Per item: one ALCH + one stock row. High feel for a swamp setting; low risk. Timed powers (a sap gives
   Histskin for 60 s) are an ALCH whose effect carries the ability spell.
8. **Conditions that make spells react to the environment.** Per effect row or MGEF; **record-only**; no script.
   Functions I could confirm exist (UESP condition-function index, titles seen: GetInWorldspace, GetInCurrentLocFormList,
   GetIsCurrentWeather; others from knowledge): IsSwimming, IsRaining, IsSnowing (one Nexus thread asks whether
   IsRaining/IsSnowing work in Skyrim; no answer seen: **test**), GetInWorldspace (e.g. the BM&V worldspace),
   GetInCurrentLoc / GetInCurrentLocFormList (a Location record list for swamp regions), LocationHasKeyword,
   IsInInterior, GetIsRace, HasKeyword (actor/object), HasMagicEffect, GetIsCurrentWeather (a spell condition with
   weather Skyrim Storm Rain is reported in the Nexus thread 2026254), GetCurrentTime / GetGameHour-style time functions,
   GetDistance (to a **specific** reference, not "any object of type"; a "near a Hist tree" condition needs a
   placed marker reference, a cloak or hazard record around the trees, or our SKSE plugin), GetActorValue. Limits: conditions run
   on the effect's **caster or target as set by "subject"**; weather/time conditions are cheap, location conditions need Location
   records in BM&V's cells (check BM&V's records first); on aimed spells the condition is checked at cast and on hit;
   an old GECK note says IsSwimming "always returns 0 on the player" - that is Oblivion, but a Nexus thread
   reports "IsSwimming" as workable on an Ability in Skyrim and one mod replaced it with a global set by a script:
   **verify in game**. Gating by hazard: a Hazard placed under a Hist tree and a cloak-like effect gives "near a tree"
   record-only but must be placed per tree (REFR) and so scales with our place pipeline.
9. **SPID/KID distribution so locals and enemies use the themed spells.** SPID is installed (7.3.3, MIT, row `spid`);
   KID (keywords) is **not** in dependencies.json. A SPID line per spell can give Argonian NPCs by race/faction/level; Natura, Plague,
   oyvveg's packs ship such files (ids above). Cost: one line per spell/NPC class; risk: combat style may not use new
   spells well (section 4).
10. **Dialogue-taught spells** (a dialogue topic result that adds the spell): needs a Papyrus fragment or SKSE; our quest builder is the
    generic route (CLAUDE.md: quests are data in one form; check whether the quest form has an "add spell" block before
    designing). Skyrim vanilla teaches via tomes and trainers more than via dialogue.

## 4. Pitfalls and balance practice

- **Vanilla cost scale.** Costs run roughly 10-30 magicka for novice up to hundreds for master spells, then perks cut cost
  (Novice..Master cost -25%/-30%... by perk) and dual casting doubles magnitude at ~2.8x cost - **from memory, unmeasured**.
  Measure from the pinned game with xEdit on the play machine: list SPEL by tier, cost, magnitude, duration
  per school; then set each Argonian spell's `magnitude x duration / cost` within +/-20% of the vanilla spell at the same tier.
- **Where mod spells break soulslike pacing.** Our stack adds stamina-poise-parry combat (Elden Parry, Precision, Stop on Slash,
  chocolate poise). Spells that stagger or stunlock, instant summons, and healing over time break it. Rules from the pack
  lessons above: heal over time slower than a flask; no free Master; summons expire and cost; cooldown on powers; DoTs
  balanced around vanilla novice (Natura ~8 dps).
- **AI use.** New spells are not used by NPCs unless on their spell list, in a class-appropriate combat style and not
  flagged "don't use"; SPID adds the spell; "NPC Spell Variance" (KID files above) is a KID-keyword system for
  varied NPC spell lists; Apocalypse's author deliberately did not touch NPCs for compatibility. Test each
  enemy spellcaster once.
- **Tome and leveled-list conflicts.** Mods that edit `LItemSpellTomes*` conflict; our Magic Expanded tomes avoid
  leveled lists and use chests (lane-1.12-magicpane.md); No-Spell-Tomes-as-loot mods 22139 exists for the opposite
  design. Prefer chest/trade-class rows.
- **UI.** Our own pane groups six schools (lane-1.12-magicpane.md) by a `mod_form` school; Wind UI's DLL has only five
  headings plus "Other". A Hist school is not feasible in Wind UI; in our pane the school is data (school_of in magic.h).
  Custom icons come from "i4"/spell-icon mods for popular packs (rijosan ids 146949 Triumvirate etc.); we would need
  our own for new spells.
- **Save safety.** Scripted spells with running tick scripts (Forgotten Magic, Shadow Spell Package ticking dots; the
  author notes "update manager scripts ... will kill themselves next load") leave script instances in saves. Record-only spells
  and perks leave none; removing a plugin that granted spells orphans them. Our add-at-data-load route (SKSE reading Magic.esp
  in place) never saves a script.
- **Crashes.** Odin and Vokrii double-cast Ice Spike CTD (fix 80716) shows novel projectile behaviours can crash; test dual cast.
- **Runtime pin.** Our runtime is 1.6.x with SKSE; most of these mods are ESP + records (safe) and a few are SKSE DLL
  mods (SPID on 1.7.104 per our register row). Per-mod DLL status is **not verified** here; check each before listing.

## 5. Cost ladder (typical work per item; risk)

Effort words follow `docs/research/new-art/PROPOSAL.md`: small / medium / large; "sure" where proven here, "unsure" where not.

| Change | Per item | Risk | Evidence |
|---|---|---|---|
| Rename/re-describe N spells or tomes | a few minutes of writing each; code does the rest (one `mod_form` row); small; **sure** | low | lane-1.12 (11 renamed in game) |
| Recolour N effects, **record-only** (EFSH keys, LIGH) | one EFSH + one MGEF re-point per colour family (a few per mod); small-medium; unsure (never done here) | low-medium | UESP EffectShader notes |
| Recolour N effects, **file** (gradients/nifs by install-time code) | the pipeline is large once; each effect after it is small; unsure; test one first | medium (shared nifs change every spell that uses them) | Nexus recolour thread; decision 0003 |
| Add N record-only spells from stock archetypes | SPEL + MGEF (+ tome + stock row + keyword): ~20-40 min each by hand, minutes by generator; medium for 20+ because of balance; **sure** | low-medium (balance, AI use) | record structure; Apocalypse etc. average dozens per author |
| Activator-granted power set | per power: SPEL + ACTI + REFR placement + one reusable script (or SKSE grant) + a description; medium; sure once the generic script exists | low (script is tiny) | standing-stone/shrine pattern (from knowledge); Freyr/Mundus show scale |
| Small perk tree or blessing system | 6-12 perks and abilities + a UI line; medium-large; unsure (perk tree layout needs a skill tree record + the pane) | medium (perk overhauls conflict) | Dawnguard trees; Path of Sorcery 6660 (perk overhaul) shows tree-edit costs |
| Scripted mechanic (transform, ritual, react-to-sap, near-tree gate without markers) | large each; **avoid**; use Script archetype or our SKSE plugin | high (saves, load order) | Arcanum/Phenderix scale; Thunderchild script warnings |

## Recommendations

1. **Compose, do not search further.** Nothing Argonian-themed exists to take whole (section 2); the stock-archetype route
   plus nature, poison and water packs as references is the sound path.
2. **Reference-only dependency (no grant): Triumvirate druid/shaman, Natura (nature, 100 MB), Venomancy (poison, Destruction or
   Restoration version), Elemental Destruction Redux (water/earth/wind), Apothecary (poison/potion balance, records
   only).** Register each as a row; only the owner opens the Permissions tab for any mod we would copy records from.
3. **Argonian racial layer:** copy the *design* of Argonian Upgrades 48524 (no scripts) and Heritage 129813, Freyr 88043; implement
   by overriding the Argonian race spell list or SPID in our plugin (we edit race records alone).
4. **Make the first small step the one already proven:** rename and re-describe the Magic Expanded/vanilla spells with Argonian words
   at data load, then a spell trade class (the gap in lane-1.12-magic.md) so the marsh sells them.
5. **Test before committing:** one recolour (EFSH + LIGH) cast in game; the IsSwimming and IsRaining conditions on an ability
   in game; a KID/SPID line on one NPC; xEdit measurement of vanilla cost per tier.
6. **Open questions for the owner or a browser:** the Permissions tab of every mod above (none machine-readable); whether
   Wintersun's deity list includes Argonian deities; each SKSE DLL's version against 1.6.x.

Covered: docs/research/mods (lane-1.12-magic, lane-1.12-magicpane), docs/research/new-art/PROPOSAL.md and 3 siblings
(recolour precedent), docs/research/morrowind-level-scripting.md (grep), mods/dependencies.json (ids, spid row),
mods/sourcing-register.json (permission form, Magic Expanded and SPID rows), decision 0003; Nexus API for ~45 mods and ~70 searches ·
Skipped: nexusmods.com pages, ck.uesp.net and archive.org (HTTP 403 or blocked, so permissions and CK text unread),
game files (not on this machine), Nexus article pages, YouTube/Reddit.

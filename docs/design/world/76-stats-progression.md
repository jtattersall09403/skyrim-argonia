<!-- imported unchanged from elder-souls-argonia docs/world/76-stats-progression.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Part VIII-b — Stats, progression and character systems (§100–104, §116–129)

> Module of the world-generation master plan — see [README](README.md) for the router
> and [00-core.md](00-core.md) for the universal principles.
>
> Companion: [75-combat-compatibility.md](75-combat-compatibility.md) (§51–57) — the
> portability boundary and capability profiles this module feeds. Placement:
> decision [0019](../old-decisions/0019-stats-system-workstream-and-placement.md);
> the code home: decision [0088](../old-decisions/0088-the-stats-model-lives-in-game-core-and-reads-injected-data.md).

**Two parts.** §100–104 hold the binding constraints and where the system
lives. **§116–129 are the design** — the spec. An agent authoring an enemy,
pricing a service or gating a quest reads §102 and the design.

| Looking for… | Section |
|---|---|
| The binding constraints (fixed danger, no dice, protected feel) | §102 |
| How the design was settled; where the code lives | §103 · §104 |
| The character at a glance | §116 |
| Attributes · skills · character creation | §117 · §118 · §119 |
| Levelling, *vastei*, health, anti-grind rules | §120 |
| Damage, stamina, poise, armour, blocking, condition | §121 |
| Movement, burden, swimming, climbing, breath | §122 |
| Magic, spellmaking, enchanting | §123 |
| Alchemy, smithing, trade, training, crime | §124 |
| Speech, disposition, faction standing | §125 |
| Healing, rest, saving, death, respawn | §126 |
| Races, birthsigns, and the one effects stack | §127 |
| The D0–D5 absolute ladder and the NPC/enemy schema | §128 |
| Where the numbers live (data files) | §129 |

## 100. The baseline the stats sit on

The combat feel (timing, weight, per-hit numbers at the reference loadout,
§116) was calibrated and playtested before any character statistics existed.
The stats layer is **additive**: it decides where that feel sits on the curve
and varies from there; it never re-answers "is the combat fun?".

## 102. The constraints any stat design must satisfy (binding)

- **Fixed difficulty (decision 0004) is the dominant constraint.** The world
  never receives the player's level. Every enemy, every trap and every loot
  item resolves to a **fixed absolute** number that never reads player state.
  Authors write *semantically* — "a strong D3 swamp troll", "a D2 weapon cache"
  — and a compiler emits the absolutes (§128), so "this is a D3 creature" means
  something numerically.
- **Fixed difficulty binds the world, never the player.** It fixes the world's
  enemies, stats and parameters; it never caps the player's earned capacity to
  cope. Earning money and alchemy skill to brew your way through a hard area is
  the intended fun — this is why there is no estus flask (§126), and it is the
  tie-breaker for any "should we bound the player here?" argument.
- **Becoming absurdly powerful is a feature.** It is fixed danger's payoff:
  the swamp that killed you at hour three is trivial at hour eighty. What the
  design protects instead:
  - **power is earned through system mastery** the player discovers and
    combines (alchemy, enchanting, trade, training, rare gear, quest rewards),
    not handed out by the levelling curve;
  - **it is not the intended path.** The critical path and the danger bands are
    tuned for a competent, ordinarily-equipped character;
  - **it is not the norm in the first hours** — design intent, not an enforced
    invariant: no validation machinery. An accidental early gem is an easter
    egg (the *Morrowind* jump-scroll rule);
  - **the world does not break when it happens** — quests, gates and access
    progression degrade into "you skip the challenge", never into unfinishable
    states.
- **Player skill stays the primary variable in ordinary play.** Real-time
  hitboxes, parry windows, i-frames, stamina: **no hidden to-hit roll** — a
  swing that visibly connects lands. Character skill modifies damage,
  stagger/poise, stamina cost, recovery, reach and reliability. **No dice
  anywhere** (combat, casting, blocking, locks, persuasion, enchanting,
  repair): every check is a threshold or a continuous scale.
- **Stats never touch feel constants.** i-frame windows, parry windows, input
  responsiveness and animation windups are never stat-gated. Recovery phases,
  stamina costs and roll *distance* are fair game.
- **The calibrated feel at the reference loadout is protected** (§52, §116):
  timing and weight. Stat- and load-linked variation (recovery scaling,
  equip-load roll tiers) is design space, not drift.
- **Capability profiles are the world↔stats contract** (§52, §122). Profiles
  are generated from the stat system; no world data changes with a retune.
- **Argonian physiology is a world-acceptance rule** (00-core): breath,
  swimming and disease resistance are race modifiers (§127).
- **Birthsigns are calendar-shaped**: a birth date yields a birthsign from the
  world clock (module 55 §95). The slot and all thirteen signs ship together (2.8).
- **There are no followers or companions** (decision 0028). Hirelings, guides
  and escorts are quest actors with their own authored numbers.
- **Respawn on rest** (decision 0031): generic enemies respawn when the player
  rests; named actors never; cleared dungeons stop (§126).

## 103. How the design was settled

**"Morrowind chassis with a Souls combat layer"**: every Morrowind pathology
maps onto a part the design deletes (the dice, the level-up bookkeeping, the
unclamped self-referential loops). Sourced items arrive in Skyrim's taxonomy
and the chassis wants Morrowind's categories; the item mapping is §118/§121
and the keep/drop outcome (spears, pikes, halberds, staves, medium armour and
unarmed kept; whips, crossbows and thrown weapons cut) is decision 0031, with
sourcing evidence in module [90 §74.3](90-asset-strategy.md). The owner rounds
are decisions 0031, 0033, 0035 and 0037. The live evidence is
[reference games](../research/combat-and-systems/stats-progression-reference-games.md)
(Morrowind's real formulas, the Souls layer, Skyrim's lessons); the working
papers in [docs/research/archive/workstream-s/](../research/archive/workstream-s/)
hold superseded drafts and are provenance, never a spec.

**The simulation is evidence, not law.** It is arithmetic over a design: no
animation, no spacing, no player hands. Where it and a playtest disagree, the
playtest wins. Its job is to catch what instinct cannot — a curve that
diverges at hour ninety, a build that cannot finish, an exploit that shows
over a thousand fights — and to make retuning cheap. Its absolute pacing is
trustworthy because it is anchored to a known answer (§120.5). Its invariants
are standing tests in `packages/game-core/src/stats/sim`.

## 104. Where the system lives

`packages/game-core/src/stats` implements §116–129; definitions are data files
(§129) consumed like `races.json`, read by both apps. The standing
guarantees:

- the reference character reproduces the calibrated timing, weight and
  per-hit numbers (§116);
- the progression economy is whole (§120): Morrowind's per-use values, the
  worthiness modifier and its damping, a maxed skill still pays, the 1:3
  miscellaneous credit;
- capability profiles regenerate from the stat system and the world's
  traversal probes pass (§52, §122);
- NPCs, enemies, merchants, loot and traps carry one schema plus a level,
  authored **semantically and compiled to absolutes** (§128.2) from world data
  only — a curve retune and recompile rebalances all content coherently;
- poise applies to player and enemies alike (§121.3);
- the power ladder has **five combat bands D1–D5**; D0 is a safe-ground
  location property authored with the places, never an enemy tier (§128).

---

# The decided design (§116–129)

Numbers are the *shapes and constants*; the machine-readable tables live in
`packages/game-core/src/stats/data/` (§129).

## 116. The character in one screen

A character is: **7 attributes**, **27 skills**, a **level**, a **race**, a
**birthsign**, a **class** (5 major / 5 minor / a specialization / 2 favoured
attributes), **health / stamina / magicka**, an **inventory with weight**, an
**effect stack** (§127) and a **vastei** balance (§120).

Everything mechanical is derived from those by the formulas below. Two
conventions make the whole system one system:

1. **One skill curve, over Morrowind's own score.** Morrowind computes a
   *score* — `skill + attribute/5` — and rolls against it. We compute the same
   score and **compare it deterministically** instead. That one substitution is
   the whole no-dice port (§117.1):

   ```
   score(skill, attr) = (skill + attr/5) / 1.2      # Morrowind's term, normalised to 0–100
   k(s)               = 1 − (1 − s/100)^1.6         # 0 at score 0, 1 at score 100
   band(lo, hi)       = lo + (hi − lo) × k(score)
   ```

   The `/5` weight is Morrowind's own convention, used almost everywhere in the
   game (*Morrowind:Combat*, *:Security*, *:Sneak*, *:Spells*, *:Enchant*); the
   `/1.2` only rescales it so a character at 100/100 reads 100. `k` is
   front-loaded and self-soft-capping: 25 buys 36 % of a range, 50 buys 67 %,
   75 buys 88 %, the last 25 points buy 12 %.

   **Which attribute** is whichever one Morrowind's formula for that check
   named — Agility for anything that was a hit, block, sneak or lock roll;
   Willpower for casting; Intelligence for enchanting; Personality for
   persuasion — **not** the skill's governing attribute (§117.1 explains why
   those differ, in canon as well as here).
2. **One effect stack.** Racials, birthsigns, diseases, potions, spells,
   enchantments and the allegiance rites (decision 0028) are all `StatEffect`
   entries against the same fields (§127). Nothing has a bespoke pathway.

**Calibration is done against a *set* of characters, not one.** The balance
harness runs every stage of the game × six build styles × every danger band,
plus edge cases (unarmoured mage, over-encumbered hauler, best-in-slot tank,
hour-one novice) and six whole-playthrough runs. No single character defines
the curve.

One of that set is named, because it is the **continuity anchor**: the
**Marsh Hand** — Str/End/Agi/Spd 50, Wil/Int/Per 40; Long Blade 60, Block 50,
Heavy Armor 45, Athletics 40; steel straight sword, steel kite shield, steel
cuirass/gauntlets/boots, head bare, at **mid burden**. She comes out at 100
health, 100 stamina, 180 kg capacity and 24.06 % mitigation against a
24-damage blow (steel rates 50 raw; her Heavy Armor 45 band makes it 47.51,
the `steelRef` every invariant is calibrated on; the sandbox's placeholder
ran on the raw 50 and 25.0 %). Note that her health
falls out of Morrowind's own formula with no fitting at all:
`(Str+End)/2 + level × End/10` = 50 + 50 at level 10.

That correspondence is a **convenience, not a law**. The sandbox's constants
were placeholders chosen to make the combat feel good in a vacuum (§102), and
this design is free to re-base any of them. Keeping the anchor means a change
here can always be compared against something that has actually been played;
it does not mean 100 health is sacred. What *is* protected is the **feel** —
timing, weight, the rhythm of a trade — not the integers.

## 117. Attributes

Seven — Morrowind's eight minus Luck, whose entire mechanical existence was a
half-weight term inside dice rolls (*Morrowind:Luck*: it governs no skill and
touches no derived stat). Range 0–100 by purchase; effects may push a value
above 100 and the design does not cap that (§102, god-build).

**Every job below is Morrowind's, with Morrowind's coefficient.** Where the
canon formula was deterministic we port it unchanged; where it fed a die roll
we keep the score and make the comparison deterministic (§117.1). The right
column says which it was.

| Attribute | What it does here | Canon (*Morrowind:*…) |
|---|---|---|
| **Strength** | melee damage `×(Str+50)/100` · carry capacity · half the health base · repair rate. **Not bows** — see below | *Combat*, *Encumbrance*, *Health*, *Armorer* — all deterministic except the repair roll |
| **Endurance** | `maxHealth = (Str+End)/2 + level × End/10` · `maxStamina = 60 + 0.8×End` to End 50, `+ 4` per point above (§121.2) · stamina regen · disease/poison resistance floor | *Health*, *Fatigue* — deterministic. Canon's health-per-level is **not** retroactive; ours is (§117.2) |
| **Agility** | the score term in every check that was a hit, block, sneak or lock roll (`+Agi/5`) · **base poise = Agi/2** (§121.3) · dodge stamina · bow steadiness | *Combat*, *Block*, *Security*, *Sneak* — all were rolls; base poise re-houses canon's knockdown threshold (`Agility × 0.5`) |
| **Speed** | ground, swim and climb speed (§122). Nothing else — and in canon it appears in **no dice roll at all** | *Speed* — deterministic, and the one attribute we can port verbatim |
| **Willpower** | the score term in casting (`+Wil/5`, §123) · magicka regen · innate magic resistance | *Spells*, *Willpower* — the cast roll is deleted, the score survives |
| **Intelligence** | `maxMagicka` · alchemy potency (`+Int/10`, canon's odd half-weight) · enchanting point budget (`+Int/5`) | *Magicka*, *Alchemy*, *Enchant* |
| **Personality** | disposition `+0.5×(Per−50)` · persuasion score (`+Per/5`) · price band (`+0.2×Per`, capped 10) | *Disposition*, *Speechcraft*, *Mercantile* — disposition and prices were already deterministic |

Three divergences worth naming, because a future agent will otherwise "fix"
them back:

1. **Strength does not multiply bow damage**, though canon applies it to both.
   Our arrow damage is *physical* — draw force, power stroke, arrow mass — so
   the archer's strength is already in the model twice over: in the draw weight
   of the bow they can handle, and in the soft requirement that charges a weak
   archer extra stamina for a heavy one. Canon's term would be a third count.
2. Our magicka pool is `20 + 3×Int`, not canon's `Int × multiplier` — canon's
   100-magicka ceiling cannot sustain a Souls-length fight (§123).
3. Magic skill scales spell magnitude here, where canon left it flat: canon's
   skill bought *reliability*, and we deleted the roll it was reliable against.

### 117.1 The no-dice port: keep the score, drop the roll

Morrowind's attribute model has three layers. **Direct scalars** (Strength into
damage and carry, Speed into movement, Endurance into health, Intelligence into
magicka) port unchanged. **The level-up multiplier** is replaced by the vastei
sitting (§120.4). The third layer is the interesting one: Morrowind's *dice*.

Almost every check in the game computes a score of the form

```
score = skill + primaryAttribute/5 + Luck/10          (then × a fatigue term)
```

and rolls 0–99 against it. Luck is always exactly half-weight; the primary
attribute is always `/5`. That convention holds across combat, blocking,
sneaking, lockpicking, trap disarming, spellcasting, enchanting and persuasion
(*Morrowind:Combat*, *:Block*, *:Sneak*, *:Security*, *:Spells*, *:Enchant*,
*:Speechcraft*).

**So we do not delete Agility's job — we delete the die.** The same score is
computed and compared against a fixed difficulty:

| Morrowind rolls… | We compare… |
|---|---|
| `HitRate = WeaponSkill + Agi/5` vs the target's Evasion | the same score sets **where in the weapon's damage range** the blow lands (§121.1) — reliability becomes quality |
| `(Security + Agi/5) × ToolQuality − LockLevel` | a lock opens iff `(Security + Agi/5) × ToolQuality ≥ LockLevel` |
| `Elusiveness = (Sneak + Agi/5 − shoeWeight) × distanceTerm` vs an observer's Spot Chance | the same two scores compared directly; canon's direction multiplier (×1.5 seen from the front, ×0.5 from behind) is kept |
| `(Block + Agi/5)` clamped 10–50 % | the same score scales **guard stability** — blocking is a player input here, so the score buys how much a block costs you |
| `SpellSkill×2 + Wil/5 − SpellCost` | a spell is castable iff `2 × SpellSkill + Wil/5 ≥ SpellCost` — canon's own boundary, now a gate instead of a gamble (§123) |
| `Enchant + Int/5 − 3 × points` | solve it for points: your budget **is** `(Enchant + Int/5)/3` (§123) |
| `Speechcraft + Per/5 + Reputation` vs the NPC's rating | the same score against an authored threshold (§125) |
| `Agility × 0.5 ≤ damage` → knocked down (immune at Agi 100) | the same number becomes your **naked poise** — Agility/2 is the base of the poise pool (§121.3) |

That last row is worth flagging: it gives Agility a real defensive job with
Morrowind's exact coefficient, expressed through the poise system the owner
reinstated at round 4 (§121.3) rather than as a second, separate threshold.

**What a governing attribute still does.** In canon it does three things: sets
the level-up multiplier, caps training, and — often — is *not* the attribute in
that skill's formula at all. Canon is full of these mismatches: Security is
governed by Intelligence but every lock roll uses Agility; Conjuration and
Illusion are governed by Intelligence and Personality but both cast through
Willpower; Acrobatics is governed by Strength, which appears nowhere in jumping;
Hand-to-hand is governed by Speed and its damage uses neither Speed nor
Strength. We keep that faithfully — the formula attribute and the governing
attribute are different things — and the governing attribute keeps one job:

- **the trainer cap**, exactly as canon: *you cannot train a skill above its
  governing attribute* (*Morrowind:Trainers*), reading **base** values, which
  kills canon's drain-and-train exploit. (It briefly had a second job — a
  practice discount on attribute prices — cut at round 4, §120.4.)

### 117.2 How level, Endurance and health fit together

Three separate things:

- **Skill ranks** come from use; counted major/minor ranks make a level ready, one at level 1 rising by one a level to eight from level 8 on (§120.5).
- **Levels** are banked at a rest, and each one adds health.
- **Endurance** is bought with vastei at the sitting.

The formula is canon's, with one deliberate change:

```
maxHealth = (Strength + Endurance)/2  +  level × Endurance/10
```

Canon computes the same two terms but *adds them as they happen*, so the health
you got at level 3 is frozen at your level-3 Endurance — which is why
Morrowind players are told to max Endurance before anything else or "ruin" the
character. Ours is a **formula over your current values**, so it is retroactive:
at level 10 with Str 50/End 50 you have 100 health; raise Endurance to 70 and
it becomes 130 immediately, with nothing replayed. Same numbers, no homework.

### 117.3 The one canon rule we deliberately do not port into combat

Morrowind multiplies nearly every check by `0.75 + 0.5 × (fatigue/maxFatigue)`
— a ±25 % swing on everything, driven by a pool fed by four attributes. It is
the most universal rule in the game. We do **not** apply it to combat: our
stamina bar already punishes exhaustion by preventing action, and taxing damage
on top would double-punish and muddy a Souls exchange. We do apply a gentler
version out of combat, where "worn out" is flavour rather than a second
penalty: non-combat scores (sneak, security, persuasion, brewing, repair) are
multiplied by `0.85 + 0.15 × (stamina/maxStamina)`. If that reads as fiddly in
play, deleting it costs nothing else.

## 118. Skills

Morrowind's 27, with three substitutions: **Armorer → Smithing** (repair +
bounded tempering + crafting, the Skyrim keeper), **Mysticism kept** despite the
4E Synod dissolution (foreign magical institutions never took root in Black
Marsh; the folk school survives — lore note in
`world/sources/lore/topics/magic-practice.md`), and every dice-based skill
re-expressed as a threshold, with one exception: pickpocketing is a
visible chance and a seeded roll, the one gamble (decision 0151). No
crossbow or thrown skill (decision 0031).

Bands are written `lo→hi` across `k(score)` (§116). **Gov.** is the governing
attribute — canon's, and it sets the trainer cap
(§117.1), *not* the formula. **Score** is the attribute that actually enters
this skill's maths, which in canon is frequently a different one. "Wear" is
condition loss per use (§121).

| Skill | Gov. | Score | Spec. | What the curve moves |
|---|---|---|---|---|
| Long Blade | Str | Agi | Combat | damage-range position 0.40→1.00 · stamina cost ×1.25→0.80 · wear ×1.4→0.6. Damage is then multiplied by `(Str+50)/100` (§121.1) |
| Blunt | Str | Agi | Combat | as Long Blade (class identity is the weapon table, not the skill) |
| Axe | Str | Agi | Combat | as Long Blade |
| Spear | End | Agi | Combat | as Long Blade |
| Short Blade | Spd | Agi | Stealth | as Long Blade; its sneak-opener table is the best after the dagger's (§121.5) |
| Marksman | Agi | Agi | Stealth | delivered-damage position 0.40→1.00 (a multiplier on top of the ballistics) · nock speed ×1.0→1.6 · draw speed ×1.0→2.0, the ×1.0 at skill 10 for the reference character (decision 0074 §3; continuous, monotone; so the bands' `lo` at score 0 is 0.80 and 0.66) · sway ×1.4→0.6 · draw stamina ×1.25→0.80. **No Strength multiplier** — deliberate divergence from canon, §117 point 1 |
| Hand-to-Hand | Spd | Agi | Stealth | damage position 0.40→1.00 · stamina damage to the target ×1.0→2.0; empty an opponent's stamina and they can be finished. **No Strength multiplier** — canon's H2H damage uses neither Speed nor Strength |
| Block | Agi | Agi | Combat | stability ×0.85→1.15 (absolute cap 0.95) · guard stamina ×1.30→0.78 |
| Heavy Armor | End | — | Combat | worn heavy rating ×0.55→1.20 · its effective weight ×1.10→0.90 · wear ×1.4→0.6. (Canon is `rating × skill/30`, i.e. naked at skill 0 and ×3.3 at 100; ours is compressed because the rating band is calibrated against the hits-to-die targets, §128) |
| Medium Armor | End | — | Combat | as Heavy, for medium pieces |
| Light Armor | Agi | — | Stealth | as Heavy, for light pieces |
| Unarmored | Spd | — | Magic | rating `0.0065×skill²` per bare slot — canon's own formula (60 at skill 100 over four slots) |
| Athletics | Spd | Spd | Combat | run ×0.94→1.10 · **swim ×0.5→1.5** (canon leans on Athletics hard for swimming, and swimming is a pillar) · `breath = 25 + 0.35×Athletics + 0.25×End` seconds · sprint drain ×1.20→0.85 |
| Acrobatics | Str | — | Stealth | jump ×0.80→1.60 · safe-fall height `2 + Acrobatics/25` m (canon: fall damage is reduced by 1.5 per point) · **climbing**: speed ×0.85→1.25, stamina drain ×1.25→0.75 (§122.1) |
| Sneak | Agi | Agi | Stealth | `Elusiveness = (Sneak + Agi/5 − boot weight) × (0.5 + distance/500)` against an observer's spot score × canon's direction multiplier (×1.5 front, ×0.5 behind) — compared, never rolled · **the sneak-opener band** (§121.5) |
| Security | Int | **Agi** | Stealth | a lock opens iff `(Security + Agi/5) × toolQuality ≥ lockLevel`; keys and Open magnitude always work. Canon's mismatch kept: Security is governed by Intelligence and uses Agility. **Picks wear** (owner, round 4): a pick loses condition per lock, scaled by `lockLevel / yourScore` — an easy lock barely scratches it, one near your ceiling chews most of a pick. Hard locks cost real consumables without any die; better picks are a higher ceiling *and* more durable |
| Smithing | Str | Str | Combat | repair per stroke 6→22 condition · temper grades 0/1/2/3 at score 25/55/80 · craftable material tier ≤ 1+floor(score/14) |
| Mercantile | Per | Per | Stealth | price band from `Mercantile + 0.2×Per + (disposition−50)` against the merchant's own (§124) |
| Speechcraft | Per | Per | Stealth | persuasion score `Speechcraft + Per/5 + standing` (§125) · topic access thresholds |
| Alchemy | Int | **Int/10** | Magic | potency/duration (§124, canon formula) · ingredient effects visible at skill 15/30/45/60 (canon's `fWortChanceValue`) |
| Enchant | Int | Int | Magic | point budget `(Enchant + Int/5)/3` — canon's success formula solved for points · constant effect costs double · charged-item use cost `×(1.1 − skill/100)` (canon exactly) |
| Alteration | Wil | **Wil** | Magic | castability `2×skill + Wil/5 ≥ spellCost` (§123) · cost ×1.40→0.80 · cast time ×1.20→0.85 · magnitude ×0.75→1.25 |
| Conjuration | Int | **Wil** | Magic | as Alteration (+ summon duration ×0.8→1.4). Canon: every school casts through Willpower, whatever governs it |
| Destruction | Wil | **Wil** | Magic | as Alteration |
| Illusion | Per | **Wil** | Magic | as Alteration |
| Mysticism | Wil | **Wil** | Magic | as Alteration |
| Restoration | Wil | **Wil** | Magic | as Alteration |

**Weapon classes map to skills** by the chassis taxonomy, not Skyrim's 1H/2H
split, so a sourced item lands in the right skill automatically:

| Skill | Classes today (`equipment/weaponClasses.ts`) | Sourced additions (decision 0031) |
|---|---|---|
| Short Blade | dagger, shortSword | parrying dagger |
| Long Blade | straightSword, scimitar, greatsword | katana, rapier |
| Blunt | mace, warhammer, staff | quarterstaff, short staff |
| Axe | axe, greataxe | poleaxe |
| Spear | spear, halberd | shortspear (1H + shield), pike, trident |
| Marksman | shortbow, longbow, warbow | — |
| Hand-to-Hand | — (70 vanilla clips incl. beast claws) | — |

Class identity (speed, reach, power, stamina, guard) stays entirely in the
existing class table: the skill positions you on a weapon's range, it never
changes what kind of weapon it is.

**There is no boat or piloting skill.** Boats gate on ownership and route
knowledge (module 60), not on a stat — a skill nobody can fail at is not a
skill. Likewise **arrow recovery** is the existing stick/break probability model
in `combat/ballistics.ts`, not Morrowind's flat 25 % rule.

## 119. Character creation

1. **Race** — attribute baselines, skill bonuses and a permanent effect package
   (§127).
2. **Birthsign — chosen directly** (owner, round 2), from the thirteen
   constellations the world clock already models (module 55 §95). The birth
   *date* stays as flavour on the character sheet and in dialogue ("born under
   the Shadow" is a canon social fact, not a mechanic); it does not decide your
   sign. A sign is a permanent effect-stack entry like any other; the slot
   and all thirteen signs are authored as data in 2.8 (decision 0144).
3. **Class** — Morrowind's structure in full: **5 major skills** (start +25),
   **5 minor** (+10), everything else miscellaneous (start 5), a
   **specialization** (Combat / Stealth / Magic: +5 to its skills and ×0.8 XP
   cost), and **2 favoured attributes** (+10). Race bonuses stack on top;
   nothing here gates anything later — it shapes *growth rates* and the
   starting shape only.

   **Eighteen presets** ship (`classes.json`), plus the custom builder. Eleven
   are the canonical Elder Scrolls classes — Warrior, Knight, Barbarian, Scout,
   Thief, Assassin, Mage, Spellsword, Nightblade, Healer, Monk — so the roster
   reads as pan-Tamrielic and every playable race has an obvious home. Seven are
   province-specific and named from canon offices in the lore dossiers: **Kaal**
   (war-captain), **Root-herald** (the tribe's outward face), **Tree-minder**,
   **Grave-singer**, **Shadowscale-trained**, **Marsh guide** and **Reed-sail
   hand**. Any race may take any class; the presets carry a "typical" line for
   the creation screen and nothing more.

Starting skill floor after all bonuses is 5; nothing starts at 0, so no skill
is unusable at creation. There are **no wield or use requirements** anywhere
(owner ruling): finding a way to a powerful weapon early is a legitimate joy.
Attribute requirements printed on items are **soft** (§121).

## 120. Progression: use, vastei, levels

Skills grow by doing; a currency called **vastei** accrues from the same
qualifying uses and is spent at the level screen to buy attribute points
(decision 0031, F1 variant ii).

### 120.1 Skill experience

The rank cost is Morrowind's, unchanged (*Morrowind:Skills*):

```
pointsToNextRank = (skill + 1) × classFactor × specFactor
classFactor       = 0.75 major | 1.0 minor | 1.25 miscellaneous
specFactor        = 0.8 if the skill is in your specialization, else 1.0
```

So a major, specialised skill costs 10 uses per rank at 15, 19 at 30, 31 at 50
and 58 at 95 — the first level is roughly twenty-five times cheaper than the
last, which is why a Morrowind-shaped curve feels generous early and slows
without ever stopping.

**The value of a use is Morrowind's too.** These are canon (each skill's UESP
page), and adopting them wholesale is what makes the pace Morrowind-shaped
rather than something we invented:

| Use | Points | Use | Points |
|---|---|---|---|
| Weapon connects | **1.0** (axe 1.2, short blade 0.75) | Block a blow | **2.5** |
| Take a damaging hit (armour skill of the struck slot, or Unarmored) | **1.0** | Cast a spell that does something | **1.0** |
| Brew a potion | **2.0** | Pick a lock | **2.0** · disarm a trap **3.0** |
| Persuade someone, successfully | **1.0** | Trade | **0.3 × the percent your skill moved the price** |
| Enchant, recharge or disenchant an item | **5.0** | Repair | **0.4** · temper **2.0** · forge **5.0** |
| Running | **0.02 / second** · swimming **0.03 / s** | Climbing | **0.2 / metre ascended** · a jump that clears something **0.15** · a survived damaging fall **3.0** |

Two of those deserve notice because they are what actually levels a character:
**Block at 2.5 a blow** is the richest tick in the game, and **Athletics is a
clock, not an action** — half an hour of ordinary travel is 36 points, free.
Morrowind levels fast early because four or five skills tick constantly during
play that is not "training" at all. Ours must too, which is why the anti-grind
rules below target *degenerate repetition* and never ordinary play.

A jump **clears something** when it lands at least 0.35 m above its take-off
or at least 2.5 m along the ground from it (`curves.jump.clearsRiseM`,
`clearsRunM`); a hop on the spot pays nothing.

Trainers and skill books grant ranks directly (§124) — **and grant no vastei**,
which closes gold → training → vastei → attributes.

### 120.2 Worthiness — the anti-grind rules ("in anger")

A use counts only if it could plausibly have mattered. This is one shared
worthiness function because vastei inherits every skill-grind exploit
(decision 0031); the simulation hunts the survivors.

| Family | A use counts when… | Damping |
|---|---|---|
| Melee / marksman / unarmed | the blow connects with a hostile, living actor that can fight back | value scales with `damageDealt / targetMaxHealth`, capped at 1 per blow |
| Block | a real incoming attack is absorbed | none needed |
| Armour skills | **two events, class-weighted** (owner, round 4 — see below): you **kill** a hostile while wearing the class, or you **take a hit** in it | kill value scales with the victim's health against yours; hit value scales with damage taken |
| Destruction / Restoration / Alteration / Illusion / Conjuration / Mysticism | the spell **has a real effect** — damage dealt, a wound closed, a lock opened, a creature summoned, a mind changed, **or a self/utility effect that mattered** (water-breathing while actually underwater, a light in the dark, feather while over-loaded, invisibility while someone could see you). Untargeted magic is not second-class: it counts when the situation it answers is real | per-spell-per-rest diminishing returns; casting a spell whose effect changes nothing — light at noon, water-breathing on dry land — is worth nothing |
| Athletics | distance covered while running/swimming **outside settlement bounds** | per-rest cap ≈ 20 minutes of travel |
| Acrobatics | **climbing** (per metre actually ascended), a jump that clears a real gap, or a survived fall that dealt damage | falls count once per location per rest (kills Morrowind's fall-grinding); climbing counts on the way *up* only |
| Sneak | you are inside a detection cone that could have seen you, and are not seen | only near actors that would react |
| Security | the lock's rating is within 10 of your current ceiling or above it | none |
| Alchemy | a brew you have not made since your last rest | per-recipe diminishing |
| Smithing | repairing real damage, tempering, or forging | value scales with condition restored / item tier |
| Mercantile | a transaction, worth what it was worth — the value that counts is capped by **how much money the merchant actually has**, so you cannot farm one village grocer by selling and rebuying the same crate | per-vendor-per-rest cap |
| Speechcraft | a check that had a real outcome (topic opened, price moved, quest branch) | never repeatable on the same NPC state |

**Worthiness scales the canon value; it does not replace it.** A blow worth
≥15 % of the target's health is a full point; below that it scales down (chip
damage on a giant is nearly worthless — the anti-grind rule), floored at 0.05.
Armour hit value uses the mirror of the same rule on damage *taken*. Blocks,
casts, brews, locks, persuasions, repairs and travel are **not** worthiness-
scaled — there is no "chip damage" equivalent for them. **There is no
repeat-target damping** (owner ruling, round 4): no reference game diminishes
repeat use, and killing respawning enemies again after a rest is legitimate
play — nobody *has* to grind, but choosing to is fine. Nothing accrues at all
against actors that are helpless through a bug (broken pathing, stuck
geometry), against creatures you summoned yourself, or against anything flagged
`trainingDummy`.

**Armour accrual in full** (owner, round 4, decision 0037). In a game where
3–6 unavoided hits kill you, Morrowind's "learn armour by being hit" is both
starved and perverse — it rewards playing badly, and a skilled light-armour
character earns nothing in their own signature skill (Skyrim has the same
defect: UESP documents letting NPCs beat on you as the standard armour-
levelling method). So armour skills earn from **two events**, each weighted by
armour class:

```
on killing a hostile while wearing the class:
  points = winWeight(class) × 3.0 × clamp(victimMaxHealth / (2 × yourMaxHealth), 0.05, 1)
on taking a damaging hit in the class:
  points = hitWeight(class) × 1.0 × hit worthiness (damage taken, as above)

           winWeight   hitWeight
light        1.0         0.25       (and Unarmored follows light)
medium       0.6         0.6
heavy        0.35        1.0
```

The kill award keys to the **corpse, never to "the encounter ended"** — so
aggroing something hard and running away teaches nothing, and there is no
survive-near-danger loophole to farm. Killing something big and dangerous next
to your own size pays a full award; squashing vermin pays the 0.05 floor. The
class weighting is the semantics of each armour: a light-armour fighter is
*supposed* to win without being hit, so wins are their teacher; a heavy-armour
fighter tanks by design, so tanking is theirs; medium sits between. Vastei
flows from both events like any other qualifying use. Blocked hits feed
**Block** (2.5 a blow), never the armour skill — the shield did that work.

**A maxed skill is never a dead end.** Once a skill reaches 100, its qualifying
uses keep earning **vastei**, and they keep feeding the level counter at the
miscellaneous rate (§120.4). Without that rule a warrior whose Long Blade,
Heavy Armor and Block are all at 100 stops progressing from fighting at all —
which is exactly what the whole-game simulation caught: **38 % of every
use-point a character generated was being discarded** into skills that could no
longer absorb them.

### 120.3 Vastei — the currency

```
vastei per qualifying use = 4 × worthiness × (1 + effSkill/50)
```

Named for the Argonian word for **change** (`vastei`; one who brings necessary
change is *ku-vastei*) — the Clutch of Nisswo's doctrine that change is the only
god, and the reason the currency is *earned by acting* and *lost by clinging*.
Deliberately **not** soul gems, which keep their canon meaning: an Argonian's
soul is Hist sap and returns to the tree (dossiers
`topics/sithis-nisswo-shadowscales.md`, `topics/hist-and-sap.md`;
`topics/magic-practice.md` records the naming). The in-game UI label is
"vastei"; the tutorial line is "the change you have earned".

A property worth knowing (it falls out of the algebra, and the simulation
confirms it): because a rank costs proportionally more use-points than a
low-worth action supplies, **worthiness cancels** — the vastei earned while
taking one rank is `4 × (skill+1) × classFactor × specFactor × (1 + effSkill/50)`
regardless of *how* you earned it. The currency therefore cannot be farmed
faster than skill ranks themselves; the only exploit surface is §120.2, which
is exactly why those rules guard both.

**It must be taught, in fiction, in the opening hours** (owner requirement,
round 2). No player arrives knowing what *vastei* is, and a currency that is
earned by acting, spent on becoming, and dropped where you die needs one clear
diegetic explanation: a **Nisswo** — a travelling preacher of change, which is
exactly what the Clutch are — puts it in their own words in the tutorial
stretch, and the level screen repeats it in one line. 2.8 shipped the
mechanic and the line; the opening's packet (3.4) owes the scene.

Rules:

- **One job**: vastei buys attribute points at a level sitting. Nothing else.
  Gold buys everything else.
- **Death**: the carried balance drops at the death spot as a recoverable pile;
  dying again replaces it (the old pile is gone). Skills, levels, items and gold
  are never lost (§126).
- **Recovery**: within **2 m** (ground distance) of the pile the floating
  prompt offers it ("Take Vastei" with the count) and the activate press takes
  it all back (`curves.vastei.pileRecoveryRadiusM`), never a search of the
  ground around it. Taking it back is not a grant. The pile shows where the
  player fell as a held gold ring the reach's size with a halo and rising wisps
  (the magic layer's `areaRing` and `selfGlow` families, `deathPileMarker.ts`).
- **Hunted**: a rest is refused while any observer searches for the player,
  whatever its notice has decayed to (`restAlertOf`); only a rest taken
  becomes the wake point.
- **Never granted by**: trainers, skill books, quest rewards or looting.

### 120.4 Levels and the level sitting

- **10 major/minor skill ranks → one pending level** (canon's `iLevelupTotal`).
  A rank in a **miscellaneous** skill — or in *any* skill already at 100 —
  counts **1 : 3**. That is a deliberate divergence: in canon misc ranks never
  level you at all, which is why Morrowind's ceiling is exactly 78. Ours is a
  slope rather than a wall, and it means no hour of play is ever worth nothing.
  The rule is **per skill**, not "once everything is maxed".
- **Resting consolidates one pending level per sitting** (§126). Health
  recomputes from the formula in §117.
- At the sitting you spend vastei on attribute points:

```
cost(attr, n) = base(level) × (1 + attrValue/50)² × (1 + 0.5×(n−1))
base(level)   = 40 × (1 + level/10)^1.3
n             = the n-th point bought in this attribute this sitting (cap 5)
```

  Three brakes in one line: attributes get dearer as they rise (a soft cap that
  needs no cap), each extra point in one sitting costs more (spread or commit —
  a real choice), and the level index means a hoarder gains nothing by waiting.
  **Unspent vastei carries over**; no level is ever wasted.

  **There is no practice discount** (owner ruling, round 4, decision 0037). An
  earlier draft priced attributes cheaper if you had recently ranked skills
  they govern — Morrowind's ×1–×5 level-up multiplier expressed as a price.
  Cut, because a discount worth up to ×5 recreates exactly Morrowind's
  spreadsheet: grind the right skills before banking a level. It also let
  gold buy cheaper attributes through trainers (trained ranks would have
  counted as practice). You spend vastei on whatever you like, at list price,
  and what you practised has already paid you once — in the skill itself.
  (The balance harness never implemented the discount, so every validated
  pace and cost figure was already computed at list price; no retune needed.)
- **Deferral is strictly bad, by construction**: purchases happen only at a
  sitting, each pending level is its own sitting priced at its own level, and
  delaying levels delays health. The simulation asserts this as the
  *no-deferral-advantage* invariant.

### 120.5 The pace we are aiming at

Morrowind is the reference, and it is a documented one. Its ceiling is exactly
78 (775 major/minor ranks ÷ 10); its own main quest gates on level 21 as
"famous enough to skip the trials"; community completions of the main line
cluster at level 20–30 in roughly 40 hours. Morrowind asks ten counted ranks
of every level, so its first level-up comes after one to two hours and the
gap only widens. We depart from it on the owner's words
([0147](../old-decisions/0147-early-levels-come-fast.md)): "level 2 after 15–30
minutes; early level-ups closer together than later ones; never ages between
levels later on". The level-up is the hook moment, so the counter asks a
**ranks-per-level curve**, `curves.levelUp.ranksPerLevel` = 1, 2, 3, 4, 5, 6,
7, 8 (entry *n* takes level *n* to *n* + 1), and every level from 8 on asks
the **ceiling of 8**. Use values, rank costs, the 1 : 3 credit and the
attribute prices are unchanged.

The pace table, measured by the campaign harness (time a level is *earned*,
its last counted rank; a rest banks it, one per sitting, §126) and checked by
`stats/balance.test.ts`:

| Measure | Target | Warrior · scout · mage |
|---|---|---|
| level 2 earned | 15–30 min | 30 · 30 · 20 min on the progression store; the harness agrees to its quarter-hour slice (0.5 h); the first rest banks it at 35 min |
| level 5 earned | — | 1.6 · 1.9 · 1.4 h |
| level 10 earned | — | 5.9 · 5.9 · 4.1 h |
| level 20 earned | — | 21.4 · 22.1 · 17.7 h |
| mean hours per level, hours 2–10 / 10–40 / 40–100 | rising | 0.9 / 1.5 / 2.4 · 1.0 / 1.7 / 2.1 · 0.8 / 1.6 / 2.3 |
| late gap (hours 40–100) | at most 2.5 h | 2.1–2.4 h, against 2.5–2.9 h under a flat ten |
| level at hour 20 / 40 / 150 | — | 19 / 33 / 75 · 18 / 30 / 73 · 21 / 33 / 77 |
| a whole campaign's end level, six builds | 50–100 | 69–90 |
| ceiling | — | none hard: the misc/maxed 1/3 tail keeps paying, ever more slowly |

The ceiling of 8 is the lowest the attribute economy carries: each sitting's
vastei comes from that level's ranks, and at a ceiling of 7 or below a
level-20 to level-30 sitting buys one point, under the 2–8 band the
`affordability-band` invariant holds (§120.4). A late gap well under two
hours (a ceiling of 5 gives 1.3–1.5 h) needs the sitting's price keyed to
something other than the level counter; that is an owner call, recorded in
0147. There is no hard level ceiling: level is bounded by hours played, not
by a wall at 78.

Two things make that pace real rather than aspirational: the canon use-values
in §120.1 (especially Block and Athletics, which tick during play that is not
training), and the rule that a maxed skill still pays (§120.2). The harness
validates the first by running the *same* campaign model under Morrowind's own
rules and checking it reproduces Morrowind's known pace — a known-answer test
rather than another guess (`packages/game-core/src/stats/sim`, `morrowind-known-answer`).

### 120.6 Where late power comes from

Not the level counter. The curve `k` flattens, attribute costs escalate, and
the biggest damage lever stays **found gear** — which in a fixed world means
power is geography you conquered. On top of that sit the mastery systems
(alchemy, enchanting, spellmaking, smithing, trade, training) that the owner
explicitly wants to be able to run away with (§102).

## 121. Combat

### 121.1 Damage

```
listedDamage = motionValue(class, attack) × material.damageScale × 24   # today's code
score        = (weaponSkill + Agility/5) / 1.2                          # Morrowind's HitRate, no dice
P(score)     = 0.40 + 0.60 × k(score)                                   # where in the range you strike
strength     = (Strength + 50) / 100                                    # Morrowind's own damage term
damage       = listedDamage × P × strength × critical × hitZone          # a weapon's condition never scales it (§121.6)
```

A blow lands when the weapon's sensor touches any of the target's hurtboxes, an outstretched limb included, as in Skyrim (owner ruling, 2.9x); reach is never tuned to exclude limbs.

**No dice (owner ruling, 2.9x).** No roll decides whether a blow lands or how
hard; the only chance draws in the game are these, all from one seeded source
per walk: the critical-hit chance (×2), enemy variety (heavy choice, strafe
side, backstep, decision jitter), archer aim spread, creature wander, and
Morrowind's Spell Absorption percentage. A new chance draw is an owner call,
never a mechanic.

Two terms, both canon, doing two different jobs. **Skill and Agility decide how
well you connect** — Morrowind rolled that same score for hit-or-miss, and we
spend it on the quality of the blow instead, which is the no-dice port of the
single most important formula in the game. **Strength decides how hard you
are** — `(Str+50)/100` is canon verbatim, neutral at Strength 50, ×0.5 at 0 and
×1.5 at 100, and canon applies it to bows as well as blades. Critical (×2) and
head-zone (×2) multipliers are today's. A weapon above 0 condition does its full
damage; at 0 it cannot be swung (§121.6).

Hand-to-hand is the documented exception: canon's unarmed damage uses neither
Speed nor Strength, only the skill, and drains stamina rather than health. We
keep that (§118).

**Stagger is poise's job** (§121.3). Morrowind's knockdown threshold —
`Agility × 0.5`, immune at 100 — survives as the *base* of the poise pool, and
whether a blow interrupts you is decided by that pool, worn armour and the
attacker's weapon-class poise damage, not by a bare damage comparison.

**Soft requirements.** Items keep their `requirements`, but they never block:
for a shortfall `d` (points below a requirement), stamina cost ×`(1 + 0.07d)`,
capped at `d = 20`. A heavy blade found early is usable, exhausting, and
glorious — at the worst possible shortfall a swing costs about 85 of a starting
character's 92 stamina, so they get one swing and a long breath.
`d` is the largest single shortfall over the weapon's requirements (the attribute
furthest below its minimum; `requirementShortfall`, `game-core/src/combat/playerModifiers.ts`),
applied in `playerMeleeModifiers` given the weapon's stats, the source the item card reads too.

**Marksman** keeps the physical ballistics model; skill and Agility drive the
existing `RangedModifiers`, and `P(effMarksman)` multiplies delivered damage
(a clean loose, not a stronger arrow). **Arrow material is its own damage axis**
(Morrowind: iron 1–3 against daedric 10–15) — good arrows are placed loot, so a
marksman's endgame damage is geography like everybody else's. Arrowheads pierce:
armour is only ~60 % as effective against an arrow as against a blade.

**Hand-to-Hand** deals low health damage but heavy **stamina** damage (§118);
an opponent whose stamina you empty is open to a knockout finisher —
Morrowind's fatigue-knockout, Souls-shaped, and it needs no new systems.
Argonian and Khajiit claw clips are already in the vault.

### 121.5 Sneak attacks

A blow landed on an actor that has not detected you is multiplied. Skyrim's
shape (*Skyrim:Sneak*: dagger ×6/×15, one-handed ×3/×6, bow ×2/×3, unarmed and
two-handed ×2), rebuilt as **Sneak-skill bands** so it needs no perk economy:

| Sneak | Dagger | Short blade | One-handed | Two-handed | Bow | Unarmed | Spell |
|---|---|---|---|---|---|---|---|
| 0–19 | ×3 | ×2.5 | ×2 | ×2 | ×2 | ×2 | ×1.5 |
| 20–39 | ×5 | ×3.5 | ×2.5 | ×2.5 | ×3 | ×2.5 | ×2 |
| 40–59 | ×7 | ×4.5 | ×3 | ×3 | ×4 | ×3 | ×2.5 |
| 60–79 | ×10 | ×6 | ×4 | ×3.5 | ×5 | ×3.5 | ×3 |
| 80–99 | ×13 | ×7 | ×5 | ×4 | ×6.5 | ×4 | ×3.5 |
| 100 | ×15 | ×8 | ×6 | ×5 | **×8** | ×4.5 | ×4 |

Skyrim's ceilings are dagger ×15 and bow ×3; ours keeps the dagger and takes
the **bow to ×8** (owner, round 3 — stealth-archery should be a build worth
committing to, not a footnote). Melee still leads ranged, because closing to
knife distance unseen is the hard part. The blow deals the multiplier times its
damage and **never auto-kills**: there is no one-shot rule and no band cap
(0151 item 1); only an aware, boss or warded target withholds it. When the
scaled blow is lethal, an unseen backstab plays the paired kill (the dagger's
vanilla sneak kill crouched); otherwise it lands as a hit. It applies to the **first blow only**;
a botched opener is just an ordinary attack, and it is the whole reason a
stealth build can punch above its armour class. In the whole-game runs it is
what carries a light-armour build through the lethal middle game.

**Ripostes and backstabs are a separate, existing system** (owner, round 4
addendum). The sandbox already ships paired criticals — a riposte after a
parry or guard-break, a backstab from behind an engaged enemy — with a
per-weapon `criticalMultiplier` (today a flat ×2 across the arsenal). The
design adopts them as-is with two rulings: the multiplier becomes
**per-weapon-class data** rather than one constant (daggers top the table,
great weapons bottom it — DS1's shape; provisional values are a sandbox
calibration, not sacred), and character skill enters only through the normal
damage pipeline (§121.1: a riposte is `listedDamage × P × strength ×
critMultiplier`) — earning the opening is player skill, so no extra stat hook.
**The two tables never stack**: a blow on an *undetected* target uses the
sneak table above, even when delivered as a backstab animation; ripostes and
combat backstabs are punishes on an *aware* enemy and use the class
multiplier. Poise break does not open a riposte — parry and guard-break do,
exactly as the sandbox behaves today.

### 121.2 Stamina

`maxStamina = 60 + 0.8×End` up to the reference End 50 (100), then `+ 4` per point above it (296 at End 99, 300 at 100), so a high-Endurance character carries a clearly long bar (owner, 2.10b); regen `12 + 0.24×Agi` per second after the
unchanged 1.05 s delay, suppressed while guarding. Action costs are today's
class-scaled values × the skill band × a burden multiplier (×1.00 fast, ×1.08
mid, ×1.20 fat). **One bar** — the second "fatigue" layer was rejected (owner
round 1, Q4); long-loop exertion (sprinting, swimming, climbing, heavy loads)
hooks this pool instead.

### 121.3 Poise (owner reversal, round 4, decision 0037)

Round 2 cut poise; the owner reinstated it at round 4, on **Dark Souls 1's
model** (researched at implementation level:
[research/combat-and-systems/dark-souls-poise-mechanics.md](../research/combat-and-systems/dark-souls-poise-mechanics.md)).
One system, shared by the player and every NPC/enemy.

**The pool.** Every character has a hidden poise pool. Each incoming hit
subtracts that attack's *poise damage* (independent of health damage). While
the pool holds, a hit interrupts nothing — a hit flash and sound, no reaction
animation. When it empties, the character **staggers** (the sandbox's existing
heavy reaction — no new animation) and the pool refills. As in DS1 the pool
does not trickle back: it refills **instantly to full** after ~5 s without
being hit. All constants live in `gear.json`/`curves.json` and are
**provisional until sandbox calibration** — poise is feel, and feel is
tuned with a controller in hand (§102), never from this document.

**Where max poise comes from** — the same trick as weapon damage (§121.1):

```
maxPoise = Agility/2  +  Σ worn pieces: piece.poiseLo + (piece.poiseHi − piece.poiseLo) × k(armour-class score)
          + effects (enchantments, spells, potions, rings, amulets)
```

- **Agility/2 is Morrowind's knockdown rule re-housed**: canon knocks you down
  when damage reaches `Agility × 0.5` — here that same number is your naked
  poise, so an agile character shrugs light hits bare-skinned and Agility keeps
  its defensive job (this *replaces* the damage-threshold stagger rule in
  earlier drafts of §121.1/§117.1 — one stagger system, not two).
- **Each armour piece carries a poise range, and your skill in its class sets
  where in the range you sit** — exactly the weapon-damage construction.
  Better material within a class raises floor and ceiling; classes tier as
  **heavy > medium > light** in both; some pieces run wider ranges than others
  (a great helm is a narrow high band; a chitin cuirass a wide low one).
- **Effects are first-class**: poise is a `StatEffect` field (§127) like any
  other, so fortify-poise potions, an Alteration "stone-flesh" spell tier,
  enchanted rings and amulets (DS1's Wolf Ring), and allegiance rites can all
  move it. So can drain/damage variants on enemy weapons.

**Attacker side — poise damage is a weapon-class stat**, DS1's shape: each
weapon class carries a base poise damage (dagger lowest → great hammer
highest), multiplied by an attack-type factor (light ×1.0, heavy ~×1.5,
two-handed and running attacks higher), all data on the existing class table —
no per-item authoring. Spells carry poise damage on the effect. Shield bash
and guard-break keep their existing special behaviour.

**Enemies use the identical system**: an enemy's poise derives from its band,
loadout and Agility through the same formula, compiled like everything else
(§128). This is what makes weapon class matter tactically — a dagger build
interrupts nothing big and relies on not being hit; a great hammer staggers
through anything smaller than a troll. Boss-grade actors may carry
`staggerable: false` exactly as DS1's biggest bosses do.

**What poise touches elsewhere**: the weapon data model gains
`poiseDamage` (class level), the armour model gains `poiseLo/poiseHi` (piece
level), the effect stack gains `poise` and `blockStability` fields, and the
ladder compiler emits poise per actor. A hit staggers only when it breaks
the pool (`combat/poise.ts`). i-frames, parry windows and attack
windups remain untouched by all of this (§102).

### 121.4 Defence

```
mitigation = AR / (AR + 135.6 + 0.6 × incomingDamage)  # 0…1, never reaches 1
AR = Σ worn pieces (× that class's armour-skill band) + unarmoured contribution + effects
```

with `constant = 135.6` and `damageCoefficient = 0.6`. Today's asymptotic curve
with one addition: **big hits punch through**. At the reference (AR 50, a
24-damage blow) it returns exactly today's 25.0 %; best-in-slot plate (AR ~406)
turns 73 % of a light blow but only 56 % of a D5 one, and even then the hardest
hit in the game still takes a fifth of that character's health. Armour that
helps everywhere and trivialises nothing — Morrowind's `min(1 + AR/dmg, 4)`
behaviour, expressed in our curve so the reference is preserved.

**Armour has its own material ladder**, separate from the weapon damage ladder
and far steeper (Morrowind's runs 8× from iron to daedric; the weapon ladder
runs 2.3×). Steel is 1.0, so the reference set still rates 50:

| | studded | iron | steel | imperial | dwarven | elven | orcish | akaviri | glass | ebony | daedric |
|---|---|---|---|---|---|---|---|---|---|---|---|
| armour scale | 0.55 | 0.75 | **1.00** | 1.10 | 1.60 | 1.50 | 1.90 | 2.20 | 2.60 | 3.40 | 4.40 |

This is what makes "typical endgame armour = three unavoided blows,
best-in-slot = five or six" possible at all; with the weapon ladder reused for
armour the entire endgame sat inside a factor of 1.4. **Armour class then
scales the rating**: light ×0.75, medium ×0.9, heavy ×1.0 — light armour
protects meaningfully less and weighs far less, which is the trade the class
choice is supposed to be.

**Armour classes are a per-material data tag** — no new assets, the Morrowind
category reintroduced by reclassification:

| Class | Materials |
|---|---|
| Light | studded, elven, glass, forsworn |
| Medium | imperial, falmer (chitin), draugr (ancient mail), orcish, akaviri |
| Heavy | iron, steel, silver, dwarven, nordhero, ebony, daedric |

**One global lethality knob.** `difficulty.enemyDamageMultiplier` multiplies
incoming enemy damage and nothing else — not populations, not loot, not gates,
so decision 0004 is untouched. It exists so the whole game can be made harsher
or gentler in one number, and it is the natural back-end for a **play-time
difficulty setting** (0.7 forgiving / 1.0 normal / 1.35 harsh). 2.8 shipped
the knob (`difficultyMultiplier` on enemy blows); the setting screen comes later.
The knob scales the **whole** enemy blow, blocked or not: a guard's chip and
its stamina cost are taken from the scaled blow (`resolveHit.ts`). One rule
with no exception is the cleanest, and it keeps the balance between options
fixed: were blocks unscaled, a harsh setting would make turtling relatively
cheaper and a forgiving one would leave blocking as costly as before, so the
setting would change the best tactic instead of only the lethality. At 1.0
nothing differs (owner call, 2.9b).

Beast races wear **every** piece they can wear in Skyrim (owner veto of the
canon boot/closed-helm ban).

### 121.6 Blocking, condition, and what skill never touches

Blocking is the sandbox's existing stability/absorption/chip/guard-break system;
Block skill scales stability and cuts guard stamina cost. **Stability is also
an effect-stack field** (owner, round 4): enchantments, spells and potions can
fortify a shield's or weapon's block stability like any other stat (§127).
**Condition**: every
item has 0–100 condition, worn by use and by blocking. **A weapon is unusable at
condition 0 and does its full normal damage at any condition above 0** (owner
ruling, 2026-10-24): no scaling, no floor. The attack is refused with "Your
weapon is broken" and nothing is spent; it **never breaks mid-swing** — no
surprise. Enemies' weapons carry no condition, so the rule is the player's.
Worn armour still guards in proportion to its condition (`effectiveness`, never
below the economy table's `services.conditionFloor`). Repair is Smithing plus a hammer, or a service (§124).
The repair hammer wears per stroke by its record's `condition.wearPerUse`:
max 100, 4 a stroke, 25 uses (the economy table's `services.repairHammer`;
Morrowind's cheap tiers last 20 to 25, dossier `tool-wear-morrowind`).

Never stat-scaled, ever: i-frames, parry windows, attack windups, contact
windows, input buffering (§102).

## 122. Movement, burden, swimming, climbing

**Burden ratio** `r = carriedKg / (30 + 3×Str)`:

| r | Tier | Roll distance | Roll recovery | i-frames | Stamina |
|---|---|---|---|---|---|
| < 0.20 | fast | ×1.10 | ×0.90 | ×1.15 | ×1.00 |
| < 0.35 | **mid** (the reference) | today's roll exactly | ×1.00 | ×1.00 | ×1.08 |
| < 1.00 | fat | ×0.80 | ×1.25 | ×0.80 | ×1.20 |
| ≥ 1.00 | overloaded | no roll at all | — | — | cannot run, jump or swim upward; walk at 40 % speed; may still fight and cast (Morrowind's hard stop, softened so it is never a soft-lock) |

**Invulnerability frames do vary by tier** — Dark Souls 1's behaviour
(13 / 11 / 9 frames at light / medium / fat), and the reason the rule in §102
is worded the way it is: *stats* never touch i-frames, because a hidden stat
gating a feel verb is the Dark Souls 2 Adaptability mistake. Equip load is not
a hidden stat; it is a visible choice you make every time you pick up a
breastplate, and the game tells you which tier you are in. (DS3 and Elden Ring
flattened i-frames across tiers instead, varying distance and recovery only —
if playtesting says our roll reads better that way, it is one constant.)

The thresholds are calibrated so the reference kit is *mid*, a full endgame
plate kit is *fat* until Strength grows into it, and a looted-up hoarder is
*overloaded*: carrying capacity is a real progression axis rather than a
formality.

### 122.1 Climbing (the Acrobatics verb)

BotW-style climbing is a **stamina problem governed by Acrobatics**, and it is
the reason the skill exists alongside Athletics:

```
climb speed      = 1.1 m/s × band(0.85 → 1.25)
stamina drain    = 7.5 /s × band(1.25 → 0.75) × burden (fast 0.85 / mid 1.0 / fat 1.35)
mantle at the top= 18 stamina × the same band       ledge grab = 8
hanging still    recovers 12 % of normal stamina regen
```

What that produces, which is the point of stating it in numbers:

| Climber | Speed | Drain | Reach (with rests) |
|---|---|---|---|
| Hour one (Acrobatics 15, mid load) | 1.0 m/s | 8.52 /s | ~12 m |
| Competent (45, mid load) | 1.2 m/s | 7.1 /s | ~24 m |
| Scout (70, light load) | 1.3 m/s | 5.2 /s | ~63 m |
| Master (100, light load) | 1.4 m/s | 4.8 /s | 160 m+ |

**The underwater contract, for authors** (the sibling of the climbing one
below): **a 30-second submerged stretch is open to everyone, 45 s wants a
competent swimmer, 60 s a specialist, and beyond 75 s is Argonian, spell or
equipment ground.** No route is ever mandatory-Argonian — water breathing
creates advantages, never exclusive progression (quests 80 §63), so every such
route needs a degraded alternative (quests 20 §11).

So a cliff is a **gate you can see** — a beginner reads 12 m of wall as "not
yet", and the same wall is nothing to a scout. Falling costs the §122 fall
rules; being overloaded means you cannot start. Authors get a simple contract:
**a wall under 10 m is open to everyone, 25 m wants a real climber, and beyond
40 m is specialist ground** — and, like every other capability, a climb-only
route needs a fallback (quests 20 §11).

Everything the world's traversal validation consumes is a
`TraversalCapabilityProfile` field, generated from the stat system
(§52) instead of hand-set:

Movement is the one place canon ports almost verbatim, because Speed appears
in no dice roll anywhere in Morrowind — it simply *is* how fast you go:

| Field | Formula | Canon it comes from | Reference |
|---|---|---|---|
| walkSpeed | `4.5 m/s × (0.75 + Speed/200) × (1 − 0.3 × loadRatio)` | `WalkSpeed = 100 + Speed`, `× (1 − 0.3 × encumbrance)` — compressed from canon's 2× spread to 1.7× so combat spacing survives | 4.5 m/s |
| sprintSpeed | `walk × (1 + Athletics/250)` | `Run = Walk × (Athletics/100 + 1.75)` — same shape, compressed | 6.0 m/s |
| swimSpeed | `1.6 m/s × (0.5 + Athletics/100) × burden penalty` | canon's `0.5 + 0.02×Athletics` walking / `0.5 + 0.1×Athletics` running; kept near-full strength because swimming is a pillar | ~1.5 m/s |
| jumpApex | `1.378 m × (0.80 + Acrobatics/125)` | canon's two-part Acrobatics jump curve, smoothed | 1.378 m |
| safe fall | `2 + Acrobatics/25` metres | canon reduces fall damage by 1.5 per Acrobatics point | ~3.6 m |
| breathSeconds | `25 + 0.35×Athletics + 0.25×End`, **unlimited for Argonians** | canon is a flat 20 s for everyone; ours is skill-driven because underwater play is a pillar | 49 s |
| climbSpeed / gripStamina | `1.1 m/s × Acrobatics climb band` / drain × its stamina band (§122.1) | ours — Morrowind has no climbing | — |
| currentResistance / depthTolerance | End + effects (spells and gear can move both) | ours | — |

Touch sprint band (input tuning, `TOUCH_SPRINT_ENTER`/`LEAVE` in `packages/game-core/src/io/input.ts`): the stick sprints from 0.95 of travel and keeps it down to 0.85; below that is the stamina-free run. 

Encumbrance's speed penalty is canon's coefficient exactly (`×(1 − 0.3 ×
loadRatio)`), and it stacks with the roll tiers above rather than replacing
them: load costs you speed continuously and roll quality in steps.

Authored underwater routes are validated against profile **ranges**, so world
data never encodes a speed (module 60 §43). Spells, potions and enchantments
modify these like anything else (§127) — a water-breathing charm is a route
opener, never a mandatory gate (quest rule).

## 123. Magic

**Casting never fails.** Morrowind's cast dice are the magic twin of the
misclick-miss, and they are gone.

- `maxMagicka = 20 + 3×Int` × race/birthsign multipliers; regen
  `0.5 + 0.05×Wil` per second, full restore at rest. Both were raised by the
  balance sim: at the first (Morrowind-sized) values a mage could not sustain a
  boss fight even with a full potion belt. An Atronach-style sign may
  remove regen and add absorption — the hook exists.
- **Six schools** (Alteration, Conjuration, Destruction, Illusion, Mysticism,
  Restoration) as skills, plus Alchemy and Enchant. Mysticism survives here as a
  folk school (§118).
- **What you can cast is canon's own boundary, turned into a gate.** Morrowind
  computes `chance = 2 × schoolSkill + Willpower/5 − spellCost` and rolls
  against it; below zero the spell simply never works. We keep the expression
  and drop the roll:

  > **A spell is castable when `2 × schoolSkill + Willpower/5 ≥ spellCost`.**

  A novice (skill 10, Willpower 30) can manage a 26-point spell; a master
  (skill 100, Willpower 100) reaches 220. Nothing fizzles, nothing is wasted,
  and the thing skill buys is the *size of spell you can hold* — which is what
  it bought in canon, minus the frustration. The familiar tier names are
  descriptive labels over cost ranges, not separate machinery:

  Two refinements the harness forced. Canon's boundary is where the chance
  reaches *zero*, which is not a spell you would actually carry, so the
  reliable line sits **50 points inside it**: `castable ≤ 2 × skill +
  Willpower/5 − 50`. And a caster does not lead with the largest spell they can
  hold — the working spell is about **60 %** of it. That puts a starting mage on
  a ~19-damage spell and a master on ~100 before magnitude and gear, which is
  where Morrowind's own starting and master spellbooks sit. The gate is
  canon's boundary (the cast cycle refuses past it, and a seller stocks
  anything inside it); the reliable line and the working fraction are only
  the rule for which spell a caster leads with (`ai/casterSeam.ts`), and the
  stats sim's working spell.

  | Tier | Typical cost | Reachable at |
  |---|---|---|
  | novice | ≤ 15 | skill ~5 |
  | apprentice | ~30 | skill 12–15 |
  | journeyman | ~60 | skill 25–30 |
  | expert | ~110 | skill 50–55 |
  | master | ~180 | skill 85–90 |

  Spell damage is elemental: it **bypasses physical armour** and meets magic
  resistance instead (which is why a mage keeps pace against heavily-armoured
  endgame enemies), and it is the highest burst in the game — bounded by
  magicka, not by damage. Canon leaves spell magnitude *flat* — skill bought
  only reliability — so scaling magnitude with skill (×0.75→1.25) is our
  divergence, and a deliberate one: with the reliability roll deleted, skill
  needs something to buy, and Skyrim's flat-magnitude late game is the
  cautionary tale.

  **Willpower also resists.** Canon's magic resistance is `Willpower × 1.0` —
  the single largest attribute coefficient in the game — rolled against the
  incoming effect. Ours is deterministic and gentler: **innate magic resistance
  = Willpower/4 percent** (25 % at Willpower 100), stacking additively with
  racial and worn resistances and clamped at 100.
- Cost, cast time and magnitude scale on the same bands as weapons (§118), so
  **every damage source sits on one multiplier stack** — the fix for Skyrim's
  late-game Destruction collapse. The quest plan requires the hardest fight to
  be winnable by a magic build; this is what makes that true.
- **Spellmaking**: Morrowind's model — up to 8 effects, fee = 7 × magicka cost,
  magnitude/duration bounded by school skill and Int. Spells you cannot afford
  to cast are makeable and useless, which is self-limiting.
- **Spell-cost reduction** from enchanted gear is the classic mage endgame and
  we keep it, **capped at 75 %** across all sources (owner, round 2: rare,
  hard-won gear should hit hard). Every spell still costs something, so no
  infinite-cast loop exists — Skyrim's 100 %-reduction exploit is closed by the
  cap rather than by removing the fun. Reaching the cap should take genuinely
  rare, placed items, not shop stock.
- **Enchanting**: your point budget is canon's success formula solved for
  points — Morrowind rolls `Enchant + Int/5 − 3 × points`, so the largest
  enchantment you can reliably make is **`points = (Enchant + Int/5) / 3`**
  (40 points at Enchant 100 / Intelligence 100). Item capacity by
  slot/material/weight bounds where it can go; charged-item use cost is canon
  verbatim, `×(1.1 − Enchant/100)`. **Constant effects are tiered by soul size, not one
  flat gate** (owner, round 2 — they are one of the most enjoyable things in
  Morrowind and small ones should be attainable): a petty soul (30) buys a
  small permanent effect, a grand one (600) buys a large one, with lesser,
  common and greater in between: a soul caps a constant effect's magnitude at
  its capacity / 600 of that effect's full range (the largest magnitude any
  catalogue spell gives it; `magic.json` `constantEffectMagnitudeShareBySoul`),
  and skill still sets the point budget on top.
  **Learn-by-disenchanting** (the Skyrim keeper): destroying a magic item
  teaches its effect. Enchanting services exist and are expensive.
- **The crafting loop is allowed, and priced** (owner, decision 0144):
  crafting reads the **effective** skill and attributes, fortified or
  drained, so a fortify-Alchemy brew does make the next brew stronger.
  The loop is bounded by supply, not by rule: every source of a fortify
  effect on a crafting skill or on a crafting input attribute, whether a
  spell, a scroll, an ingredient or a soul, is **rare or expensive** (a
  handful of placed sources in the province, no common spell merchant
  sells it, high purchase price, no vendor restock of the rare ones), so
  the climb costs real exploration and gold each step and cannot be
  ground on a village grocer. The spell catalogue (2.9) and the
  ingredient table (2.9b) flag these effects and the integrity gate
  checks their sources stay scarce.
- **Scrolls** are single-use, unbounded by school skill, and deliberately
  spicy — the sanctioned early-power easter egg (jump-scroll rule, §102).
- **Casting in the hand** (decision 0146): a spell is equipped in a hand
  like a weapon; each hand takes a weapon, a spell, a torch or a shield,
  equipped from the inventory, the magic window or the quick belt (a belt
  press rotates its spell, weapon or shield into a hand, displacing what
  was there; nothing casts from the belt), and the
  same spell in both hands dual-casts at Skyrim's ratios, magnitude ×2.2
  and cost ×2.8 (`magic.json` `dualCast`). Hold to charge, release to fire;
  stream spells run while held and drain per second. A hit that breaks
  poise interrupts the cast. Fire, frost and shock resist separately.
  Powers are once a day.
- **Who sells and teaches** (0146): spells are bought from folk
  practitioners (tree-minders, Nisswo), taught informally, found as
  scrolls, or held from the start by class and race. A seller's stock is
  a pick of the spells their own compiled skills could cast, plus a
  signature list; no guild or order record decides it. The pick (0148,
  dossier `topics/spell-sellers.md`) holds 10 to 24 spells, around
  Morrowind's median of 15. The count rises with the best school skill.
  Each school's share follows the role (tree-minder, priest or
  hedge-caster) and the seller's skill in it. The pick is seeded by the
  seller's id. No Tribunal-named, person-named, shrine or birthsign row is
  sold.
- **Levitate speed** (derived from OpenMW, dossier `topics/magic-effects.md`):
  `(5 + 0.01×(Speed + magnitude)×295) × (1 − 0.3×load)` Morrowind units per
  second × 0.01428 m, in `magic.json` `levitate` and `levitateSpeedMps`;
  Speed 50 gives 2.6 m/s at magnitude 10 and 3.4 m/s at 30.
- Folk magic is the province's register (dossier `topics/magic-practice.md`):
  day-labourers casting Illusion, Hist spore-clouds, dream-wallow visions. No
  robed-mage guild is implied by any of this.

## 124. Crafting, economy, services and crime

**Alchemy** (Morrowind's shape, on effective stats; the fortify loop is
priced by rarity, §123):

```
strength = (Alchemy + Int/10) × apparatusQuality / (3 × effectBaseCost)
duration = (Alchemy + Int/10) × apparatusQuality / effectBaseCost
```

An effect on a current pool (health, stamina, magicka) has its strength times
magic.json `magnitudeMultiplier` (18, the heal-amount scale); a stat effect keeps the formula's points.

Canon verbatim (*Morrowind:Alchemy*), including the oddity that Intelligence
enters at half weight here (`/10`) where it is `/5` almost everywhere else.
Canon's creation roll is deleted: a brew always succeeds, and the skill decides
how *good* it is. Ingredient effects become visible at skill 15/30/45/60 —
canon's `fWortChanceValue` of 15, unchanged. Regional ingredients
come from the lore ecology feed. Potions are the healing economy (§126).

**Weapon poisons and oils** (owner, round 4 addendum — the Oblivion/Skyrim
mechanic): a brew whose effects are harmful (poison, drain, paralyze) or
elemental (a fire oil) can be **applied to an equipped weapon** instead of
drunk. Skyrim's delivery rule, kept for its simplicity: the application coats
the **next successful hit**, which delivers the effect onto the victim
through the ordinary effect stack (§127), then wears off. Potency and
duration come from the same alchemy formula above; applying is a real-time
action with a commitment animation, like drinking. Arrows can be coated the
same way (one coating, one arrow). The standing bounds apply — resistances
resist (an Argonian shrugs your poison), and the brew is the same alchemy product economy, so poisons are
bought, brewed, looted and priced like any other potion.

**Smithing** merges Morrowind's Armorer with Skyrim's forge: repair (rate and
achievable ceiling by skill), **tempering** to at most three grades (gated at
effSkill 25/55/80, each grade ≈ +8 % damage or AR — material tier is a crafting
gate, not a danger band: a grade-3 cheap weapon may out-hit a plain better metal,
because the better metal's tempered version still beats the cheaper one's, so
forging and tempering the better one stays worth it), and crafting up to material tier `1 + floor(effSkill/14)`.
A stroke restores the §118 band (6→22) and never fails; repair restores up
to the item's max condition at any skill (economy `services.repairCeiling`
1.0, a fraction of max). Skill sets the rate, never the ceiling.
Smithing reads effective stats like the other crafts; a fortify-Smithing
source is rare or expensive by the §123 rule.

**Trade and what replaces haggling.** Morrowind's price is already
deterministic — only the *haggle* was a roll. Canon builds two terms,
`pcTerm = (Disposition − 50) + min(Mercantile,100) + min(0.2×Personality, 10)`
and the merchant's mirror image, and prices the trade on their difference. We
keep exactly that and delete the haggle:

```
advantage  = pcTerm − npcTerm                       # canon's two terms, no Luck, no roll
buy price  = base × clamp(1.35 − advantage/200, 0.80, 1.35)
sell price = base × clamp(0.55 + advantage/200, 0.55, 0.95)
```

So an unskilled, disliked stranger pays about 1.5× what a skilled, welcome one
pays, and sells for about half as much — a 3× swing across the whole system,
which is worth investing in without ever opening a minigame. No repeated
haggling attempts, no "offer" button.
**Vendor purses are finite and refresh on a schedule**, which is also why
Mercantile use cannot be farmed on one village grocer (§120.2). A purse is the
trade class's `purse`, its Skyrim VendorGold list (general 750, provisioner
100, smith 1000, apothecary 500, salvage fence 1000; a trader in kind 0),
times the place tier's `vendorPurse` multiplier (city 1, town 0.75, village
0.5, interior 0), refilled every 48 h; the village multiplier is Skyrim's own
step from a city smith (1000) to a village one (500). **Rich buyers** carry
Morrowind's structure on that index: two people with a fixed purse at
Morrowind's ratio to its Trader median (400), applied to the general trader's
village purse (375): the Reed-Sail Compact's flotilla speaker at Lilmoth's
lighter moorings, 9,375 (Mudcrab merchant 10,000, 25×), and Chasepoint's
station-keeper on the wrecking coast, 4,688 (Creeper 5,000, 12.5×). Like
Morrowind's rich creature merchants they trade at base value, no band
(trade class `atBase`). Disposition
moves with race and faction priors, deeds, gifts, bribes and quest state
(§125). Reward design still holds that
"gold is the least interesting thing we can give" (quests 00 §4) — gold's real
job is to feed training, services, potions and enchanting.

**Training and services**: a trainer raises a skill by one rank per session at
canon's price — **10 × the current skill level** in gold (*Morrowind*'s
`iTrainingMod`), then through the barter formula above, so disposition and
Mercantile move it. That is ≈8,000 gold to take a skill 30→50 and ≈45,000 from
30→100: a major sink, and the reason gold matters in a province where quest
rewards are access rather than coin; **a skill can never be trained above its
governing attribute** (reads *base* values, so drain-and-train is dead). Skill
books grant one rank each, five per skill. Neither grants vastei (§120.3).
The training multiplier 10 is also Skyrim's (`fTrainingMultCost` 10). A spell
costs **2 gold per point of magicka** before the band, Skyrim's spell-tome
median (1.86 a point, `skyrim-tier-reference.json spellTomes`).
Services: repair, enchanting, spellmaking, recharging, cure disease, guides,
ferries, tolls, information (Ahnjazzi's danger oracle) — the sinks that make
gold matter.

**Crime is assessed as an Owing debt**, not a gold bounty (owner round 1, 13a):
the province has no courts, treasury or state prisons (quests 10 §5). A witnessed
crime produces an assessment in *nushmeekos* against the ledger, with regional
parameters (who assesses, at what rate, how transferable), city jails as the only
custodial fallback. At a guard stop the player pays the assessment in gold,
serves it as custody (the clock advances, pending skill progress is lost) or
resists and fights the watch (decision 0151). Audit, buy out and burn are
the Owing as the quest lines use it (the Chainbreakers' bookkeeping), never
a guard-stop verb. Debt is never a player-spendable currency.

## 125. Speech, disposition and standing

Speech is a **first-class, ending-grade system** (owner round 1, 13b): every
ending family must be resolvable by speech-plus-evidence or a hard fair duel.

```
persuasionScore = Speechcraft + Personality/5 + standing      # canon's own rating
                + evidenceBonus (authored flags)               # ours: the quest layer
threshold       = authored, scaled by 1 − 0.01 × (disposition − 50)
```

The first line is Morrowind's persuasion rating verbatim minus Luck
(*Morrowind:Speechcraft*: `Speechcraft + Personality/5 + Luck/10 +
Reputation`); Luck is out because nothing here is luck. The disposition
factor is canon's `d` term and is signed: a warmer target (above 50) lowers
the threshold, a colder one raises it. The verb bases and slope are data
(`PERSUASION_RULES`, `packages/dialogue/src/persuasion/persuasion.ts`). What we add is
the evidence bonus and the authored threshold in place of the roll.

Checks are **authored thresholds** — never dice, never skill alone. A check
publishes what it wants, so a quest author can require "evidence X plus a
moderate tongue" or "no evidence, but a formidable one". Disposition is per-NPC,
moved by race/faction priors, deeds, gifts, bribes and quest state.
`FactionStanding {membership, rank, reputation, competencyFlags, sponsors}`
(quests 40 §27–28) supplies advancement and topic gates.

**Every stat gate must be expressible in the quest plan's finite typed condition
vocabulary** (quests 80 §58): `attributeAtLeast`, `skillAtLeast`,
`persuasionAtLeast`, `capabilityProfile`, `effectActive`, `itemInInventory`,
`factionStanding`, `evidenceFlag`. Nothing in this design requires new NPC
perception or pathing AI (the deliverability bound).

Speechcraft and standing are on the quest plan's inspectable-capability list
(quests [60 §49](../quests/60-writing-and-lore.md)), so a
quest author can gate a route on a persuasion threshold the same way they gate
one on water breathing.

## 126. Health, rest, death and respawn

**Healing is potions** (owner round 1, Q7 = Morrowind-style). The estus flask is
**cut**. Potions heal instantly and are stackable; their
bounds are weight, gold, alchemy skill, ingredient scarcity and the drink
animation (~0.9 s with recovery — a real commitment in a fight, never a
cooldown). Restoration spells heal too, on the same effect stack. This follows
directly from the owner's ruling that fixed difficulty binds the world and not
the player's capacity to cope (§102).

**Rest** is the one mechanic that carries: it saves, consolidates one pending
level and opens the attribute sitting (§120.4), restores health/magicka/stamina,
and (with safe-rest knowledge, decision 0007) feeds access progression. You may
camp **anywhere calm in the wild** — never in a dungeon, never in combat, never
while hunted — but **not inside a settlement** (decision
0039 S3): in towns you may only **wait** (passes time, no
save/level/recovery); resting there needs a bed you own or rent, which makes
inns economically real. Beds carry **quality tiers** (camp < rented bed < owned
bed): a rented or owned bed grants a **rested** entry on the effect stack,
skill experience ×1.05 for eight game hours (owned ×1.08), a camp grants
nothing beyond the sitting (decision 0144) — tiering yes, hunger-style
survival pressure no (0039 S2: cut). A hidden suspend-save covers browser
interruption.

**Death**: you wake at your last rest. The world and your character persist; no
skills, levels, items or gold are lost; your carried **vastei** stays where you
died as a single recoverable pile, and dying again replaces it.

**Respawn-on-rest** (owner ruling, decision 0031, binding on 2.4, 2.7 and every packet that places actors):
generic enemies — creatures, wildlife, miscellaneous dungeon denizens — respawn
when the player rests; **named NPCs, minibosses, bosses and quest actors never
do**; a cleared dungeon flips its generic population to non-respawning
(completion authored per dungeon); **waking from death counts as a rest**, so a
retrieval run crosses repopulated ground. Respawned creatures carry only their
template drops — **placed treasure never respawns**, so decision 0004 is intact.
The data model is a per-actor/per-socket respawn class
`onRest | never | untilCleared`, emitted by the roster and encounter compilers (2.4, 2.7).

## 127. Races, birthsigns and the one effects stack

Racials are **Morrowind-weight**: permanent, build-defining packages, not
Skyrim's erasable +10s. Each race is `{attributeBaselines, skillBonuses,
effects[], powers[]}`. Argonian, exact (canon, *Morrowind:Argonian*):

- attributes M Str 40 / Int 40 / Wil 30 / Agi 50 / Spd 50 / End 30 / Per 30
  (F: Int 50 / Wil 40 / Agi 40 / Spd 40) — Luck's 40 is dropped with Luck;
- Athletics +15; Alchemy, Illusion, Medium Armor, Mysticism, Spear,
  Unarmored +5;
- **Resist Poison 100 %**, **Resist Common Disease 75 %**, **water breathing**
  (unlimited breath, §122);
- **no gear restrictions** (owner veto).

Other playable races port their Morrowind packages the same way (Breton magicka
and magic resistance, Dunmer fire resistance, Nord frost, Orc berserk, Redguard
adrenaline and poison/disease resistance, Bosmer/Khajiit stealth packages,
Altmer magicka with elemental weaknesses, Imperial personality/mercantile).

**One effect stack.** A `StatEffect` is
`{field, op: fortify|drain|damage|restore|resist|absorb|ability, magnitude,
duration|permanent, source}`, applied over base values. Every one of these is
the same kind of object:

| Source | Example |
|---|---|
| Race | Argonian Resist Poison 100 |
| Birthsign | Steed +25 Speed; Atronach absorption, no regen |
| Disease / blight | swamp fever: −10 End, −15 Athletics until cured (module 30 §26) |
| Potion / poison | Restore Health 60; Fortify Long Blade 10 for 60 s |
| Spell / enchantment | Water Breathing; Feather 80; Fortify Strength 20; Fortify Poise 25 (a stone-flesh ring); Fortify Block Stability 10 |
| **Allegiance rites** (decision 0028) | corprus-style permanent packages: +Str/+End, −Wil/−Per, deepening per tier |
| Hist / quest state | permanent boons and marks |

Bounds carried from §123: crafting reads effective values, and every source
of a fortify effect on a crafting skill or input attribute is rare or
expensive. Resistances are additive
percentages, clamped to 100 % for "immune" and allowed negative for weaknesses.

**The thirteen birthsigns** (Morrowind's, exact; dossier
`world/sources/lore/topics/birthsigns.md`; data `stats/data/birthsigns.json`).
Constant abilities are stack entries; the powers and spells are rows of
`packages/magic/src/data/spells.json` (`BIRTHSIGN_SPELL_IDS`).
"×Int" adds to the §123 magicka multiplier.

| Sign | Month (guardian) | Stack entries | Powers and spells |
|---|---|---|---|
| Warrior | Last Seed (guardian) | attack +10 | — |
| Mage | Rain's Hand (guardian) | magicka +0.5 ×Int | — |
| Thief | Evening Star (guardian) | sanctuary +10 | — |
| Lady | Hearthfire (Warrior) | Personality +25, Endurance +25 | — |
| Steed | Midyear (Warrior) | Speed +25 | — |
| Lord | First Seed (Warrior) | fire resistance −100 | Blood of the North |
| Apprentice | Sun's Height (Mage) | magicka +1.5 ×Int; magic resistance −50 | — |
| Atronach | Sun's Dusk (Mage) | magicka +2.0 ×Int; spell absorption 50; magicka regen ×0 | — |
| Ritual | Morning Star (Mage) | — | Mara's Gift; Blessed Word, Blessed Touch |
| Lover | Sun's Dawn (Thief) | Agility +25 | Lover's Kiss |
| Shadow | Second Seed (Thief) | — | Moonshadow |
| Tower | Frostfall (Thief) | — | Tower Key; Beggar's Nose |
| Serpent | none: it wanders the sky and has no month | — | Star-Curse |

`attack` and `sanctuary` (Morrowind's hit and evasion chances) sit on the
stack and the sheet; no combat formula reads them yet.

## 128. The absolute ladder (D0–D5) and the NPC/enemy model

Fixed danger means every actor, item and trap resolves to fixed absolute
numbers that never read player state — authored **semantically** and compiled
(§128.2). The bands are what a 4.2 packet author means by "a D3 creature" —
anchored so the reference character (§116) finds D2 a fair fight and D4 a bad
idea.

**D0 is not a combat rung.** The province's danger vocabulary is set by the
quest plan (quests 20 §12) and decision 0009: **D0 means safe ground** — city
streets, civic buildings, faction halls, settlement interiors — where ordinary
crime happens but no ambient lethal ecology does. It is an authored *location
property*, not a band of the compiled danger field (which runs 1–5 and has no
band 0). A dungeon entrance inside a city carries its own band, authored
separately. Where a settlement is written "D0–D2", read it as *safe interior,
band 1–2 surrounds*.

So the combat ladder has **five rungs, D1–D5**, and vermin live at the bottom
of D1 rather than in a tier of their own:

| Band | Meaning (quests 20 §12) | Health | Light hit | AR | Magic resist | Blows that kill you |
|---|---|---|---|---|---|---|
| D0 | **safe** — no ambient hostiles at all | — | — | — | — | — |
| D1 | low — vermin at the bottom, an unprepared traveller may survive at the top | 18–28 | 4–14 | 0–18 | 0–10 % | 6 |
| D2 | standard — a new but prepared character survives | 27–62 | 24–40 | 18–45 | 10–20 % | 4 |
| D3 | substantial combat/traversal capability required | 40–90 | 52–92 | 45–80 | 15–30 % | 3.5 |
| D4 | specialist equipment, route knowledge, allies | 50–110 | 120–210 | 80–130 | 20–35 % | 3 |
| D5 | fixed endgame, reachable early, never scaled | 96–205 | 185–320 | 100–170 | 25–45 % | 3 |

**The last column is the design input, and the damage column is derived from
it** (owner ruling, round 2: *getting hit must matter*). "Blows that kill you"
means completely unavoided, unblocked hits landing on the character the band is
meant for, in typical armour for their stage. Heavy armour of the day buys a
blow or two more; genuinely best-in-slot, tempered, enchanted plate buys five or
six — and nothing buys more than that. Change the target, re-run the
calibration, and every band's numbers move together.

`damage` is a **typical light hit**; heavy attacks land at ~2.4× it. Attack
period runs 3.0 s (a mudcrab) down to 1.8 s (D5). Loot value runs 2 → 2200
gold. **Poise is not a hand-authored column**: an actor's poise derives from
its Agility, loadout and variants through the player's own formula (§121.3),
compiled with everything else; boss uniques may set `staggerable: false`.

D1 is deliberately the widest band, because "not really dangerous" covers
everything from a mudcrab to an armed smuggler; the *position* within the band
carries that range (a mudcrab is D1 @ 0.05, a smuggler D1 @ 0.85). Bands D2–D5
map one-to-one onto the compiled danger field's bands 2–5.

**Variants may not invent a tier**: a compiled field is clamped to ±25 % of its
band's edges, so "strong armoured" stays a hard D5 rather than a secret D6.

Boss uniques may exceed D5 on named fields: the `boss` variant
(`bossVariants` in `ladder.json`, health ×5) is exempt from the clamp on the
fields it names.

**The invariant that makes the ladder meaningful** (owner's own test): a D5 NPC
in D5 gear near-one-shots a starting character and takes negligible damage from
one — verified in the simulation: a mid-D5 blow lands 263 on a level-1
character with 44 health, and that character's reply is 6.4 against 151 health
(4.2 % a swing).

**What the simulation says the ladder feels like** (full report:
[the harness findings](../research/archive/workstream-s/stats-sim-findings.md);
§128.1 for the toughness counts): an endgame build kills the final boss in
21–57 s depending on archetype (melee, greatsword, spear, marksman, stealth
and magic all inside a ×2.8 spread).

**Every NPC, enemy and merchant carries the player's schema plus a level** — attributes, skills, equipment, effects, respawn class, plus the AI
profile fields the archetype already has. **Authoring is semantic, compiled to
absolutes** (decision 0019's fourth amendment):

```jsonc
{ "id": "swamp-troll-fen",
  "band": "D3", "position": 0.6,           // where in the band
  "variants": ["strong", "diseased"],       // named modifier packages
  "loadout": "…", "respawn": "onRest" }
```

**The ladder in numbers** for authors (2.8a3): what each preset class at each
band and position 0.1, 0.5 and 0.9 compiles to is the generated table
[`stats/ladder-table.md`](../../packages/game-core/src/stats/ladder-table.md).
A person's level is its band's `characterLevel` in `ladder.json` (D1 1,
D2 10, D3 20, D4 35, D5 50); its combat block
is the band's, so fixed danger holds.

### 128.1 The toughness ladder

The owner's sentences (2.9b): a D1 enemy dies to one or two longsword
backstabs or ripostes from an early warrior, to one or two sneak headshots
from an early stealth archer, to a couple of fireballs from an early mage; a
D5 enemy the same to a very high level character; a scale of toughness
between; bosses apart. The health column above is that ladder.

- **Counts.** `ladder.json` `toughness` holds the openers each build may take
  at its own band's checkpoint: warrior 1–2, archer 1–2, mage 1–3. The sim's
  `toughness-ladder` invariant (`sim/bandLadder.ts`, 400 seeded individuals a
  band) measures it: warrior 1–2 and archer 1 in every band, mage 2–3 at D1,
  1–2 at D2–D4, 1–3 at D5.
- **Individuals.** Each enemy stands at its own seeded place in its band
  around its authored position (`individualPosition`, `individualSpread`
  0.8), so the one-blow and the two-blow enemy meet in every band.
- **Fixed danger.** The same enemies met by a start character take more
  blows band by band: a start warrior's medians run D1 1, D2 3, D3 4, D4 6,
  D5 12.
- **Bows.** An early iron longbow body shot with the iron war arrow takes two
  to three on D1; the sneak headshot kills (decision 0090). A sneak shot is the bow
  multiplier times its damage on any band (0151 item 1); it kills when that
  is lethal, and an ordinary hit otherwise.
- **Pace by the value of a use.** Fights are one or two blows at band, so
  levelling keeps its pace by what a fight's use is worth, never by longer
  fights: `curves.worthiness.fightUseScale` multiplies a connect, a block, a
  hit taken, the armour kill and a cast on an enemy by the enemy's band (D1
  2.2, D2 2.75, D3 3.3, D4 4.2, D5 3.4), measured so a fight at its band's
  checkpoint yields what it did at the old ladder. Every other use is
  unscaled.
- **Morrowind's known answer** plays against Morrowind's old toughness
  (`content-vvardenfell.json` `enemyHealth`), so it still reproduces
  Morrowind's pace.

### 128.2 The same trick for loot and traps

The actor schema above is only a third of what packet authors place. Loot
and traps get the same treatment — semantic in, absolutes out — so a curve
retune rebalances the whole world rather than the monsters only (gap found by
decision 0034):

```jsonc
// loot: a placed item, not a levelled list — nothing reads the player
{ "id": "wreck-hold-cutlass", "band": "D3", "kind": "weapon",
  "class": "scimitar", "quality": 0.55,        // where in the band's material window
  "condition": 0.3,                             // provenance is visible on the item
  "enchant": { "budget": 0.4, "theme": "sea" }, // optional, compiled to a real effect
  "provenance": "went down with the Sallow Reed, 4E 194" }

// traps: damage derives from the band's damage row, not from a hand-typed number
{ "id": "xanmeer-dart-line", "band": "D3", "position": 0.4,
  "type": "dart", "multiplier": 0.6,   // of a band-typical light hit
  "avoidable": "sight+security", "resets": true }
```

Rules that keep this honest: a band's **material window** is what "quality"
interpolates (a D3 weapon is dwarven-to-orcish, never daedric); **placed
treasure never respawns** (§126) so compiling it is a one-time derivation;
uniques may override any field literally; and a trap's damage is expressed as a
fraction of its band's light hit, so the lethality knob (§121.4) moves traps
with everything else.

**Loot is built (2.3a).** `compileLoot({band, position})` in
`packages/game-core/src/stats/ladder.ts` returns the band's `lootValue` at the
position, its value tier and the band's material window. `ladder.json` holds
`materialWindow` per band (set tiers of `items.json` `sets[*].tier`: D1 1–1,
D2 1–2, D3 2–4, D4 4–6, D5 5–8) and `valueTiers` (gold per item: trivial
0–10, low 5–40, moderate 30–150, high 120–600, precious 500+), the tiers a
socket's and a loot rule's `valueTier` name. `loot.test.ts` keeps every item's
set inside its band's window. Traps remain open, owned by 2.10.

**Income pacing (2.9b c11).** `economy.json` `income.perBandClear` is gold per
hostile actor killed, read by the campaign sim (`campaign.ts`) and `sweeps.ts`.
It is the measured take of a hostile person at the Skyrim value index (body
gold plus worn goods sold at 0.55 to a general trader, `incomeSim.py`): D1 151,
D2 272, D3 379, D4 715, D5 1212; the yardstick moved, not the goods. A camp's
take overflows a village general trader's 375 purse by 10 to 20 times, so only
the rich buyers absorb a whole camp: the designed Morrowind throttle.

**Containers by the guardian's band (2.9b c11).** What a container holds comes
from what the place is (a sunken pirate ship keeps gold and jewels; a legion
deserter camp a chest of legion weapons and one of armour; a rich tailor's
wardrobe fine clothes), never from the player. The band only sets how much it
is worth. A place's guardian band is the highest `statblock.band` among its
hostile bodies, else its catalogue `dangerTier`. Each `ladder.json` band holds
`tierWindow`, the lowest and highest `valueTier` a container there may carry
(D1 trivial–low, D2 low–moderate, D3 moderate–high, D4 high, D5 high–precious),
and `chestValue`, the summed value of its best guarded chest (D1 140–420, D2
230–560, D3 360–790, D4 490–990, D5 590–1,140). `chestValue` is calibrated once
against Skyrim's boss chests at the band's `characterLevel` (the 25th
percentile, and the richest plus the median enchantment premium), read from
`world/sources/economy/skyrim-tier-reference.json`, which
`worldgen.skyrim_tier_reference` mines from Skyrim.esm; nothing reads that
table at runtime and nothing is levelled. One septim is Skyrim's one: item
values are the plugin record's value, gear included.

A loot rule says what a kind of place keeps (`loot-rules.json`): one list,
or `byBand` lists for a kind found at several bands (a pirate crew's
treasure, a Legion armour chest, a cult's offering cache, a Naga band's road
cache), frozen at the guardian band with that band on the socket's
`lootTable`. `roles` tags what its items are; weapons, armour, jewels, gems,
soul gems and gold are treasure, and food, water and tools are what a place
lives on. On guarded ground (catalogue `hostility.baseline` hostile: a camp,
a cult hall, a lair) `worldgen.sockets --fill` holds every treasure
container within one tier of the band's `tierWindow`, a D4–D5 place to at
least one container inside it, and its richest container to `chestValue`; a
household's barrel stays a barrel.

**Hostiles drop by band (2.9b c6c).** A hostile person wears its kit's gear
family (`actors/data/gear-families.json`) at its band, every piece inside the
band's window, one seeded pick per slot so two of a band differ. Its frozen
drop is its kit's weapons, the worn pieces, the family band's `carries` (a
cult's D4–D5 daedra heart), its culture's blanket items and a purse of gold:
Skyrim's bandit body gold at its band (`LootBanditGold`: D1 25, D2 38, D3 62,
D4 75, D5 75; a `boss` variant `LootBanditGoldBoss`: 50, 100, 200, 250, 250),
plus any gold the blanket items hold. Worn armour and weapons are the body's
own equipment at Skyrim's prices, so a strong kill pays in gear; what limits
that windfall is who can buy it (trader purses, a few rich buyers).
Measured purses: D1 25, D2 38–148, D3 62–172, D4 75–115, D5 75. A giant
wasp's harvest carries chaurus chitin.

The compiler interpolates the band, applies variants and emits fixed numbers.
Derivation reads **world data only, never player state** — the world's numbers
are as fixed as ever, they are merely derived, so retuning a curve and
recompiling rebalances every authored actor coherently instead of requiring a
re-authoring pass. Literal overrides stay available for uniques.

## 129. Where the numbers live

The canonical machine-readable tables live in
[`packages/game-core/src/stats/data/`](../stats/README.md)
(decision 0088): one source of truth that the game and the balance harness
both read. The harness's own inputs are in `stats/sim/data/`.

| File | Contents |
|---|---|
| `data/attributes.json` | the seven attributes, the start range, the reference character |
| `data/skills.json` | the 27 skills: governing attribute, **score attribute**, specialization, effect bands |
| `data/curves.json` | `k`, `P`, mitigation, health/stamina/magicka, movement, poise, check constants, vastei and level-cost constants |
| `data/races.json` | one record per playable race, both sexes: baselines, skill bonuses, effect packages ([0096](../old-decisions/0096-one-race-record-keyed-by-the-roster-with-morrowinds-packages.md)) |
| `data/classes.json` | preset classes (majors/minors/specialization/favoured) |
| `data/birthsigns.json` | the thirteen birthsigns: guardian, month, stack entries, powers and spells by id (§127) |
| `data/ladder.json` | the **D1–D5** combat bands, each band's `characterLevel`, the hits-to-die targets they were solved *from*, and the variant packages |
| `ladder-table.md` | generated: what each class at each band and position compiles to (§128) |
| `data/magic.json` | spell tiers, healing tiers, castability, enchanting bounds, the alchemy formula |
| `data/economy.json` | potion/training/service/repair prices, vendor purses |
| `data/rules-argonia.json` | our progression rules; numbers marked `$from` are read out of `curves.json` |
| `sim/data/gear.json` | materials, weapon classes, the moveset, armour slots and sets, mirrored from `packages/game-core` equipment, and the **provisional poise block** (§121.3) |
| `sim/data/builds.json` | the progression checkpoints and archetype attribute priorities the sweeps run on |
| `sim/data/enemies.json` | worked archetypes on the ladder, including the restated Hollow Warden |
| `sim/data/rules-morrowind.json` | Morrowind's progression rules, for the known-answer test |
| `sim/data/content-argonia.json` / `content-vvardenfell.json` | what an hour of play contains. **This is the file to change if the pace is wrong**; the Vvardenfell one is the only thing tuned to make the known-answer test pass |

The tuning history, meaning every anomaly the harness found and what was done
about it, is [the harness findings](../research/archive/workstream-s/stats-sim-findings.md). The
harness itself (`stats/sim`) runs in `npm test`: the 19 invariants are
standing tests against the canonical data, and an equivalence test proves the
port equal to the retired `tooling/stats-sim` on its own tables. Nothing in
this design should ever be a hard-coded constant in gameplay code.

---

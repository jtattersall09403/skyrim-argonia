# Birthsigns — the thirteen signs as Black Marsh reads them

Sources: Lore:The Seasons of Argonia (Jekka-Wass Paxalt, Keeper of the
Xinchei-Konu; ESO Murkmire; fetched 2026-10-20 via the UESP API), the Jel
month table in [sky-moons-calendar.md](sky-moons-calendar.md) (Lore:Calendar,
Lore:Constellations), the Shadowscales in
[sithis-nisswo-shadowscales.md](sithis-nisswo-shadowscales.md) (Lore:Shadowscales),
the egg-tenders' star-sign log in [hist-and-sap.md](hist-and-sap.md), and for
the mechanics Morrowind:Birthsigns with the UESP spell pages of the signs'
powers and spells (fetched 2026-10-20).
Consumers: the stats system (docs/world/76 §119, §127; decision 0144),
`packages/game-core/src/stats/data/birthsigns.json`, the sign names and
readings in `packages/text-catalogue/src/stats-text.ts`.

Era: the Seasons of Argonia is a 2E source; it describes custom, not politics,
and nothing in the 4E record contradicts it (decision 0002), so it stands.

## How Black Marsh names the signs — CANON_EXPLICIT

The thirteen constellations are Tamriel's (Warrior, Mage, Thief and their
charges, and the monthless Serpent); each of the twelve "is typically in the
sky throughout" its month. Argonians keep the Jel calendar, which tracks the
Hist's life from sprout to death, and egg-tenders log each egg's star sign at
hatching. A sign is therefore named in Argonian mouths by the Jel month it
rules, and read by that month's meaning in *The Seasons of Argonia*. The
Serpent has no month and no Jel name.

## Season framing — CANON_EXPLICIT / DESIGN

Sources: Lore:The Seasons of Argonia, Lore:Jel, Lore:The Tide, Lore:Xinchei-Konu
Monument (UESP API, fetched 2026-10-20).

- Black Marsh's own book on the calendar is titled *The Seasons of Argonia*. It
  gives two of the months as seasons by name: Xeech is "the hiding time" and
  Sisei is "the leaping season". The Xinchei-Konu monument is the calendar of
  the twelve, one tablet per month.
- Jel has no tense and no word for "time" (Lore:Jel, quoting *The Argonian
  Account*), so Imperial "month" is the foreigner's word. *Thtithik* is "to
  hatch an egg"; egg-tenders log the star sign at hatching.
- *The Firmament* says the Serpent "has no Season".
- Tides: only the Tide-Born tribe reveres the tide, which carries memories
  to eggs in tidal pools. The tide is a belief, not a calendar, and no source
  says anyone is born under a tide. So "tide" is not used.
- DESIGN: the sheet's row is "Hatching season". Readings say "the season of…"
  and "those hatched in it"; the Serpent's say "belong to no season" and "hatched
  under them". Ids, months and effects are unchanged.

## The signs — names, readings, effects

Each row: record id (stable, the Tamrielic constellation), the Jel name as
shown, the source meaning, and the effect set. The Shadow's month is
Hist-Dooka; it alone keeps its constellation's name in the shown name,
because Black Marsh's own lore is about the Shadow sign (the Shadowscales).

| id | Shown name | Source meaning (CANON_EXPLICIT) | Effects now | Morrowind's (2.8) |
|---|---|---|---|---|
| ritual | Vakka, the Sun | first month; origins; extra respect to the tribal elders | Personality +10, Willpower +15; power Ancestor Guardian (Sanctuary 50, 60 s) | power Mara's Gift; spells Blessed Word, Blessed Touch |
| lover | Xeech, the Nut | "the hiding time"; bulbs buried, knowledge planted; first of the Three Mournings; hope and melancholy | Sneak +15, Alchemy +10, Personality −10; spell Beggar's Nose (detect animal, enchantment, key) | Agility +25; power Lover's Kiss |
| lord | Sisei, the Sprout | newness; hatchling festivals; "the leaping season"; strength, speed and willpower venerated | Strength +10, Speed +10, Willpower +10, Acrobatics +10 | Weakness to Fire 100; spell Blood of the North |
| mage | Hist-Deek, the Sapling | challenge to authority; individual agency; intra-tribal conflict; the Hist as "bond rather than bondage" | ×1 Int magicka, Resist Paralysis 25, Personality −10 | ×0.5 Int magicka |
| shadow | Hist-Dooka, the Shadow | family, tradition, obligation; the Chukka-Sei trial. Argonians born under the Shadow are given to the Shadowscales at birth | Sneak +10, Short Blade +10, Personality −10; power Moonshadow (invisibility 60 s) | power Moonshadow |
| steed | Hist-Tsoko, the Elder Hist | holiest month; knowledge, wisdom; the Root Talk; the Second Mourning: the Hist has stopped growing | Intelligence +20, Willpower +10, Speed −10 | Speed +25 |
| apprentice | Thtithil-Gah, the Egg-Basket | foolishness and frivolity; hatchling wonder, mild confusion; troupes, feasts | Personality +15, Speechcraft +10, Acrobatics +10, Intelligence −10 | ×1.5 Int magicka, Weakness to Magicka 50 |
| warrior | Thtithil, the Egg | mystery, anticipation, finality; egg-laying | Endurance +10, Block +10, Resist Blight Disease 50 | Fortify Attack 10 |
| lady | Nushmeeko, the Lizard | swift and quiet labour: cleaning, building, repairing | Speed +10, Endurance +10, Smithing +10, stamina recovery ×1.25 | Personality +25, Endurance +25 |
| tower | Shaja-Nushmeeko, the Half-Lizard | change, becoming; adolescent gatherings, "romantic entanglements", the awkwardness of youth | Agility +10, Personality +10, Willpower −10; power Lover's Kiss (paralyse 60 s, own fatigue −200) | power Tower Key; spell Beggar's Nose |
| atronach | Saxhleel, the People | pottery, woodcarving, creative pastimes; the elders gather to prepare for the deaths to come | Enchant +15, Alchemy +10, Intelligence +10, Endurance −10 | ×2 Int magicka, Spell Absorption 50, no magicka regeneration |
| thief | Xulomaht, the Deceased | the Third Mourning; remembrance; festivals for all who passed into a new life | Willpower +10, Restoration +10; spells Blessed Word, Blessed Touch (turn undead) | Sanctuary 10 |
| serpent | The Serpent | no month; four dark "unstars" that wander; "the most blessed and the most cursed" | Agility +15, Speed +10, Weakness to Magicka 25; spell Star-Curse | spell Star-Curse |

Guardians and months are unchanged (the constellations are the same stars).

## How we use it — DESIGN

- The sign is chosen directly; the birth date is flavour only (world/76 §119).
- Only existing pieces: every effect is a `StatEffect` on an `EFFECT_FIELDS`
  field with an existing op (fortify, drain, resist, ability); every power is
  a zero-cost power already in `packages/magic` spells.json; every spell is one
  of Morrowind's nine sign spells (`BIRTHSIGN_SPELL_IDS`, kept out of shops).
  No new spell, effect or field. Blood of the North, Mara's Gift and Tower Key
  are no longer on a sign; they stay shop-excluded.
- Costs are drains of an attribute (shown on the sheet's effect list) or a
  weakness, the same shapes Morrowind used.
- Luck does not exist in our game.

## Balance — DESIGN

One tally scores a sign: attribute or skill point 1; ×1 Int magicka 25;
resistance or absorption % 0.5 (a weakness 0.25); attack or sanctuary 1.5;
regeneration 40 per ×1 changed; power 15; spell 10. Morrowind's thirteen
scored −15 (Lord) to 50 (Lady) net and at most 75 in boons alone
(Atronach). The Black Marsh signs score 20 to 45 net and 35 to 45 in boons,
so none is stronger than Morrowind's strongest, and the spread is narrower.
`compile.test.ts` ("every Black Marsh sign scores inside the Morrowind
signs' spread") holds the bound.

| id | boon / net now | boon / net before |
|---|---|---|
| warrior | 45 / 45 | 15 / 15 |
| mage | 37.5 / 27.5 | 12.5 / 12.5 |
| thief | 40 / 40 | 15 / 15 |
| lady | 40 / 40 | 50 / 50 |
| steed | 30 / 20 | 25 / 25 |
| lord | 40 / 40 | 10 / −15 |
| apprentice | 35 / 25 | 37.5 / 25 |
| atronach | 35 / 25 | 75 / 35 |
| ritual | 40 / 40 | 35 / 35 |
| lover | 35 / 25 | 40 / 40 |
| shadow | 35 / 25 | 15 / 15 |
| tower | 35 / 25 | 25 / 25 |
| serpent | 35 / 28.75 | 10 / 10 |

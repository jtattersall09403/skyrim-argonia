# Creature souls and the one disease bite

Why this dossier exists: 2.9's Soultrap seam needs a soul value per slice
creature, and the disease seam needs to know which bite carries one. Both are
lore-grounded numbers, recorded here before `packages/magic/src/data/creatures.json`
reads them (era policy: [0002](../../../../docs/decisions/0002-era-and-source-confidence.md)).

Sources (UESP API, fetched 2026-10-20): `Morrowind:Soul_Gems`, the `{{soul|N}}`
field on each `Morrowind:<creature>` page, `Oblivion:Will-o-the-Wisp` and
`Oblivion:Souls`, `Lore:Wamasu`, `Lore:Voriplasm`, `Lore:Giant Snake`.

## 1. The scale

- **CANON_EXPLICIT** (Morrowind:Soul Gems): max soul petty 30, lesser 60, common
  120, greater 180, grand 600. Ours (`constantEffectSoulByMagnitude`): 30, 80,
  150, 300, 600. The two ladders agree at both ends and differ by under 2x in the
  middle, so a Morrowind creature's soul points are used **unchanged**, the
  gem a creature fills being decided by our capacities.
- **EXTRAPOLATED:** every slice creature is an animal, an insect, a spirit or a
  beast, so every value is at or under common (150). Greater and grand souls are
  Daedra and the like (Daedroth 195, Winged Twilight 300) and are not in the slice.

## 2. The rule

A row takes the soul value of its **nearest canon analogue**: Morrowind first
(its creatures carry the fixed values this game's magic is built on), then
Oblivion's soul strength where the creature is a spirit. Analogue is chosen by
body plan and threat: the same kind of animal, then the same size and manner of
hunting. Confidence: **direct** (the same creature), **close** (same body plan),
**weak** (no canon creature of the kind; chosen by size and threat, and the
reason given).

## 3. The rows

| Archetype | Soul | Analogue (UESP page) | Confidence | Why this analogue |
|---|---|---|---|---|
| `creature.slaughterfish` | 10 | Slaughterfish (MW) | direct | The same fish. |
| `creature.marsh-rat` | 10 | Rat / Cave Rat (MW) | direct | The same animal. |
| `creature.hackwing` | 20 | Cliff Racer (MW) | close | A big flying biter in flocks, the same threat. |
| `creature.bog-dog` | 10 | Nix-Hound (MW) | close | A pack-hunting hound; Black Marsh's dog stands where the nix-hound does. |
| `creature.hoarvor` | 5 | Mudcrab (MW) | close | A small scuttling chitin crawler that gives up the chase; our mesh is the mudcrab build. |
| `creature.giant-leech` | 10 | Scrib (MW) | weak | Morrowind has no leech; the scrib is its smallest invertebrate pest. |
| `creature.death-hopper` | 15 | Kwama Forager (MW) | weak | No canon frog with a soul value; a dog-sized, pack-living, poison-spitting forager of the same size. |
| `creature.giant-wasp` | 20 | Kwama Warrior (MW) | weak | No canon wasp in Morrowind; a pony-sized chitinous fighter that defends a nest. |
| `creature.crocodile` | 30 | Shalk (MW) | weak | Morrowind has no crocodile; the shalk is its armoured reptile-like ambusher, two men long here. |
| `creature.kaj-thux` | 75 | Dreugh (MW) | weak | Lore:Giant Snake gives size only; the dreugh is Morrowind's large many-legged beast of the water's edge. |
| `creature.voriplasm` | 100 | Corprus Stalker (MW) | weak | Lore:Voriplasm names no soul; a formless flesh-melting horror that hunts by sense, a mid-tier monster. |
| `creature.wisp` | 100 | Ancestor Ghost (MW); Will-o-the-Wisp (OB, at most Common) | close | A spirit; Oblivion fixes the wisp at Common or under, so 100 sits inside it. |
| `creature.wamasu` | 150 | Storm Atronach (MW) | weak | Lore:Wamasu: a large lightning-charged reptile; the storm atronach is the canon lightning body, filling a common gem exactly. |

Weak rows are the ones to revisit if a later source gives a value; changing a
row changes only `creatures.json`.

## 4. Disease

- **CANON_EXPLICIT:** disease comes from bites of vermin and swamp creatures
  throughout Morrowind (the nearest canon rule is common-disease on rat and
  similar bites), and the Black Marsh dossiers name giant leeches among the
  province's everyday hazards ([fauna-hazards](fauna-hazards.md)).
- **EXTRAPOLATED / project rule** (2.9 packet, magic line 88-90): the slice
  carries **one** disease bite, `swamp-fever` (`stats/data/magic.json`
  `diseases`), on `creature.giant-leech`, the creature that waits in the still
  dark water where fever breeds. Every other row is `null`; a second bite is a
  later packet.

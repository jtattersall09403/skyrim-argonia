# When doors lock: Skyrim and Morrowind practice

Feeds the role registry (`packages/game-core/src/people/roles.json`) and
`docs/world/72-navigation-ai.md` "The day". Owner ruling: house and shop doors
lock "whatever Morrowind and Skyrim do; it might depend on the house and the
person". Sources fetched from the UESP API 2026-10-17 (the vault extract holds
Morrowind/Black Marsh lore only, no mechanics pages). Mechanics, not lore, so
the 4E 201 era policy (decision 0002) does not filter them; the proposed rules
are our own (EXTRAPOLATED) and carry the era-free reason "a village that sleeps
by the lamp clock".

Tiers: CANON_EXPLICIT = stated on the UESP page named; CANON_DERIVED = read
from several pages; EXTRAPOLATED = our rule.

## Skyrim (UESP `Skyrim:` pages)

- **Locks are tiered, not timed by default.** Novice, Apprentice, Adept,
  Expert, Master (Skyrim:Lockpicking, lock-level table: skill 0/25/50/75/100).
  CANON_EXPLICIT.
- **Houses lock at night by occupant, at novice or apprentice level.**
  Verner and Annekke's House: "novice-locked at night, but will be unlocked
  during the day" (Skyrim:Verner and Annekke's House). Niranye's House: novice
  locks on both doors "whenever Niranye is not present and at night"
  (Skyrim:Niranye's House). Marise Aravel's House: apprentice-locked "both at
  night and during the day while Marise is selling foodstuffs at her cart"
  (Skyrim:Marise Aravel's House). Alvor and Sigrid's House: novice lock, "locked
  most of the time"; inside after midnight you are unwelcome (Skyrim:Alvor and
  Sigrid's House). Sven and Hilde's House and Whiterun Stables residence:
  novice lock plus a key the residents carry (Skyrim:Sven and Hilde's House,
  Skyrim:Whiterun Stables). CANON_EXPLICIT. So: lock depends on the house and
  the person (present or not, working abroad or not), the key sits in the
  occupant's pocket, and a few houses are locked every hour (Sarethi Farm:
  "locked night and day, no key", Skyrim:Sarethi Farm).
- **Shops keep set hours.** "Most merchants are open from around 8am to 8pm,
  but some are open all day ... most blacksmiths are only open during the day,
  whereas innkeepers are always open" (Skyrim:Merchants). Belethor opens at 8am
  and stands twelve hours at the counter (Skyrim:Belethor); Bothela "will lock
  up the shop for the night and head to bed" after twelve hours (Skyrim:Bothela);
  Arcadia stands at her desk 8am to 8pm and the shop door is locked outside
  that, with a known bug that leaves it locked in business hours
  (Skyrim:Arcadia's Cauldron, Skyrim:Warmaiden's). A keeper who leaves the shop
  "locks the doors and closes for the day" (Skyrim:Merchants, bug note). No
  lunch closing is documented: shops lock at close and at night, not at noon.
  Shop lock levels are not given by UESP; picking an owned door is a 5 gold
  crime when seen (Skyrim:Lockpicking, Skyrim:Crime). CANON_EXPLICIT for hours.
- **Inns never lock.** "innkeepers are always open" (Skyrim:Merchants); Elrindir
  at the Drunken Huntsman serves "around the clock" (Skyrim:The Drunken
  Huntsman); Dead Man's Drink "24 hrs/day every day" (Skyrim:Dead Man's Drink).
  CANON_EXPLICIT.
- **Halls: public room open, private quarters lock at night.** Mistveil Keep's
  chambers stairs are "adept locked at night when the jarl goes to bed, but
  unlocked during the day" (Skyrim:Mistveil Keep). CANON_EXPLICIT.
- **Temples and guild halls.** UESP documents no night lock on the temples
  (Skyrim:Temple of Kynareth, Skyrim:Temple of Mara) and the priest's bedroom is
  an ordinary owned room; Jorrvaskr's doors lock only during a quest
  (Skyrim:Jorrvaskr). Treated as open (CANON_DERIVED from silence; re-verify
  in-game before quoting).
- **Trespass.** Entering is not the crime, unlocking is; trespassing in an
  owned room gets one warning, then a 5 gold bounty after 30 seconds
  (Skyrim:Crime). Homes are best burgled midnight to 7-8am; most residents are
  out 8am to 8pm and asleep around midnight (Skyrim:Crime). CANON_EXPLICIT.
- **Jails and strongrooms are the high levels.** Dragonsreach cells adept-locked
  (Skyrim:Dragonsreach); evidence chest expert or master (Skyrim:Crime).

## Morrowind (UESP `Morrowind:` pages)

- **No schedule locks.** Doors do not lock by the hour. NPCs "are incapable of
  using doors which go into a different cell" and never pick locks or cast
  Open (Morrowind:Lock). A lock is a fixed number 1 to 100 (Morrowind:Security).
  CANON_EXPLICIT.
- **Most doors are unlocked always**: shops, guild halls, temples, inns, and
  inhabited homes (Pelagiad's largest house "front door is unlocked", Morrowind:
  Pelagiad Homes). Locked doors are the exception and are chosen by the house:
  an owner's or empty house carries a level 30 to 50 lock on the front door
  (Hlaalo Manor 35 front, 40 balcony; Pelagiad house 45; a Balmora house 50;
  Aryni Orethi's House 50; Balyn Omarel's House 30; Morrowind:Balmora Homes,
  Pelagiad Homes, Aryni Orethi's House, Balyn Omarel's House); inner doors and
  strongrooms run 20 to 100 (a shop back room 40 or 65, Morrowind:Hodlismod:
  Armorer, Simine Fralinie; a Legion evidence room 95, Morrowind:Crime; the
  Temple Patriarch's office is locked behind the Ordinators, Morrowind:Tholer
  Saryoni). CANON_EXPLICIT.
- **Time never changes a lock**, so "shops and guilds open at all hours" is the
  rule: trading hours are not modelled (a merchant is a fixed `Merc` entry,
  Morrowind:Merchants) and no sampled shop, guild or temple page names a closing
  time (CANON_DERIVED from the absence).
- **Crime.** Entering a door, locked or not, is no crime; unlocking an owned lock
  is (5 gold) (Morrowind:Crime). CANON_EXPLICIT.

## What the two games share (our reading, EXTRAPOLATED)

1. Public doors (inn, temple, guild hall, barracks) never lock; a private part
   inside may.
2. A private house locks when its people are in bed or absent, never by the
   clock alone, and the occupant carries the key.
3. Lock level goes with the house, not the hour: huts and ordinary homes 10 to
   35, prosperous or official homes 40 to 55, strongrooms 60 to 100.
4. A shop locks when its keeper stops working (Skyrim) and never in Morrowind;
   no midday closing in either.

Our scale is Morrowind's 1 to 100 (`world/sources/registries/locks.json:3`);
Skyrim's tiers map as Novice 15, Apprentice 30, Adept 50, Expert 75, Master 95.

## Picks, probes and trapped locks (mined 2026-10-21 for 2.10a)

**Source.** UESP via the MediaWiki API, fetched 2026-10-21: `Morrowind:Security` (revid
2922329), `Morrowind:Thieves Tools` (revid 3498595; `Morrowind:Lockpick` and
`Morrowind:Probe` redirect there), `Morrowind:Spells` (revid 3649384, the trap rows),
`Morrowind:Open` (revid 2691643), `Morrowind:Telekinesis` (revid 3280154).
**Era (decision 0002).** Morrowind (3E 427) game mechanics, not world state; no 4E claim.
CANON_EXPLICIT unless marked.

| Tool | Quality | Uses | Weight | Value |
|---|---|---|---|---|
| Apprentice's Lockpick | 1.0 | 25 | 0.25 | 10 |
| Journeyman's Lockpick | 1.1 | 25 | 0.25 | 50 |
| Master's Lockpick | 1.3 | 25 | 0.25 | 100 |
| Grandmaster's Pick | 1.4 | 25 | 0.25 | 200 |
| The Skeleton Key | 5.0 | 50 | 0.50 | 1000 |
| Bent Probe | 0.25 | 5 | 0.25 | 2 |
| Apprentice's Probe | 0.50 | 25 | 1.00 | 10 |
| Journeyman's Probe | 0.75 | 25 | 0.25 | 50 |
| Master's Probe | 1.00 | 25 | 0.25 | 100 |
| Grandmaster's Probe | 1.25 | 25 | 0.25 | 200 |

- Chance: "(Stats Modifier * Equipment Modifier * Fatigue Modifier) - Lock Difficulty",
  Stats = Security + Agility/5 + Luck/10; Equipment = the tool's quality; Fatigue =
  0.75 + 0.5 x current/max. "Traps, on the other hand, have no difficulty."
  A failed attempt still uses the tool. Vendors sell apprentice to master grades.
- Our use: world/76 §118 keeps the score (Security + Agility/5) x quality >= level with
  no roll. Our one `item.lockpick` is the apprentice grade (quality 1.0) and our one
  `item.probe` the apprentice probe (0.5); the higher grades need their own item rows.
- Open magnitude at or above the level opens a lock but "does not disarm any traps";
  "using the correct key opens the lock as well as disarms any trap"; Telekinesis can
  set a trap off from a distance.

| Trap spell | Effect | Duration | Cost |
|---|---|---|---|
| trap_fire00 | Fire Damage 2-20 pts | 3 s | 3 |
| trap_frost00 | Frost Damage 2-20 pts | 3 s | 3 |
| trap_shock00 | Shock Damage 2-20 pts | 3 s | 5 |
| trap_health00 (Lifeforce) | Damage Health 2-20 pts | 3 s | 8 |
| trap_poison00 | Poison 1-5 pts | 60 s | 16 |
| trap_paralyze00 | Paralyze | 10 s | 13 |
| trap_silence00 | Silence | 30 s | 37 |

All on Touch. The cost column is the table's trailing number (CANON_DERIVED reading).
UESP does not say whether a failed pick fires a trap or whether a fired trap is spent:
we read a trap as firing on opening a still-trapped thing and spent once fired
(EXTRAPOLATED; re-verify against OpenMW before building more on it). Our rows:
`world/sources/registries/traps.json`, magnitude the range's mean (no roll).

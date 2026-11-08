# Dialogue brief: Keeps-What-Floats (TG01 A Dry Hand in a Wet City)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; TG01's thief (we.tg01.thief): a cowardly dock thief with a round of the dock, a drinking spot and an awning he sleeps under, the necklace on him all the while. Outfit: marsh-native-kilt+marsh-native-sandals

## What the player cannot see
- Role: a dock thief who sleeps on a bedroll north-west of the house (npc)
- Factions: none
- Wants: to keep the necklace until he can sell it (invented)
- Fears: a fight; he runs from one (we.tg01.thief, Cowardly)
- Backstory: has lived on Soulrest's dock since he was a hatchling and has never held anything for long
- Invented, for 2.4 to write back to the registry: backstory

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- S'Tabi: Khajiit caravan factor
- Tilts-The-Jug: The keeper of the harbour den
- Sits-By-The-Water: the thief's drinking friend on the dock
- Bent-Spine: Night-Reed fence

## Things lines may name (and only these)
- `item.tg01.jasper-necklace`: item; the dock at Soulrest; {'after-30': "the player's", 'after-40': "Tilts-The-Jug's", 'before-30': 'on him'}
- `thing.tg01.round`: place; the dock and boardwalk at Soulrest; {'all': 'present'}
- `thing.tg01.people`: actors; Soulrest; {'all': 'present'}
- `thing.tg01.trapdoor`: place; north of Pusbottom, Lilmoth; {'all': 'locked until opened'}
- `thing.tg01.zones`: triggers; the boardwalk at Soulrest; {'all': 'present'}
- `item.lockpick`: item; inside the house; {'all': 'present'}

## Topics
### the necklace (`topic.tg01-give-it-back`; stages [30]; not essential)
- Intent: he gives up the necklace on a Speech check of 35, or sells it for 60 gold (takeGold 60, giveItem the necklace)
- May state:
  - `fact.tg01.necklace`: Keeps-What-Floats took a necklace of polished blue jaspers from another thief of the dock.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - pickpocket: pickpocket (Keeps-What-Floats), in a crowd or a market
  - pickpocket: pickpocket (Keeps-What-Floats), at night
  - speechcraft: persuade (Keeps-What-Floats), at night
- Directions to give: By day he is on the dock west of the house; in the evening he drinks at the bench by the water, and at night he sleeps on his bedroll north-west of the house. Tilts-The-Jug is inside the house, behind its one open door.
- Keeps-What-Floats's knowledge at stage 30:
  - `fact.tg01.necklace`: knows
  - `fact.tg01.round`: knows
- The player already knows at stage 30 (anything else is explained when first named):
  - `fact.tg01.desk-door`: Tilts-The-Jug keeps the Chapter's desk inside Soulrest's house.
  - `fact.tg01.test`: The Chapter wants the keepsake back from the one who took it, with no harm done to him, to see how I work.
  - `fact.tg01.necklace`: Keeps-What-Floats took a necklace of polished blue jaspers from another thief of the dock.


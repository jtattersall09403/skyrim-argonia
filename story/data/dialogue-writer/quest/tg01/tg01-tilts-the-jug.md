# Dialogue brief: Tilts-The-Jug (TG01 A Dry Hand in a Wet City)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Holds the post: the keeper of the harbour den (Soulrest). Outfit: saxhleel-tunic-wrap-orange+marsh-native-sandals

## What the player cannot see
- Role: The keeper of the harbour den (npc)
- Factions: none
- Wants: a newcomer who can take without harm (culture.faction.night-reed-chapter value Skill and restraint)
- Fears: a hand that breaks what it touches

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- S'Tabi: Khajiit caravan factor
- Keeps-What-Floats: a dock thief who sleeps on a bedroll north-west of the house
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
### the Chapter (`topic.tg01-the-test`; stages [0]; essential: no refusal band)
- Intent: the Chapter wants to see how the player works; Keeps-What-Floats took a necklace of blue jaspers from another thief of the dock; it is to come back with no harm to him; hearing it starts the quest at stage 20
- May state:
  - `fact.tg01.test`: The Chapter wants the keepsake back from the one who took it, with no harm done to him, to see how I work.
  - `fact.tg01.necklace`: Keeps-What-Floats took a necklace of polished blue jaspers from another thief of the dock.
- Tilts-The-Jug's knowledge at stage 0:
  - `fact.tg01.chapter-way`: knows
  - `fact.tg01.desk-door`: knows
  - `fact.tg01.he-runs`: knows
  - `fact.tg01.necklace`: knows
  - `fact.tg01.test`: knows
- The player already knows at stage 0 (anything else is explained when first named):

### the necklace (`topic.tg01-return`; stages [30]; essential: no refusal band)
- Intent: shown only while the player has the necklace (takeItem it); if he lives she pays and sends the player to the Chapter's trapdoor; if he is dead she says the Chapter wanted the necklace without a body, pays nothing, and sends the player all the same
- May state:
  - `fact.tg01.chapter-way`: The Chapter's way down is a locked trapdoor just north of Pusbottom in Lilmoth.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - pickpocket: pickpocket (Keeps-What-Floats), in a crowd or a market
  - pickpocket: pickpocket (Keeps-What-Floats), at night
  - speechcraft: persuade (Keeps-What-Floats), at night
- Directions to give: By day he is on the dock west of the house; in the evening he drinks at the bench by the water, and at night he sleeps on his bedroll north-west of the house. Tilts-The-Jug is inside the house, behind its one open door.
- Tilts-The-Jug's knowledge at stage 30:
  - `fact.tg01.chapter-way`: knows
  - `fact.tg01.desk-door`: knows
  - `fact.tg01.he-runs`: knows
  - `fact.tg01.necklace`: knows
  - `fact.tg01.test`: knows
- The player already knows at stage 30 (anything else is explained when first named):
  - `fact.tg01.desk-door`: Tilts-The-Jug keeps the Chapter's desk inside Soulrest's house.
  - `fact.tg01.test`: The Chapter wants the keepsake back from the one who took it, with no harm done to him, to see how I work.
  - `fact.tg01.necklace`: Keeps-What-Floats took a necklace of polished blue jaspers from another thief of the dock.


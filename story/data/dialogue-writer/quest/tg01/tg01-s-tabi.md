# Dialogue brief: S'Tabi (TG01 A Dry Hand in a Wet City)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- khajiit, male; Holds the post: Khajiit caravan factor (Soulrest). Outfit: marsh-native-kilt+marsh-native-sandals

## What the player cannot see
- Role: Khajiit caravan factor (npc)
- Factions: none
- Wants: trade with the Chapter kept quiet and steady (culture.faction.night-reed-chapter norm Silence to outsiders)
- Fears: sending the wrong stranger into the house

## Voice
- khajiit: 18% | 5.4 | Third person: "this one", "Khajiit knows" | "Friend"; their own idiom; rarely contract. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Tilts-The-Jug: The keeper of the harbour den
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
### work (`topic.tg01-the-door`; stages [0]; not essential)
- Intent: S'Tabi sends a player who asks about quiet work to Tilts-The-Jug inside the house on the dock
- May state:
  - `fact.tg01.desk-door`: Tilts-The-Jug keeps the Chapter's desk inside Soulrest's house.
- S'Tabi's knowledge at stage 0:
  - `fact.tg01.desk-door`: knows
- The player already knows at stage 0 (anything else is explained when first named):


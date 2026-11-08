# Dialogue brief: Bent-Spine (TG01 A Dry Hand in a Wet City)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; Holds the post: Night-Reed fence. Gives TG02's job in the Chapter under Pusbottom (slice round 2). Outfit: saxhleel-tunic-short-brown+marsh-native-sandals

## What the player cannot see
- Role: Night-Reed fence (npc)
- Factions: none
- Wants: the newcomer down the trapdoor by their own hand (culture.faction.night-reed-chapter value Skill and restraint)
- Fears: strangers in the Chapter

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- S'Tabi: Khajiit caravan factor
- Tilts-The-Jug: The keeper of the harbour den
- Keeps-What-Floats: a dock thief who sleeps on a bedroll north-west of the house
- Sits-By-The-Water: the thief's drinking friend on the dock

## Things lines may name (and only these)
- `item.tg01.jasper-necklace`: item; the dock at Soulrest; {'after-30': "the player's", 'after-40': "Tilts-The-Jug's", 'before-30': 'on him'}
- `thing.tg01.round`: place; the dock and boardwalk at Soulrest; {'all': 'present'}
- `thing.tg01.people`: actors; Soulrest; {'all': 'present'}
- `thing.tg01.trapdoor`: place; north of Pusbottom, Lilmoth; {'all': 'locked until opened'}
- `thing.tg01.zones`: triggers; the boardwalk at Soulrest; {'all': 'present'}
- `item.lockpick`: item; inside the house; {'all': 'present'}

## Topics
### the Chapter (`topic.tg01-welcome`; stages [40, 41]; essential: no refusal band)
- Intent: Bent-Spine takes in the player who came down the trapdoor by their own hand as a Lookout, then turns to the work he has (topic.tg02-the-job); hearing it ends the quest (90 after 40, 91 after 41) and so starts TG02 at its stage 20
- May state:
  - `fact.tg01.chapter-way`: The Chapter's way down is a locked trapdoor two squares north of Pusbottom in Lilmoth.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Lockpicking: pick-a-lock (the Chapter's trapdoor), at night
  - Lockpicking: pick-a-lock (the Chapter's trapdoor), at night
- Directions to give: The coast ship's door is on Soulrest's dock (039827); inside the ship, the other door (0AA837) comes out at Lilmoth Dock (0AA664), on Lilmoth's east side. Walk west to the Lilmoth Hist; Pusbottom lies past it by the canals, and the trapdoor (16BF7F) is in the ground two squares north of Pusbottom. Below, Bent-Spine keeps to the Chapter's inner room, past the foot of the trapdoor's ladder.
- Directions to give: The coast ship's door is on Soulrest's dock (039827); inside the ship, the other door (0AA837) comes out at Lilmoth Dock (0AA664), on Lilmoth's east side. Walk west to the Lilmoth Hist; Pusbottom lies past it by the canals, and the trapdoor (16BF7F) is in the ground two squares north of Pusbottom. Below, Bent-Spine keeps to the Chapter's inner room, past the foot of the trapdoor's ladder.
- Bent-Spine's knowledge at stage 40:
  - `fact.tg01.chapter-way`: knows
- The player already knows at stage 40 (anything else is explained when first named):
  - `fact.tg01.desk-door`: Tilts-The-Jug keeps the Chapter's desk inside Soulrest's house.
  - `fact.tg01.test`: The Chapter wants the keepsake back from the one who took it, with no harm done to him, to see how I work.
  - `fact.tg01.necklace`: Keeps-What-Floats took a necklace of polished blue jaspers from another thief of the dock.
  - `fact.tg01.he-runs`: Caught, Keeps-What-Floats runs rather than fights.
  - `fact.tg01.round`: Keeps-What-Floats walks the dock and boardwalk by day, drinks at the bench by the water in the evening and sleeps on a bedroll north-west of the house, with the necklace on him.


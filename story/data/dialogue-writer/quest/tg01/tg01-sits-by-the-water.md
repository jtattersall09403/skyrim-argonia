# Dialogue brief: Sits-By-The-Water (TG01 A Dry Hand in a Wet City)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; TG01's drinking friend (we.tg01.dock), who knows where Keeps-What-Floats sleeps. Outfit: saxhleel-tunic-wrap-orange

## What the player cannot see
- Role: the thief's drinking friend on the dock (npc)
- Factions: none
- Wants: a drink paid for, and no trouble at her spot (invented)
- Fears: being taken for his partner
- Backstory: drinks with Keeps-What-Floats most evenings and does not think much of him
- Invented, for 2.4 to write back to the registry: backstory

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- S'Tabi: Khajiit caravan factor
- Tilts-The-Jug: The keeper of the harbour den
- Keeps-What-Floats: a dock thief who sleeps on a bedroll north-west of the house
- Bent-Spine: Night-Reed fence

## Things lines may name (and only these)
- `item.tg01.jasper-necklace`: item; the dock at Soulrest; {'after-30': "the player's", 'after-40': "Tilts-The-Jug's", 'before-30': 'on him'}
- `thing.tg01.round`: place; the dock and boardwalk at Soulrest; {'all': 'present'}
- `thing.tg01.people`: actors; Soulrest; {'all': 'present'}
- `thing.tg01.trapdoor`: place; north of Pusbottom, Lilmoth; {'all': 'locked until opened'}
- `thing.tg01.zones`: triggers; the boardwalk at Soulrest; {'all': 'present'}
- `item.lockpick`: item; inside the house; {'all': 'present'}

## Topics
### Keeps-What-Floats (`topic.tg01-his-bed`; stages [20]; not essential)
- Intent: where he drinks and where he sleeps, and that he runs from a fight; given on a Speech check of 25, or for a drink (takeGold 10)
- May state:
  - `fact.tg01.round`: Keeps-What-Floats walks the dock and boardwalk by day, drinks at the bench by the water in the evening and sleeps on a bedroll north-west of the house, with the necklace on him.
  - `fact.tg01.he-runs`: Caught, Keeps-What-Floats runs rather than fights.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - sneak: follow (Keeps-What-Floats), open ground by day
  - speechcraft: persuade (Sits-By-The-Water), at night
- Directions to give: He walks the dock west of the house by day, and in the evening he drinks at the bench by the water with Sits-By-The-Water; where he sleeps is learnt by following him or from her.
- Sits-By-The-Water's knowledge at stage 20:
  - `fact.tg01.he-runs`: knows
  - `fact.tg01.necklace`: suspects
  - `fact.tg01.round`: knows
- The player already knows at stage 20 (anything else is explained when first named):


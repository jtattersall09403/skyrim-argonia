# Dialogue brief: Bent-Spine (TG02 The Drowned Lockbox)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; Holds the post: Night-Reed fence. Gives TG02's job in the Chapter under Pusbottom (slice round 2). Outfit: saxhleel-tunic-short-brown+marsh-native-sandals

## What the player cannot see
- Role: Night-Reed fence (npc)
- Factions: none
- Wants: the lockbox up before the clients find a diver (culture.faction.night-reed-chapter norm Take from those who can bear it)
- Fears: a newcomer who sells silence (culture.faction.night-reed-chapter taboo Blackmail as a trade)

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Neeta-Haj: a canal-front client of the fallen stilt house
- Okan-Tei: a canal-front client of the fallen stilt house
- Dar-Zeel: a canal-front client of the fallen stilt house

## Things lines may name (and only these)
- `thing.tg02.house`: place; the deep water north of Pusbottom; {'all': 'present'}
- `thing.tg02.eels`: actors; the deep water north of Pusbottom; {'all': 'present'}
- `thing.tg02.clients`: actors; the bank north of Pusbottom; {'all': 'present'}
- `item.tg02.bone-figurine`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}
- `item.tg02.neesak-charm`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}
- `item.glass-bead-strand`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}

## Topics
### work (`topic.tg02-the-job`; stages [20]; essential: no refusal band)
- Intent: the lockbox lies locked on the floor of the deep water north of Pusbottom beside the fallen stilt house; ripper eels hunt the water; three clients want it; get it before they find a diver, and what becomes of what is in it is the player's
- May state:
  - `fact.tg02.job`: Bent-Spine wants the lockbox from the fallen stilt house in the deep water north of Pusbottom, and leaves to me what becomes of what is in it.
  - `fact.tg02.box`: A locked lockbox of pledged things lies on the floor of the deep water beside the fallen stilt house: a bone figurine, a Neesak charm and a strand of Kothringi Glass Beads.
  - `fact.tg02.eels`: Ripper eels hunt the deep water north of Pusbottom.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: persuade (the three clients), in a crowd or a market
- Directions to give: Climb the trapdoor's ladder out of the Chapter; the fallen house lies in the deep water just north of Pusbottom by the trapdoor, and the three clients wait on its south bank.
- Bent-Spine's knowledge at stage 20:
  - `fact.tg02.box`: knows
  - `fact.tg02.eels`: knows
  - `fact.tg02.job`: knows
- The player already knows at stage 20 (anything else is explained when first named):


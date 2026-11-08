# Dialogue brief: Ussa-Rekh (BC03 The Broker's Mercy)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; Holds the post: the Soulrest broker of BC03 (adaptation.md §5). Outfit: saxhleel-tunic-wrap-brown+marsh-native-sandals

## What the player cannot see
- Role: debt broker on Soulrest's dock who hires out the crews he freed (npc)
- Factions: none
- Wants: the season worked as agreed; he can say the year it turned (36-cast-roster §56)
- Fears: that the crews he freed call him what the estates are called

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Heavy-Rope: boss of a freed crew on Soulrest's dock

## Things lines may name (and only these)
- `thing.bc03.dock`: place; Soulrest; {'all': 'present'}
- `thing.bc03.cabin`: place; Soulrest's dock; {'all': 'present'}
- `item.bc03.tokens`: item; Ussa-Rekh's chest; {'after-90': 'broken', 'during': 'in the chest, or carried'}
- `thing.bc03.people`: actors; Soulrest's dock; {'all': 'present'}

## Topics
### the season (`topic.bc03-the-season`; stages [10]; not essential)
- Intent: thirty years of buying Owings, and the crews he freed now hired out; the crew were refused
- May state:
  - `fact.bc03.freed-and-hired`: Ussa-Rekh bought out Owings for thirty years, and now hires out the crews he freed.
  - `fact.bc03.refused`: Heavy-Rope's crew asked to end their last season early and were refused.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: interrogate (Ussa-Rekh and Heavy-Rope), in a crowd or a market
- Directions to give: Soulrest's open dock is the long dock on the town's water, where the crews wait for hire; Ussa-Rekh keeps his chest beside him on the planks.
- Ussa-Rekh's knowledge at stage 10:
  - `fact.bc03.break`: knows
  - `fact.bc03.freed-and-hired`: knows
  - `fact.bc03.refused`: knows
  - `fact.bc03.tokens`: knows
- The player already knows at stage 10 (anything else is explained when first named):


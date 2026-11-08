# Dialogue brief: Heavy-Rope (BC03 The Broker's Mercy)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; BC03's crew boss (we.bc03.people); if the player stands with Ussa-Rekh, he must be talked or paid into taking the refusal. Outfit: unknown

## What the player cannot see
- Role: boss of a freed crew on Soulrest's dock (npc)
- Factions: none
- Wants: his crew done with Ussa-Rekh, a season early
- Fears: a season more under Ussa-Rekh

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Ussa-Rekh: debt broker on Soulrest's dock who hires out the crews he freed

## Things lines may name (and only these)
- `thing.bc03.dock`: place; Soulrest; {'all': 'present'}
- `thing.bc03.cabin`: place; Soulrest's dock; {'all': 'present'}
- `item.bc03.tokens`: item; Ussa-Rekh's chest; {'after-90': 'broken', 'during': 'in the chest, or carried'}
- `thing.bc03.people`: actors; Soulrest's dock; {'all': 'present'}

## Topics
### the last season (`topic.bc03-last-season`; stages [0, 10]; essential: no refusal band)
- Intent: the crew asked to end their last season early and were refused; he freed them and hires them still; offered once BC01 has reached stage 90, it starts the quest
- May state:
  - `fact.bc03.refused`: Heavy-Rope's crew asked to end their last season early and were refused.
  - `fact.bc03.freed-and-hired`: Ussa-Rekh bought out Owings for thirty years, and now hires out the crews he freed.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: interrogate (Ussa-Rekh and Heavy-Rope), in a crowd or a market
- Directions to give: Soulrest's open dock is the long dock on the town's water, where the crews wait for hire; Ussa-Rekh keeps his chest beside him on the planks.
- Heavy-Rope's knowledge at stage 0:
  - `fact.bc03.break`: knows
  - `fact.bc03.freed-and-hired`: knows
  - `fact.bc03.refused`: knows
  - `fact.bc03.tokens`: knows
- The player already knows at stage 0 (anything else is explained when first named):

### the tokens (`topic.bc03-the-tokens`; stages [10]; not essential)
- Intent: said once both accounts are heard; standing with the crew: the tokens are in the chest beside him on the dock, and a crew that breaks them before him is done with him
- May state:
  - `fact.bc03.tokens`: He keeps a crew's carved tokens in the chest beside him on the dock until their last season is worked.
  - `fact.bc03.break`: A crew that breaks its tokens before him is done with him.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: interrogate (Ussa-Rekh and Heavy-Rope), in a crowd or a market
- Directions to give: Soulrest's open dock is the long dock on the town's water, where the crews wait for hire; Ussa-Rekh keeps his chest beside him on the planks.
- Heavy-Rope's knowledge at stage 10:
  - `fact.bc03.break`: knows
  - `fact.bc03.freed-and-hired`: knows
  - `fact.bc03.refused`: knows
  - `fact.bc03.tokens`: knows
- The player already knows at stage 10 (anything else is explained when first named):

### your tokens (`topic.bc03-break`; stages [20]; not essential)
- Intent: said only with the tokens in hand (C-item): the player gives them over and the crew break them before Ussa-Rekh
- May state:
  - `fact.bc03.break`: A crew that breaks its tokens before him is done with him.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - lockpicking: open-a-strongbox (Ussa-Rekh's chest), in a crowd or a market
  - sneak: steal (the crew's tokens), in a crowd or a market
- Directions to give: Ussa-Rekh's chest stands on the planks beside him, on a low lock.
- Heavy-Rope's knowledge at stage 20:
  - `fact.bc03.break`: knows
  - `fact.bc03.freed-and-hired`: knows
  - `fact.bc03.refused`: knows
  - `fact.bc03.tokens`: knows
- The player already knows at stage 20 (anything else is explained when first named):
  - `fact.bc03.freed-and-hired`: Ussa-Rekh bought out Owings for thirty years, and now hires out the crews he freed.
  - `fact.bc03.refused`: Heavy-Rope's crew asked to end their last season early and were refused.

### the refusal (`topic.bc03-brawl`; stages [10]; not essential)
- Intent: said once both accounts are heard; standing with Ussa-Rekh: Heavy-Rope will not take the refusal from a stranger's mouth
- May state:
  - `fact.bc03.refused`: Heavy-Rope's crew asked to end their last season early and were refused.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: interrogate (Ussa-Rekh and Heavy-Rope), in a crowd or a market
- Directions to give: Soulrest's open dock is the long dock on the town's water, where the crews wait for hire; Ussa-Rekh keeps his chest beside him on the planks.
- Heavy-Rope's knowledge at stage 10:
  - `fact.bc03.break`: knows
  - `fact.bc03.freed-and-hired`: knows
  - `fact.bc03.refused`: knows
  - `fact.bc03.tokens`: knows
- The player already knows at stage 10 (anything else is explained when first named):

### enough (`topic.bc03-yield`; stages [30]; not essential)
- Intent: he takes the refusal when talked down (speechcraft) or when his crew are paid 50 gold; the crew will work the season
- May state:
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: persuade (Heavy-Rope), in a crowd or a market
  - mercantile: bribe (Heavy-Rope), in a crowd or a market
- Directions to give: Heavy-Rope waits at the middle of the dock, among his crew.
- Heavy-Rope's knowledge at stage 30:
  - `fact.bc03.break`: knows
  - `fact.bc03.freed-and-hired`: knows
  - `fact.bc03.refused`: knows
  - `fact.bc03.tokens`: knows
- The player already knows at stage 30 (anything else is explained when first named):
  - `fact.bc03.freed-and-hired`: Ussa-Rekh bought out Owings for thirty years, and now hires out the crews he freed.
  - `fact.bc03.refused`: Heavy-Rope's crew asked to end their last season early and were refused.
  - `fact.bc03.tokens`: He keeps a crew's carved tokens in the chest beside him on the dock until their last season is worked.
  - `fact.bc03.break`: A crew that breaks its tokens before him is done with him.


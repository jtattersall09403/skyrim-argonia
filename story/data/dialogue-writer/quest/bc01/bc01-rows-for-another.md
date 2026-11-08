# Dialogue brief: Rows-For-Another (BC01 Four Months for a Boat)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; BC01's held woman (we.bc01.estate); grey from years away from her tree (labour-and-bondage §2, the tell). Outfit: unknown

## What the player cannot see
- Role: woman working off an Owing on the estate north of Blackrose (npc)
- Factions: none
- Wants: to go home to her tree before she greys further
- Fears: being taken back, and that the estate's men pay for it on the next one held

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Never-Sold: Chainbreaker patron who keeps the Chainbreakers' house in Blackrose
- Hulm-Tei: steward of the ex-Archein estate north of Blackrose

## Things lines may name (and only these)
- `thing.bc01.house`: place; Blackrose; {'all': 'present'}
- `thing.bc01.landing`: place; the swamp road north of Blackrose; {'all': 'present'}
- `item.bc01.debt-book`: item; the landing; {'after-90': 'taken by Never-Sold', 'before-10': 'absent', 'during': 'in the chest, or carried'}
- `thing.bc01.estate-people`: actors; the landing; {'all': 'present'}
- `thing.bc01.never-sold`: actors; the house, then the landing; {'after-10': 'at the landing', 'after-90': 'in the house', 'before-10': 'in the house'}
- `thing.bc01.zones`: triggers; the landing and Blackrose; {'all': 'present'}

## Topics
### the channel (`topic.bc01-cut-loose`; stages [10]; essential: no refusal band)
- Intent: said only after dark (C-time): she will not wait on the book; two men stand the landing and the channel leaves the estate; she cannot drown; she follows the player; by day, or while the estate men can see, she says only: not in daylight, with the men watching; come back after dark
- May state:
  - `fact.bc01.night-men`: Two estate men walk the landing at night.
  - `fact.bc01.channel`: The channel runs from the landing out of the estate's reach, and she cannot drown in it.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Lockpicking: pick-a-lock (the steward's chest on the landing), on a worked landing by day
  - sneak: steal (the debt book), on a worked landing by day
  - sneak: sneak-past (the two estate men), at night
- Directions to give: From the Chainbreakers' house take the swamp road north out of Blackrose; the estate's landing is a short walk on, on the channel side, with boats at the water. The steward's chest stands on the landing.
- Rows-For-Another's knowledge at stage 10:
  - `fact.bc01.boat-owing`: knows
  - `fact.bc01.book-chest`: knows
  - `fact.bc01.channel`: knows
  - `fact.bc01.night-men`: knows
  - `fact.bc01.washed-out`: knows
- The player already knows at stage 10 (anything else is explained when first named):


# Dialogue brief: Hulm-Tei (BC01 Four Months for a Boat)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; BC01's steward (we.bc01.estate; gap-register QA3); keeps the estate's debt book. Outfit: unknown

## What the player cannot see
- Role: steward of the ex-Archein estate north of Blackrose (npc)
- Factions: none
- Wants: the estate's book kept and its work done (labour-and-bondage §2, the ex-Archein families keep the books)
- Fears: being called a slaver, which by the letter he is not

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Never-Sold: Chainbreaker patron who keeps the Chainbreakers' house in Blackrose
- Rows-For-Another: woman working off an Owing on the estate north of Blackrose

## Things lines may name (and only these)
- `thing.bc01.house`: place; Blackrose; {'all': 'present'}
- `thing.bc01.landing`: place; the swamp road north of Blackrose; {'all': 'present'}
- `item.bc01.debt-book`: item; the landing; {'after-90': 'taken by Never-Sold', 'before-10': 'absent', 'during': 'in the chest, or carried'}
- `thing.bc01.estate-people`: actors; the landing; {'all': 'present'}
- `thing.bc01.never-sold`: actors; the house, then the landing; {'after-10': 'at the landing', 'after-90': 'in the house', 'before-10': 'in the house'}
- `thing.bc01.zones`: triggers; the landing and Blackrose; {'all': 'present'}

## Topics
### the debt book (`topic.bc01-the-book`; stages [10]; not essential)
- Intent: every line of his book is true; he names the buy-out by it
- May state:
  - `fact.bc01.book-true`: Every line of the estate's debt book is true: her food, the boat's upkeep, her sick days.
- Hides (until the intent says otherwise):
  - `fact.bc01.book-chest`: The steward keeps the debt book in a locked chest on the landing.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Lockpicking: pick-a-lock (the steward's chest on the landing), on a worked landing by day
  - sneak: steal (the debt book), on a worked landing by day
  - sneak: sneak-past (the two estate men), at night
- Directions to give: From the Chainbreakers' house take the swamp road north out of Blackrose; the estate's landing is a short walk on, on the channel side, with boats at the water. The steward's chest stands on the landing.
- Hulm-Tei's knowledge at stage 10:
  - `fact.bc01.boat-owing`: knows
  - `fact.bc01.book-chest`: knows
  - `fact.bc01.book-true`: knows
- The player already knows at stage 10 (anything else is explained when first named):


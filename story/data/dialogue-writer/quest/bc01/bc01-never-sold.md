# Dialogue brief: Never-Sold (BC01 Four Months for a Boat)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Holds the post: the Chainbreaker patron who keeps the Chainbreakers' house in Blackrose (BM&V's House). Outfit: saxhleel-tunic-wrap-orange+marsh-native-sandals

## What the player cannot see
- Role: Chainbreaker patron who keeps the Chainbreakers' house in Blackrose (npc)
- Factions: none
- Wants: the woman bought out at what her Owing was, by the estate's own book (36-cast-roster §56, the accountant)
- Fears: a rash act that lands on the woman (principles/social.md, BONDAGE)

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Rows-For-Another: woman working off an Owing on the estate north of Blackrose
- Hulm-Tei: steward of the ex-Archein estate north of Blackrose

## Things lines may name (and only these)
- `thing.bc01.house`: place; Blackrose; {'all': 'present'}
- `thing.bc01.landing`: place; the swamp road north of Blackrose; {'all': 'present'}
- `item.bc01.debt-book`: item; the landing; {'after-90': 'taken by Never-Sold', 'before-10': 'absent', 'during': 'in the chest, or carried'}
- `thing.bc01.estate-people`: actors; the landing; {'all': 'present'}
- `thing.bc01.never-sold`: actors; the house, then the landing; {'after-10': 'at the landing', 'after-90': 'in the house', 'before-10': 'in the house'}
- `thing.bc01.zones`: triggers; the landing and Blackrose; {'all': 'present'}

## Topics
### the estate (`topic.bc01-the-estate`; stages [0]; essential: no refusal band)
- Intent: a woman on the estate took a boat on four months' work eleven years ago and works it still; Never-Sold has put by enough to buy out what it was; the steward keeps the debt book in a locked chest on the landing; Rows-For-Another talks of the channel after dark, which Never-Sold fears
- May state:
  - `fact.bc01.boat-owing`: Rows-For-Another took a boat from the estate on an Owing of four months, eleven years ago.
  - `fact.bc01.put-by`: Never-Sold has put by enough to buy out what the Owing was.
  - `fact.bc01.book-chest`: The steward keeps the debt book in a locked chest on the landing.
  - `fact.bc01.channel`: The channel runs from the landing out of the estate's reach, and she cannot drown in it.
- Never-Sold's knowledge at stage 0:
  - `fact.bc01.boat-owing`: knows
  - `fact.bc01.book-chest`: knows
  - `fact.bc01.book-true`: knows
  - `fact.bc01.channel`: knows
  - `fact.bc01.put-by`: knows
- The player already knows at stage 0 (anything else is explained when first named):

### paying her out (`topic.bc01-bring-down`; stages [10]; not essential)
- Intent: with the book in hand (C-item), Never-Sold tears out Rows-For-Another's page, gives it to her, and leaves the first price, four months, in coin in the steward's chest; nothing is argued
- May state:
  - `fact.bc01.book-true`: Every line of the estate's debt book is true: her food, the boat's upkeep, her sick days.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Lockpicking: pick-a-lock (the steward's chest on the landing), on a worked landing by day
  - sneak: steal (the debt book), on a worked landing by day
  - sneak: sneak-past (the two estate men), at night
- Directions to give: From the Chainbreakers' house take the swamp road north out of Blackrose; the estate's landing is a short walk on, on the channel side, with boats at the water. The steward's chest stands on the landing.
- Never-Sold's knowledge at stage 10:
  - `fact.bc01.boat-owing`: knows
  - `fact.bc01.book-chest`: knows
  - `fact.bc01.book-true`: knows
  - `fact.bc01.channel`: knows
  - `fact.bc01.put-by`: knows
- The player already knows at stage 10 (anything else is explained when first named):


# Dialogue brief: Never-Sold (BC02 One Out of the Smoke)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Holds the post: the Chainbreaker patron who keeps the Chainbreakers' house in Blackrose (BM&V's House). Outfit: saxhleel-tunic-wrap-orange+marsh-native-sandals

## What the player cannot see
- Role: Chainbreaker patron who keeps the Chainbreakers' house in Blackrose (npc)
- Factions: none
- Wants: the held brought out and their names kept (36-cast-roster §56)
- Fears: that the heirs' own reckoning decides who counts as the Rose's

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Third-Born Tsaxi: gate-keeper of the Rose's outer post, one of the heirs
- Says-It-Plain: man the Rose's heirs hold for speaking against them
- Hides-In-Reeds: woman the Rose's heirs hold for a killing
- Keeps-The-Old-Count: Rows-For-Another's mother, held by the Rose's heirs on their reckoning of her Owing

## Things lines may name (and only these)
- `thing.bc02.house`: place; Blackrose; {'all': 'present'}
- `thing.bc02.gate`: place; the hill west of Blackrose; {'all': 'present'}
- `thing.bc02.cells`: place; inside the keep, out of sight of each other; {'after-end': 'as BM&V left it', 'during': 'smoke under ref.bc02.smoke'}
- `thing.bc02.people`: actors; the keep; {'all': 'present'}
- `thing.bc02.zones`: triggers; the keep; {'all': 'present'}

## Topics
### the fire (`topic.bc02-the-fire`; stages [0]; essential: no refusal band)
- Intent: the heirs' outer post, the old keep above Blackrose, is burning, and three the heirs hold are inside, Rows-For-Another's mother among them; nobody says how it started; asked after BC01, it starts the quest; names all three and why each is held; Third-Born Tsaxi keeps its way in
- May state:
  - `fact.bc02.fire`: The heirs' outer post, the old keep above Blackrose, is burning, and nobody says how it started. Third-Born Tsaxi keeps its way in.
  - `fact.bc02.three-held`: Three are bound inside: Says-It-Plain, held for speaking against the heirs; Hides-In-Reeds, held for a killing; and Keeps-The-Old-Count, Rows-For-Another's mother, working off what the heirs reckon she owes.
- Never-Sold's knowledge at stage 0:
  - `fact.bc02.fire`: knows
  - `fact.bc02.three-held`: knows
- The player already knows at stage 0 (anything else is explained when first named):


# Dialogue brief: Hides-In-Reeds (BC02 One Out of the Smoke)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; BC02's second held (we.bc02.people; gap-register QA20). Outfit: unknown

## What the player cannot see
- Role: woman the Rose's heirs hold for a killing (npc)
- Factions: none
- Wants: out; she does not deny the killing
- Fears: being left as the one who deserved it

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Never-Sold: Chainbreaker patron who keeps the Chainbreakers' house in Blackrose
- Third-Born Tsaxi: gate-keeper of the Rose's outer post, one of the heirs
- Says-It-Plain: man the Rose's heirs hold for speaking against them
- Keeps-The-Old-Count: Rows-For-Another's mother, held by the Rose's heirs on their reckoning of her Owing

## Things lines may name (and only these)
- `thing.bc02.house`: place; Blackrose; {'all': 'present'}
- `thing.bc02.gate`: place; the hill west of Blackrose; {'all': 'present'}
- `thing.bc02.cells`: place; inside the keep, out of sight of each other; {'after-end': 'as BM&V left it', 'during': 'smoke under ref.bc02.smoke'}
- `thing.bc02.people`: actors; the keep; {'all': 'present'}
- `thing.bc02.zones`: triggers; the keep; {'all': 'present'}

## Topics
### come with me (`topic.bc02-come-killer`; stages [30]; not essential)
- Intent: the choice: she follows the player
- May state:
  - `fact.bc02.three-held`: Three are bound inside: Says-It-Plain, held for speaking against the heirs; Hides-In-Reeds, held for a killing; and Keeps-The-Old-Count, Rows-For-Another's mother, working off what the heirs reckon she owes.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - sneak: sneak-past (the burning floors), in a flooded ruin, root-cave or under water
- Directions to give: The three held are on the keep's floors in the smoke; the way out is the way I came in.
- Hides-In-Reeds's knowledge at stage 30:
  - `fact.bc02.three-held`: knows
- The player already knows at stage 30 (anything else is explained when first named):
  - `fact.bc02.fire`: The heirs' outer post, the old keep above Blackrose, is burning, and nobody says how it started. Third-Born Tsaxi keeps its way in.
  - `fact.bc02.three-held`: Three are bound inside: Says-It-Plain, held for speaking against the heirs; Hides-In-Reeds, held for a killing; and Keeps-The-Old-Count, Rows-For-Another's mother, working off what the heirs reckon she owes.


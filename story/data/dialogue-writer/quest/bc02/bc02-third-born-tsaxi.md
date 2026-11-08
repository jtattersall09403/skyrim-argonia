# Dialogue brief: Third-Born Tsaxi (BC02 One Out of the Smoke)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; BC02's gate-keeper at the outer post (we.bc02.people; prisons.md, the heirs; gap-register QA4). Outfit: unknown

## What the player cannot see
- Role: gate-keeper of the Rose's outer post, one of the heirs (npc)
- Factions: none
- Wants: the post kept and none of the heirs lost in the smoke (prisons.md, the heirs' hierarchy)
- Fears: being blamed for the fire

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Never-Sold: Chainbreaker patron who keeps the Chainbreakers' house in Blackrose
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
### the keep (`topic.bc02-the-gate`; stages [20]; not essential)
- Intent: said only at Speech 25: the heirs will not go in; plainly, only one will come out; he lets the player in; below Speech 25 he refuses plainly
- May state:
  - `fact.bc02.one-out`: The way out will bear one trip; whoever is left inside, the fire takes.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: persuade (Third-Born Tsaxi), open ground by day
  - sneak: sneak-past (Third-Born Tsaxi), open ground by day
- Directions to give: The keep stands on the hill a short climb west of the 'Black Rose Jail' marker, at Blackrose's edge; Tsaxi keeps its way in.
- Third-Born Tsaxi's knowledge at stage 20:
  - `fact.bc02.fire`: knows
  - `fact.bc02.one-out`: knows
  - `fact.bc02.three-held`: knows
- The player already knows at stage 20 (anything else is explained when first named):

### let them by (`topic.bc02-let-by`; stages [31, 32, 33]; not essential)
- Intent: said only at Speech 25: he lets the one brought out go by, since the heirs lost nothing they would go in for; below 25 he refuses plainly
- May state:
  - `fact.bc02.one-out`: The way out will bear one trip; whoever is left inside, the fire takes.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: persuade (Third-Born Tsaxi), open ground by day
  - sneak: sneak-past (Third-Born Tsaxi), open ground by day
  - speechcraft: persuade (Third-Born Tsaxi), open ground by day
  - sneak: sneak-past (Third-Born Tsaxi), open ground by day
  - speechcraft: persuade (Third-Born Tsaxi), open ground by day
  - sneak: sneak-past (Third-Born Tsaxi), open ground by day
- Directions to give: The way out is the way I came in, past Tsaxi.
- Directions to give: The way out is the way I came in, past Tsaxi.
- Directions to give: The way out is the way I came in, past Tsaxi.
- Third-Born Tsaxi's knowledge at stage 31:
  - `fact.bc02.fire`: knows
  - `fact.bc02.one-out`: knows
  - `fact.bc02.three-held`: knows
- The player already knows at stage 31 (anything else is explained when first named):
  - `fact.bc02.fire`: The heirs' outer post, the old keep above Blackrose, is burning, and nobody says how it started. Third-Born Tsaxi keeps its way in.
  - `fact.bc02.three-held`: Three are bound inside: Says-It-Plain, held for speaking against the heirs; Hides-In-Reeds, held for a killing; and Keeps-The-Old-Count, Rows-For-Another's mother, working off what the heirs reckon she owes.
  - `fact.bc02.three-held`: Three are bound inside: Says-It-Plain, held for speaking against the heirs; Hides-In-Reeds, held for a killing; and Keeps-The-Old-Count, Rows-For-Another's mother, working off what the heirs reckon she owes.
  - `fact.bc02.one-out`: The way out will bear one trip; whoever is left inside, the fire takes.


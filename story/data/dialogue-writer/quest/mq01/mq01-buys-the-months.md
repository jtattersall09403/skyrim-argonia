# Dialogue brief: Buys-The-Months (MQ01 No Name on the Work Roll)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; Holds the gang's bought months and hires it to Hereguard Plantation; stands on the pier at Dock1 (we.mq01.broker). Outfit: saxhleel-tunic-long-grey+marsh-native-foot-wraps

## What the player cannot see
- Role: the debt-labour broker (npc)
- Factions: none
- Wants: the gang up the plank and in Hereguard's paddies by dark with every month it owes still his (QA7)
- Fears: a hand who owes nothing on his roll, since he cannot hire out what is not owed

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Wuleen-Sei: npc.opening.overseer
- Ux-Xeek: npc.opening.roll-reader
- Mee-Tuja: npc.opening.courier
- Sal-Sei: the clutch-keeper
- Deesh-Duun: the witness
- Ties-The-Loose-Plank: a gang family
- Dives-Without-A-Rope: a gang family
- Finds-The-Other-Bank: a gang family
- Cuts-the-Old-Knot: Leader of the Unbound Root

## Things lines may name (and only these)
- `thing.mq01.hold`: place; Lilmoth, Lilmoth's dock; {'after-90': "crew and gang off (MQ01's crew parent disabled)", 'before-90': 'crew and gang present'}
- `thing.mq01.crew`: actors; the hold, the plank and the shore path; {}
- `thing.mq01.broker`: actors; the pier at Lilmoth's dock, Lilmoth; {'after-90': 'gone from the pier', 'before-90': 'on the pier'}
- `thing.mq01.gang`: actors; the hold, the march, the camp; {'all': 'present until the strike'}
- `thing.mq01.families`: actors; the camp; {'after-41': 'Sal-Sei follows the player (alias package, stages 41 to 90)', 'after-42': 'Deesh-Duun follows the player (alias package, stages 42 to 91)', 'all': 'present until the strike'}
- `thing.mq01.survivors`: actors; the shore below the camp; {'after-90': 'on the shore, burnt and wet', 'before-90': 'off'}
- `thing.mq01.camp`: place; the paddy edge of Hereguard Plantation; {'after-90': 'aftermath (the cutting withdrawn, the clutch grey)', 'at-40': 'attacked (fire in the huts)', 'before-40': 'orderly'}
- `thing.mq01.cutting`: dressing; the camp; {'after-40': 'withdrawn (light out)', 'before-40': 'lit'}
- `thing.mq01.cell`: actors; the water's edge of the camp; {'after-40': "Cuts-the-Old-Knot gone; the two cutters at the shed, then on the plank boards, then disabled at the water's edge", 'at-40': 'enabled', 'before-40': 'disabled'}
- `thing.mq01.zones`: triggers; the camp and the shore below it; {'all': 'present'}
- `thing.mq01.changes`: record; Lilmoth and Hereguard Plantation; {'all': 'as the ledger says'}

## Topics
### the hire (`topic.mq01-the-hire`; stages [10]; not essential)
- Intent: on the pier at the plank: whose the gang's months are and where they are hired; what he makes of the answer he heard given
- May state:
  - `fact.mq01.broker-holds`: The broker on the pier at Lilmoth's dock holds the gang's months and hires them out to Hereguard Plantation; my blank line is his to fill or to leave.
  - `fact.mq01.owing-roll`: Everyone on the broker's gang owes months, and the roll adds months for food.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: lie (Wuleen-Sei), before witnesses (a council, a hearing, a household)
  - Sneak: spy (Mee-Tuja), in a crowd or a market
  - Speechcraft: persuade (Buys-The-Months), in a crowd or a market
- Directions to give: The hold is the barge's one room below the deck; its door leads up to the plank and the pier of Lilmoth's dock. From the plank at Lilmoth's dock the shore path runs north and west along the water, past the first of the rice dikes; the camp is the cluster of huts on the reed bank at the paddy edge, where the path meets the reeds. The fire is in the middle of the camp; the hatching shed stands beside the cutting at the camp's far end.
- Buys-The-Months's knowledge at stage 10:
  - `fact.mq01.blank-line`: knows
  - `fact.mq01.broker-holds`: knows
  - `fact.mq01.owing-roll`: knows
- The player already knows at stage 10 (anything else is explained when first named):


# Dialogue brief: Cuts-the-Old-Knot (MQ01 No Name on the Work Roll)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Holds the post: the leader of the Unbound Root (The Quiet Camp). Outfit: glass-helmet+elven-cuirass+glass-gauntlets+elven-boots

## What the player cannot see
- Role: Leader of the Unbound Root (npc)
- Factions: none
- Wants: the satchel, and the cutting severed from its clutch
- Fears: the gang families defending the cutting before her cell has cut it

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Wuleen-Sei: npc.opening.overseer
- Buys-The-Months: the debt-labour broker
- Ux-Xeek: npc.opening.roll-reader
- Mee-Tuja: npc.opening.courier
- Sal-Sei: the clutch-keeper
- Deesh-Duun: the witness
- Ties-The-Loose-Plank: a gang family
- Dives-Without-A-Rope: a gang family
- Finds-The-Other-Bank: a gang family

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

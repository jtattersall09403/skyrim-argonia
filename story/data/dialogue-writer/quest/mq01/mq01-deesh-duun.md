# Dialogue brief: Deesh-Duun (MQ01 No Name on the Work Roll)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Knows every family in the camp and mends the nets at the shed's corner. Outfit: marsh-native-kilt+marsh-native-foot-wraps

## What the player cannot see
- Role: the witness (npc)
- Factions: none
- Wants: off the roll and out of the broker's hire
- Fears: the cell's blades, and the fire in the huts

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- Stance voice: chatter rambling; contraction rate 0.4; addresses the player as "visitor"; favourite subject faction
- Quirk: Names a person by their family's hand on the roll.
- Never mentions: Who among the neighbours took the An-Xileel's side in 4E 48.
- Never mentions: That a family was once owned, or once owned others.
- Never mentions: Who sold the last cargo.
- Never mentions: How many on the roll never came back.
- Never mentions: The Chukka-Sei naming secrets.

## Culture chain (most specific last)
- **Black Marsh** (province): formality plain; never says: Who among the neighbours took the An-Xileel's side in 4E 48.; That a family was once owned, or once owned others.
- **Alten Corimont and the river camps (the pirate freeholds)** (region): formality low; never says: Who sold the last cargo.; How many on the roll never came back.
- **Argonian, tribal and interior-raised** (people): formality formal; never says: The Chukka-Sei naming secrets.; What the Hist said in the last dream-wallow.
- **Gang Ground** (settlement): formality low; never says: How much a named hand still owes.
- **The gang families** (group): formality low; never says: That the families should leave the clutch. Two break this on purpose. Finds-The-Other-Bank would take the families to the port. Ri'Sakka is counted a hand and never kin, so the clutch does not hold him.

## Others in the quest (the player may be sent to them)
- Wuleen-Sei: npc.opening.overseer
- Buys-The-Months: the debt-labour broker
- Ux-Xeek: npc.opening.roll-reader
- Mee-Tuja: npc.opening.courier
- Sal-Sei: the clutch-keeper
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

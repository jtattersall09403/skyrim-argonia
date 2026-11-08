# Dialogue brief: Dives-Without-A-Rope (MQ01 No Name on the Work Roll)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Has the shed names by heart and says them in order after a shift. Outfit: saxhleel-tunic-short-blue+marsh-native-foot-wraps

## What the player cannot see
- Role: a gang family (npc)
- Factions: none
- Wants: to stand beside the camp's cutting before her colour is gone, as she cannot beside her own Hist
- Fears: that the camp's cutting will not be there on the morning

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- Stance voice: chatter terse; contraction rate 0.05; addresses the player as "you"; favourite subject hist
- Quirk: Lists things in threes, the way she says the shed names.
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
- Deesh-Duun: the witness
- Ties-The-Loose-Plank: a gang family
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
### the years from home (`topic.mq01-the-march`; stages [10]; not essential)
- Intent: on the march, if the player walks beside her, what the years from her Hist have cost and what the cutting is to the families
- May state:
  - `fact.mq01.washed-out`: Two of the gang have been kept from their Hist so long that their colour and markings have thinned.
  - `fact.mq01.gang-hist`: The gang families keep a Hist cutting from Nine Bends at their camp, with their clutch at its roots.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: lie (Wuleen-Sei), before witnesses (a council, a hearing, a household)
  - Sneak: spy (Mee-Tuja), in a crowd or a market
  - Speechcraft: persuade (Buys-The-Months), in a crowd or a market
- Directions to give: The hold is the barge's one room below the deck; its door leads up to the plank and the pier of Lilmoth's dock. From the plank at Lilmoth's dock the shore path runs north and west along the water, past the first of the rice dikes; the camp is the cluster of huts on the reed bank at the paddy edge, where the path meets the reeds. The fire is in the middle of the camp; the hatching shed stands beside the cutting at the camp's far end.
- Dives-Without-A-Rope's knowledge at stage 10:
  - `fact.mq01.gang-hist`: knows
  - `fact.mq01.owing-roll`: knows
  - `fact.mq01.washed-out`: knows
- The player already knows at stage 10 (anything else is explained when first named):


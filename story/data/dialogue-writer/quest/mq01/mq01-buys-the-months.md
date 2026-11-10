# Dialogue brief: Buys-The-Months (MQ01 No Name on the Work Roll)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; Holds the gang's bought months and hires it out to unload the lighters at Lilmoth's dock; stands on the pier at Dock1 (we.mq01.broker). Outfit: saxhleel-tunic-long-grey+marsh-native-foot-wraps

## What the player cannot see
- Role: the debt-labour broker (npc)
- Factions: none
- Wants: the gang unloading his lighters at the dock with every month it owes still his (QA7)
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
- `thing.mq01.crew`: actors; the hold, the plank and the dock; {}
- `thing.mq01.broker`: actors; the pier at Lilmoth's dock, Lilmoth; {'after-90': 'gone from the pier', 'before-90': 'on the pier'}
- `thing.mq01.gang`: actors; the hold, the march, the camp; {'all': 'present until the strike'}
- `thing.mq01.families`: actors; the camp; {'after-41': 'Sal-Sei follows the player (alias package, stages 41 to 90)', 'after-42': 'Deesh-Duun follows the player (alias package, stages 42 to 91)', 'all': 'present until the strike'}
- `thing.mq01.survivors`: actors; the shore just west of the camp; {'after-90': 'on the shore, burnt and wet', 'before-90': 'off'}
- `thing.mq01.camp`: place; where Lilmoth's dock meets the land, Lilmoth; {'after-90': 'aftermath (the cutting withdrawn, the clutch grey)', 'at-40': 'attacked (fire in the huts)', 'before-40': 'orderly'}
- `thing.mq01.cutting`: dressing; the camp; {'after-40': 'withdrawn (light out)', 'before-40': 'lit'}
- `thing.mq01.cell`: actors; the water's edge of the camp; {'after-40': 'Cuts-the-Old-Knot gone; the two cutters at the shed until the ending', 'at-40': 'enabled', 'before-40': 'disabled'}
- `thing.mq01.zones`: triggers; the pier, the camp and the shore just west of it; {'all': 'present'}
- `thing.mq01.changes`: record; Lilmoth and Lilmoth's dock; {'all': 'as the ledger says'}
- `thing.mq01.roll`: dressing; the hold, then the camp's fire; {'after-40': 'burnt in the fire', 'before-40': 'with Wuleen-Sei'}
- `thing.mq01.strap`: item; under the boards by the camp's fire; {'after-40': 'in the trap'}
- `thing.mq01.trap`: container; under the boards by the camp's fire; {'all': 'present'}

## Topics
### Whose gang is this? (`topic.mq01-the-hire`; stages [20, 30]; not essential)
- Intent: whose the gang's months are and what work he hires the gang to
- May state:
  - `fact.mq01.broker-holds`: The broker on the pier at Lilmoth's dock holds the gang's months and hires them out to unload the lighters at Lilmoth's dock; my blank line is his to fill or to leave.
  - `fact.mq01.owing-roll`: Everyone on the broker's gang owes months, and the overseer adds months to the roll for food.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: persuade (Buys-The-Months), in a crowd or a market
- Directions to give: The hold's way out is the door at the top of its stairs, which opens onto the pier at Lilmoth's dock.
- Directions to give: From the plank's foot the dock runs about fifty paces toward the land; the camp's fire burns on the open ground at the dock's landward end, with the hatching shed beyond it and the families' huts on the water to the west.
- Buys-The-Months's knowledge at stage 20:
  - `fact.mq01.blank-line`: knows
  - `fact.mq01.broker-holds`: knows
  - `fact.mq01.owing-roll`: knows
- The player already knows at stage 20 (anything else is explained when first named):
  - `fact.mq01.owing-roll`: Everyone on the broker's gang owes months, and the overseer adds months to the roll for food.
  - `fact.mq01.blank-line`: The roll has a line for me and no name on it.
  - `fact.mq01.washed-out`: Two of the gang have been kept from their Hist so long that their colour and markings have thinned.

## Already said near you

These people stand in the same place during the same stretch of play, and the player hears them one after another. Each fact below is theirs to say: do not restate it. Say what only you would say, from your own work and stake; where the player needs the fact, point to its owner by name ("ask Wuleen-Sei about the months") in a few words. Do not reuse their wording.

- Finds-The-Other-Bank (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Ri-Sakka (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Tsanji (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Llarvi-Maryon (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Wuleen-Sei (MQ01 stages 20, 30 at lilmoth): answers Where are we going?
- Mee-Tuja (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Sal-Sei (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Deesh-Duun (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Nesh-Neel (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Cuts-The-Old-Knot (MQ01 stages 20, 30 at lilmoth): answers Who are you?
- Uleesh (MQ01 stages 20, 30 at lilmoth): answers talk.secret; owns `fact.lilmoth.01512d.secret.salty` (A giant crab called Old Salty lives in the shallows about 70 m south-south-west of here.)
- Flaa Heet (MQ01 stages 20, 30 at lilmoth): answers talk.lore, talk.someone; owns `fact.lilmoth.02a1e7.someone.tseeta` (Tseeta sells from her stall about 10 m north of here, and Okeeh-Jas from hers about 5 m south-south-west.); `fact.lilmoth.lore.council` (Lilmoth has no single ruler; a council of powerful merchants governs it and pays guards to patrol the streets.); `fact.lilmoth.lore.elders` (In Lilmoth people take their quarrels to their elders, retired Shadowscales among them, not to a court.)
- Peeks-Under-Boats (MQ01 stages 20, 30 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a1e9.someone.headman` (Flaa Heet, the headman, stands by the cooking spit about 20 m south of here.); `fact.lilmoth.02a1e9.someone.hums` (Hums-To-The-Rain is usually about 20 m south-south-west of here, on the west side of the village.)
- Tseeta (MQ01 stages 20, 30 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a1ed.someone.rival` (Okeeh-Jas keeps the other stall about 20 m south of here.)
- Hums-To-The-Rain (MQ01 stages 20, 30 at lilmoth): answers talk.lore; owns `fact.lilmoth.lore.washed-out` (An Argonian kept long from their own Hist fades: colour thins and markings go soft, and they come back when...)
- Okeeh-Jas (MQ01 stages 20, 30 at lilmoth): answers talk.lore, talk.rumours; owns `fact.lilmoth.02a1f2.rumours.drinker` (A drinker called Deep-In-His-Cups sits out on the shore track about 150 m north-east of here, and he talks to...); `fact.lilmoth.lore.owing-sold` (An owing can be sold on: a holder owed months can sell them to someone who needs hands, and the worker goes...)
- Haxal-Tei (MQ01 stages 20, 30 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a204.someone.band` (His band camp here: Heem-Tsal the fire mage about 10 m west-south-west and Keeps-Both-Edges about 5 m west of...)
- Heem-Tsal (MQ01 stages 20, 30 at lilmoth): answers talk.lore, talk.someone; owns `fact.lilmoth.02a205.someone.books` (A bookseller, Looks-At-Books, keeps her shelf at Hereguard Plantation, about 360 m west of here.); `fact.lilmoth.lore.council.ask-02a205` (Ask Flaa Heet about it: Lilmoth has no single ruler; a council of powerful merchants governs it and pays...)
- Keeps-Both-Edges (MQ01 stages 20, 30 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a206.someone.thieves` (Two Argonians loiter by the leeks to the north, Sheeh-Vos about 45 m north-north-east and Waits-For-Lanterns...)
- Deep-In-His-Cups (MQ01 stages 20, 30 at lilmoth): answers talk.lore, talk.rumours; owns `fact.lilmoth.02a207.rumours.dead-dunmer` (Three dead Dunmer lie at the east end of Lilmoth Dock, about 70 m north-north-east of here; nobody has buried...); `fact.lilmoth.dock.big-ship` (A big ship lies moored at Lilmoth Dock, with steps going down from the dock to the water beside it.)
- Sheeh-Vos (MQ01 stages 20, 30 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a208.someone.drinker` (Deep-In-His-Cups sits about 25 m south-south-east of here; he sees everything at the dock and remembers half.)
- Waits-For-Lanterns (MQ01 stages 20, 30 at lilmoth): answers talk.secret; owns `fact.lilmoth.02a209.secret.trapdoor` (Near the graves north of Lilmoth's walls, about 145 m north-west of here, a trapdoor in the ground leads down...)


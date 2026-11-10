# Dialogue brief: Ux-Xeek (MQ01 No Name on the Work Roll)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Holds the post: npc.opening.roll-reader (The Roll). Outfit: saxhleel-tunic-short-brown

## What the player cannot see
- Role: npc.opening.roll-reader (npc)
- Factions: none
- Wants: the names called without a mistake
- Fears: being the hand who loses a name from the hold

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Wuleen-Sei: npc.opening.overseer
- Buys-The-Months: the debt-labour broker
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
### Who are you? (`topic.mq01-the-water`; stages [10]; not essential)
- Intent: hands the player the day's water and calls the names; says what the months for food come to
- May state:
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: lie (Wuleen-Sei), before witnesses (a council, a hearing, a household)
- Directions to give: The hold is the barge's one room below the deck; Wuleen-Sei stands in it with the gang.
- Ux-Xeek's knowledge at stage 10:
  - `fact.mq01.blank-line`: knows
  - `fact.mq01.owing-roll`: knows
- The player already knows at stage 10 (anything else is explained when first named):

## Already said near you

These people stand in the same place during the same stretch of play, and the player hears them one after another. Each fact below is theirs to say: do not restate it. Say what only you would say, from your own work and stake; where the player needs the fact, point to its owner by name ("ask Wuleen-Sei about the months") in a few words. Do not reuse their wording.

- Wuleen-Sei (MQ01 stage 10 at lilmoth): answers (Say nothing.), Do what you like with your roll., Put down the name I carry., Where are we going?, Why am I here?; owns `fact.mq01.blank-line` (The roll has a line for me and no name on it.); `fact.mq01.owing-roll` (Everyone on the broker's gang owes months, and the overseer adds months to the roll for food.)
- Dives-Without-A-Rope (MQ01 stage 10 at lilmoth): answers Why is your colour so thin?; owns `fact.mq01.gang-hist` (The gang families keep a Hist cutting from Nine Bends at their camp, with their clutch at its roots.); `fact.mq01.washed-out` (Two of the gang have been kept from their Hist so long that their colour and markings have thinned.)
- Finds-The-Other-Bank (MQ01 stage 10 at lilmoth): answers Who are you?
- Ri-Sakka (MQ01 stage 10 at lilmoth): answers Who are you?
- Tsanji (MQ01 stage 10 at lilmoth): answers Who are you?
- Llarvi-Maryon (MQ01 stage 10 at lilmoth): answers Who are you?
- Mee-Tuja (MQ01 stage 10 at lilmoth): answers Who are you?
- Sal-Sei (MQ01 stage 10 at lilmoth): answers Who are you?
- Deesh-Duun (MQ01 stage 10 at lilmoth): answers Who are you?
- Nesh-Neel (MQ01 stage 10 at lilmoth): answers Who are you?
- Cuts-The-Old-Knot (MQ01 stage 10 at lilmoth): answers Who are you?
- Uleesh (MQ01 stage 10 at lilmoth): answers talk.secret; owns `fact.lilmoth.01512d.secret.salty` (A giant crab called Old Salty lives in the shallows about 70 m south-south-west of here.)
- Flaa Heet (MQ01 stage 10 at lilmoth): answers talk.lore, talk.someone; owns `fact.lilmoth.02a1e7.someone.tseeta` (Tseeta sells from her stall about 10 m north of here, and Okeeh-Jas from hers about 5 m south-south-west.); `fact.lilmoth.lore.council` (Lilmoth has no single ruler; a council of powerful merchants governs it and pays guards to patrol the streets.); `fact.lilmoth.lore.elders` (In Lilmoth people take their quarrels to their elders, retired Shadowscales among them, not to a court.)
- Peeks-Under-Boats (MQ01 stage 10 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a1e9.someone.headman` (Flaa Heet, the headman, stands by the cooking spit about 20 m south of here.); `fact.lilmoth.02a1e9.someone.hums` (Hums-To-The-Rain is usually about 20 m south-south-west of here, on the west side of the village.)
- Tseeta (MQ01 stage 10 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a1ed.someone.rival` (Okeeh-Jas keeps the other stall about 20 m south of here.)
- Hums-To-The-Rain (MQ01 stage 10 at lilmoth): answers talk.lore; owns `fact.lilmoth.lore.washed-out` (An Argonian kept long from their own Hist fades: colour thins and markings go soft, and they come back when...)
- Okeeh-Jas (MQ01 stage 10 at lilmoth): answers talk.lore, talk.rumours; owns `fact.lilmoth.02a1f2.rumours.drinker` (A drinker called Deep-In-His-Cups sits out on the shore track about 150 m north-east of here, and he talks to...); `fact.lilmoth.lore.owing-sold` (An owing can be sold on: a holder owed months can sell them to someone who needs hands, and the worker goes...)
- Haxal-Tei (MQ01 stage 10 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a204.someone.band` (His band camp here: Heem-Tsal the fire mage about 10 m west-south-west and Keeps-Both-Edges about 5 m west of...)
- Heem-Tsal (MQ01 stage 10 at lilmoth): answers talk.lore, talk.someone; owns `fact.lilmoth.02a205.someone.books` (A bookseller, Looks-At-Books, keeps her shelf at Hereguard Plantation, about 360 m west of here.); `fact.lilmoth.lore.council.ask-02a205` (Ask Flaa Heet about it: Lilmoth has no single ruler; a council of powerful merchants governs it and pays...)
- Keeps-Both-Edges (MQ01 stage 10 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a206.someone.thieves` (Two Argonians loiter by the leeks to the north, Sheeh-Vos about 45 m north-north-east and Waits-For-Lanterns...)
- Deep-In-His-Cups (MQ01 stage 10 at lilmoth): answers talk.lore, talk.rumours; owns `fact.lilmoth.02a207.rumours.dead-dunmer` (Three dead Dunmer lie at the east end of Lilmoth Dock, about 70 m north-north-east of here; nobody has buried...); `fact.lilmoth.dock.big-ship` (A big ship lies moored at Lilmoth Dock, with steps going down from the dock to the water beside it.)
- Sheeh-Vos (MQ01 stage 10 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a208.someone.drinker` (Deep-In-His-Cups sits about 25 m south-south-east of here; he sees everything at the dock and remembers half.)
- Waits-For-Lanterns (MQ01 stage 10 at lilmoth): answers talk.secret; owns `fact.lilmoth.02a209.secret.trapdoor` (Near the graves north of Lilmoth's walls, about 145 m north-west of here, a trapdoor in the ground leads down...)


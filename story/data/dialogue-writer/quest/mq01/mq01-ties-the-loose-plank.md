# Dialogue brief: Ties-The-Loose-Plank (MQ01 No Name on the Work Roll)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; Saves the fish heads for the clutch-keeper. Outfit: saxhleel-tunic-long-green

## What the player cannot see
- Role: a gang family (npc)
- Factions: none
- Wants: his family's months paid
- Fears: the fire, now that the huts burn

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- Stance voice: chatter terse; contraction rate 0.1; addresses the player as "you"; favourite subject hist
- Quirk: Counts time in shifts and fish heads, never in days.
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
## Already said near you

These people stand in the same place during the same stretch of play, and the player hears them one after another. Each fact below is theirs to say: do not restate it. Say what only you would say, from your own work and stake; where the player needs the fact, point to its owner by name ("ask Wuleen-Sei about the months") in a few words. Do not reuse their wording.

- Nesh-Deeka (MQ03 stage 20 at lilmoth): answers I will serve the Reed., I will tell you what I saw at the camp., Not yet., Who are you?; owns `fact.mq03.no-claim` (The roll burnt in the camp's fire: nobody can show what I owe, or that I was ever on it.); `fact.mq03.reed-named` (Nesh-Deeka is of the Veiled Reed, the state's quiet service, which shows no face and wants a hand it can deny.); `fact.mq03.reed-offer` (Nesh-Deeka offers the Reed's protection, a door in Lilmoth and a stipend, on condition I serve the Reed.); `fact.mq03.sap-cell` (The Reed has word of a cell that cuts a Hist's roots and draws its sap into jars; the camp is the first work...); `fact.mq03.satchel-hers` (The courier's satchel was Nesh-Deeka's to see carried, and she says no more of it.); `fact.mq03.witness-wanted` (Nesh-Deeka wants the survivor's account of the cell's work, and then the Reed's people see the survivor home.)
- Salts-The-Catch (MQ03 stage 20 at lilmoth): answers Who are you?
- Reed-Stranger (MQ03 stage 20 at lilmoth): answers Who are you?
- Uleesh (MQ03 stage 20 at lilmoth): answers talk.secret; owns `fact.lilmoth.01512d.secret.salty` (A giant crab called Old Salty lives in the shallows about 70 m south-south-west of here.)
- Flaa Heet (MQ03 stage 20 at lilmoth): answers talk.lore, talk.someone; owns `fact.lilmoth.02a1e7.someone.tseeta` (Tseeta sells from her stall about 10 m north of here, and Okeeh-Jas from hers about 5 m south-south-west.); `fact.lilmoth.lore.council` (Lilmoth has no single ruler; a council of powerful merchants governs it and pays guards to patrol the streets.); `fact.lilmoth.lore.elders` (In Lilmoth people take their quarrels to their elders, retired Shadowscales among them, not to a court.)
- Peeks-Under-Boats (MQ03 stage 20 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a1e9.someone.headman` (Flaa Heet, the headman, stands by the cooking spit about 20 m south of here.); `fact.lilmoth.02a1e9.someone.hums` (Hums-To-The-Rain is usually about 20 m south-south-west of here, on the west side of the village.)
- Tseeta (MQ03 stage 20 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a1ed.someone.rival` (Okeeh-Jas keeps the other stall about 20 m south of here.)
- Hums-To-The-Rain (MQ03 stage 20 at lilmoth): answers talk.lore; owns `fact.lilmoth.lore.washed-out` (An Argonian kept long from their own Hist fades: colour thins and markings go soft, and they come back when...)
- Okeeh-Jas (MQ03 stage 20 at lilmoth): answers talk.lore, talk.rumours; owns `fact.lilmoth.02a1f2.rumours.drinker` (A drinker called Deep-In-His-Cups sits out on the shore track about 150 m north-east of here, and he talks to...); `fact.lilmoth.lore.owing-sold` (An owing can be sold on: a holder owed months can sell them to someone who needs hands, and the worker goes...)
- Haxal-Tei (MQ03 stage 20 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a204.someone.band` (His band camp here: Heem-Tsal the fire mage about 10 m west-south-west and Keeps-Both-Edges about 5 m west of...)
- Heem-Tsal (MQ03 stage 20 at lilmoth): answers talk.lore, talk.someone; owns `fact.lilmoth.02a205.someone.books` (A bookseller, Looks-At-Books, keeps her shelf at Hereguard Plantation, about 360 m west of here.); `fact.lilmoth.lore.council.ask-02a205` (Ask Flaa Heet about it: Lilmoth has no single ruler; a council of powerful merchants governs it and pays...)
- Keeps-Both-Edges (MQ03 stage 20 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a206.someone.thieves` (Two Argonians loiter by the leeks to the north, Sheeh-Vos about 45 m north-north-east and Waits-For-Lanterns...)
- Deep-In-His-Cups (MQ03 stage 20 at lilmoth): answers talk.lore, talk.rumours; owns `fact.lilmoth.02a207.rumours.dead-dunmer` (Three dead Dunmer lie at the east end of Lilmoth Dock, about 70 m north-north-east of here; nobody has buried...); `fact.lilmoth.dock.big-ship` (A big ship lies moored at Lilmoth Dock, with steps going down from the dock to the water beside it.)
- Sheeh-Vos (MQ03 stage 20 at lilmoth): answers talk.someone; owns `fact.lilmoth.02a208.someone.drinker` (Deep-In-His-Cups sits about 25 m south-south-east of here; he sees everything at the dock and remembers half.)
- Waits-For-Lanterns (MQ03 stage 20 at lilmoth): answers talk.secret; owns `fact.lilmoth.02a209.secret.trapdoor` (Near the graves north of Lilmoth's walls, about 145 m north-west of here, a trapdoor in the ground leads down...)


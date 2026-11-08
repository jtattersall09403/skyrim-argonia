# Dialogue brief: Nesh-Deeka (MQ03 A Dead Prisoner's Use)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Veiled Reed field handler at Alten Corimont; the recruit's handler, removed at the midpoint. Full brief in docs/quests/36-cast-roster.md. Outfit: saxhleel-tunic-wrap-purple+marsh-native-sandals

## What the player cannot see
- Role: Veiled Reed field handler for the freeholds (npc)
- Factions: none
- Wants: the satchel traced and the cell's method learned without the Reed named (culture.faction.veiled-reed); a hand she can deny, and the survivor's account of the cell's work
- Fears: that the cell will do the same at a tree with a village round it

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Salts-The-Catch: the fish-trader who keeps the Reed's house
- Ties-The-Loose-Plank: a gang family
- Never-Writes-Twice: Reed officer who files the honest report
- Cuts-the-Old-Knot: Leader of the Unbound Root

## Things lines may name (and only these)
- `thing.mq03.camp`: place; the camp at -1,0 on Hereguard Plantation's paddy edge; {'all': 'aftermath'}
- `thing.mq03.jar-marks`: dressing; the shed at the camp; {'all': 'aftermath'}
- `thing.mq03.sap-phial`: item; the shed at the camp; {'after-10': 'carried', 'at-10': 'on the shed floor', 'before-10': 'absent (the jar-marks parent off)'}
- `thing.mq03.courier-token`: item; the deep water under the plank boards at the camp's fire; {'after-10': 'carried if taken from the trap, else in the trap', 'at-10': 'in the locked fish-trap; the picks on the boards above', 'before-10': 'absent (the jar-marks parent off)'}
- `thing.mq03.reed`: actors; the camp's shore; {'after-20': 'gone', 'before-20': 'at the shore'}
- `thing.mq03.house`: place; Lilmoth; {'all': 'present'}
- `thing.mq03.hurt`: actors; the house; {'after-90': 'gone', 'at-20-to-40': 'on a mat', 'before-20': 'on the shore'}
- `thing.mq03.dream`: dressing; the barge hold, 0F9178:Black Marsh.esm; {'at-40': 'on', 'before-40': 'off'}

## Topics
### the attack (`topic.mq03-the-attack`; stages [20]; essential: no refusal band)
- Intent: hears what the player saw at the camp; asks twice about jars, and takes the phial to look at, if the player has one; the roll is ash; telling it sets its quest global (E-global)
- May state:
  - `fact.mq03.sap-cell`: The Reed has word of a cell that cuts a Hist's roots and draws its sap into jars; the camp is the first work of it the Reed has seen.
  - `fact.mq03.no-claim`: The roll burnt in the camp's fire: nobody can show what I owe, or that I was ever on it.
  - `fact.mq03.satchel-hers`: The courier's satchel was Nesh-Deeka's to see carried, and she says no more of it.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: persuade (Ties-The-Loose-Plank), inside someone's house or a guarded store
- Directions to give: The house has no mark; the back room is past the front room's table, behind the screen, the mats beside it. The street door opens from inside; the camp is the shore path north and west of the dock.
- Nesh-Deeka's knowledge at stage 20:
  - `fact.mq03.barge-gone`: knows
  - `fact.mq03.courier-token`: suspects
  - `fact.mq03.house-reed`: knows
  - `fact.mq03.no-claim`: knows
  - `fact.mq03.reed-named`: knows
  - `fact.mq03.reed-offer`: knows
  - `fact.mq03.sap-cell`: knows
  - `fact.mq03.sap-fresh`: suspects
  - `fact.mq03.satchel-hers`: knows
  - `fact.mq03.witness-wanted`: knows
  - `fact.mq03.clean-cut`: knows
  - `fact.mq03.jar-rings`: knows
- The player already knows at stage 20 (anything else is explained when first named):
  - `fact.mq03.clean-cut`: The cutting's roots were cut clean at the ring, one stroke each, by hands that knew where.
  - `fact.mq03.jar-rings`: Ring-marks of jars stand in the sap spilled on the shed floor: the cutters came with jars and filled them there.
  - `fact.mq03.sap-fresh`: The spilled sap is fresh, drawn at dusk, and the rings are many: the cell means to keep what it draws, so it is a long work and not a raid.
  - `fact.mq03.courier-token`: The courier's brass tag on its strap fell through the burnt plank boards at the camp's fire into the families' sunk fish-trap below: he was the state's man.

### the Reed (`topic.mq03-the-offer`; stages [20]; essential: no refusal band)
- Intent: whom she serves; nobody can claim the player; the Reed's protection, the door and the stipend, on condition
- May state:
  - `fact.mq03.reed-named`: Nesh-Deeka is of the Veiled Reed, the state's quiet service, which shows no face and wants a hand it can deny.
  - `fact.mq03.reed-offer`: Nesh-Deeka offers the Reed's protection, a door in Lilmoth and a stipend, on condition I serve the Reed.
  - `fact.mq03.no-claim`: The roll burnt in the camp's fire: nobody can show what I owe, or that I was ever on it.
  - `fact.mq03.witness-wanted`: Nesh-Deeka wants the survivor's account of the cell's work, and then the Reed's people see the survivor home.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: persuade (Ties-The-Loose-Plank), inside someone's house or a guarded store
- Directions to give: The house has no mark; the back room is past the front room's table, behind the screen, the mats beside it. The street door opens from inside; the camp is the shore path north and west of the dock.
- Nesh-Deeka's knowledge at stage 20:
  - `fact.mq03.barge-gone`: knows
  - `fact.mq03.courier-token`: suspects
  - `fact.mq03.house-reed`: knows
  - `fact.mq03.no-claim`: knows
  - `fact.mq03.reed-named`: knows
  - `fact.mq03.reed-offer`: knows
  - `fact.mq03.sap-cell`: knows
  - `fact.mq03.sap-fresh`: suspects
  - `fact.mq03.satchel-hers`: knows
  - `fact.mq03.witness-wanted`: knows
  - `fact.mq03.clean-cut`: knows
  - `fact.mq03.jar-rings`: knows
- The player already knows at stage 20 (anything else is explained when first named):
  - `fact.mq03.clean-cut`: The cutting's roots were cut clean at the ring, one stroke each, by hands that knew where.
  - `fact.mq03.jar-rings`: Ring-marks of jars stand in the sap spilled on the shed floor: the cutters came with jars and filled them there.
  - `fact.mq03.sap-fresh`: The spilled sap is fresh, drawn at dusk, and the rings are many: the cell means to keep what it draws, so it is a long work and not a raid.
  - `fact.mq03.courier-token`: The courier's brass tag on its strap fell through the burnt plank boards at the camp's fire into the families' sunk fish-trap below: he was the state's man.

### I will serve (`topic.mq03-take-oath`; stages [20]; not essential)
- Intent: the player takes the Reed's oath; offered only once the attack and the night are told (the two globals those topics set, C-global); the answer sets 40
- May state:
  - `fact.mq03.reed-offer`: Nesh-Deeka offers the Reed's protection, a door in Lilmoth and a stipend, on condition I serve the Reed.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: persuade (Ties-The-Loose-Plank), inside someone's house or a guarded store
- Directions to give: The house has no mark; the back room is past the front room's table, behind the screen, the mats beside it. The street door opens from inside; the camp is the shore path north and west of the dock.
- Nesh-Deeka's knowledge at stage 20:
  - `fact.mq03.barge-gone`: knows
  - `fact.mq03.courier-token`: suspects
  - `fact.mq03.house-reed`: knows
  - `fact.mq03.no-claim`: knows
  - `fact.mq03.reed-named`: knows
  - `fact.mq03.reed-offer`: knows
  - `fact.mq03.sap-cell`: knows
  - `fact.mq03.sap-fresh`: suspects
  - `fact.mq03.satchel-hers`: knows
  - `fact.mq03.witness-wanted`: knows
  - `fact.mq03.clean-cut`: knows
  - `fact.mq03.jar-rings`: knows
- The player already knows at stage 20 (anything else is explained when first named):
  - `fact.mq03.clean-cut`: The cutting's roots were cut clean at the ring, one stroke each, by hands that knew where.
  - `fact.mq03.jar-rings`: Ring-marks of jars stand in the sap spilled on the shed floor: the cutters came with jars and filled them there.
  - `fact.mq03.sap-fresh`: The spilled sap is fresh, drawn at dusk, and the rings are many: the cell means to keep what it draws, so it is a long work and not a raid.
  - `fact.mq03.courier-token`: The courier's brass tag on its strap fell through the burnt plank boards at the camp's fire into the families' sunk fish-trap below: he was the state's man.

### not yet (`topic.mq03-refuse-oath`; stages [20]; not essential)
- Intent: the player refuses; she says the Reed will send for them for hire; offered only once the attack and the night are told (the two globals those topics set, C-global); the answer sets 40
- May state:
  - `fact.mq03.reed-offer`: Nesh-Deeka offers the Reed's protection, a door in Lilmoth and a stipend, on condition I serve the Reed.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: persuade (Ties-The-Loose-Plank), inside someone's house or a guarded store
- Directions to give: The house has no mark; the back room is past the front room's table, behind the screen, the mats beside it. The street door opens from inside; the camp is the shore path north and west of the dock.
- Nesh-Deeka's knowledge at stage 20:
  - `fact.mq03.barge-gone`: knows
  - `fact.mq03.courier-token`: suspects
  - `fact.mq03.house-reed`: knows
  - `fact.mq03.no-claim`: knows
  - `fact.mq03.reed-named`: knows
  - `fact.mq03.reed-offer`: knows
  - `fact.mq03.sap-cell`: knows
  - `fact.mq03.sap-fresh`: suspects
  - `fact.mq03.satchel-hers`: knows
  - `fact.mq03.witness-wanted`: knows
  - `fact.mq03.clean-cut`: knows
  - `fact.mq03.jar-rings`: knows
- The player already knows at stage 20 (anything else is explained when first named):
  - `fact.mq03.clean-cut`: The cutting's roots were cut clean at the ring, one stroke each, by hands that knew where.
  - `fact.mq03.jar-rings`: Ring-marks of jars stand in the sap spilled on the shed floor: the cutters came with jars and filled them there.
  - `fact.mq03.sap-fresh`: The spilled sap is fresh, drawn at dusk, and the rings are many: the cell means to keep what it draws, so it is a long work and not a raid.
  - `fact.mq03.courier-token`: The courier's brass tag on its strap fell through the burnt plank boards at the camp's fire into the families' sunk fish-trap below: he was the state's man.


# Dialogue brief: Ties-The-Loose-Plank (MQ03 A Dead Prisoner's Use)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; Saves the fish heads for the clutch-keeper. Outfit: saxhleel-tunic-long-green

## What the player cannot see
- Role: a gang family (npc)
- Factions: none
- Wants: home
- Fears: the house, and what it keeps

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
- Nesh-Deeka: Veiled Reed field handler for the freeholds
- Salts-The-Catch: the fish-trader who keeps the Reed's house
- Never-Writes-Twice: Reed officer who files the honest report
- Cuts-the-Old-Knot: Leader of the Unbound Root

## Things lines may name (and only these)
- `thing.mq03.camp`: place; the camp where Lilmoth's dock meets the land; {'all': 'aftermath'}
- `thing.mq03.jar-marks`: dressing; the shed at the camp; {'all': 'aftermath'}
- `thing.mq03.sap-phial`: item; the shed at the camp; {'after-10': 'carried', 'at-10': 'on the shed floor', 'before-10': 'absent (the jar-marks parent off)'}
- `thing.mq03.courier-token`: item; the deep water under the plank boards at the camp's fire; {'after-10': 'carried if taken from the trap, else in the trap', 'at-10': 'in the locked fish-trap; the picks on the boards above', 'before-10': 'absent (the jar-marks parent off)'}
- `thing.mq03.reed`: actors; the camp's shore; {'after-20': 'gone', 'before-20': 'at the shore'}
- `thing.mq03.house`: place; Lilmoth; {'all': 'present'}
- `thing.mq03.hurt`: actors; the house; {'after-90': 'gone', 'at-20-to-40': 'on a mat', 'before-20': 'on the shore'}
- `thing.mq03.dream`: dressing; the barge hold, 0F9178:Black Marsh.esm; {'at-40': 'on', 'before-40': 'off'}

## Topics
### the night (`topic.mq03-the-night`; stages [20]; not essential)
- Intent: the woman with the cord and the cutters at the roots, seen from the shore; he tells it when shown the courier's tag, or talked round; telling it sets its quest global (E-global)
- May state:
  - `fact.mq03.cord-woman`: The woman with the knotted cord at her wrist led the cell; she took the courier's satchel and left the cutting to her cutters.
  - `fact.mq03.clean-cut`: The cutting's roots were cut clean at the ring, one stroke each, by hands that knew where.
  - `fact.mq03.barge-gone`: Wuleen-Sei marched the unhurt back to the barge at Lilmoth's dock; hurt hands are no hire.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Speechcraft: persuade (Ties-The-Loose-Plank), inside someone's house or a guarded store
- Directions to give: The house has no mark; the back room is past the front room's table, the mats beside it. The street door opens from inside; the camp is where Lilmoth's dock meets the land.
- Ties-The-Loose-Plank's knowledge at stage 20:
  - `fact.mq03.barge-gone`: knows
  - `fact.mq03.clean-cut`: knows
  - `fact.mq03.cord-woman`: knows
- The player already knows at stage 20 (anything else is explained when first named):
  - `fact.mq03.clean-cut`: The cutting's roots were cut clean at the ring, one stroke each, by hands that knew where.
  - `fact.mq03.jar-rings`: Ring-marks of jars stand in the sap spilled on the shed floor: the cutters came with jars and filled them there.
  - `fact.mq03.sap-fresh`: The spilled sap is fresh, drawn at dusk, and the rings are many: the cell means to keep what it draws, so it is a long work and not a raid.
  - `fact.mq03.courier-token`: The courier's brass tag on its strap fell through the burnt plank boards at the camp's fire into the families' sunk fish-trap below: he was the state's man.


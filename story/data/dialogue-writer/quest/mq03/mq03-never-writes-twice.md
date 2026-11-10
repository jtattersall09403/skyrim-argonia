# Dialogue brief: Never-Writes-Twice (MQ03 A Dead Prisoner's Use)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; Holds the post: the Reed officer who files the honest report (Stormhold). Outfit: saxhleel-tunic-long-green

## What the player cannot see
- Role: Reed officer who files the honest report (npc)
- Factions: none
- Wants: an honest service: here she is one of the strangers at the camp's shore, sees the player and says no name
- Fears: a Reed face seen

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Nesh-Deeka: Veiled Reed field handler for the freeholds
- Salts-The-Catch: the fish-trader who keeps the Reed's house
- Ties-The-Loose-Plank: a gang family
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
### the boat (`topic.mq03-the-boat`; stages [10]; essential: no refusal band)
- Intent: they take the hurt, and the player is hurt; offered only once the player has tasted the sap (the activator's fragment sets a stage-done mark, C-stage) and holds the phial or the tag (GetItemCount on the INFO), and the boat goes; her greeting says a friend of the courier's sent them; she names no one
- May state:
  - `fact.mq03.satchel-hers`: The courier's satchel was Nesh-Deeka's to see carried, and she says no more of it.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - Alchemy: test-a-sample, open ground by day
  - Lockpicking: pick-a-lock, in a flooded ruin, root-cave or under water
- Directions to give: The shed stands beside the withdrawn cutting at the camp's far end. The burnt plank boards lie at the camp's fire over the deep water; the courier's strap and tag lie in the families' locked fish-trap on the bottom straight below them, one breath down; lockpicks lie loose on the boards beside the fire.
- Never-Writes-Twice's knowledge at stage 10:
  - `fact.mq03.satchel-hers`: knows
- The player already knows at stage 10 (anything else is explained when first named):


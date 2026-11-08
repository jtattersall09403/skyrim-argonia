# Dialogue brief: Okan-Tei (TG02 The Drowned Lockbox)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, male; TG02's second client (we.tg02.clients): claims the Neesak charm. Outfit: marsh-native-kilt+marsh-native-sandals

## What the player cannot see
- Role: a canal-front client of the fallen stilt house (npc)
- Factions: none
- Wants: the charm back without paying for it (invented)
- Fears: being known to have sold it
- Backstory: sold the merchant the charm when coin was short and wants it back for nothing
- Invented, for 2.4 to write back to the registry: backstory

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Bent-Spine: Night-Reed fence
- Neeta-Haj: a canal-front client of the fallen stilt house
- Dar-Zeel: a canal-front client of the fallen stilt house

## Things lines may name (and only these)
- `thing.tg02.house`: place; the deep water north of Pusbottom; {'all': 'present'}
- `thing.tg02.eels`: actors; the deep water north of Pusbottom; {'all': 'present'}
- `thing.tg02.clients`: actors; the bank north of Pusbottom; {'all': 'present'}
- `item.tg02.bone-figurine`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}
- `item.tg02.neesak-charm`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}
- `item.glass-bead-strand`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}

## Topics
### the lockbox (`topic.tg02-charm-claim`; stages [20]; not essential)
- Intent: the charm was only pledged, never sold, he says; he says it only on a Speech check of 30, or for 20 gold (takeGold 20, setFlag flag.tg02.okan-paid true)
- May state:
  - `fact.tg02.claim-charm`: Okan-Tei says the charm was only pledged and never sold.
- Hides (until the intent says otherwise):
  - `fact.tg02.charm-remounted`: The charm sits in a new silver mount the merchant put on it, as no one does to a thing only pledged.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: persuade (the three clients), in a crowd or a market
- Directions to give: Climb the trapdoor's ladder out of the Chapter; the fallen house lies in the deep water two squares north of Pusbottom by the trapdoor, and the three clients wait on its south bank.
- Okan-Tei's knowledge at stage 20:
  - `fact.tg02.box`: knows
  - `fact.tg02.charm-remounted`: hides: he sold it outright
  - `fact.tg02.claim-charm`: knows
- The player already knows at stage 20 (anything else is explained when first named):

### the pledges (`topic.tg02-hand-over`; stages [40]; not essential)
- Intent: shown only while the player holds all three things (C-item); the player gives Okan-Tei all three, and he pays 80 gold
- May state:
  - `fact.tg02.box`: A locked lockbox of pledged things lies on the floor of the deep water beside the fallen stilt house: a bone figurine, a Neesak charm and a strand of Kothringi Glass Beads.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - athletics: dive (the deep water north of Pusbottom), in a flooded ruin, root-cave or under water
  - sneak: sneak-past (ripper eels in a cistern), in a flooded ruin, root-cave or under water
  - Lockpicking: open-a-strongbox (the lockbox), in a flooded ruin, root-cave or under water
  - speechcraft: persuade (the three clients), in a crowd or a market
- Directions to give: The fallen house lies on its side on the floor of the deep water below the bank; the lockbox is in the open beside it. The three clients wait on the bank above.
- Okan-Tei's knowledge at stage 40:
  - `fact.tg02.box`: knows
  - `fact.tg02.charm-remounted`: knows
  - `fact.tg02.claim-charm`: knows
- The player already knows at stage 40 (anything else is explained when first named):
  - `fact.tg02.job`: Bent-Spine wants the lockbox from the fallen stilt house in the deep water north of Pusbottom, and leaves to me what becomes of what is in it.
  - `fact.tg02.box`: A locked lockbox of pledged things lies on the floor of the deep water beside the fallen stilt house: a bone figurine, a Neesak charm and a strand of Kothringi Glass Beads.
  - `fact.tg02.eels`: Ripper eels hunt the deep water north of Pusbottom.
  - `fact.tg02.claim-figurine`: Neeta-Haj says the bone figurine was carved for her clutch.
  - `fact.tg02.claim-charm`: Okan-Tei says the charm was only pledged and never sold.
  - `fact.tg02.claim-beads`: Dar-Zeel says the beads are old family work.

### your pledge (`topic.tg02-sell-back`; stages [40]; not essential)
- Intent: shown only while the player holds the charm (C-item); the player names the lie the new mount gives and, on a Speech check of 30, sells it to Okan-Tei for a fixed 50 gold (takeItem it, giveGold 50), a sale and not a price for silence
- May state:
  - `fact.tg02.charm-remounted`: The charm sits in a new silver mount the merchant put on it, as no one does to a thing only pledged.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - athletics: dive (the deep water north of Pusbottom), in a flooded ruin, root-cave or under water
  - sneak: sneak-past (ripper eels in a cistern), in a flooded ruin, root-cave or under water
  - Lockpicking: open-a-strongbox (the lockbox), in a flooded ruin, root-cave or under water
  - speechcraft: persuade (the three clients), in a crowd or a market
- Directions to give: The fallen house lies on its side on the floor of the deep water below the bank; the lockbox is in the open beside it. The three clients wait on the bank above.
- Okan-Tei's knowledge at stage 40:
  - `fact.tg02.box`: knows
  - `fact.tg02.charm-remounted`: knows
  - `fact.tg02.claim-charm`: knows
- The player already knows at stage 40 (anything else is explained when first named):
  - `fact.tg02.job`: Bent-Spine wants the lockbox from the fallen stilt house in the deep water north of Pusbottom, and leaves to me what becomes of what is in it.
  - `fact.tg02.box`: A locked lockbox of pledged things lies on the floor of the deep water beside the fallen stilt house: a bone figurine, a Neesak charm and a strand of Kothringi Glass Beads.
  - `fact.tg02.eels`: Ripper eels hunt the deep water north of Pusbottom.
  - `fact.tg02.claim-figurine`: Neeta-Haj says the bone figurine was carved for her clutch.
  - `fact.tg02.claim-charm`: Okan-Tei says the charm was only pledged and never sold.
  - `fact.tg02.claim-beads`: Dar-Zeel says the beads are old family work.


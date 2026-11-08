# Dialogue brief: Neeta-Haj (TG02 The Drowned Lockbox)

Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.

## What the player can see
- argonian, female; TG02's first client (we.tg02.clients): claims the carved figurine. Outfit: saxhleel-tunic-wrap-orange

## What the player cannot see
- Role: a canal-front client of the fallen stilt house (npc)
- Factions: none
- Wants: the figurine, for what it would fetch (invented)
- Fears: the figurine being seen for what it is
- Backstory: lives on the bank and knew the merchant by sight
- Invented, for 2.4 to write back to the registry: backstory

## Voice
- argonian: 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. (dialogue-write/voices.md)
- No stance row for this person: 2.4 composes one before lines are written.

## Others in the quest (the player may be sent to them)
- Bent-Spine: Night-Reed fence
- Okan-Tei: a canal-front client of the fallen stilt house
- Dar-Zeel: a canal-front client of the fallen stilt house

## Things lines may name (and only these)
- `thing.tg02.house`: place; the deep water north of Pusbottom; {'all': 'present'}
- `thing.tg02.eels`: actors; the deep water north of Pusbottom; {'all': 'present'}
- `thing.tg02.clients`: actors; the bank north of Pusbottom; {'all': 'present'}
- `item.tg02.bone-figurine`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}
- `item.tg02.neesak-charm`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}
- `item.glass-bead-strand`: item; the lockbox; {'after-40': "the player's", 'before-40': 'in the box'}

## Topics
### the lockbox (`topic.tg02-figurine-claim`; stages [20]; not essential)
- Intent: the bone figurine was carved for her clutch, she says
- May state:
  - `fact.tg02.claim-figurine`: Neeta-Haj says the bone figurine was carved for her clutch.
- Hides (until the intent says otherwise):
  - `fact.tg02.figurine-old`: The figurine is worn smooth by many years of handling, older than any clutch of Neeta-Haj's.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - speechcraft: persuade (the three clients), in a crowd or a market
- Directions to give: Climb the trapdoor's ladder out of the Chapter; the fallen house lies in the deep water just north of Pusbottom by the trapdoor, and the three clients wait on its south bank.
- Neeta-Haj's knowledge at stage 20:
  - `fact.tg02.box`: knows
  - `fact.tg02.claim-figurine`: knows
  - `fact.tg02.figurine-old`: hides: she wants it for its worth
- The player already knows at stage 20 (anything else is explained when first named):

### the pledges (`topic.tg02-hand-over`; stages [40]; not essential)
- Intent: shown only while the player holds all three things (C-item); the player gives Neeta-Haj all three, and she pays 80 gold
- May state:
  - `fact.tg02.box`: A locked lockbox of pledged things lies on the floor of the deep water beside the fallen stilt house: a bone figurine, a Neesak charm and a strand of Kothringi Glass Beads.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - athletics: dive (the deep water north of Pusbottom), in a flooded ruin, root-cave or under water
  - sneak: sneak-past (ripper eels in a cistern), in a flooded ruin, root-cave or under water
  - Lockpicking: open-a-strongbox (the lockbox), in a flooded ruin, root-cave or under water
  - speechcraft: persuade (the three clients), in a crowd or a market
- Directions to give: The fallen house lies on its side on the floor of the deep water below the bank; the lockbox is in the open beside it. The three clients wait on the bank above.
- Neeta-Haj's knowledge at stage 40:
  - `fact.tg02.box`: knows
  - `fact.tg02.claim-figurine`: knows
  - `fact.tg02.figurine-old`: knows
- The player already knows at stage 40 (anything else is explained when first named):
  - `fact.tg02.job`: Bent-Spine wants the lockbox from the fallen stilt house in the deep water north of Pusbottom, and leaves to me what becomes of what is in it.
  - `fact.tg02.box`: A locked lockbox of pledged things lies on the floor of the deep water beside the fallen stilt house: a bone figurine, a Neesak charm and a strand of Kothringi Glass Beads.
  - `fact.tg02.eels`: Ripper eels hunt the deep water north of Pusbottom.
  - `fact.tg02.claim-figurine`: Neeta-Haj says the bone figurine was carved for her clutch.
  - `fact.tg02.claim-charm`: Okan-Tei says the charm was only pledged and never sold.
  - `fact.tg02.claim-beads`: Dar-Zeel says the beads are old family work.

### your pledge (`topic.tg02-sell-back`; stages [40]; not essential)
- Intent: shown only while the player holds the figurine (C-item); the player names the lie the worn figurine gives and, on a Speech check of 30, sells it to Neeta-Haj for a fixed 50 gold (takeItem it, giveGold 50), a sale and not a price for silence
- May state:
  - `fact.tg02.figurine-old`: The figurine is worn smooth by many years of handling, older than any clutch of Neeta-Haj's.
- What the player does at these stages (set it up: who, where, what danger, what they need):
  - athletics: dive (the deep water north of Pusbottom), in a flooded ruin, root-cave or under water
  - sneak: sneak-past (ripper eels in a cistern), in a flooded ruin, root-cave or under water
  - Lockpicking: open-a-strongbox (the lockbox), in a flooded ruin, root-cave or under water
  - speechcraft: persuade (the three clients), in a crowd or a market
- Directions to give: The fallen house lies on its side on the floor of the deep water below the bank; the lockbox is in the open beside it. The three clients wait on the bank above.
- Neeta-Haj's knowledge at stage 40:
  - `fact.tg02.box`: knows
  - `fact.tg02.claim-figurine`: knows
  - `fact.tg02.figurine-old`: knows
- The player already knows at stage 40 (anything else is explained when first named):
  - `fact.tg02.job`: Bent-Spine wants the lockbox from the fallen stilt house in the deep water north of Pusbottom, and leaves to me what becomes of what is in it.
  - `fact.tg02.box`: A locked lockbox of pledged things lies on the floor of the deep water beside the fallen stilt house: a bone figurine, a Neesak charm and a strand of Kothringi Glass Beads.
  - `fact.tg02.eels`: Ripper eels hunt the deep water north of Pusbottom.
  - `fact.tg02.claim-figurine`: Neeta-Haj says the bone figurine was carved for her clutch.
  - `fact.tg02.claim-charm`: Okan-Tei says the charm was only pledged and never sold.
  - `fact.tg02.claim-beads`: Dar-Zeel says the beads are old family work.


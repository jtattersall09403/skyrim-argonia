# Outcome tables: the main quest's endings and the Chainbreakers' (the worked example)

The owner's ruling of 2026-11-13 (owner-bar, "The bar"): each choice and ending says what it gives and costs in play.
These are proposals for the writers' second round of [main](../lines/main.md) and
[chainbreakers](../lines/chainbreakers.md), written by the recipe in
`.claude/skills/quest-write/principles/choices.md`; every row is built by results the quest form holds
([outcome-kinds](../../../../docs/research/skyrim/outcome-kinds.md)). The stories are not changed here.

Conventions. A spell, power or perk is a load-order record taught under our name (`teach_spell`, `add_perk`): its
editor id is given, its form key is found with `ArgoniaPlugin find`; none is Nordic (decision 0006). A unique thing
is a `template_item` on the named load-order item, with its fixed enchantment and our name. "A second placement"
is a person placed off and switched on by the ending while the player is in the trench (the away rule). A stored
number is written only with what reads it. Numbers are fixed (decision 0035). Factions named for `make_enemy` are
the load-order factions the place's people stand in (place-people names them); where the people are ours, the
writer asks for them to be placed in such a faction, or uses `speaker_hostile` and second placements instead.

## The main quest: CUT, CLAIM, MEND

What each already leaves in the story (who greets how, Helstrom's spring, the Egg) stays; the rows below add what the
player can use. The three gains are of three kinds: CUT a lasting ability and a cult's services; CLAIM a daily power,
the Wardens' stores and a unique thing; MEND the Hist's knowledge, a craft and peace with everyone who stays.

### CUT (the Egg poured into the basin)

| What the player gains in play | What the player loses or can no longer get | Who pays, and where the player sees it | Form results |
|---|---|---|---|
| **Rootless**, a lasting ability (copy of `doomLordAbility`: armour and resist magic): nothing passes between trees, and nothing reaches the player through one | the **pool's blessing** (Jal-Veesa's breath power from MQ12) is gone: the trees no longer answer | Asheem-Lei at Jal-Veesa's pool, who used to hear Helstrom in it | `teach_spell` doomLordAbility "Rootless"; `forget_spell` the pool's blessing |
| the **Unbound Root at Seafalls** treat the player as theirs: their quartermaster's chest is the player's, their healer and their trader open | the Reed's officer Never-Writes-Twice will not deal again: the Reed's stores and trainer close | the Wardens' last officer; the Reed's house in Helstrom | `make_peace` the cult's faction; `give_ownership` the cult's chest at Seafalls; their trader's second placement `switch_on`; `set_number main.ending 1` read by the Reed's lines (closed) |
| | the Egg is spent: no seed for the dead tree, so Heem-Jasa at Vel-Sapha has nothing to give | Heem-Jasa | (nothing given: the CLAIM row's unique thing is not here) |

### CLAIM (the Eye set in the socket)

| What the player gains in play | What the player loses or can no longer get | Who pays, and where the player sees it | Form results |
|---|---|---|---|
| **The Eye's Shutting**, a power once a day (copy of `TGNightingaleSubterfuge`: those near turn on each other): one hand shuts a mad tree out | Helstrom's people are **hostile on sight** ("Helstrom will not forgive it"): its traders, beds and spring are shut | the naheesh at Helstrom's spring | `teach_spell` TGNightingaleSubterfuge "The Eye's Shutting"; `make_enemy` Helstrom's faction |
| the **Wardens' backing**: the Reed's rank, its stores chest at the household, its trainer to the top of its skill | Asheem-Lei's lessons at the pool end: she asks who gave the player leave | Asheem-Lei | `set_rank` the Reed; `give_ownership` the Reed's stores chest; `set_number main.ending 2` read by the trainer's and Asheem-Lei's lines |
| **the dead tree's seed** carried home: Heem-Jasa gives the stand's thanks, a unique amulet (template: a plain load-order amulet with a fixed restoration enchantment, no god's or Nord's mark), and the Vel-Sapha sap-seller's best stock | the cult at Seafalls is gone: their healer and trader with it | the listeners at Seafalls (switched off) | `give_item` the amulet (`template_item`); the sap-seller's second placement `switch_on`; the cult's people `switch_off` |

### MEND (the first consent read into the root)

| What the player gains in play | What the player loses or can no longer get | Who pays, and where the player sees it | Form results |
|---|---|---|---|
| **The Root's counsel**: the effects of the marsh's Hist-touched ingredients are known, and the making of a sap tonic is open at any cook pot | the **pool's blessing** goes with Jal-Veesa's tree, which left the joining | Asheem-Lei, who did not know her tree wanted to leave | `learn_ingredient` for each named ingredient (Hist sap and the sap-road's herbs); `open_recipe` sap tonic at the cook pot; `forget_spell` the pool's blessing |
| **Every tree's people at peace with the player**: Helstrom's and Jal-Veesa's traders, beds and Root Talk stay open; a raise in Alchemy and Restoration from the tree-minders | the cult lives and keeps cutting: the listeners at Seafalls are **hostile** and their ground is closed | the cult at Seafalls; whoever their next cut hurts | `raise_skill` Alchemy 5, Restoration 5; `make_enemy` the cult's faction |
| | the Egg goes to the root: no seed for Vel-Sapha, no unique thing | Heem-Jasa ("I am told it was done rightly") | (nothing given) |

**Recommendation.** Take all three as written: a lasting defence and a cult's services (CUT), a daily power, a base
and a unique thing at the price of a town (CLAIM), knowledge and craft and peace at the price of a blessing and an
enemy (MEND). A player choosing only for the reward has a real decision: the strongest single gain (CLAIM's power and
stores) costs the most in places shut. The trade is told before the choice by the Collector at the door ("the Eye
makes you their keeper, and Helstrom will never open to you again"), and found after at the pool, the spring,
Vel-Sapha and Seafalls, as the story already places it.

## The Chainbreakers

The line's rewards today are the same for every ending of each quest (gold, an enchanted ring or gloves, a rank).
The rows below keep the rank on every completed ending, so the line never strands, and make the rest differ in kind.

### The line's ending (BC06: whom the gate key goes to)

| Outcome | What the player gains in play | What the player loses or can no longer get | Who pays, and where seen | Form results |
|---|---|---|---|---|
| to **Xeekh** | the heirs' hierarchy owes the player: a bed and a chest in the Rose's upper hall, and the heirs' fence takes stolen goods | Never-Sold's house closes: her trainer (Lockpicking) and her lines | Never-Sold, in her house | `give_ownership` the bed and the chest; the fence's second placement `switch_on`; `set_number bc06.key 1` read by Never-Sold's lines |
| to **Never-Sold** | the Chainbreakers' top rank and their supply chest in her house; her trainer teaches to the top | the heirs are hostile on sight in the Rose | Xeekh's heirs, in the Rose | `set_rank` the Chainbreakers 5; `give_ownership` the supply chest; `make_enemy` the heirs' faction |
| to **Ossu** | **Grave-Song**, a spell that turns the restless dead (copy of a load-order Turn Undead spell), and the bones' grave is a place on the map where the restless dead no longer rise | the dead levels are sealed: the Rose's lower doors lock for good, and what lies there is lost | the Rose's bone-pickers, who lose their trade | `teach_spell` the Turn Undead spell "Grave-Song"; `lock_door` the gate; `mark_on_map` the grave; `switch_off` the levels' restless dead |
| to the **Nisswo** | every reckoning witnessed: the player's own bounty at the Rose is cleared, and the Nisswo teaches Speech and opens a witness's road (a door at the post) | no faction backs the player at the Rose: no bed, no chest | the heirs and the Chainbreakers both, coolly | `set_bounty` the Rose's crime faction 0; `raise_skill` Speech 5; `unlock_door` the witness's door |
| "Will you tell them?" **yes** | Never-Sold's desk: the leader's chest and the house itself as the player's | the Chainbreakers lose their founder twice; her lines close | Never-Sold, gone from the house | `own_room` her house; `give_ownership` the leader's chest; `switch_off` Never-Sold |
| **no** | Never-Sold stays: her trainer and her rank's gifts go on | the desk is never the player's | the faction, which never learns | (nothing more) |

### BC01, Four Months for a Boat

| Outcome | Gains in play | Losses | Who pays, and where | Form results |
|---|---|---|---|---|
| **Lifted** | the ring enchanted for Lockpicking, the first rank; Rows-For-Another at the landing ferries the player across the channel when asked | the estate's store is barred to the player | Hulm-Tei, the keeper, at the estate store | `give_item` the ring; `set_rank` 0; her ferry line gated on `bc01.way = 1`; `lock_door` the store |
| **Struck** | the first rank and the keeper's gratitude: Hulm-Tei, paid in full, gives the store's key and what the store holds is the player's | the ring: the dozen strangers' leaves are paid from it | a dozen unseen hands; Never-Sold, coldly | `set_rank` 0; `give_ownership` the store chest; `give_item` its key |
| **Cut loose** | the channel cleared: the boat route opens a way north (a door unlocked); the fetcher's kit, if he died | half the gold, and Rows-For-Another's way home | Rows-For-Another, gone from the bank | `unlock_door` the channel's gate; `set_rank` 0; `give_gold` 50 |

### BC02, One Out of the Smoke

| Outcome | Gains in play | Losses | Who pays, and where | Form results |
|---|---|---|---|---|
| **Walks-Far** freed | the gloves enchanted for Pickpocket; Walks-Far, free, teaches what he knows (a skill book of Speech, given) | the Rose's heirs will not treat with the player: their gate-warden's line closes | the two left behind, in the stone house | `give_item` the gloves and the book; `set_number bc02.freed 1` read by the warden's lines |
| **Mends-Nets** freed | the gloves; Mends-Nets, a killer, gives the player his hidden blade (a unique dagger, template a steel dagger with a fixed absorb-stamina enchantment) | Never-Sold's next gift is withheld ("the people who loose killers"), and the post's healer will not tend the player | Never-Sold; the post's healer | `give_item` the dagger (`template_item`); `set_number bc02.freed 2` read by Never-Sold's and the healer's lines |
| **Seven-Floods** freed | the gloves; her daughter's place is shown on the map, and passing the word there earns a blessing (a lasting resist disease, copy of `RaceArgonianResistDisease`) | Walks-Far's three seasons, and his clutch-brother's | Walks-Far, left in the stone house | `mark_on_map` the daughter's place; the blessing taught by that later line's stage (`teach_spell`) |

### BC03, The Broker's Mercy

| Outcome | Gains in play | Losses | Who pays, and where | Form results |
|---|---|---|---|---|
| **Broken off** | the ring enchanted for Sneak, the next rank, 150 gold from the crew | Ussa-Rekh's dock will not hire through the player again: his berth-master's passage closes | eleven at Thorn, unseen; the dock | `give_item` the ring; `set_rank` 1; `give_gold` 150; `set_number bc03.way 1` read by the berth-master's lines |
| **Released** | the same rank and ring; Ussa-Rekh's pride: his berth-master carries the player by boat to Thorn and back (a door opened) | the crew's gold | Never-Sold ("that is the worst of him") | `give_item` the ring; `set_rank` 1; `unlock_door` the boat's way |
| **The season worked** | the rank, and the Broker's shelf: his chest is the player's | no gift from Never-Sold, and Heavy-Rope's crew greet coldly and sell nothing | Heavy-Rope's crew, at the dock | `set_rank` 1; `give_ownership` the Broker's chest; `set_number bc03.way 3` read by the crew's lines |

**Recommendation.** Every quest keeps the rank on each completed ending (the line never strands) and changes what
else it gives in kind: a ring against a key and a store against a road (BC01); a book against a blade against a
blessing found later (BC02); a ring and gold against a boat route against a chest (BC03). The line's ending gives
four different kinds of home in the world: the heirs' bed and fence, the faction's top rank and chest, an ability
and a grave, or a clean name and a road; and the desk is the one way to lead.

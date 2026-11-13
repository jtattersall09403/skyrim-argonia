# What a quest of ours can give: outcome kinds, measured

What a choice or an ending can change in play, measured from the repo and the load order on the build machine, not
assumed. The craft of using it is `.claude/skills/quest-write/principles/choices.md`; why it matters is
[choice-and-consequence](../writing/choice-and-consequence.md). Labels: [M] measured this pass (command below);
[R] read in the repo (file named); [V] read this pass at the URL; [S] search summary only; [K] prior knowledge.

## How it was measured

- `ArgoniaPlugin spells <plugins...>` (tools/ArgoniaPlugin/SpellStudy.cs): counts of spells by type and how they are
  taught, enchanted unique-looking items, perks, and every recipe's workbench and gating functions, over Skyrim.esm,
  Update, Dawnguard, HearthFires, Dragonborn, Magic.esp (Magic Expanded) and Black Marsh.esm, from
  `~/games/skyrimse/Data`. Counts and editor ids only; no game text is read (decision 0003).
- The quest form's results and the builder's operations: [quest-form](../../design/quest-form.md),
  `papyrus/ARG_Effects.psc`, `tools/ArgoniaPlugin/QuestForm.cs`. [R]
- Morrowind's mechanisms: Morrowind Scripting for Dummies, faction, reputation, disposition and crime chapters:
  https://raw.githubusercontent.com/sultan-of-rum/morrowind-scripting-for-dummies/master/MSFD9.tex [V];
  [morrowind-level-scripting](../morrowind-level-scripting.md) [R]. UESP and Fandom refused every request (403,
  402), so Morrowind's quest-by-quest examples stay [S] or [K].

## What there is to give [M]

| Stock | Count | Notes |
|---|---|---|
| spells a tome teaches | Skyrim 93, Dawnguard 8, Dragonborn 9, Magic Expanded 139 | Magic Expanded's are tome-taught: a quest can teach one directly, or give its tome |
| powers no tome teaches and no person carries | Skyrim 28 + 3 lesser, Dawnguard 1 + 12 lesser, Dragonborn 20 + 6 lesser | quest and stone gifts: the three Nightingale powers, the standing stones' (Serpent, Shadow, Ritual), the racial powers, Dragonborn's Black Book powers and its six standing stones |
| abilities no tome teaches and no person carries | 326 in all; Magic Expanded 7 | the standing-stone blessings (Lord, Lady, Steed, Atronach, Thief, Mage, Warrior, Lover, Tower, Apprentice), Argonian water breathing and disease resistance, ring and weapon blessings |
| enchanted armour and weapons with no template (uniques and set pieces) | Skyrim 130 + 95, Dawnguard 38, Dragonborn 102, Magic Expanded 16, Black Marsh 1 | a unique of ours is a `template_item` copy of one, with our name and its fixed enchantment |
| playable perks | Skyrim 349, Dawnguard 39, Dragonborn 53, Magic Expanded 1 | tree perks and a few gifts |
| recipes (constructible objects) | 1,385 | 38 gated on a quest's stage or completion (Dragonborn's Stalhrim forge 18; Skyrim's armour table 20), 64 on a global (the Skyforge 9, Dawnguard's forge 10), 43 on a spell known (Dragonborn's staff enchanter) |

Not Nordic is the filter (decision 0006): the Nightingale, racial, Daedric, Magic Expanded and standing-stone
effects pass under our names; a dragon word, a Skyforge piece or a Nord hero's relic does not.

## Every kind of outcome, and how our game builds it

"Result" means a word of the quest form, carried out by `ARG_Effects` as one engine call; "record" means the builder
writes a record with a condition and nothing runs. Morrowind's mechanism is from MSFD [V] unless marked.

| Kind | Morrowind | Skyrim, one call or one record | Ours |
|---|---|---|---|
| items, gold | `AddItem` | `AddItem` | `give_item`, `give_gold` (and `take_*`) |
| a unique named thing | a unique item record (Wraithguard [S]) | an item record with a fixed enchantment | a `template_item` with our name |
| a spell, power, lasting ability, blessing | `AddSpell` (the Corprus cure leaves disease immunity [K]; Azura's and shrine gifts [K]) | `AddSpell` of a spell record (type spell, power, lesser power or ability) | `teach_spell`, `forget_spell`, of our copy under our name |
| a perk | none | `AddPerk` | `add_perk`, `remove_perk`, of our copy under our name |
| a skill raised | `ModSkill` [K]; skill books | `Game.IncrementSkillBy`; a skill book (an item) | `raise_skill`; `give_item` of a skill book |
| an attribute, carry weight, health, a resistance | `ModStrength` and the like | `ModActorValue` needs the value's name; an ability spell with a fortify effect does it with a record (the Steed stone: carry weight) | `teach_spell` of such an ability |
| a recipe at a forge, cook pot, tanning rack or smelter | none | a constructible object whose condition is `GetStageDone` (38 vanilla, above) | `open_recipe`: our recipe record, open once the stage is done |
| an ingredient's effects known | none | SKSE `Ingredient.LearnAllEffects` (in the staged SKSE's `Scripts/Source/Ingredient.psc` [M]; `IncrementSkillBy`, `AddToMap` and `Cell.SetActorOwner` likewise) | `learn_ingredient` |
| a recipe note | a book | a book | `give_item` of an item with words |
| an enchantment learnt | the spellmaker and enchanter services | only by disenchanting; no call teaches one [K] | not given: give the enchanted thing |
| a word of power | none | `Game.TeachWord` | never: dragon shouts are Nordic (decision 0006) |
| a faction joined, a rank, its expulsion | `PCJoinFaction`, `PCRaiseRank`, `PCExpell` | `AddToFaction`, `SetFactionRank`, `RemoveFromFaction` | `join_faction`, `set_rank`, `leave_faction` |
| what a rank opens: a trainer, a seller's stock, a guide, a bed, a supply chest, the next job | services conditioned on rank, reputation and skills | dialogue conditioned on `GetFactionRank`; a bed or chest owned by the faction | lines gated on `rank_at_least`; a chest given (`give_ownership`) or a door unlocked at the rank's stage |
| faction reputation | `ModPCFacRep` | none | a stored number, read by the lines that open what it unlocks |
| disposition, prices | `ModDisposition` (0-100), which prices and persuasion read | relationship rank -4 to 4, which barter does not read | `change_regard`; a price is two lines with two fixed prices gated on it |
| a group hostile or friendly | `SetFight`, `ModFactionReaction` | `Faction.SetPlayerEnemy` | `make_enemy`, `make_peace` |
| a bounty cleared or set | `PayFine`, `SetPCCrimeLevel` | `Faction.SetCrimeGold` | `set_bounty` |
| a bed, a chest, a home | strongholds; a house given [K] | `SetActorOwner` on the reference or the cell | `give_ownership`; `own_room`; `unlock_door` |
| a stronghold built in stages | Tel Uvirith in three phases, each adding people [S] | placements switched on at a stage | `switch_on` per stage (one stage per phase) |
| a trader's wider stock | rank-gated vendors; stronghold traders [K] | a merchant chest resets to its base list, so an item added by script is lost at restock [K] | a second placement of the trader, switched on |
| a place on the map, travel | propylon indices, guild guides [K] | `ObjectReference.AddToMap` | `mark_on_map` |
| a title, how people greet the player | greetings conditioned on rank (Hortator, Nerevarine) | greeting lines conditioned on rank or a number | a greeting gated on the stored number or rank |
| a topic opened | `AddTopic` | a line conditioned on a stage | a line's window |
| who lives to trade or teach | a death | a death; a placement switched off | a death the player chooses; `switch_off` |
| a later quest easier or harder | journal indices read by later lines | a stage or global read by later lines | a stored number read by later lines |
| vampirism, lycanthropy and their cures | `PCVampire`, `BecomeWerewolf` and their quests [S] | the vanilla vampire and werewolf quests' own scripts | not given: they need watching (hunger, transformations) |
| a follower | `AiFollow` | a follower framework | never: nobody walks for a quest |
| spellmaking | the spellmaker service | none; mods add it (proposal in [choice-and-consequence](../writing/choice-and-consequence.md), "Spellmaking") | later, a plugin of ours |

Every "Ours" word is in the quest form now, through the compiler, the rules, `sketch`, the paper game, `ARG_Effects`,
the builder and the reader ([quest-form](../../design/quest-form.md)); `open_recipe` and `learn_ingredient` are the
two the builder writes as a record and an SKSE call.

## What Morrowind's ranks teach us

A rank was the reward because of what it opened: each rank of a guild opened trainers, spell sellers, guides, beds
and chests, and the next job, gated by skills, reputation and finished quests [V MSFD; S UESP]. Titles cost nothing:
one script set the faction and every line conditioned on it spoke differently [V MSFD]. So a standing, a rank or a
stored number is never an outcome by itself: it is written with what it opens.

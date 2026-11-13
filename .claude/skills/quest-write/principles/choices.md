# Choices and endings that matter in play

Read with `general.md` (which holds the source tags' key) for any quest or line with a choice or more than one
ending. A choice is finished only when each of its outcomes changes what the player can do, get or reach, and the
player knows the trade before choosing [OB bar; CC P1].

## What each outcome holds

1. **Each outcome gives something the player can use the next day and costs something they would have used.** Write
   both as things, from the table below: a power, a thing, a recipe, a trader's stock, a trainer, a bed or room, a
   door, a group's peace or hostility, the next job. What people say about it afterwards is how it is shown, never
   the outcome itself [CC P1; CC P7; OB bar].
2. **Standing is never an outcome by itself.** A stored number, a regard or a rank is written only with what it opens
   or shuts that the player can go and use: "rank 3 in the Reed: the quartermaster's chest is theirs and the trainer
   teaches to 50", never "standing with the Reed rises" [GK; CC P1; owner, 2026-11-13].
3. **Different in kind, not better and worse.** Give each outcome a different kind of gain (a power against a place
   against a thing against a service), so a player who chooses only for the reward still has to decide what kind of
   play they want [CC P2; CC WS Skyrim table].
4. **No strictly dominant pick, no outcome that only punishes.** Put the outcomes side by side; if one is better in
   every column, trade a column. Ask which a player who ignores the story would take: the answer must split [CC P3].
5. **The kind option costs something felt**: name what mercy gives up (a power, a trader, a purse the player would
   spend), and never pay it back until it costs nothing. No route spares every cost [CC P4].
6. **The cost falls on someone the player has met**, and shows where the player will pass it: a shop shut, a teacher
   gone, a door barred, a greeting turned cold [CC P5].
7. **Say the trade before; let the texture be found after.** Before the choice a person the player trusts says in
   plain words what each side gives and costs in kind ("take the Hist's mark and the Shellbacks will never trade with
   you"); who is pleased and who grumbles is found later. The trade is never hidden [CC P6; OB bar].
8. **Access over a purse.** A service, a place, a lasting power or a recipe comes before gold; gold alone is never an
   ending's whole gain [CC P8].
9. **Fixed and in proportion.** Every reward is a fixed number or a fixed thing (nothing scales with the player's
   level), sized to the work and to the strongest of its kind already in the stack; a power never trivialises the
   next quest [CC P9; OB shape; decision 0035].
10. **A unique thing is an existing model under our name.** We make no art: a reward worth remembering is a
    `template_item` on a load-order item whose model reads as what it is called, with that item's fixed enchantment,
    and a name of ours; a power is a load-order spell under our name (`teach_spell`) [GK; quest-form "New items"].
11. **A faction's ending reaches as far as its own people and places.** It opens or shuts its own traders, doors,
    beds, recipes and greetings, and may turn a named faction for or against the player; another line's door is
    reached only through a stored number that line's own lines read, never by moving its stages [OB shape; CC P11].
12. **Promise only what is built**: every sentence that says "this will change things" names the thing, and that
    thing is a row of the outcome table below [CC P12].
13. **End on what the player did**: the last beat uses the places, people and powers the choice touched [CC P13].

## The outcome table

Every choice and every ending carries this table in the quest record (`endings`) and in the line's story document.
A row whose gains or losses are only words, or only a standing, is not finished.

| Outcome | What the player gains in play | What the player loses or can no longer get | Who pays, and where the player sees it | The form results that build it |
|---|---|---|---|---|

## What an outcome can be, and what builds it

Items and gold head the list: they are already results, and they are the plainest reward. Each other kind is one
result word, or a line gated on a stored number, a rank or a stage that the outcome sets.

| Kind | Builds as |
|---|---|
| a thing, gold | `give_item`, `give_gold` (`take_*` for a cost) |
| a unique named thing | a `template_item` placed or given, with the template's fixed enchantment and our name |
| a spell, power or lasting ability (a standing-stone-like blessing) | `teach_spell` of a load-order spell under our name; `forget_spell` to take one |
| a perk | `add_perk`, `remove_perk` |
| a skill raised | `raise_skill` (1 to 10), or a skill book given |
| a crafting recipe at a forge, cook pot, tanning rack or smelter | `open_recipe`: our recipe opens when the stage is done |
| an ingredient's effects known | `learn_ingredient`; a recipe note is an item with words |
| a trader's wider stock, a trainer, a service | a second placement of the trader switched on (`switch_on`/`switch_off`), or their lines gated on the stored number or rank the outcome sets |
| a bed, a chest, a room as a home | `give_ownership` of the bed or chest; `own_room` for the whole room; `unlock_door` |
| a door or place opened or shut | `unlock_door`, `lock_door`; a person or thing switched on or off away from the player |
| a place shown on the map | `mark_on_map` |
| a bounty cleared or set | `set_bounty` |
| a group at peace or hostile | `make_peace`, `make_enemy` (a load-order faction) |
| a faction's rank and what it opens | `join_faction`, `set_rank`, `leave_faction`, each with the lines, doors and chests the rank opens |
| who is alive to trade or teach | a death the player chooses, or a placement switched off |
| what people call the player | a greeting gated on the stored number or rank (shows a gain, never is one) |
| a later quest easier or harder | a stored number its lines read (an extra way, a price, a person who helps) |

Not in the form: a follower (nobody walks for a quest), a timed effect, a spell the player designs (later, by a
plugin of ours: [CC SM]), a word of power (Nordic: decision 0006).

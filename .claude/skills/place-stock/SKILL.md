---
name: place-stock
description: Stock one place of the new world (a city, a village, a camp, a ruin, a wreck) with what is in it - each person's possessions, each container's contents, the loose things and the traders' lists - on the one fixed scale, every thing with its reason, every promise of the place record delivered. Use after the place is drafted (place-system) and place-people has given its people their identities, and again for the rows a recast person or a changed fact of the place touches.
---

# Stock a place

You decide what each thing is and why, from the tools' measurements. Everything you author goes into the place's stock source,
`newworld/sources/stock/places/<place_id>.json`. Who each person is comes from the skill `place-people`
(`newworld/sources/people/<place_id>.json`); you read it and never rewrite it here.
The contract (file shapes, tables, what the build and its check do) is `docs/design/place-studio.md`, section Stock.
Nothing is random and nothing is levelled (decision 0035). Set dressing (food, crockery, cheap clutter, furniture) stays as
the source has it; everything significant is authored here. Never write mod record content into a source: ids, counts
and reasons only. Where this step sits in the work on a place is in the skill `place-system`.

## Inputs

- The place's facts: `db.open("newworld")`. You need `place` (kind, status, importance, culture, siting),
  `place_danger` (its disposition, strength inside and reward band, each with its reason:
  `python3 -m tools.newworld.place_danger show <place>`),
  `place_note` (above all `economy`, `hooks`, `people`, `present`), `place_give` (its promises), `place_wealth` (band, ceiling: the highest tier the place holds, open tier: the tier of what lies unlocked, reason), `place_good`, `person` and `household` (its people), and the roads.
- The scale, `newworld/sources/stock/scale.json`: tiers and their materials, gold, locks and value limits; the
  wealth bands; security, effort, owner and provenance rules; budgets; traders' gold and list values; the split.
- The drafted place as a bundle, `out/places/bundles/draft.<place_id>` (`python3 -m tools.places draft-bundle
  <place_id>`), and its place files: rooms, containers, beds, who lives where.
- Vanilla's yields as a check: `docs/research/skyrim/stocking-yields.md`.
- The lore for every world call (decision 0032): `story/lore/` and the place's own notes.

## 1. Be sure of the facts first

1. Every person has an identity: `python3 -m tools.places identities check <place>` shows 0 problems. If it does
   not, the skill `place-people` comes first. A place without people (a ruin, a wreck) skips this.
2. Read `place_wealth` for the place (`python3 -m tools.newworld.wealth show <place>`) and its `place_danger`. If a
   band reads wrong for what the lore says the place is, say so to the owner with the reason. The owner overrules
   wealth with an `owner` block in `place_wealth.json` and danger in `newworld/sources/danger/owner.json`; you never
   edit a derived value by hand.
3. Fill the place's `goods` in its stock source from its economy note: what it makes, trades and needs, each with
   the words of the note that say so. Provenance is computed from these rows.

## 2. Run the split, and look at what it catches

`python3 -m tools.places stock classify <place> --json <scratch>/classify.json`

The split sorts from record data, never by eye. Read its list before anything is taken out. Note the source's
own best things (an enchanted blade on a guard, a unique lying loose): every one of them is taken out unless you
author it back with a reason.

## 3. Derive the measurable part

`python3 -m tools.places stock derive <place> --to <scratch>/<place>.derived.json`

It writes a first stock source: a store per household by the head's band and the household's size, bodies' few
things, each person's tool or weapon, the guard's gear, jewellery and carried gold by band, and each trader's gold and
list, all with reasons. It also lists what it leaves open. Treat it as a draft: read every row against the facts and
change what the facts say otherwise.

## 4. Materials: who holds what

Everything of gear is made of a material of ours, and the material decides where it may be held and how often
([items](../../../docs/design/items.md) explains the model; the facts are in `materials.json`, `item_material.json`,
`regions.json`, `kits.json` and `scale.json`). Work from the province down to the person:

1. **Province.** Each tier has its own Black Marsh materials for each slot (`scale.json` tiers `weapon`, `heavy`,
   `light`, `shield`). An item's tier is its power (`items.json` `stock_tier_id`), never its keyword. Wood, bone,
   flint, hide and leather are common. Bog iron, scale, shell and chitin are uncommon. Obsidian and bronze are rare.
   Imperial gear, bonemold and Shadowscale gear are situational. Relics, Ayleid elven, glass and ebony are ruin
   finds. Daedric and dragon gear enter only through the ledger. Dwarven, Orcish and decision 0006's list are never
   stocked.
2. **Region.** Read the region's profile (`region_profile`, `region_people`, `region_material`, `region_good`).
   Prefer its local materials and its signature goods, carry traded materials in more thinly and at a higher price,
   and hold nothing it marks absent. Give each region something a player would notice: Murkwood's fellrunner down and
   sap jars, the Valley of Storms' chitin and saltrice, a Skeith Isle pirate's mixed hoard.
3. **Place.** `python -m tools.places stock mix <place>` gives the expected mix and names the rule behind each share:
   the class target, then the bends for the region's peoples, the place's culture, its trade and its metal. Stock
   to within about 15 points of each share. A tribal or Naga camp holds organic gear only. A material whose reach the
   place does not meet (an Imperial piece where the record gives no reason, glass outside a ruin) has no place there.
4. **Household and person.** Each person takes their trade kit (`trade_kit`, matched by their trade or role) and
   their race's overlay. The kit says what they carry, what they wear, what their store keeps, the food in the house,
   and what they would never own. A household's store follows its head's kit. Where the facts call for something
   outside the kit (a dead husband's sword over the door), keep it with an `exception` on the row that gives the
   reason in words.

Worked examples:

- **An Argonian fisher in a village** (an eel-trapper at Teel-Fen Weir, W2). Kit `fisher`. She carries a T1 flint
  fishing knife (Saxhleel Fishing Knife) and a bone harpoon (New Armory Argonian Fishing Harpoon) and wears hide
  wraps. The hut's store holds dried fish, twine and traps (river-fish, reed-weaving), with saltrice and eggs as food.
  She owns no metal two-handed weapon, no heavy armour and nothing rare.
- **A Dunmer holdout's household** (a gang-master at Ashgate Landing, a stone-grey place that bonemold reaches).
  Kit `overseer` with the `dunmer-household` overlay. He carries a bonemold sword (Bonemold Weapon Pack) and wears
  chitin. The store holds saltrice and the work's stores. He keeps no Imperial issue without a reason.
- **An Imperial clerk at a levy post** (a toll-keeper at a Warden Marches fort, where Imperial gear reaches through
  the culture crimson-red). Kit `clerk` with the `imperial-household` overlay. He carries a Legion Pugio (HTBM, T1
  Imperial), wears plain clothes and no armour, and keeps the post's ledgers and Cyrodiilic goods. He owns no
  bonemold and no relic.

The derive puts the smithing ingredients on the traders' lists. A smith sells every recipe ingredient whose good
the place makes (five of each) or its region lists (three of each). A general trader sells the leather and wood
among those. Both sell leather strips (six). Keep these rows unless the facts say otherwise.

`python -m tools.places stock reach <place>` flags every row that breaks one of these rules, naming the rule
(`material reach`, `region`, `place class` or `kit <id>`) and the record text it read. Bring it to zero before
hand-over, by changing the row or by giving it an `exception`.

## 5. Author the stock source

Write `newworld/sources/stock/places/<place>.json` from the draft and the facts. For each kind of holder:

**People's possessions** follow from who they are: role, household, wealth band, fixed level and backstory.
- The baseline is the archetype of role × band × culture: the band's carried gold and clothes, a tool or weapon
  of the trade, and jewellery from W3 up.
- Each person's gear follows their trade kit and their region (section 4).
- Guards carry the guard's issue (scale.json `guard_issue`, which the derive applies). Where the place's mods
  provide its own culture's guard set and the place's ceiling reaches the set's tier, the guards wear that set
  (in Black Marsh, BM&V's Argonian scale guard armour, T3, the scale material's tier), with the set's weapon if the source's guards carried one.
  Otherwise they wear the plain issue (T2). Every guard also carries one plain torch to light the way after dark. Each
  reason says why the place earns the set, such as a capital or a city of standing.
- Differences come from the facts: a net-maker carries a knife and twine, a feather-dresser a fine blade, a
  household's elder the family's old ring. Draw them from the person's trade, household and backstory.
- A notable person is written by hand: the leader, the richest household, anyone the record's hooks name.
- Read what the source outfit leaves once its significant pieces go (armour, anything enchanted). When it loses its
  only body piece, give a plain worn garment of the person's station (set dressing), so that every person is dressed.
- `worn` on a weapon means it hangs at the belt: the build carries it and the person draws it. Only armour and
  clothing make the outfit.

**Containers' contents** follow from what the container is, where it stands and whose it is.
- A container is keyed by its space and its ref: houses copied from one source share ref ids, so each row names its `space` and one row is written per space.
- A household has one store, its best-kept container, at the head's band. Its other containers keep their set
  dressing only.
- Value and protection agree. What lies open is ordinary. Each tier above the open tier is kept behind one more
  step of security. The lock is the lock of the best tier inside.
- A lock whose keeper the record or the people source names gets its key: the row's `key` {name, who or what holds
  it, why}, named for the container ("Strongbox Key") and held by that person (`person`), in another container
  (`in`) or at a spot (`pos`). The build makes the key, sets it as the lock's key and places it; a lock nobody keeps
  stays keyless, to be picked.
- The owner is a person, a household or a faction, so that taking it is stealing. Only bodies, the wild and the
  ruined are nobody's.
- On wild ground the tier follows the place's reward band: the way in is stocked one tier below it, and the
  hardest spot at the band's own tier. The boss's chest holds the band's tier and twice its gold. A loot promise
  names the store and where it is; its tier is always the reward band's (`docs/design/danger.md`).
- An encounter near a settlement (a fight with `setting: nearby`) keeps its reward with it, outside the settlement
  and nobody's: the loot give marked `nearby` is stocked at the highest reward band of the nearby fights that name
  it (`place_encounter`, in `place_danger show <place>`), never at the settlement's ceiling.
- Each container stays within its budget: its tier's `value_max` times its owner's share. A container the owner asks to hold more
  carries `owner_exception` {ruling (his words, where and when), why} in its row: the tier and value rules pass it by
  that ruling, and every other rule holds.

**Loose things** follow from what the place is and its record: an offering at a shrine, a lost pack in the reeds,
tools at a bench. Each lies on a ref or at a position, with an owner where people live.
- Decide each significant loose thing of the source one by one. To keep it, write a row whose `id` is its ref
  (no `on`, no `pos`) with an owner and the reason. To replace it, keep none and add a new row. Anything without a
  row is not built; list it under `removed` with the reason.
- A thing in a home is the household's: give `owner_faction` the household's id. A thing in a shared room is the
  town's (`<place>.town`).
- What lies open in a street is the open tier. A source's display of fine or exceptional things in the open goes.

**Traders' lists** are fixed: a trader's merchant chest restocks to its own list and nothing else. The gold is the scale's vanilla figure times the place's
band. The list runs from T1 to the place's ceiling, fewer of each tier upward, within the band's list value. Things
made here come first and in number; carried-in things are rarer, by road distance.

Price every choice by its **provenance**. Something made here is common. Something carried in counts against the budget at its value times the scale's `cost`, and is stocked at the made-here number times the scale's `count`. The derive's reason gives the distance.

**The exceptional** (a unique, anything of T6) goes in only by story. It needs a row in
`newworld/sources/stock/unique.json` naming the story that puts it there, and the game-wide count stays within
`ledger.caps`.

A reason or note at the tier `OWNER_STATED` is the owner's own words: never change or remove it. The derive keeps
such rows as they stand and lists where it would differ (`owner_kept`); raise a difference with the owner if the facts
argue for it.

Give every row a `why` that names the facts it stands on. Add `cites` where a holder takes them from the record or
the lore.

## 6. Deliver every promise

`python3 -m tools.newworld.stockdb promises <place>` lists each `place_give` row and what delivers it. Loot,
treasure and gold-hoard promises are yours: deliver each with a container or loose thing at the right tier, and a
`deliveries` row naming it. A promise whose spot is not in the place files needs the spot built: never improvise
the spot or its foes. Look for it in the drafted extent and in the database (a place of its own nearby); if it is in
neither, write the delivery `open` with a `why` that says what is missing and what would deliver it (the
drafting pass (`place-story`), the placed people at a fixed level, the container at its tier), and put the choice to the owner:
build the spot, or edit the record. Editing the record is the owner's call. When the owner rules it, change the
record, mark the delivery row `dropped` and name the edit in its `why` (the record's own narrow change is in the skill `place-research`).

A service promise (a trade, a trainer, a travel stop) is delivered by the person whose `people.jsonl` service names
its seq; the place files give it (the skill `place-routines`). When the place's people hold the right person but the
place files do not yet give them the service (a rootworm handler at the root landing for a `rootworm-stop`), run `python3 -m tools.places draft people <place>`, which gives a resident's promise to its keeper (the skill `place-people`, section 2). A promised station the files lack is `draft stations <place>`. Only when neither stage can give it, write the
delivery `open`, `by: person`, naming them, with a `why` that says which service at which seq and where they work.

## 7. What stocking never breaks

- A thing a quest names is the quest's: never moved, removed or restocked.
- Ownership is set wherever people live, so stealing is stealing.
- A lock is a fixed level, never one that follows the player.
- An authored container never respawns. Only a trader's merchant chest restocks, and only to its fixed list.
- No levelled list anywhere, and no never material (decision 0006), judged on our material.

## 8. Load, check and iterate

1. `python3 -m tools.newworld.stockdb items` (adds every item you named to the catalogue), then
   `python3 -m tools.newworld.refresh` (the tables, the story digest and the story explorer, in order). A load error reports the row and the
   column: fix the source, never the table.
2. `python3 -m tools.newworld.stockdb promises <place>`: nothing open. `python -m tools.places stock reach
   <place>`: no row flagged; `stock mix <place>`: each share as expected or explained.
3. Build and check the place (`python3 -m tools.places build <place>`, `check <place>`). Its `stock` check passes
   only when every significant thing traces to a row, every row is built, owners and locks are set, every keyed lock's key is with its holder, nothing respawns
   but a merchant chest, and each holder is within its budget and band. Its `promises` check passes only when no
   promise is open.
4. `python3 -m tools.places stock report <place>` prints the place in numbers and its ten most valuable things. Read
   them against vanilla's yields: a house's gold, a strongbox's, a trader's list value. If a number is far from them,
   either the facts explain it or the row is wrong.
5. Commit the sources and the tables the load rewrote (`newworld/story/data/db/`) by path
   (`tooling/lane_commit.sh`), with the place's counts in the message.

## 9. Change a stocked place narrowly

The stock source is derived whole once. After that, change only the rows a change touches and leave every other
row as it stands.

- A person is recast, or their trade or band changes: rewrite that person's `possessions` row, their household's
  store if they head it, and their `traders` row if they trade.
- A fact of the place changes (its wealth, its reward band, a promise): rewrite the rows whose reason names that
  fact.
- The owner changed contents in the studio: those rows are the owner's and stand as finalised.

Run `stock derive` to a scratch path to see what the facts give, and carry over only the rows you are
changing; never write a fresh derive over the stock source. Then run section 8 again.

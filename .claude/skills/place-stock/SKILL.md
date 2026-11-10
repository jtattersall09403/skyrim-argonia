---
name: place-stock
description: Stock one place of the new world (a city, a village, a camp, a ruin, a wreck) with what is in it - each person's possessions, each container's contents, the loose things and the traders' lists - on the one fixed scale, every thing with its reason, every promise of the place record delivered. Use after place-build has drafted the place and its people have light identities, and again when a person is recast or the place's facts change.
---

# Stock a place

You decide what each thing is and why, from the tools' measurements. Everything you author goes into the place's stock source,
`newworld/sources/stock/places/<place_id>.json`. People's identities live in `newworld/sources/people/<place_id>.json`.
The contract (file shapes, tables, what the build and its check do) is `docs/design/place-studio.md`, section Stock.
Nothing is random and nothing is levelled (decision 0035). Never write mod record content into a source: ids, counts
and reasons only.

## Inputs

- The place's facts: `db.open("newworld")`. You need `place` (kind, status, danger, importance, culture, siting),
  `place_note` (above all `economy`, `hooks`, `people`, `present`), `place_give` (its promises), `place_wealth` (band,
  ceiling, open tier, reason), `place_good`, `person` and `household` (its people), and the roads.
- The scale, `newworld/sources/stock/scale.json`: tiers and their materials, gold, locks and value limits; the
  wealth bands; security, effort, owner and provenance rules; budgets; traders' gold and list values; the split.
- The drafted place, `out/places/bundles/draft.<place_id>`, and its place files: rooms, containers, beds, who lives
  where.
- Vanilla's yields as a check: `docs/research/skyrim/stocking-yields.md`.
- The lore for every world call (decision 0032): `story/lore/` and the place's own notes.

## 1. Be sure of the facts first

1. Every person has an identity: `python -m tools.places identities check <place>` shows 0 problems. A place without
   people (a ruin, a wreck) skips this.
2. Read `place_wealth` for the place (`python3 -m tools.newworld.wealth show <place>`). If its band reads wrong for
   what the lore says the place is, say so to the owner with the reason. The owner overrules it with an `owner`
   block in `place_wealth.json`; you never edit the derived part by hand.
3. Fill the place's `goods` in its stock source from its economy note: what it makes, trades and needs, each with
   the words of the note that say so. Provenance is computed from these rows.

## 2. Run the split, and look at what it catches

`python -m tools.places stock classify <place> --json <scratch>/classify.json`

The split sorts from record data, never by eye. Read its list before anything is taken out. Note the source's
own best things (an enchanted blade on a guard, a unique lying loose): every one of them is taken out unless you
author it back with a reason.

## 3. Derive the measurable part

`python -m tools.places stock derive <place> --to <scratch>/<place>.derived.json`

It writes a first stock source: a store per household by the head's band and the household's size, bodies' few
things, each person's tool or weapon, the guard's gear, jewellery and carried gold by band, and each trader's gold and
list, all with reasons. It also lists what it leaves open. Treat it as a draft: read every row against the facts and
change what the facts say otherwise.

## 4. Author the stock source

Write `newworld/sources/stock/places/<place>.json` from the draft and the facts. For each kind of holder:

**People's possessions** follow from who they are: role, household, wealth band, fixed level and backstory.
- The baseline is the archetype of role × band × culture: the band's carried gold and clothes, a tool or weapon
  of the trade, and jewellery from W3 up. Guards carry the guard's issue, at the tier the guard's faction keeps.
- Differences come from the facts: a net-maker carries a knife and twine, a feather-dresser a fine blade, a
  household's elder the family's old ring. Draw them from the person's trade, household and backstory.
- A notable person is written by hand: the leader, the richest household, anyone the record's hooks name.

**Containers' contents** follow from what the container is, where it stands and whose it is.
- A household has one store, its best-kept container, at the head's band. Its other containers keep their set
  dressing only.
- Value and protection agree. What lies open is ordinary. Each tier above the open tier is kept behind one more
  step of security. The lock is the lock of the best tier inside.
- The owner is a person, a household or a faction, so that taking it is stealing. Only bodies, the wild and the
  ruined are nobody's.
- On wild ground the band sets the tier: the way holds the tier below and the hardest spot the band's own. The
  boss's chest holds the band's tier and twice its gold.
- Each container stays within its budget: its tier's `value_max` times its owner's share.

**Loose things** follow from what the place is and its record: an offering at a shrine, a lost pack in the reeds,
tools at a bench. Each lies on a ref or at a position, with an owner where people live.

**Traders' lists** are fixed and restock to themselves. The gold is the scale's vanilla figure times the place's
band. The list runs from T1 to the place's ceiling, fewer of each tier upward, within the band's list value. Things
made here come first and in number; carried-in things are rarer, by road distance.

Price every choice by its **provenance**. Something made here is common. Something carried in counts `cost` times its value
against the budget and comes in `count` times the number. The derive's reason gives the distance.

**The exceptional** (a unique, anything of T6) goes in only by story. It needs a row in
`newworld/sources/stock/unique.json` naming the story that puts it there, and the game-wide count stays within
`ledger.caps`.

Give every row a `why` that names the facts it stands on. Add `cites` where a holder takes them from the record or
the lore.

## 5. Deliver every promise

`python3 -m tools.newworld.stockdb promises <place>` lists each `place_give` row and what delivers it. Loot,
treasure and gold-hoard promises are yours: deliver each with a container or loose thing at the right tier, and a
`deliveries` row naming it. A promise whose spot is not in the place files needs the spot built: ask for a
place-build pass. Otherwise edit the place record, case by case, with the reason. In that case change the record,
mark the delivery row `dropped` and name the edit in its `why`; a promise is never dropped to avoid the work.

## 6. What stocking never breaks

- A thing a quest names is the quest's: never moved, removed or restocked.
- Ownership is set wherever people live, so stealing is stealing.
- A lock is a fixed level, never one that follows the player.
- An authored container never respawns. Only a trader's merchant chest restocks, and only to its fixed list.
- No levelled list anywhere, and no never-material (decision 0006).

## 7. Load, check and iterate

1. `python3 -m tools.newworld.stockdb items` (adds every item you named to the catalogue), then
   `python3 -m tools.newworld.stockdb load`. A load error reports the row and the column: fix the source, never the
   table.
2. `python3 -m tools.newworld.stockdb promises <place>`: nothing open.
3. Build and check the place (`python -m tools.places build <place>`, `check <place>`). The check passes only when every
   significant thing traces to a row, that ownership and locks are set, and that nothing is levelled or respawns.
4. Read the result against vanilla's yields: a house's gold, a strongbox's, a trader's list value. If a number is far
   from them, either the facts explain it or the row is wrong.
5. Commit the sources and tables by path (`tooling/lane_commit.sh`), with the place's counts in the message.

---
name: place-people
description: Give every person of one drafted place of the new world a light identity - a name, a household and a place in it, a trade, a wealth band and a line or two of backstory, each grounded in the place record and the lore - as rows of the place's people source. Use after place-build has drafted the place and before place-stock, and again for the one person a recast or a changed promise touches.
---

# Light identities for a place's people

You decide who each placed person is. The drafter decided where they sleep, work and walk. That stays in the
place files. Everything you write goes into the place's people source, `newworld/sources/people/<place_id>.json`,
one row per person of `newworld/places/<place_id>/people.jsonl` under the same id. A light identity holds no
dialogue, no personality and no fixed level: the story casts those later, and may recast anyone. The file's shape
and tables are in `docs/design/place-studio.md` (Stock: the people source). Where this step sits in the work on a
place is at the top of the skill `place-build`.

## Inputs

- The drafted people, `newworld/places/<place_id>/people.jsonl`: each person's `id`, `role`, `shift` (guards),
  `home`, `household` (`{id, relation}`, where the drafter made one), `services` (the promises they deliver) and
  `base_from`.
- The actor each person is built on: the row of `base_from` in the source bundle's `npcs.jsonl`
  (`out/places/bundles/src.<source_id>/`). It fixes the person's `sex` and `race`.
- The place record: `db.open("newworld")`, tables `place` (kind, culture, population, held by), `place_note` (read
  `people`, `economy`, `present`, `faith`, `look`, `dangers`, `hooks`) and `place_give` (its promises, by `seq`).
- The place's wealth: `python3 -m tools.newworld.wealth show <place_id>` (band P1 to P5).
- The person bands W1 to W5: `person_wealth_bands` in `newworld/sources/stock/scale.json`; each band's `about` says
  what a person of it owns.
- The lore (decision 0032): `story/lore/` (its `README.md` routes you), the place's culture and region rows, and
  the extrapolation in `story/lore/extrapolation/`.
- The naming rules: `story/design/quests/35-cast.md` section 54 and `story/design/quests/86-never-reuse-names.md`.
- Every name already given: the `name` of every person in `newworld/sources/people/*.json`.
- The lookups, `newworld/sources/people/lookups.json`: the ids a row may use for `race`, `role`, a household role
  and a relation. A row uses an id only after the lookup has it.

## 1. Lay out the households

1. Write one `households` row for each roof that people sleep under: `{id, home_space, name: null}`. A home's id
   is the one the drafter gave its people (`<place_id>.household.<home space>`). The inn's keeper heads a household
   of the inn. The guards who sleep in their camp or barracks are one household of it (`home_space` the space
   their beds are in), headed by the one who leads them.
2. Give every person `household: {id, role}`. The members of a household share one `home` in `people.jsonl`, and a household has one `head`, never two and never none.
   - A person the drafter made `head` or `partner` keeps that role.
   - A person the drafter made `kin` takes the tie that fits the household you are building: `grown child`,
     `elder`, `sibling`, `cousin`, `child`, or `kin` when the degree is left unsaid.
   - A guard who sleeps in a family's home is its `lodger`. A guard of the camp's household is `levy`.
3. Make each household a family that reads as one: at most three generations, the elder a parent of the head or
   the partner, ties that agree with each person's sex. Record every tie a backstory states as a `relations` row
   (`{to, kind}`) on the person it is said of, so that the tie is a fact of the database.

## 2. Give each person a trade

Copy `role` from `people.jsonl` unchanged. The `trade` is what the person does, in the place's own words.

- **A service person**: the trade is the promise they deliver, in the words of its `place_give` detail, with every
  further promise they keep (a trainer who is also the apothecary: "sap and herb seller; teaches alchemy").
- **A guard**: the place's guard body and the watch, from `shift`: "the city levy, night watch". The leader's
  trade says they lead. In Black Marsh the guard body is the levy, and the check reads that word in the trade.
- **A resident who keeps a promise** (a rootworm stop's handler, a follower): the drafter gives such a promise to
  the resident whose trade says the most of the promise's kind and detail. Choose who keeps it by writing their
  trade in the promise's words ("rootworm handler at the root landing").
- **Every other resident**: a trade the place's record supports. Start from the `economy` note (what the place
  makes, trades and needs), then `people`, `present`, `faith` and `look`, then the culture and the region's lore.
  The goods named in the economy note take the most hands. A household's trades hang together, as kin work
  together: a smith's partner tans, their child is the apprentice. An elder keeps the lighter work of an old
  trade. No trade is held by more than two people of the place unless the economy note makes it the place's
  living.
- A trade never rests on a mechanic or a theme the place record may not use (the skill `place-research` holds
  both rules).

## 3. Set each wealth band

Read the band's `about` in the scale and choose the one that describes the person. The place's own band bounds it.

- Most people of a place sit one or two bands under the place's number: in a P4 city, W2 and W3.
- W2: labour and gathering (porters, carriers, gatherers, the rank and file of the guard), and dependants.
- W3: a skilled trade, the head and partner of an ordinary household, the guard's leader.
- A trader or other service person reaches the place's number where their trade is the place's wealth (a P4
  city's market trader, smith and apothecary are W4). Those who serve travellers for a fare or a bed stay W3.
- W5 only for a person the record's `people` or `hooks` note names as rich or ruling.
- W1 only with the reason in the backstory (a debtor working off what is owed).
- Within a household no member's band is above its head's.

## 4. Name each person

1. Read every name in `newworld/sources/people/*.json` first. A name is used once in the whole new world.
2. Choose the form by who carries it (35-cast section 54):
   - Jel, untranslated, for the marsh-born and anyone whose life faces inward: one word or two joined by a
     hyphen, built from the sounds of the Jel names in the lore and equal to none of them.
   - A translated name (Verb-the-Noun, "Poles-Upriver") for those whose work faces outsiders: boatmen, traders,
     innkeepers. At most a third of the place carries this form.
   - A nickname for the notorious (a guard, a sailor, a criminal), earned by something the backstory can say.
   - A chosen name for someone who has remade themselves.
   - For a person of another people, a name by their own province's conventions.
3. An image (water, reed, root, stone, shadow, sky, boat, blade, eye, hand) appears in one name of the place at
   most.
4. No canon name, no name the lore files carry, no name on the never-reuse list, no name of a talker of BM&V (Black Marsh & Valenwood, the world mod the story plays in), and
   nothing Nordic (decision 0006).

## 5. Write each backstory

One note per person with `aspect: backstory`: one or two sentences, plain, in the present tense.

- Say what the person does and one thing particular to them: a tie to someone in the place, where they came from,
  what they did before, a habit.
- Draw the particular from this place's notes and the lore. A backstory may invent a motive, a habit or a tie.
  It never invents a fact about the world that the record or the lore does not hold.
- It may touch one of the record's hooks from where the person stands. It never resolves one.
- No sentence is shared between two people with only the names changed.
- `cites` lists every source the note draws on, at least one: a repo path (`story/lore/topics/material-culture.md`)
  or a database row (`place_note:<place>/<aspect>`, `place_give:<place>/<seq>`, `culture:<id>`, `region:<id>`).
- The note's `tier` (its statement tier: how far the statement rests on canon) is `AGENT_INVENTED`, or `EXTRAPOLATED` where the cited lore gives the reasoning.

## 6. Complete each row

`{id, name, sex, race, culture_id, household: {id, role}, role, trade, wealth, level: null, status: "alive",
tier: "AGENT_INVENTED", notes: [...], relations: [...]}`. `sex` and `race` are the built-on actor's. `culture_id` is
the place's culture unless the backstory makes the person an outsider. `level` stays null.

A name, note or reason at the tier `OWNER_STATED` is the owner's own words, written in the studio. Never change or
remove it. Build the rest of the person round it.

## 7. Check, review and hand on

1. `python3 -m tools.newworld.stockdb load` loads the source into the database. A load error is mended in the source, never in the table.
2. `python3 -m tools.places identities check <place_id>` shows 0 problems. It proves a row for every placed person
   and a person for every row, roles equal to `people.jsonl`'s, names unique in the place and by the naming
   rules, one roof and one head for each household, the drafter's head and partner kept, guards in the levy, one
   or two sentences of backstory and every cite existing. It does not read other places' people: the check of names against every other place (section 4, step 1) is yours.
3. Text review (the skill `text-review`) of the people source by someone other than the writer: one reader pass
   against the style guide, the rewrites applied, then the linter with `--race argonian` at 0 hard hits. Run the
   check again afterwards.
4. `python3 -m tools.places draft people <place_id>` writes each name onto the person's placement row and gives
   each resident's promise to its keeper. Read its counts, then run `python3 -m tools.places draft check <place_id>`.
5. Commit the people source, the tables the load rewrote (`newworld/story/data/db/`) and `people.jsonl` by path (`tooling/lane_commit.sh`), with the place's
   counts in the message. The place is ready for the skill `place-stock`.

## Change a person narrowly

When the story recasts someone, a promise of the record changes or the owner's note asks for it, change that
person's row and the rows it forces (a household role, a relation, a name another backstory mentions). Leave
every other row as it stands. Then run section 7 again, and stock the changed person again with the skill
`place-stock`.

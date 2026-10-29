# Dialogue lines per place

One file per place, named by the full place id: `lines/<place-id>.json`
(`lines/place.dunmer-north.riverwalk.json`, never `lines/riverwalk.json`):
`{schemaVersion: 1, domain: "dialogue-lines", placeId, entries}`. The people
are the place's roster rows in `world/sources/registries/npcs.json`; an
optional `people: [{id, topics}]` adds topics a person raises unasked
(the fixture lists whole people because it has no roster rows).

Entries are content units (standard 11, quests/85 § C):

- an **override**, a person's own line on a topic: `id`
  `override.<person-slug>.<topic-slug>`, `type: "dialogue"`, `speaker`
  (the `npc.` id), `keys.topic`, `words`, `available`, and
  `derivedFrom: {poolLineId, hash}`, the pool line it was written from and
  that line's hash then, and `factIds`, the pool line's facts it states
  (`../facts.json`; each fact's cue must be in the words). It states no
  fact its pool line does not; on a newcomer, faction or role topic it
  carries at least 60 percent of them, explaining before it deflects.
- a **person greeting**: `id` `greeting.<slug>`, `type: "greeting"`,
  `speaker`, `words`, `available`. A greeting banded on
  `speakerDispositionAtLeast` up to 75 is reached by the walk's `trusted` state.
- a **bark**, said aloud outside a conversation: `id`
  `bark.<person-slug>.<slot>[-n]`, `type: "bark"`, `speaker`, `slot`
  (`passing`, `at-work`, `night`, `warning` or `rumour`), `words`,
  `available`. It overrides the x5 bark table for that person. Once a
  place has any bark, every person needs a `passing` and an `at-work` one.

Fold an address term into a sentence: a one-word greeting such as
"Citizen." repeats across the province and the duplicate gate reds it.

Services come from the roster's `services` words, mapped to the dialogue
kinds by `dialogue_lines.SERVICE_KIND` (ferry -> travel, beds -> rest,
trade -> barter, stable -> stable); an unmapped word is a gate red.

What a person must answer (the `people` gate): every topic whose
`requiredFor` names their place or role in `../topics.json`, and the
newcomer topic of every glossary term their own lines name (forms matched
whole-word, longest first). Each needs an override, and each person needs
a greeting of their own.

A pool file (`../pool/*.json`) is shared by every place lane: write it
only with `python3 -m worldgen.dialogue_pool add --file <pool file>
--entries <json array or path>` (cwd `tooling/world-generation`), which
locks `pool/.lock`, re-reads the file, refuses an id already there and
renames a temp file over it. Never write a pool file from an in-memory
copy. `dialogue_pool dedupe --file` repairs doubled ids; the load gate
reds any.

Per place (0140): `python3 -m worldgen.dialogue_lines --write --place <id>`
rewrites only that place's bundle; `--check --place <id>` checks only that
place's bundle and catalogue rows; `--stamp --place <id>` fills empty
`derivedFrom.hash` values after writing an override (never a set one).
Then `dialogue_gates.py --place <id>` and `dialogue_walk.py --place <id>`.
The gates' `style.*` section measures how the place reads (style-core §4):
each answer inside its speaker's `answerLength` band, medians, contractions,
explains, sentence spread, asides, the routing shape and the terse share.

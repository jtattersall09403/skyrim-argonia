# The writing skills fitted to the import (0.1 §i)

Lane 0.1-i, 2026-10-29 (decisions 0024, 0025).

## What changed

- **quest-write.** `quest-record.md` is now the imported quest object (`world/sources/quests/README.md`, field
  names unchanged, stages in the imported shape: `place`, `journal`, `onEnter`, `objectives`, `successors`,
  `failForward`, `ending`) plus the record's sections, with the engine-mapping table, the journal rules and
  the investigation coverage. `SKILL.md` carries the novelty rule and shape budget (old 55 §47c), cast from
  36-cast-roster and the registry, and paths into `world/` and `docs/design/`. `skill-uses.yaml` takes the old
  verb tags, a `systems` table naming the engine feature and chunk for every player system, supporting acts,
  and allowed settings per use. `profiles.yaml` has one profile per line in `lines.json` plus the detectives,
  each cited to 40-factions and its culture sheet; `fighters` and `mages` are gone. `shapes.yaml` routes by
  the quest's `group`. `action_plan.py` builds plans on each shape's beats (find, get there, crux as two
  approaches, resolve), keeps one target across a plan and picks settings a use allows. `brief.py` reads the
  registry, stance, culture sheets, place facts, topic web and condition vocabulary, refuses a record with a
  non-vocabulary term, a missing stage field, a missing fail-forward or fewer than two endings, and writes a
  journal brief. LH38 is rebuilt in the new format; MR01 (Many-Root) is new.
- **quest-review.** Paths to the world records; the gaps in its numbering filled (evidence and accusation,
  journal register, vocabulary and fail-forward, novelty rule, registry match); item 18 completed; findings go
  to the record's `review`.
- **dialogue-write.** `place_brief.py` takes only `--person` and reads `npcs.json`, the stance row, its culture
  chain, the place facts and `topics.json`; no hand-made persona file. `lint.py` now requires `--race` (any
  case): a capitalised or missing race skipped the race bans and exited 0 on a hit.

## Needs a decision (from the mapping table)

1. `present-evidence` and `accuse`: no vocabulary term and no dialogue-view act.
2. Rival factions' reactions to a solved case: no term or rule.
3. `witnessed` and `recordWitnessed`: no chunk builds the event ledger.
4. `custody` and `evidenceState`: evaluated in 2.5, but nothing sets them.
5. `setSchedule` for spy stages: no chunk swaps a person's day per stage.
6. Disguise (`wearing`, `disguisedAs`), the Hist step (`grantHistStep`) and fishing: no chunk.
7. `lockIs`, `seenBy` and `inZone` are marked "planned: 2.10" in 85; the plan builds them in 2.11.
8. `timeOfDay` gates on stages: the generator must re-check on the clock, not only in dialogue.

## What 2.5 and 2.12 must add (decision 0025)

The import already covers evidence-gated topics (`knowsTopic`, `topicHeardFrom`, `hasEvidence`, `not`), catching
a lie (`topicHeardFrom`) and possession of evidence. Missing: a "show" act (item or learned topic, shown to a
person, with a response); an "accuse" act naming the suspect and exhibits with a threshold and outcome stages;
the actions that set custody and tampering; the event ledger for witnessing; and a rule for which rival
faction reacts, and how. 2.5 §a builds the terms and the dialogue-view acts; 2.12 §a builds the generator
side and the investigation stages.

## Import findings for other lanes

- `stance/greenspring.json` describes Reeh-Shaal (female in `npcs.json`) with "he"; LH38's old draft had the
  sexes of three people wrong against the registry.
- MR01's essential topic `topic.greenspring-sick-root` has no row in `topics.json`.
- LH38 and MR01 shared a misdiagnosis (salt) at the same spring: LH38 now blames the food.
- MR01's dive is at the drowned stair (packet 4.2), outside the slice: the planner must choose.
- The imported quest README cites `docs/quests/` and `tooling/world-generation`, neither in this repo, so the
  novelty rule's validator (`worldgen.quests --check`) does not run here yet.

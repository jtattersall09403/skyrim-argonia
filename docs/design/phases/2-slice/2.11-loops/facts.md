<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/facts.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# The place facts record and its audit

Part of [2.11](../2.11-quests-journal-map.md) (the facts lane, decision 0153 §2).
Every consumer of a world fact reads one record per built place,
`world/sources/placement/facts/<place-id>.json` ([world/98](../../../world/98-data-model.md) "Place fact").

## The record

- `facts[]`: one claim each, with `sourceField` (the catalogue path it restates) and a
  carrier, built `{uid, type}` (sign, readable, visual-cue, npc, container, piece-set) or
  queued `{type, ref}` (npc-topic, book, quest-beat).
- `world`: derived whole by `worldgen.place_facts --write` (`worldgen/place_world.py`) from
  the record, the published bundle, `npcs.json` and the place's dialogue lines:
  position and extent, stands, sockets (area, slot), landmarks with `inSight`, people
  with topics, counts of nodes, plants, items and containers by area, services with
  who gives them, and the hostility block with its flips. A stale block reds the facts
  gate (`place_facts --check`).
- Prose is split into claims by `place_facts --id <place> --add <split.json>`.

## Commands

    cd tooling/world-generation
    python3 -m worldgen.place_facts --id <place> --write          # regenerate tag facts + world block
    python3 -m worldgen.place_facts --id <place> --add split.json # put a prose split in
    python3 -m worldgen.facts_audit --slice [--reds] [--json]     # the audit over the 18 slice places
    npm run look -- place <place> <x> <z> --radius <m> --out lanes/2.11-facts/look/<slug>

## The audit

`worldgen/facts_audit.py` prints every catalogue and prose claim of a place as
`carried`, `deferred` or `red`, judged by `script` or `eyes`:

| Row | Carried when |
|---|---|
| fact | its carrier resolves (built uid in the bundle with the right type; queued ref a person with topics here or at their home place, a rumour pool, a quest anchored here, a book naming an item); a visual-cue or piece-set fact also needs a reader verdict `seen` |
| prose | some fact restates that prose path |
| promise | the ledger row is filled by ids present in the bundle; a row the ledger defers to a named later system (`later-phase-system` with a note) is `deferred` |
| world | the position lies within `footprintRadiusM` of the built boundary; every roster slot has an npc socket; every promised service has a giver or a filled parcel; the custody post exists; every hostility flip key is in the condition vocabulary (`packages/dialogue/src/conditions.ts`) |

Reader verdicts live in `lanes/2.11-facts/readers/<slug>.json` over the look sheet in
`lanes/2.11-facts/look/<slug>/`; the checklist each reader judged is `<slug>.todo.json`.

## Consumers

| Consumer | Reads | Proof |
|---|---|---|
| directions | position and arrival landmark (`placesFromFacts`, packages/dialogue/src/directions/factsPlaces.ts; the walker `routes` command passes `factsDir`) | `factsPlaces.test.ts` moves a fact and the place moves |
| dialogue `groundedIn` | fact ids, claims, landmark ids (`dialogue_grounded.record_set`) | `test_dialogue_grounded.py::test_groundedin_reads_the_place_facts_record` |
| quest validator | quest `sockets` against the anchor place's world block (`quest_facts.socket_reds`, appended in `quests.graph_reds`) | `test_facts_audit.py::test_a_quest_socket_missing_from_the_facts_world_block_is_red` |
| journal text | stage journal text is written over the quest stages the validator holds to the facts record | through the quest validator |

## Survey

STATUS: see the lane report `lanes/2.11-facts/report.md` for the measured totals.

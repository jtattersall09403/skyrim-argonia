# Lane 1.1-schema: the message schema, the family round trip and the router registry (report)

Dated 2026-10-29. Chunk 1.1 §c, plus §b's L2 round trip and §d's router registry as pure code. Route 5, test level
L1/L2, no game. Everything here is tech-neutral: it serves PrismaUI, Scaleform or a hybrid alike (1.2 §0).

## What exists

| Piece | Where | What it is |
|---|---|---|
| The schema | `ui/schema/{types,common,dialogue,journal,hud,chart,view,index}.ts` | the one source: a small descriptor language (`str`, `int`, `num` with ranges, `bool`, `oneOf` enum, `list`, `opt`, `ref`) and 12 versioned messages |
| The generator | `tools/schema_gen/{gen,model,emit_cpp,emit_ts,families,router}.ts` | Node 22.11 with `--experimental-strip-types`, no npm package; pinned `node=22.11.0` in `infra/build-vm/toolchain.lock` |
| C++ twin | `skse/core/generated/argonia/core/messages.h` | structs, enums, `Traits<T>`, `Push`/`Intent`/`Message` variants, `encode`, `decode`, `decode_intent`, `decode_push`; header-only over the new `json` module |
| TS twin | `ui/schema/generated/messages.ts` | interfaces, unions, `validate`, `decodePush`, `decodeIntent`, `encodeIntent`, `encodePush`, `schemaHash` |
| JSON | `skse/core/{include,src}/…/json.*` | strict parser and writer (duplicate keys, trailing text, bad UTF-8, lone surrogates, out-of-range numbers and depth > 64 refused) and the field readers the twin uses |
| Family layouts | `skse/core/schema/families.json` → `generated/…/family_layouts.h` | each family's payload layout per version |
| Round trip | `skse/core/{include,src}/…/roundtrip.*` | `sample`, `conforms`, `check(registry, schema)` |
| Router registry | `data/router/surfaces.json` → `generated/…/router_table.h` | 6 hooks, 41 surfaces |
| Router | `skse/core/{include,src}/…/router.*` | `install` (once per hook), `handle` (one per surface), `on_menu`, `on_surface`, `awaiting`, `load_log` |
| Fixtures | `ui/fixtures/{dialogue,journal,hud,chart}.json` | `{screen, doc, states: {name: envelope}, intents: {name: envelope}}`; 22 states and 10 intents |

### The messages (all version 1)

Wire form: `{"type": "<screen>.<name>", "v": N, "body": {...}}`. Each message is a full snapshot. Every field is
required unless `opt`. An absent optional is omitted, never sent as null.

- **Pushed to views:**
  - `dialogue.state`: the speaker; entries (greeting, answer or notice, an optional heading, and text as runs, where
    a run with a `topic` is a keyword span); the topic list; disposition (value 0–100 and band low, mid or high);
    persuasion (available, and options with id, label, enabled and an optional gold cost); `canLeave` (Goodbye).
  - `journal.state`: tab (entries or quests), page and pageCount, an optional quest filter, the page's entries
    (quest, name, date, kind, runs), and the quest index (status, date started, optional directions).
  - `hud.state`: visible; the bars (health, stamina, magicka, breath, climb, each with current, max and shown); the
    sneak eye (0–1); the effect stack; the vastei plaque (carried, plus a recent gain); the place banner; the prompt
    with a glyph per device; notices.
  - `hud.bars`: the bars alone, for the frequent update.
  - `chart.state`: the worldspace, the sketch image id, the revealed cells, the places (cell units, discovered or
    not) and the view. There is no player position (C9).
- **Intents sent back:** `dialogue.topic`, `dialogue.keyword`, `dialogue.persuade`, `dialogue.goodbye`,
  `journal.page` (tab, page, quest filter), `chart.pan` (view), and `view.close`.
- **Dates:** `GameDate` carries `text`, because views never format game dates.

## Acceptance, measured

- **The schema covers the four screens:** 12 messages. Every type appears in a fixture, and both sides test this.
- **Both twins are generated, with refusal tests on each side:**
  - C++ `core.messages`: 32 fixture envelopes decode, re-encode to the same JSON (structural compare), and are
    accepted on their own side only. Seventeen refusals are checked by message: unknown type, wrong version, extra
    envelope key, missing `v`, extra body key, missing field, wrong type, enum value outside its set, int out of
    range, fractional int, null optional, num out of range, missing nested field, not an object, bad JSON, and both
    directions. `encode` refuses a negative bar, a NaN and disposition 101.
  - TS (`ui/schema/tests/validate.test.ts`, in the new `make ui` part): the same fixtures, and the same 15 refusal
    strings matched against the C++ wording. `encodeIntent` refuses an off-schema view, a push sent as an intent
    and a NaN. Both twins carry one `schemaHash`, and each test checks the other twin's copy.
- **The gate checks the twin, and was made to fail once:**
  - `skse/check.sh` now runs `gen.ts --check` beside `core_tables --check`.
  - With `hud.bars` bumped to version 2 and nothing regenerated, `bash skse/check.sh` exited 1:
    `schema twins are stale … messages.h:22: stale / tree: kSchemaHash = "6a6e27ff2a000392" / want: … "57566a37e2b2ea81"`,
    with the same for `messages.ts:5`. It passed again once restored.
  - `tools/schema_gen/tests/gen.test.ts` keeps the proof: a temp copy with an edited and a deleted twin names both.
- **The family round trip and migration pass:** `core.roundtrip` proves all 8 schemas (META, STAT, DISP, JRNL, ITEM,
  DETH, TEST, TSTN) through `roundtrip::check`:
  - 24 sampled payloads per family load and save back byte for byte;
  - a payload cut by one byte, or with one extra byte, is refused;
  - the reset state round-trips;
  - TEST v1 migrates to a payload that fits v2;
  - TSTN v1 has no migration, so it is refused and reset with
    `co-save family TSTN: saved at version 1, this build reads version 2 and has no migration from version 1 to 2; load refused, the family is reset`.
  - Every registered family has a schema, and every schema has a family.
  - The check can fail: a drifted DISP layout, TSTN wrongly declared as migrating, and a family with no
    registration each give failures.
- **The router refuses a duplicate hook:** `core.router` checks four things.
  - A second `install(dialogueIntercept)` gives `hook dialogueIntercept: already installed; a system registers a handler, never a hook`.
  - A second handler on a surface is refused, as is a handler before its hook, a handler on a restyled surface
    and an empty handler.
  - The registry has all six kinds (menu, dialogue, death, levelUp, hud, notification), and `dialogueMenu` carries
    `dialogueIntercept` from 1.3 §b.
  - The verdicts:
    - a view with a handler blocks and runs the handler;
    - a view without one passes and is logged;
    - suppressed blocks;
    - restyled passes;
    - an unlisted menu passes and is logged.
- **`bash skse/check.sh`:** `100% tests passed out of 21`, 15.5 s wall, peak RSS 323 MB. `core.messages` takes
  9 s to compile, because the twin is header-only.
- **`make check`:** guard, lint, unit (199 passed), budget, links, world, skse, immersion and the new `ui` were all green: 47.7 s wall, peak RSS 171 MB. `plugin-check` could not run. It waits on `out/.plugin.lock`, which the 2.W4 lane's `pipeline.py navmesh` build was holding (a run of tens of minutes). None of this lane's paths reach it.

## Calls made inside the brief

- **Node, not Python, runs the generator,** so the TS schema is executed rather than parsed. Node 22.11 was already
  in `~/.local/bin`. It is now pinned, but `infra/build-vm/setup.sh` does not install it (that file is outside this
  lane's paths).
- **Keyword spans are text runs, not offsets.** This avoids UTF-8 versus UTF-16 offset drift between C++ and JS.
- **Validation is strict on both ends.**
  - An extra key is refused. A JS object key whose value is `undefined` counts as absent, as `JSON.stringify` drops it.
  - One asymmetry remains: JS `JSON.parse` keeps the last of two duplicate keys, while C++ refuses them. Views only
    receive from C++, which never writes duplicates.
- **The family round trip is generated from data, not per family.**
  - `families.json` holds each version's layout. `roundtrip::check` is generic: sampled payloads, byte-exact
    save-back, truncation, padding, reset, and each older version's migration or refusal.
  - The module codecs stay hand-written and unedited. The test binds them.
  - Ranges are kept inside what the decoders accept. For example, ITEM's condition is drawn from 0–50 and its max
    from 50–1000, because the decoder requires condition ≤ max.
- **The router registry lives in `data/`, not the world db,** because it is a code contract rather than world
  content. Menu names follow CommonLibSSE-NG's `MENU_NAME`, but they were not checked against the pinned CommonLib
  here, because no copy was on the VM. They are **UNVERIFIED** until S10a or S11a.
- **Router rules:**
  - `hudMenu` is *restyled*: the movie stays and its elements are separate rows.
  - A *view* surface whose system has not landed passes and is logged, rather than leaving the player with nothing.
  - *Suppressed* blocks with or without a handler. Death is suppressed, with `by: respawn` as its flow.
- **Fixtures:** the Signs-For-The-Cargo and Claywater Station ids, lines and topics come from the world db. The
  journal entry text and three ids are marked mock in each file's `doc`. `threeHundredTopics` is there for 1.2 §0's
  probe.

## Owed by others

- `docs/design/world/98-data-model.md`: the router registry and `families.json` as new data homes (1.1 §e). That
  file is outside this lane's paths.
- `infra/build-vm/setup.sh`: install the pinned Node on a fresh VM.
- `skse/README.md`: name the `json`, `router` and `roundtrip` modules and `schema/`.
- ArgoniaCore (1.1): bind the families to one `Registry`, check it with `gen::family_schemas()` at load (S10a), drive
  `router::Router` from the real hooks, and send pushes with `msg::encode`.
- The 1.2 §0 choice may need further message fields. Each change bumps that message's version.
- `cosave::upgrade` and `families::Registry` are still two lift chains, as the core-rules report noted.

# Lane journey-lint (2026-10-30)

Goal: the authoring errors game-13 met in game (`g13-all.log`) caught by `run_journey.py --dry` /
`run_batch.py --dry`, so by `make check`, before a batch runs.

## What game-13 failed on, and the rule that now catches it

| Item | Console said | Rule |
|---|---|---|
| combat-trial-a `player.hasperk TKDodgeAddon.esp\|0x809` | Syntax Error, reference not allowed | The console takes no `plugin\|offset`. The bridge DLL does not resolve one either (`find_form` takes a hex id or an editor id). So the Python client (`tools/bridge.py` `resolve_plugin_forms`) now writes `<file>.esp\|0x<hex>` as the runtime id from the `plugin` read's prefix (light plugins `FE xxx`), quoted when it calls a function. The lint fails a malformed one (no `0x`, bad extension). The journey stays as written. |
| fight-archetype `{opp}.GetLevel` (`1000088C.GetLevel`) | Script command not found | A calling ref that is a raw or kept id must be quoted: `"{opp}".GetLevel` (the convention `tools/ref_ids.py` already writes for `ARG_*`). Static error. |
| fight-damage-builds `av OneHanded` | no actor value OneHanded | Vocab rule: the `av` read's name must be one of the actor value names the game round-trips. The journey now reads `player.getbaseav OneHanded/TwoHanded/Marksman` at the console. |

## Static lint over tests/journeys (no vocab cache)

16 errors in 4 journeys, all unquoted `{opp}.Func` calls, fixed: die-and-recover (5), fight-archetype (2),
fight-damage-builds (4), grow-at-rest (5). All other journeys are clean.

## Vocabulary

- `vocab` is a new dev-only ArgoniaBridge read (`skse/ArgoniaBridge/src/ep_dev.cpp`). It returns the console and
  script functions from CommonLib's `SCRIPT_FUNCTION` tables (name, short name, `numParams`, whether it takes a
  calling ref, and its kind) and every name from `ActorValueList::GetActorValueName`.
- The game keeps no placed ref's editor id (game-7). So the refs come from the world database
  (`ref_ids.ref_rows`, `ARG_Ref_*`), and `tools/fetch_vocab.py` adds them to the cache.
- The cache is `$ARGONIA_PRIVATE/vocab.json` and is never committed. With it, the lint checks:
  - the function name of each console line;
  - the argument count against `numParams`;
  - the `av` name;
  - each `ARG_Ref_*` word.

  Without it, `--dry` prints one warning and keeps to the static rules, and the gate never fails for want of the cache.

**Fill the cache (game-13, the game running with the dev bridge):** `python3 tools/fetch_vocab.py`

## Tests

`tools/tests/test_journey_lint.py`: each rule is shown both failing a bad line and passing a good one. The client's
plugin-form resolution is tested against the fake bridge socket from `test_bridge.py`. 5 passed. `make check`: see
the commit.

## Open

- Bridge build: `job_guard.sh run --gpu bridge-vocab -- infra/gpu-box/skse_build.sh build windows-dev` was queued
  behind the batch; its result is in `~/.argonia/jobs/bridge-vocab.log`. The `SCRIPT_FUNCTION` names
  (`GetFirstConsoleCommand`, `Commands::kConsoleCommandsEnd`) are from CommonLibSSE-NG memory, so the build can still
  fail on them.
- The `av` read refusing `OneHanded` is unexplained until the cache shows what `GetActorValueName` returns.
- The `>> 0.00` that `getbaseav` prints is the console's float format. It is not yet seen in game.

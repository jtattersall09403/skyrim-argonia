# Lane combat-trial-prep (2026-10-30)

This lane got Dark Souls Combat SE (Nexus 28567) ready to trial as combat groups B and B2, so the game lane can run
it in one slot. The trial plan and the verdict table are in `docs/research/journals/combat.md`, in the section "the
combat trial".

## Done (L1)

**DSC's row.**
- The archive's sha256 (`ca203060…`) matches.
- The row no longer has `from: 2.7`: the set alone gates it, and A is the default. It now lists its plugins.
- **The drop.** `drop sound/fx/bb_dsc*` comes with `drop_why`. The stage removes 7 files and prints the count.
- **The per-set values.** `plugin_values` writes them into the staged ESP:
  - B: `RollKey` 277, the pad's B, which controlmap.py binds to Sprint.
  - B2: `BB_Poise_VarCritsAllowed` 0 and `RollKey` 0.
  - Both: `BB_Poise_VarDebugTrace` 1, because the Papyrus log is DSC's only poise read.

**stack.py.**
- `edit_plugin` sets a GLOB's FLTV and a quest script's int property, and the record and GRUP sizes follow. It is
  idempotent.
- The chosen set is part of the stage key, so switching between B and B2 restages DSC.
- An unknown `--set` is refused.
- `stage --into DIR --group G` stages one group into a scratch folder, and only there.
- `combat A|B|B2 [--dry DIR]` and `pandora-check` are new.

**Allowlist.** DSC's three start-enabled quests are on it, each with its reason.

**Journeys.**
- `tests/journeys/combat-trial-{a,b,b2}.yaml` are runnable (26, 27 and 26 steps), and `--dry` passes for each.
- `parry-riposte` is `owed` until pad.ps1 can hold a trigger.

**Test.** `tools/tests/test_stack_combat.py` has 5 tests:
- the ESP edit on a synthetic plugin;
- the edit is refused when the plugin lacks the record;
- the rows each set lays;
- the B and B2 values;
- an unknown set is refused.

## Measured

`stack.py combat A B B2 --dry <scratch>` on the build VM staged:

| Set | Rows | Files | DSC files |
|---|---|---|---|
| A | 22 | 6,357 | none |
| B | 9 | 3,982 | 53, none under `sound\` |
| B2 | 22 | 6,256 | 53 |

- Staging A again gave A's first stage exactly, and a second stage restaged nothing.
- The staged ESP differs between B and B2.
- On a re-parse of the edited ESP: CritsAllowed is 0.0, and RollKey is a new VMAD property.

## Not done, and why

- **Pandora on Linux.** It is a self-contained Windows exe and Wine is ruled out. `pandora-check` is written to run
  on the machine and has not run.
- **The bash journey step.** pad.ps1 has no held button or trigger, so the step is owed. The runner is not in this
  lane's paths.

## Findings

- **Out of the box, DSC never rolls on a pad.** It registers one keyboard key, LAlt (56).
- **DSC reads its globals only every fifth update.** A console `set` at scene step 0 is therefore unreliable, so the
  values are staged into the plugin instead.
- **In B, ArgoniaCore's roll lock has no tk-dodge.toml to read**, because TK Dodge is not laid. Check its log line.
- `make check`: CHECK GREEN (347 unit tests passed). The game lane, game-10, has been sent the trial steps.

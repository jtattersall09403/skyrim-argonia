# Install step: the skill-tree perk text (1.12 §4; decisions 0003, 0012, 0014 §7–8)

Made on the player's machine after the mods are laid and before the first launch. The output is a derived file: it
carries the player's own copy of 273 skill-tree PERK records (Skyrim.esm and Dawnguard.esm), so it is git-ignored
and never shipped or committed. 3.4 builds the installer around this command; the build VM runs the same one into
`out/perks/argonia-perks/`.

Needs: the .NET SDK and the built `tools/ArgoniaGen` (`dotnet build -c Release`); the player's Skyrim.esm and
Dawnguard.esm under `$ARGONIA_GAME_ROOT/Data`; the official string tables extracted to `out/strings-cache` (or
`$ARGONIA_STRINGS`), which the generator reads for each copied perk's entry labels. Our wording is
`world/db/perk_text.jsonl` (273 rows, committed; no vanilla text in it).

0. **One command.** `python -m tools.argonia_world.perk_plugin --out <mods>/argonia-perks` runs
   `ArgoniaGen perks --in world/db/perk_text.jsonl --data <Data> --out <mods>/argonia-perks/ArgoniaPerks.esp`. It
   writes one PERK override per row: the master's record copied whole, only the name (FULL) and description (DESC)
   ours. Masters are listed in load order (Skyrim.esm, Dawnguard.esm). 273 overrides in about 2 s, 101 KB.
1. **Order.** `argonia-perks` goes above our ESMs in the profile (MO2 `modlist.txt`: earlier line wins) and
   `ArgoniaPerks.esp` is added to `plugins.txt` after them. `infra/gpu-box/stack.py stage` does both when
   `out/perks/argonia-perks/ArgoniaPerks.esp` exists; `deploy.sh` rebuilds it (step `perks`) before the stage.
2. **Verify.** `pytest tools/argonia_world/tests/test_perk_plugin.py` parses the ESP: exactly 273 PERK overrides,
   every subrecord other than FULL, DESC and EPF2 (the button label, a string-table id in the master and inline
   here) equal to the master's, and every number in each DESC equal to the vanilla text's (needs
   `out/perk-text/vanilla.json` from `tools/immersion/perk_extract.py`).

`Argonia.esm` does not carry these overrides on purpose (`tools/argonia_world/intermediate.py`): its YAML is in git.

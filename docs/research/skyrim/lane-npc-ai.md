# Lane npc-ai: Claywater's people run no AI (L1; L4 by game-7)

## Done
- **The diff table** is in docs/research/journals/npc-ai.md. It compares our people's NPC_ and PACK records field by
  field with Bendt, Hefid, SailorXander, their PACKs and the four TreasCorpse/WERoadCourier templates, read with the
  new read-only `ArgoniaGen npcai`. That tool reads the binary overlay with explicit fields and peaks at 195-366 MB.
  Its first version walked an NPC_ by reflection and ran to 10.9 GB before the planner killed it.
- **Writers fixed** to the vanilla townsperson shape:
  - **NPC_:** AutoCalcStats; AIDT energy 50, NoCrime, Neutral, HelpsNobody (it was energy 0, Mutagen's default);
    sound level Normal; a default outfit (it had none, so they stood naked).
  - **CombatRecords.cs** takes these as optional fields, plus combat style and factions. Absent, the archetypes
    write as before.
  - **PACK:** the data inputs no longer carry `Flags 0` (a vanilla templated PACK has no input labels), and the
    events drop the template's SCHR.
- **Outfits:** new `build_person` columns `outfit_form_key`, `outfit_stand_in` and `outfit_why` (schema.sql). The
  four people take King of the Murkmire stand-ins, flagged as such, until their `look_outfit` clothing is ours.
- **L1 check:** `place_build.check_people` fails the build when a person lacks packages, AI data, outfit or class,
  or when a PACK's `inputCount` differs from its template's (12 sandbox, 17 sleep). ArgoniaGen also refuses a PACK
  whose written count differs. Proved failing once on the real data: with Livia's outfit blanked, the intermediate
  raised `ARG_Npc_WellKeeper: no outfit`. Tests: tools/argonia_world/tests/test_people_records.py (7).
- **Control:** tests/scenes/claywater-control.txt places vanilla Golldir (00019FE8, one Sandbox PACK near his
  editor location) and a temporary copy of ARG_Npc_WellKeeper at Livia's work spot. It is dev only.
- **Gate:** `make plugin` twice gives the same out/Argonia.esm, sha256 f6888c4f… (455,940 bytes). plugin-check is
  green. `make check` is green (321 pytest).

## Open
- **No record difference explains a total AI stop.** The packages are present and resolve, and the actors are
  filed in the WRLD persistent cell as vanilla files them. The suspects that remain:
  - AI toggled off globally (`tai` in infra/gpu-box/smoke.py:234,239, if a run stopped between the two toggles);
  - the persistent placement;
  - the navmesh.

  The control scene splits these three.
- **Factions:** the people have none (no faction rows yet); the town's crime faction is owed.

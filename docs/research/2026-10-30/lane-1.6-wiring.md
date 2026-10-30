# Lane 1.6-wiring report (2026-10-30)

## Hand-off (context past the mark; everything below is committed and green)

Built:
- the wiring spec (docs/research/2026-10-30/combat-wiring.md);
- the combat tables, filled;
- the stack.py settings hook;
- the carrier perk, the D2 archetype and the steel sword's listed damage, generated into Argonia.esm;
- four L4 drafts;
- an L1/L2 test (tools/argonia_world/tests/test_combat_records.py, 6 pass).

Commit dbf8da4 carries both this lane and 1.5-build's records, because the shared files took both lanes' hunks.
`make plugin` gave the same 424,440-byte esm on three runs, plugin-check is green, and make check is green
(265 passed).

Next, in order:
1. **ArgoniaCore lane (skse; not in this lane's paths).**
   - Write the 4 wired carriers on every sheet, equip and burden change; the values are in the spec's carrier table.
   - Add ARG_Perk_Carriers to the player.
   - Pin the OneHanded, TwoHanded and Archery base AVs at 0.
   - Toggle TK Dodge Addon's required perk by burden tier, and only then add the `bUsePerkLock` = true row.
2. **The game slot.**
   - Run fight-damage-builds, fight-roll-burden, fight-lock-on and fight-archetype; the scenes `bat duel-ring` and
     `bat claywater-ambush` do not exist yet.
   - The archetype's actor is not yet placed in a cell. Place it in the claywater-ambush scene or with 2.W5's
     population.
   - The race's start health (50) and the perk entry tab counts are `GUESS` facts. These runs settle them.
3. **2.7.** Every `GUESS:`/`MOD:` value is DSR-owed (parry window, i-frames, roll cost, lock range, regen delay,
   motion values). The thin rows (OAR stamina, guard stamina, i-frames by tier, left hand) go to the combat map.
4. **Owner (1.7).** Review the spec draft.
5. **Owed not done.**
   - No /code-review of this lane's diff.
   - Journal docs/research/journals/combat.md is not opened (it needs the owner's 0.0 notes; not in this lane's
     paths).

## What was decided and why

- **Settings live in the db, not data/combat/ or the manifest.** Decision 0030 makes one relational home per fact,
  and every value carries a provenance and a wiring foreign key.
  - Bindings stay in the manifest.
  - Elden Parry's window moved out of the manifest; an L1 test refuses a key that has both homes.
  - stack.py re-stages only rows that have db settings.
- **The GMSTs go into 1.5-build's `game_setting` table**, one home with a child table `game_setting_combat`; there
  is no second GMST writer.
- **The formid CHECK now admits engine-named GMSTs.** Both lanes' new GMSTs (fDiffMultHP*, fXPPerSkillRank) failed
  without it.
- **Carriers use Multiply 1 + AV Mult**, so an unwritten AV leaves damage unchanged.
  - Mutagen 0.54.4 cannot name the limb AVs 46–52, so the av-audit order skips to the skill-advance AVs.
- **Mitigation is applied at the reference blow 24.** This loses at most 5.6 pp at AR 100 against a 92-damage blow
  (the table is in the spec).
- **The archetype is compiled (P5).** It has fixed level 10 and an ECZN with min = max = 10. Its own perk carries
  ×1.3333 damage and ×0.826 incoming. Its face is a Traits template of a vanilla Imperial male (0014 §3).

## Evidence

- `pytest tools/argonia_world/tests/test_combat_records.py`: 6 passed.
- `db check`: 557 tables green.
- make plugin-check: regenerate twice identical, Spriggit round trip byte-identical.
- make check: CHECK GREEN, 265 passed.
- stack.py apply_ini, run on staged copies of tk-dodge-re-addon and elden-parry, wrote fDodgeCost 15.0,
  fIFrameDuration 0.3 and fParryWindow 0.02/0.2.

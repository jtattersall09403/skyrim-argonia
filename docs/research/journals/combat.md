# Journal: combat (chunks 1.6, 1.7, 2.7)

This journal records what was tried, measured and learned for the combat stack and its wiring to the sheet, so
nothing is lost at a hand-off. The design of record is `docs/research/2026-10-30/combat-wiring.md` (1.6's draft of
2.7 §a). The rows live in the world db (`combat_wiring`, `combat_carrier`, `combat_constant`, `combat_mod_setting`).
The owner's 0.0 play notes on combat feel are not in the repo yet. They are owed here when 1.7's duel runs.

## 2026-10-30: the wiring's state (lane core-wiring)

**What is built, by wiring row.** Every row below is L2-proved on the build VM. None is L4-proved, because the
game machine was another lane's and nothing was deployed.

| Row | Built where | L2 (ctest) | L4 owed |
|---|---|---|---|
| w.damage.position-strength (VoicePoints = P × S − 1; bow P − 1) | `skse/core/src/combat.cpp`, `ArgoniaCore/src/combat.cpp` | `core.combat` the_spec_table (the five builds within 5e-4 of the spec's table) | fight-damage-builds |
| w.stamina.power (VoiceRate = stamina × − 1) | same | the_spec_table | fight-damage-builds |
| w.armour.mitigation (Energy = −mitigation(AR, 24)) | same | armour_and_mitigation | fight-damage-builds |
| w.guard.stability (OneHandedSkillAdvance = stability − 1) | same | armour_and_mitigation | fight-archetype |
| w.damage.vanilla-skill (OneHanded, TwoHanded, Marksman base 0) | same | pinned_skills_are_never_mirrored | fight-damage-builds |
| w.roll.tier (no roll when overloaded) | TK Dodge's own perk lock: `bUsePerkLock = true` (combat_mod_setting) and ArgoniaCore gives or takes `sDodgeRequiredPerkID` by tier | roll_lock | fight-roll-burden |
| ARG_Perk_Carriers on the player | `EnsurePerks` (engine.cpp), with the rest intercept | none (an engine call) | fight-damage-builds step 0 |

- **When the values are written.** A pass runs on game ready, equip, a carried-item change (the burden tier), a skill
  rank, an attribute change and the sitting's close. It runs on the main thread through SKSE's task queue. The log
  line is `combat: carriers (<why>): burden <tier>, AR <x>; <AV>=<value> ...`, and it is written only when the values
  change.
- **The carrier names come from the db.** `core_tables.py` now writes `tables_combat.h` from `combat_carrier` and
  `combat_constant`. A new wired row with no formula in `carrier_value` fails `core.combat`, so it never stays
  neutral without notice.
- **The roll lock is the least invasive one.** TK Dodge RE Addon already has a "dodging requires a perk" option. Its
  DLL's strings show `bUsePerkLock`, `sDodgeRequiredPerkID = "TKDodgeAddon.esp|0x809"` and "Dodge perk is: {}".
  ArgoniaCore reads the staged `Data/SKSE/Plugins/tk-dodge.toml` at data loaded, so it follows whatever perk the
  mod is configured with. So there is no input filter, no behaviour edit and no hook. **The DLL and the restaged
  toml must go together.** With the lock on and no ArgoniaCore, no tier can roll.

**Found and fixed on the way (review of 1.5 and 1.6):**
- `life.cpp`'s skill mirrors used the menu names `Archery` and `Speech`. The engine's actor value names are `Marksman`
  and `Speechcraft`, so `LookupActorValueByName` returned none. Two skills were never mirrored and never had their
  vanilla gain zeroed. Fixed, and test_life refuses the menu names.
- Marksman was mirrored from our Marksman skill, but the wiring pins it at 0 (Skyrim's skill damage term must stay
  neutral). The mirror is removed, and a test checks that no mirror writes a pinned skill.

**Losses, stated:**
- **AR is only the Unarmored term until the item rows carry a rating.** Our ARMO records have rating 0 (w.armour.vanilla),
  and `item` has no armour-rating column yet. So `Energy` reflects Unarmored only (0.0065 × skill² for each of the 4
  slots that no piece covers). A borrowed vanilla piece reads its own rating. This is owed to 2.7's data, as a column
  the adapter reads instead of `GetArmorRating()`.
- **Effects are not in the pass.** `Effective::of(sheet)` is used until the effect stack lands (2.1). A fortify or
  drain changes no carrier yet.
- **Item soft requirements are 0.** `requirement_shortfall` is 2.7's.
- **Medium armour has no marker**, so it counts as clothing (1.5's loss, carried here).
- **Skyrim's own Block skill term.** Vanilla blocking also scales with the Block actor value, which is still mirrored
  from our Block skill. Whether that doubles with `body.block` is an L4 question for fight-archetype. If it does,
  Block joins the pinned list.

**Next:** game-5 deploys the DLL and restages tk-dodge-re-addon. Then fight-damage-builds and fight-roll-burden run
at L4 from `bat duel-ring`.

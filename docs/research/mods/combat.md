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

**The /code-review pass** (high; 1.5's, 1.6's and this lane's commits, 48c12a6..2bf575c) gave 10 findings. 8 are
fixed, each with a test where its logic sits:
- **Spell and unclassed-weapon hits trained Hand-to-hand**, because `hit_dealt(nullopt)` means fists. Fixed by
  `life::blow_skill` (a non-weapon or an unclassed weapon trains nothing), tested in core.life.
- **Armour counted pieces, not slots**, so a shield used up a slot. Fixed: `Piece::covers` is a slot bitmask, and
  core.combat tests the shield, the overlap and the full set.
- **A borrowed vanilla piece's rating counted twice**, once by the engine and once by the carrier. Fixed:
  `raw_rating` is 0 until our data holds one.
- **The hit and the carriers walked the armour separately**: now one walk, through `WornPieces`, `life::worn_of`
  (tested), and one shared `AvNamed`.
- **WriteCombat is coalesced**, so Take All queues one task, not one per item.
- **HealthWatch was not cleared at a rest**, so the first hit after it read 0. **ResetActors** used SetPosition (no
  cell change, the living stayed hurt). It now uses MoveToEditorLocation and restores the pools. These two are
  engine calls, so their proof is L4 (die-and-recover, grow-at-rest).
- **The engine save points are SkyrimPrefs.ini settings.** They are now looked up in INIPrefSettingCollection first,
  and a miss is logged (L4: rest-is-the-only-save).
- **The camp spot was invisible.** `bedrollground.nif` is a marker only. It is now `bedroll01.nif`
  (life_records.py), and test_life_records refuses the marker.

Not changed:
- **`view.close` for the sitting.** The schema's ViewId has no `sitting`, so that intent cannot be decoded. The
  sitting closes by `sitting.done` (its Escape).
- **Block, HeavyArmor and LightArmor mirrors and Skyrim's own terms.** The armour half is closed by the 0 raw
  rating. Block is the L4 question below.

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

## 2026-10-30: the combat trial, A against B and B2 (lane combat-trial-prep)

The owner asked to try Dark Souls Combat SE (Nexus 28567) as group B. The research is
`docs/research/2026-10-29/combat-mod-28567.md`. This section is the trial plan. The game lane runs it in one slot
and fills in the table. Neither B nor B2 ships: its i-frames are Papyrus waits, and it runs scripts on every
actor. The trial decides which of DSC's rules (the poise pool, the weight bands, counter damage) 2.7 builds in
`ArgoniaCombat` from DSR numbers.

**What is ready (L1, build VM):**
- **The sets are data.** `data/dependencies.json` has `combat` sets `souls-0.0` (A, the default), `dsc-b` and
  `dsc-b2`. DSC's archive sha256 `ca203060…` matches. Its row drops `sound/fx/bb_dsc*` (7 Dark Souls audio rips) at
  stage, and the stage prints the count.
- **The per-set settings are written into the staged plugin.** `plugin_values` writes them into the staged
  `Dark Souls Combat.esp` (decision 0014: made at install, never shipped). B: `RollKey` 277, the pad's B. The mod
  registers only LAlt, so out of the box a pad never rolls. B2: `BB_Poise_VarCritsAllowed` 0 and `RollKey` 0, so TK
  Dodge alone rolls. Both: `BB_Poise_VarDebugTrace` 1. Poise is a script variable, and DSC's Papyrus log is its only
  read. The script reads the globals only every fifth update, so they cannot be set at scene step 0.
- **DSC's quests stay running.** `BB_Poise_GivePlayerAbilityQuest`, `BB_RollCameraQuest` and `BB_Poise_ConfigMenuQuest`
  are on `data/quarantine/allowed-quests.json`. A shelled roll quest would break every poise monitor too.
- **The switch.** Dry-run on the build VM: `stack.py combat A B B2 --dry <scratch>` staged the combat group only.
  - A: 22 rows, 6,357 files.
  - B: 9 rows, 3,982 files. 14 A rows out (TK Dodge, Dynamic Dodge, i-frame generator, Elden Parry and Rim Parry
    with patches, Modern Stagger Lock); DSC in, with 53 files and none under `sound\`.
  - B2: 22 rows, 6,256 files. A without Modern Stagger Lock, plus DSC.
  - Staging A again gave A's first file set exactly. A second stage of the same set restaged nothing.
- **Pandora cannot be checked on the build VM.** It is a Windows-only exe (decision: no Wine).
  `stack.py pandora-check` runs on the machine after Pandora and reads three things:
  - Pandora's engine log for `BBDarkSoulsCombat`;
  - the generated behaviours for 5 DSC events: 3 rolls, and the 2 paired (`pa`) killmoves, which are the known risk;
  - the animation data for DSC's clips.

  `stack.py combat B|B2` runs the check after install. If the roll events are missing, B is dead.

**The steps (game lane, one slot):**
1. `stack.py combat B2`. The result must say `PANDORA-DSC OK`. Then run `run_journey.py tests/journeys/combat-trial-b2.yaml`
   and fetch `Papyrus.0.log` beside the report.
2. The same for `combat B` with `combat-trial-b.yaml`.
3. `stack.py combat A` and `combat-trial-a.yaml`. This also restores the base stack, and `stack.py verify` must say
   VERIFY OK.

The base save is made under A and is never saved over. A save under B holds DSC script instances.

**Owed by the runner:**
- `parry-riposte` is `owed` in all three journeys. pad.ps1 holds only sticks across steps, but a bash needs L1/L2 held
  while R1 taps. The fix is a held trigger (`+LT=1`), and the step names the sequence.
- The opponent is `actors 3000`'s first listed actor. If duel-ring lists another actor first, use a nearer radius.

**Known before it runs (static):**
- **DSC's pad direction.** It reads W/A/S/D with `Input.IsKeyPressed`, so on a pad every roll may be the backstep. Each
  roll step keeps the player's position before and after.
- **DSC's band edges** are roll weight against max stamina: fast ≤ stamina/8, mid ≤ stamina/4. The load steps keep
  stamina and the carried weight. DSC counts our steel set as poise 25: the int weights 12+3+2+3+3+2, with shields
  ignored.
- **Recovery is +20 poise every 3 s**, so the full set may never stagger against the deserter. That would be a finding,
  not a failure.

**The verdict table (fill with numbers from the three reports and the Papyrus logs):**

| Measure | A | B | B2 | Source |
|---|---|---|---|---|
| Pandora: DSC events in the behaviours (rolls / paired) | n/a | | | pandora-check |
| Hits to stagger, naked / full steel (poise 0 / 25) | | | | poise steps: hit events, the log's "current poise" |
| Roll distance fast / mid / fat, forward (units) | | | | roll steps' `call: [player]` |
| Roll direction honoured on the pad (4 of 4?) | | | | roll steps' positions |
| Backstab: power hit from behind lands / killmove plays | | | | backstab steps |
| Parry into riposte, riposte count (B2: exactly 1) | | | | parry-riposte (owed: held trigger) |
| Papyrus stacks: start / 5 fighters / settled; overstressed | | | | ready, script-load, settle |
| Owner's feel (L6, packet) | | | | owner |

What decides it:
- **B is out** if Pandora drops its rolls, if the pad cannot roll in all four directions, or if the queue grows
  under 5 fighters without draining.
- **B2 is the candidate** if its poise staggers by worn weight and one riposte plays: the rule set to port.
- **A stays** if B2 adds nothing over A's stagger. Either way, the numbers DSC uses are not DSR's (decision 0004).

## 2026-10-30: A restored exactly; DSC's engine fallback tried (lane game-11)
**A's 20 bad files.** `stack.py verify` after game-10's B/B2 -> A switch: 20 *missing*, every one with a CJK name:
rim-parry's `... - 副本.wav` copies and the `.hkx` and `.xlsm` files under openanimationreplacer (all in rim-parry's
staged tree). Windows `tar` converts each pax UTF-8 name through the ANSI code page (1252) and skips one it cannot
convert ("Archive entry has empty or unreadable filename ... skipping", exit 1, which the push ignored). Proved on a
two-file tar: `°` laid, `副本` skipped. Fix (3fea556): names that are not ASCII go in a zip that .NET's ZipFile
unpacks, since it honours the UTF-8 flag; tar's exit code is checked; a test is in tooling/tests/test_stack_push.py.
rim-parry re-pushed: **verify 0 bad, 0 unrecorded** (22,573 files; tk-dodge.toml matches too).

**A plays, once the roll perk is granted.** After the restore, combat-trial-a failed at pandora-wired (moved 0) and
smoke's roll saw no TKDR_DodgeStart. ArgoniaCore logged "the sheet is uninitialised, no carrier is written". The
base save starts with `coc` from the main menu, which sends no kNewGame, so NewCharacter (e668b08) never ran. No
roll tier was set, and TK Dodge's perk lock (bUsePerkLock, TKDodgeAddon.esp|0x809) refused every roll. With
`player.addperk FE00D809` added by hand, smoke's roll passed (> 300 units). fixes-2 fixed it at source in 2dab64e
(the character is made at game ready). That fix has not been deployed or re-proved in game yet. combat-trial-a's own
pandora-wired step (stick held 300 ms) moved 11 units with the perk; smoke's roll (500 ms) passed. Re-run trial-a
after the deploy.

**DSC through Nemesis (0.2's named fallback): no wiring so far.**
- Nemesis Unlimited Behavior Engine v0.84-beta (Nexus 60033, GPL-3) is a B/B2-only tool row.
- `stack.ps1 nemesis` lays its engine into `Data\Nemesis_Engine`, but not its 16 bundled patches, one of which is
  `mod\tkuc`. It turns 197 behaviour and animation-data files in Data from hard links into copies, so it never
  writes through into a mod. It runs `-update`, then `-generate <our 9 codes>`.
- On the machine (B2 laid):
  - `-update` **crashed** (exit -1073741819, 0xC0000005). The last UpdateLog line was "New Animations extraction
    start (Folder: behavior templates\b\behavior)", the FNIS `b` template, where DSC's 30 `b` lines would be read.
  - `-generate` **hung** at 0 CPU until its 900 s limit, and wrote no behaviours.
- DSC's shipped hkx files are SE packfiles (hk_2010.2.0-r1, 8-byte pointers), so the format is not the cause.
- Pandora 5.0.0-beta's FNIS parser (its source, read by a research agent; tag v5.0.0-beta) needs both
  `animations\<folder>\FNIS_<folder>_List.txt` and `behaviors\FNIS_<folder>_Behavior.hkx` in the real Data. It drops
  annotations (TSprintStop, TWeapEquip), and its paired (`pa`) case is commented out.
- **Owed before the verdict:** one Pandora run on the B2 Data, reading its "FNIS Parser ... BBDarkSoulsCombat" lines.
  It was cut short when the machine was stopped for the owner. Then FNIS for SE (Nexus 3038; no documented
  unattended mode, and it would replace the Nemesis-format behaviours that TDM, TK Dodge and the rest of the stack
  need), or the verdict "DSC not viable on this stack".

| Group | Engine | DSC events | Journey | Verdict |
|---|---|---|---|---|
| A (0.0 stack) | Pandora | n/a | smoke roll ok with the perk; trial-a owed after 2dab64e's deploy | restore exact (verify 0 bad) |
| B (DSC) | Pandora (game-10) | all MISSING | scene load failed | dead at Pandora |
| B2 (DSC, crits off) | Pandora (game-10) / Nemesis (game-11) | all MISSING / update crashed, generate hung | not run | not wired; Pandora's parser lines owed |

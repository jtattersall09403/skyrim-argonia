# Parry, riposte and backstab for the 0.0 combat test (Skyrim 1.7.104.0)

Research date 2026-10-29, for chunk 0.0 §d. Sources: Nexus API v1 (files, changelogs, content previews) and v2
GraphQL (requirement lists), read with our Premium key; GitHub API; the archives' file lists. Two small GitHub
release archives (MaxuBlockOverhaul, ModernStaggerLock) and two Precision toml patches were downloaded to the
scratchpad and inspected only.

**Prior art:** `docs/research/2026-10-27/skyrim-combat-traversal.md` (§1 combat table, §3 verdicts) listed the
same candidates. Its gap was versions. The old project
(`jtattersall09403/elder-souls-argonia`, decision 0040) credits **Rim Parry and Execution** for PARRY, RIPOSTE,
GREATSWORD/GREATAXE_RIPOSTE and BACKSTABBED_FORWARD. The owner confirmed that is the mod to use. This report checks
it and everything it needs against 1.7.104.

The gate (from `docs/research/2026-10-28/stream-and-combat-stack.md` §2.1): SKSE 2.3.1 on 1.7.99+ disables any
address-library DLL built before 2025-05-26 without the new flag. So every DLL below is either a rebuild from
after 20 Aug 2026, or the mod has no DLL.

## Recommended set (add to the current stack)

One coherent set: **Rim Parry and Execution** with **Elden Parry** as its parry engine. Elden Parry gives a real
timed window. Rim Parry adds the riposte (its "execution") and the backstab.

| # | Mod (Nexus SSE id) | File id, name, version, date | Why 1.7.104 is OK | Role |
|---|---|---|---|---|
| R1 | Rim Parry and Execution (114366) | **499427** "00 Rim Parry Stand Alone - v1.1 Update" v1.1, 2024-05-09 | **No DLL.** OAR animations, an ESP, 11 small `.pex` scripts, Payload Interpreter configs, SPID ini | parry animations, riposte, backstab |
| R2 | ↳ "02 Rim_Parry_Elden Parry_patch SA ver" (114366) | **499429** v1.1, 2024-05-09 | ESP + ini only | hands the parry to Elden Parry |
| R3 | Rim Parry v1.1 CTD fix (114366's author's fix page, 143312) | **600715** v1.1, 2025-03-02 | ESP only; **replaces** `RimExecutionHitSA.esp` | fixes a start-up crash in v1.1 |
| R4 | Rim Parry - One Parry Patch (164526) | **687622** v1.0, 2025-11-15 | OAR condition files only | **one parry opens the riposte, as in DS1** (default is two) |
| R5 | Elden Parry (70240) | **304517** "Elden Parry AE" 1.3, 2022-08-04 | original DLL will **not** load; install for its ESP, ini and sounds, then R6 | timed parry |
| R6 | dTry Plugin Updates (85740, doodlum) | **793442** "Elden Parry" 1.7.99, 2026-08-22 | CommonLibSSE-NG rebuild "with support for 1.6.1170 and 1.7.99" (source doodlum/EldenParry, GPL-3.0). Overwrites `EldenParry.dll` | Elden Parry on 1.7.x |
| R7 | Elden Parry Precision Fix (188223) | **789181** v1, 2026-08-13 | toml only. Diffed against Precision 2.0.6's own `Precision_base.toml`: it only removes the light-bash collisions and `bashStart` | stops Precision giving bash a vanilla hit, which would bypass the parry |
| R8 | Payload Interpreter (65089) | **394150** v1.1.0, 2023-06-02 | its DLL will not load; install, then R9 | Rim Parry's execution triggers |
| R9 | Payload Interpreter - 1.7.104.0 Update (192679) | **809282** v2, 2026-09-22 | NG rebuild for 1.7.104 (MIT); overwrites the DLL | |
| R10 | BDI's "Payload Interpreter - Nemesis Less Patch" (78146) | **328880** v1.0, 2022-11-04 | one BDI json (`SKSE/Plugins/BehaviorDataInjector/PayloadFramework_BDI.json`), no DLL. Use with our BDI Universal Support (78159 / 794609) | Rim Parry: "Without these two the Execution can't be triggered" |
| R11 | Modern Stagger Lock (GitHub only; **not** Nexus 151478, which is a different mod) | GitHub `SkyHorizon3/ModernStaggerLock` release **`v1.07a-1.7.99+`**, asset `Modern.Stagger.Lock.1.07a.7z`, 2026-10-27, MIT | full package, with the DLL rebuilt 2026-10-27 ("add support for 1.7.99+"). It is a fork of max-su-2019's repo. Alternative: max-su v1.07a + Nexus **195580 / 821402** (DLL only, 2026-10-17) | hard requirement: "Execution can't work without it" |
| R12 | MaxuBlockOverhaul (GitHub only) | `max-su-2019/MaxuBlockOverhaul` release **v0.24**, asset `MaxsuBlockOverhaul-V0.24a.7z`, 2025-02-17, MIT | **no DLL**: a Nemesis patch plus OAR animations (86 files) | block-hit animations ("won't work without it"); cosmetic, not needed for parry or riposte |
| R13 | dTry's Key Utils (69944) | **292793** "dTry's Key Utils AE" 1.1, 2022-06-21 | its DLL will not load; install, then R14 | listed requirement |
| R14 | DtryKeyUtil-1.7.104-Patch (189573) | **794857** "DtryKeyUtil 1.7.99 Compatibility Patch", 2026-08-25 | recompiled DLL for 1.7.99 and 1.7.104 | |
| R15 | Spell Perk Item Distributor (36869) | **795621** v7.3.3, 2026-08-26 | changelog: "Updated for 1.7.79 [sic] … Migrated to CommonLibSSE-NG", built after 1.7.99 shipped | hands out Rim Parry's perk (`RimParryPerk_DISTR.ini`) |

**Already in the stack and required by Rim Parry:** OAR (92109), Precision (72347), TDM (51614, a hard requirement
because parry and execution need a lock-on), IFrame Generator (82737), AMR (191697 port), BDI (78159), Pandora.

**Left out on purpose:**
- Elden Rim - Weapon Arts (65625) and Rim Parry's "01 … Elden Rim_patch": the Stand Alone file carries the
  system itself.
- Dual Wield Parrying SKSE (85505): only for dual-wield and unarmed blocking. On 1.7.104 it would need
  196543's in-memory runtime patch.
- Dual Wielding Unlocker (85814): dual daggers only.
- "Precision Elden Parry Compatibility toml" (91508): a 2023 copy of Precision's toml. R7 does the same job
  against the current toml.

## Controls (Skyrim defaults with this set; third person)

| Action | Keyboard + mouse | Xbox pad |
|---|---|---|
| Lock on (required first) | middle mouse (TDM `uTargetLockKey = 258`) | tap the right stick (R3) (TDM `fTargetLockThumbstickTapDuration = 0.15`) — **verify** in TDM's MCM |
| Block | hold right mouse | hold LT |
| **Parry** | hold block, **tap** left mouse (a light bash) just as the enemy's blow lands | hold LT, tap RT, timed the same way |
| **Riposte** | after a parry the enemy kneels; within 120° in front (or 60° behind), press **left mouse** (right attack) | RT |
| **Backstab** | locked on, within **60° behind** the enemy, light bash (hold right mouse + tap left mouse): the enemy is knocked down; then left mouse executes | LT + RT, then RT |

- **Parry timing.** Elden Parry's light bash has no hit frame. A parry happens only if you are hit between
  `fParryWindow_Start` and `fParryWindow_End` seconds into the bash. Rim Parry says Start must be above 0, and its
  author uses Start = 0.02 and End = 0.2. These are stock values for the feel test, not our numbers (decision 0004).
- **Backstab.** It works on aware enemies (there is no sneak condition), as in DS1. It takes two inputs (bash, then
  attack), not DS1's single R1.
- **What can be ripostes.** Humans and draugr only ("Parry attack from the NPC or Draugr"; backstab is "the NPC or
  Draugr"). The Embershard bandits qualify.
- **Third person only.** The archive has no `_1stperson` paths. That suits the owner, who plays only in third person.
  Elden Parry works in both views.

## Install notes for the stager (`combat_test_stage.py` / `combat-test-mods.json`)

1. **Order (later wins):**
   1. the current stack;
   2. Elden Parry 304517, then 793442 (DLL);
   3. Precision 2.0.6, then 188223 (toml);
   4. PI 394150, then 809282 (DLL), then 328880;
   5. dTry Key Utils 292793, then 794857 (DLL);
   6. SPID 795621;
   7. MSL (GitHub);
   8. MBO (GitHub);
   9. Rim Parry 499427, then 143312 (overwrites its ESP), then 499429, then 164526.
2. **Plugins to enable**, in this order: `EldenParry.esp`, `Keytrace.esp`, `RimExecutionHitSA.esp` (the CTD-fix
   copy), `EREP_patchSA.esp`. Precision's ESP is already enabled.
3. **No FOMOD choices.** Every file above is a plain archive. dTry Plugin Updates is per-plugin files, so take
   only 793442. Precision keeps its current selection.
4. **Two sources are GitHub, not Nexus** (MSL and MBO). The stager needs a GitHub-release source, or uses the
   Nexus fallback for MSL (195580 over max-su's v1.07a, which is also GitHub-only). MBO is optional if that is a
   problem.
5. **Pandora must re-run.** New patches:
   - MSL `slmco` (human, draugr and falmer behaviours);
   - MBO `block`;
   - PI `evfmgo`.

   Rim Parry asks for the BDI route for PI, so either untick PI's `evfmgo` patch in `ActiveMods.json` or drop
   328880. Not both (**verify** which in Pandora's `Engine.log`). MSL asks for "Nemesis Creature Behaviour
   Compatibility" (45966) under Nemesis. Pandora's need for it is unverified. The test fights humans, so if the
   draugr or falmer part fails, it does not block.
6. **Drop on staging:**
   - Rim Parry's 208 `.bat` files inside OAR folders (inert);
   - its `Sound/.../新建文件夹` and `BEIFEN` ("new folder" and "backup") sub-folders, which are unused copies
     with non-ASCII names;
   - the 27 MB `ModernStaggerLock.pdb`.

   The longest path in the archive is 144 characters, which stays inside the 260 guard under a standard Steam Data
   path.
7. **Edit the Elden Parry ini.** In `SKSE/Plugins/EldenParry.ini` set `fParryWindow_Start = 0.02` and
   `fParryWindow_End = 0.2`, as Rim Parry requires.
8. **Check `skse64.log` after the first launch.** Each of EldenParry, PayloadInterpreter, ModernStaggerLock,
   DtryKeyUtil and SPID should say loaded, not "must be recompiled". The Elden Parry build says 1.7.99. 1.7.104 is
   **verify**, but the same NG builds of Ersh's and doodlum's mods load on 1.7.104.

## Conflicts with the current stack

- **SkySA.** Its DAR folders replace `*_blockbash*` clips and `1hm_recoil*` (priorities 3020–4060). Rim Parry's
  OAR folders sit at priority 2,130,000,016 and up, so Rim's bash and parry clips win. That is intended. Rim's
  `0LtStaggerREP` (1,091 clips) also takes stagger slots, and its author warns it "takes a lot of OAR priority".
  **Verify** that SkySA's attack recoils still play. Elder Souls - Sword has no bash or block clips.
- **DMCO / Dodge Framework NG.** No conflict. MSL ships `DMCO_MSL.json` (`QuickRecoveryEvents: ["Dodge"]`), so a
  roll cancels a stagger lock. That suits the owner's test.
- **Precision.** It is required. R7 is needed, or Precision's own bash collision staggers without a parry.
- **TDM.** It is required. Rim also suggests setting TDM's Missile Aim Mode to "Predictive".
- **OAR-added Stamina Cost.** No overlap found. A successful Elden Parry costs no stamina by default
  (configurable in its ini).
- **Rim's own list** of incompatibilities: Disable NPC Taunt, Impactful Blocking, Dynamic Grip MCO. None of these
  are in the stack.
- **Valhalla Combat is not added.** It has its own timed and perfect block and its own stamina system. The page
  says to run only one timed-block system and one stamina system. It would fight Elden Parry and DMCO's stamina.
  It would also take TrueHUD's special bar (which clashes with Poise mods). Its executions need a stun-depleted
  enemy and a bound key, and its back-side killmove has a known bug (fix: 97195).

## Licences and permissions (private install only; never redistributed)

- Rim Parry: Nexus permissions were not readable through the API. It is installed on our test machine only, never
  committed (decision 0003).
- Elden Parry: the update is GPL-3.0 (doodlum fork); D7ry's upstream has no licence file.
- MSL, MBO, Payload Interpreter, SPID: MIT.
- Valhalla Combat (if ever used): BSD-3-Clause.
- Rim's execution animations are based on Elden Rim's, which is a Chinese community moveset. Decision 0004 covers
  Argonia, not this stock test. The old project's use of these clips is a separate question for later chunks.

## Candidates checked and their status on 1.7.104

| Mod (id) | Main file (date) | 1.7.104 build? | Verdict |
|---|---|---|---|
| Rim Parry and Execution (114366) | 499427 (2024-05-09) | no DLL | **use** |
| Elden Parry (70240) | 304517 (2022-08-04) | yes, via 85740 / 793442 (2026-08-22) | **use** (with R6) |
| Elden Counter (65579) | 2022 | yes, 85740 / 794613 (2026-08-24) | usable; a guard counter, not needed |
| Valhalla Combat (64741) | 342628 v1.3.3 (2022-12-21) | yes, two ports: **191704 / 806722** "V1.3.5 AE 1.7.104.0" (2026-09-17, full replacer, BSD source) and **190197 / 815324** v8 (2026-10-06, DLL only, GPL) | usable; **not chosen** (overlaps) |
| zxlice BackStab and Parry (43436) | 178759 (2021-01-10) | **no** rebuild found | **NOT usable** |
| Blade and Blunt (34549) | 799519 v4.0.3 (2026-09-03, "Updated for 1.7.104") | yes | usable; systemic rebalance, no riposte or backstab |
| Dual Wield Parrying SKSE (85505) | 484090 (2024-03-25) | only via 196543 in-memory patch (2026-10-23) | not needed |
| Critical Hit - Backstab and Parry (17400) | 2018, "Unsupported" | no | **NOT usable** |
| Ultimate Combat | NG DLL update 163377 (2026-08-23) exists, 1.7 support unverified | ? | legacy; not built on (prior art) |
| Simple Elden Counter NG (169450), Stance-broken Execution (164374), Posture and Execution for Simple Timed Block (164288), Parry for all (167873), Timed Block-Dodge and Counter (181239) | 2025–26 | not checked (the brief keeps us to Rim Parry's set) | — |

## Open checks (in game, L4, at the `ArgoniaBanditCamp` save)

1. `skse64.log`: all five new DLLs load.
2. `Engine.log`: MSL, MBO and PI/BDI patches are accepted, and SkySA's patch is still accepted.
3. A timed light bash against a bandit's swing staggers them and gives the kneel (One Parry Patch), and attack
   then plays the riposte.
4. A bash from behind within 60° knocks them down, and attack then executes.
5. SkySA's recoils and Elder Souls' swings are unchanged, and DMCO's roll still cancels stagger.

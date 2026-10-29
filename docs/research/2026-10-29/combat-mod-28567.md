# Dark Souls Combat SE (Nexus 28567) as combat group B

Research 2026-10-29 for the owner's trial request. Sources: Nexus API v1 (mod, files, download link), the downloaded
archive (inspected in a scratch folder, never committed: decision 0003), its `.psc` sources and `.esp` records
(parsed), Pandora's README and releases, the stack docs. Nexus comment tabs return 403 to our fetcher, so no user
bug reports were read; every compatibility claim below is **static analysis, not observed**, and says so.

## Live docs that cover this

- `docs/research/2026-10-28/stream-and-combat-stack.md` (stack choice) and `docs/research/2026-10-29/parry-riposte-backstab.md`
  (Rim Parry + Elden Parry set): confirmed as the description of group A (`infra/gpu-box/combat-test-mods.json`,
  `data/dependencies.json` rows with `"set": "souls-0.0"`).
- Contradicted/superseded: stack doc "FNIS is not used" holds for A only. DSC ships FNIS-format animation lists;
  Pandora's README says it "supports the patch formats of both Nemesis ... and FNIS" (line 16), so B needs Pandora's
  FNIS path, which A never exercises.
- Contradicted: `1.6` says "TK Dodge RE's tiers mapped to ours". The TK Dodge RE page (56956) lists one roll with one
  `iFrameDuration` INI value, no weight tiers; Dynamic Dodge (79598) is weapon-specific, not weight-specific. Burden-tier
  rolls are not shown to exist in A. DSC has them.
- **The one doc to edit:** `docs/phases/2-slice/2.7-combat.md` §0 (the combat map): add group B as a candidate source for
  the poise, roll-band, parry, riposte and backstab rows. Set rows go in `data/dependencies.json` (existing `sets`).

## 1. Facts

| Item | Finding | Evidence |
|---|---|---|
| Name, author | Dark Souls Combat SE by TheDriedFinger; SE port uploaded by Ryuz4kii | API `name`, `author`, `uploaded_by` |
| Version, date | 1.5.3, uploaded 2019-08-26, one file (104449, 880 KB, rar); never updated on SE; original Skyrim LE mod dated 2015 | API files list; `updated_time` = `created_time` |
| Maintained | **No.** Last change 2019; the port's author asked the original author for leave (description line 1). Version history ends at v1.5.3 | description |
| Permissions / AI clause | **Owner-confirmed 2026-10-29: fine for our use.** Not investigated further, per ruling | coordinator message |
| Binary type | **No DLL.** `Dark Souls Combat.esp` (24.8 KB, 105 records, master Skyrim.esm only), 9 `.pex`+`.psc`, 36 `.hkx`, FNIS list + FNIS behaviour `.hkx`, 6 `.wav` | archive listing; `parse.py` over the ESP |
| Runtime | Runtime-independent (no address library). Needs SKSE only for `RegisterForKey`, `Input.GetMappedKey`; SKSE 2.3.1 provides both. `.hkx` headers are 64-bit packfiles (8-byte pointers) = SE format. **Works on 1.7.104: VERIFIED by construction, PARTIAL until an L4 run** | archive header bytes `08 01 00 01` |
| Record conflicts | **None.** No GMST, no override of a vanilla record: only new KYWD/GLOB/MGEF/SPEL/QUST/PERK/IDLE/FLST/SNDR | ESP record census |
| Requirements | SKSE, FNIS 5.5+, SkyUI (optional, for its MCM). Third person only; the author wants 40+ FPS | description |
| Pandora instead of FNIS | **PARTIAL.** Pandora reads FNIS lists (README:16). But the list uses `b -a,Tn,...` basic animations with `MD` motion data (covered by Pandora) and two `pa` (paired) killmoves; Pandora's README says paired support is limited to anim info, and its issue tracker has paired-FNIS parsing open. Expect rolls and backsteps to load, DSC's own riposte/backstab killmoves not. Not tested | `FNIS_BBDarkSoulsCombat_List.txt`; Pandora README and search result on its paired-animation issue |
| Bundled sound | `sound/fx/BB_DSC/*.wav` are Dark Souls rips (the readme links a Dark Souls audio extract). **Exclude the folder** at stage (decision 0004, 0003); the SNDR records then play nothing | `DSC Sounds.txt` |

## 2. Features and how each is done

| Feature | Implementation (file:line in `scripts/source/bb_poise_monitorpoisescript.psc` unless named) | Papyrus load |
|---|---|---|
| Poise pool | Sum of worn armour `GetWeight() as int`, shields ignored (`:325-364`); non-humanoids a flat per-type value (`:349-364`); max poise changes on equip events (`:393-448`) | per-actor ActiveMagicEffect |
| Poise damage | `OnHit` (`:588-760`): weapon weight x1.0 (x1.5 power attack), unarmed = gauntlet weight, arrows a flat value, x1.5 if the target is mid-attack ("counter"), blocked hits do none | `OnHit` on every actor in range |
| Poise refill, stagger | Global defaults: +20 per tick, tick 3 s (30 s when full), `VarPoiseRecovery`/`VarUpdateTime`; break at <0, then `StaggerStart`/`StaggerStop` via `Debug.SendAnimationEvent` with `Utility.Wait` (`:768-910`); max combo 3, then 2-3 s immunity spell | polling `OnUpdate` + waits |
| Weight bands | Roll weight = poise + held weapon/shield/torch weight: fast <= maxStamina/8, medium <= maxStamina/4, else fat (`:540-545`, `RollWeightToStaminaRatio` = 4) | recomputed on equip |
| Rolls | 4-way + backstep, 3 weights x (weapon / magic-out) = 30 clips; keyboard keys read with `Input.IsKeyPressed(Input.GetMappedKey("Forward"...))` (`:975`, `:1005`, `:1029`, `:1065`); tap of roll key (default LAlt, code 56); cost 15 stamina (`BB_Poise_RollStamina`) | key events, `Utility.Wait` spin loops |
| I-frames | **Papyrus**: `Player.SetGhost(true)`, `Utility.Wait`, `SetGhost(false)`. Fast ~0.6 s window, medium ~0.45 s (`:997-1004`, `:1146-1157`). Not frame-exact; a script stalled mid-roll could leave the player a ghost (inferred) | script-timed |
| Attack cancel by roll, stagger break-out | Roll before `preHitFrame` cancels; fast roll can end a stagger late in it (`RollStaggerCancelDelayPercent_*` 0.5/0.65/0.8) | 8 `RegisterForAnimationEvent`s (`:205-212`) |
| Bash parry | **Player:** `BB_Poise_ShieldParryPerk` (PERK, entry-point conditions) applies a "riposte-prep" contact spell on the bashed actor. **NPC aggressor:** `OnHit` with `abBashAttack`, target `IsAttacking`, facing 135-225 deg (`:604-612`). Parried actor ragdolls to bleedout state, `SetGhost`, takes x2 (`BB_Poise_VarCritDamageMult` 2.0) | spell + script per parry |
| Riposte | Front hit on a parried actor: `Aggressor.PlayIdleWithTarget(Kill1H/2H/H2H)` paired idle, damage via deferred kill, scaled by the skill (`bb_poise_riposteprepeffectscript.psc:21-104`) | script |
| Backstab | Only on a **power attack** from within `BackstabAngle` behind (`:596-602`): target down, x2, paired killmove, NPCs only | script |
| Counter damage | +50% damage dealt and taken while attacking, +50% poise damage (description) | |
| Stamina | Attack cost from held-item weight (`:520-530`), no regen mid-action, regen delay after roll/bash, zero stamina staggers the swing, crits fail at 0 | `DamageStaminaRate` spells + script |
| Settings | MCM (SkyUI `SKI_ConfigBase`, `bb_poise_configmenuscript.psc`, 448 lines) writing the 20 `BB_Poise_Var*` globals (poise recovery 20, update 3.0, attack mult 1.0, power 1.5, max combo 3, stagger level 3, crits on, creature ripostes off) | MCM |

Papyrus risk (decision: logic stays out of Papyrus). This is the worst case in our stack: every actor near the player runs
a monitor effect (cloak ability, `BB_Poise_CloakAddAbilityScript`), an `OnHit`, eight animation-event registrations, equip
events and a repeating update; the roll is a polled state machine with spin waits. The author says staggers may be "delayed by
a split second" and rolls "less responsive". It also fails 1.6's acceptance ("no growing script lag") by design risk, which
is why B is a trial and a fallback, never the shipped route.

Gamepad risk (new, **PARTIAL, unverified**): the gamepad branch (`GamepadUsed`, `:546-548`) still decides roll direction with
`Input.IsKeyPressed(Input.GetMappedKey("Forward"...))` (`:1126`, `:1158`). A thumbstick is not a key, so a pad roll may always
backstep. The owner plays on a pad through the stream, so this is the first L4 check.

## 3. Direct answers

**Q1. Can it replace our planned poise and roll-band work? PARTIAL: it can prototype them, not replace them.**
- Poise: structure yes (armour-weight pool, weapon-weight damage, refill, stagger tiers), numbers no. Poise is integer
  armour weight, not a per-piece DS1 stat; damage is weapon weight, not per-attack; no hyper-armour; no armour-skill
  position (2.7 §a). Tunable only through the 20 globals. Armour weight would carry poise, roll band and our burden
  (carry 30+3xStr): one field doing three jobs.
- Roll bands: three bands with different speed, i-frames and recovery (the thing A lacks), but the thresholds use
  max stamina (stamina/8, /4), not our fraction of carry capacity (0.2 / 0.35). The i-frame lengths are Papyrus waits, which
  breaks "fix timing on the animation side".
- Item-details UI: the mod exposes **no API**. Current poise is a script variable; max poise = sum of worn weights is
  computable from records in our own core, and the band edges follow from max stamina. So the UI can show those two derived
  numbers without the mod; it cannot show live poise.

**Q2. Combine with Dynamic Dodge 79598 / TK Dodge RE for 8-way? YES for the hybrid (B2); NO within one roll.**
- DSC's rolling can be switched off (MCM "Roll Key" set to an unused key; `UnregisterForKey`, `bb_rollcameraquestscript.psc:51-63`,
  description "Rolling can be disabled"). Then TK Dodge RE + DDA (8-way; 79598 says 8-way needs dTry Key Utils, already in the
  stack; with TDM's Combat 360 Movement on, 8-way only when locked on) own the roll.
- DSC's weight bands and 4-way clips cannot become 8-way without new animation files and a rewritten Papyrus roll. So
  weight bands + 8 directions together = new work, not a mod pairing. With both enabled the two systems fight over the roll tap.

**Q3. Rim Parry and Execution's parry/riposte alongside it? YES, by switching DSC's crits off.**
- `BB_Poise_VarCritsAllowed` = 0 disables DSC's backstab and riposte prep (`:596-612` is gated on it). Rim Parry (OAR clips +
  Payload Interpreter, no paired-idle dependency) plus Elden Parry's timed window then own parry, riposte and backstab.
  This is "best of each": DSC's poise/stamina/counter layer under A's parry stack. This also avoids Pandora's weak paired
  support. Remaining overlap to test: DSC's shield-parry PERK (granted by quest `BB_Poise_GivePlayerAbilityQuest`) still modifies
  incoming damage on bash; set the global at scene step 0 (the console/SkyLink), since MCM is manual.

**Q4. Fallback and easy switch? YES.** Set swap is already in `infra/gpu-box/stack.py` (`--set combat=NAME`, `chosen()` at `:66`);
`stack.ps1 on` starts from bare Data each time, which is the exact undo. Caveat: a save made under B holds DSC script instances
(the mod ships an MCM "Uninstall"). The base save is made under A and never overwritten by B; B work saves elsewhere and is thrown away.

## 4. Known conflicts with the 0.0 stack (static analysis; no field report found)

| Mod | Expected | Basis |
|---|---|---|
| SkySA + Elder Souls | Probably fine. DSC cancels attacks with `AttackStop` and reads `preHitFrame`/`HitFrame`/`WeaponSwing`; SkySA emits standard events. Rolls cancel out of SkySA chains | `:205-212` |
| Precision | Likely fine: hits still arrive as `OnHit` (weapon form passed). Check that `akSource` is the weapon, else poise damage is 0 (`(akSource as Weapon)` gate `:649`). Pandora's Precision patch has a reported CTD with large graphs (search result) | `:649` |
| TDM | Roll direction is read from keys, ignoring TDM's camera-relative 360 movement and lock-on; rolls may go the wrong way. Same warning TDM gives TK Dodge | `:975` |
| TrueHUD | No clash (no special bar used); do not enable TrueHUD's special bar for poise (it was flagged against Poise mods in the parry doc `:131`) | parry doc |
| TK Dodge RE + Dynamic Dodge | Same tap on the sprint key; two rolls fire. In B2 set DSC's roll key to an unused key | A's config |
| Elden Parry | A parried hit may never reach DSC's `OnHit`, so DSC's parry does not trigger (good); the PERK overlap is the open risk | Q3 |
| Rim Parry and Execution | Double riposte if both active; solved by `VarCritsAllowed` = 0 | Q3 |
| One Click Power Attack NG | Fine: the backstab and the x1.5 poise hit key off the engine's power-attack flag | `:596`, `:668` |
| Modern Stagger Lock | Overlaps DSC's own combo cap; MSL hooks vanilla stagger, DSC forces stagger by animation event. Remove in pure B | design |
| MaxsuBlockOverhaul | Cosmetic block clips; keep | parry doc R12 |
| OAR-added Stamina Cost | Overlap on stamina; DSC attack costs can be switched off in the MCM (`BB_Poise_VarAttackStaminaCost`). Keep OAR's block/stagger costs, pick one for attacks | `:520-530` |

## 5. Trial profile "combat group B"

Rows in `data/dependencies.json`; the three groups are named sets on the `combat` group. `chosen()` accepts one string in
`"set"`, so shared rows must be **untagged** (always laid) and only the differing rows tagged. Retag: A-only rows keep
`souls-0.0`; B-only rows carry `dsc-b` / `dsc-b2`. (Alternative: let `"set"` hold a list; a small stack.py change.)

| Row | A (`souls-0.0`) | B pure (`dsc-b`) | B2 hybrid (`dsc-b2`) |
|---|---|---|---|
| precision, tdm, truehud, skysa, elder-souls-sword, one-click-power-attack, oar-stamina-cost, maxsu-block-overhaul | yes | yes | yes |
| tk-dodge-se, tk-dodge-re, tk-dodge-re-addon, dynamic-dodge, iframe-generator | yes | **no** (DSC rolls) | yes (rolls) |
| elden-parry, -1.7.99, -precision-fix, rim-parry, ctd-fix, elden patch, one-parry, bdi-payload-patch | yes | **no** | yes (parry/riposte/backstab) |
| modern-stagger-lock | yes | **no** | **no** (DSC poise) |
| **dark-souls-combat (28567, file 104449; prune `sound/fx/BB_DSC`)** | no | **yes** | yes |

Load order: DSC's ESP has only Skyrim.esm as master and overrides nothing, so any position works; place it last in the
combat group, after all combat rows. Run Pandora after laying (existing step); check the Pandora log for
`BBDarkSoulsCombat`. Optional: ESM-flag copy (description recommends ESM for script speed); our stage step could set the header
flag on the player's machine.

Switch: `stack.py install --set combat=souls-0.0` (A) or `--set combat=dsc-b` / `dsc-b2`; a thin `stack.py combat A|B|B2`
maps to those names. `stack.ps1 on` rebuilds from bare Data, so undo is exact; base save stays on A.

Per-set settings, applied at scene step 0 (not MCM): B2: `BB_Poise_VarCritsAllowed` 0, roll key to an unused key.
B pure: out of the box (the stated fallback).

## 6. L4 checks (from a scene on the base save)

1. **Pandora (L1, first):** engine log lists the DSC FNIS patch and 30 animations; the generated behaviour holds `BB_DSC_ForwardRoll_Fast`. If it fails, B is dead and only the A-side hybrid ideas remain.
2. **Poise break by weight:** same enemy hits a naked player vs a heavy-armoured player with the same weapon; read `GetWornForm` weights, count hits to stagger via a hit log. Pass: heavy needs more hits, ratio matches the weight sum.
3. **Bash-parry into riposte (B pure):** enemy swings, player bashes; read `IsInKillMove` and enemy health; a still per step. B2: same with Elden/Rim and DSC crits off; assert only one riposte plays.
4. **Backstab:** power attack from behind within `BackstabAngle`; enemy health drop and `IsInKillMove`.
5. **Roll distance (4-way B, 8-way B2):** pad and keyboard; log position before and after for each direction and band; assert distance and invulnerable window (`IsGhost` sampled). Include the pad-direction bug above.
6. **Script lag:** a 5-minute duel with 4 enemies; `Debug` stack dump or SkyLink script-latency read must not grow.

## 7. DS1 behaviour map, group A vs group B

| DS1 behaviour | A | B / B2 | Closer to DS1 |
|---|---|---|---|
| Poise (pool, break) | none in stack besides MSL cap | weight pool, tiers, refill | **B** (structure) |
| Roll i-frames by equip load | one value, one tier (TK Dodge RE INI) | three bands, Papyrus waits | **B** in structure; A in frame accuracy |
| Roll directions | 8-way (DDA) | 4-way | **A** |
| Backstep (no i-frames) | stationary step (DDA) | backstep, no i-frames (documented) | tie |
| Roll-cancel attack | TK Dodge | early roll cancel | tie |
| Parry window | Elden Parry timed window | bash during enemy attack, no frames | **A** |
| Riposte | Rim Parry via OAR | paired-idle killmove (Pandora-risky) | **A** |
| Backstab | Rim Parry; single press tweak open | power attack only | **A** |
| Stamina | OAR costs | attack, roll, bash regen delay | **B** |
| Stagger recovery / break-out | MSL | roll out of stagger late | tie |
| Counter damage | none | +50% while attacking | **B** (flavour; the number is not measured from DSR) |

Neither sets DSR numbers (decision 0004); both are starting points for 2.7 §b.

## 8. Recommendation

Trial B2 first, then B. B2 isolates the one thing worth testing, DSC's poise and band structure under A's best parry, roll and
backstab. B is the owner's stated fallback. Neither ships: Papyrus-timed i-frames and per-actor polling violate "logic stays out of Papyrus" and
0014. Use the trial to decide which of poise-pool, weight-band and counter-damage rules to **build** in `ArgoniaCombat` from
DSR measurements.

Blockers: (1) Pandora FNIS-format support for the `-a,Tn` clips and the behaviour `.hkx` is unproven; (2) pad roll direction;
(3) mod unmaintained since 2019, no field reports readable (Nexus tab blocked); (4) the DS sound rips must be pruned.

## Recommendations (beyond the brief)

- Fix the 1.6 text "TK Dodge RE's tiers" with evidence from the TK Dodge RE page (single `iFrameDuration`): roll tiers need
  OAR conditions or DSC's pattern. Edit `docs/phases/1-core-loop/1.6-fight-on-the-stack.md`.
- If bands are ported, port the **structure** (three FNIS-free clips per direction picked by OAR condition, i-frames from IFrame
  Generator) rather than the Papyrus; evidence: the 30 clips are plain `.hkx` under `BBDarkSoulsCombat/`, and OAR conditions already exist in 2.7 §c.

Covered: ZIP contents of mod 28567 file 104449 (scripts, ESP records, FNIS list), Nexus API mod/files/download, 79598 and 56956 descriptions, Pandora README, `infra/gpu-box/{combat-test-mods.json,stack.py}`, `data/dependencies.json`, decision 0019, 1.6 and 2.7 briefs, the two combat research docs · Skipped: Nexus posts tab (403), Dynamic Dodge/TK Dodge file contents, any in-game test (research lane, no game machine), the other 12 ESP-script sources beyond the roll/poise/riposte/backstab paths, permission research (owner ruling)

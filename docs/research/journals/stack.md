# Journal: the Argonia stack on the game machine (chunk 0.2)

What was tried, measured and learned for `infra/gpu-box/stack.*` and `data/dependencies.json`, so nothing is lost
at a hand-off.

## 2026-10-29: install, menu, conflicts (lane 0.2-stack, continuation)

**The install from bare Data reaches the main menu.** `stack.py install --skip-fetch --dev` runs stage, push,
`stack.ps1 off` (68,927 files removed), Pandora (29 behaviour files from 10 Nemesis-format mods: block, evfmgo,
skysa, slmco, svimex, tdmh, tdmlen, tdmv, tkuc, xpmse), then `menu`. Data loaded after 46 s, MAIN-MENU OK, and
all 35 SKSE plugins logged "loaded correctly" on 1.7.104.0 (after Engine Fixes was added). Wall clock 4 min 21 s
with nothing to re-stage or push. Pandora's 15 "FNIS Parser ... FAILED" warnings are folders under
`animations\` with no FNIS list, not errors.

**Dropped and added:**
- SkyLink AI 1.0.0 (175682, dev) does not load: `SkyrimMCPPlugin.log` says "failed to open address library
  file". Its CommonLib predates Address Library format 5 (1.7.99+), and the report_and_fail modal blocks
  start-up. Its only file is 1.0.0 (2026-03-27). Dropped (`"dropped"` in the manifest, skipped by
  `chosen()`); 0.3's ArgoniaBridge takes the state reads.
- Community Shaders 1.9.1 needs `EngineFixes.dll`. Without it, CS shows "Required DLL ... EngineFixes.dll was
  missing, will disable all hooks and features" at the main menu. SSE Engine Fixes 7.0.21 beta (17230 file 794484,
  "for 1.7.99 only") loads on 1.7.104 and installs its fixes (`EngineFixes.log`); the AE folder is picked, no
  preloader needed on 1.7. A "1.7.104 build" commit (b289e3de, 2026-08-29) exists on GitHub without a release.
- CS then compiles its shader cache once: 3,484 shaders, about 30 min on the g4dn.xlarge's 4 vCPUs, kept in
  `Data\ShaderCache` across `off`. Its first-run modal ("choose a hotkey ... Press Escape or Enter") takes
  neither WScript SendKeys nor a SendInput scan code, so `stack.ps1 on` seeds `SettingsUser.json` with
  `Menu.FirstTimeSetupCompleted = true` (read in CS `src/Menu.cpp:476`). The game-written CS files are kept
  across `off`/`on` (`$Keep`).

**Staging fixes:** SkyLink's archive held `Data/` beside an example JSON, so `data_root` now skips loose doc files
when it looks for a single `Data` folder. A tool row (houseCARL) was laid as a mod after an earlier pass, so a
tool row is now re-staged unless `tools/<id>` exists. Skyrim Ferries' FOMOD marks "Main" Optional, so the row
names it.

**houseCARL 2.1.1** (MCP over the portable instance `C:\argonia\MO2`), report in
`~/.argonia/stack/housecarl/`:
- 88 mods and 45 plugins (35 ours plus 10 implicit); 0 missing masters; 0 parse failures.
- SKSE layer: 35 plugins (32 Address Library, 3 version-locked: FreeClimb declares up to 1.6.1130 yet loads,
  and Fuz Ro D'oh and PapyrusUtil are locked to 1.7.104 itself).
- Native pairing: every third-party native class pairs to a loading DLL.
- Contested DLLs: the six base rows overridden by their 1.7 builds (AMR, Payload Interpreter, dTry Key Utils,
  TK Dodge RE, Elden Parry, ConsoleUtil), each intended. "Data (loose)" in every chain is the hard-linked
  profile itself.
- 374 dangling references inside the mods' own records: King of the Murkmire 336 (statics pointing at
  `000028:Skyrim.esm`), Depths of Skyrim 22, Here There Be Monsters 13 plus 2, EREP 1. These are upstream
  leftovers that this load order did not introduce. The 398 in the base masters are vanilla's.

**Disk.** The build VM's root filled to 100 % when `push` wrote BM&V (21 GB staged) as one local tar. Now:
1 GB parts streamed by `split --filter` (one on disk at a time), joined on the machine; a 10 GB reserve
(`room()`) before any write over 2 GB; archives cached in `s3://argonia-private-050977237313/mods/` with their
sha256 as metadata (`evict` deletes local copies, `verify` checks the cache); `prune` cuts staged mods to their
plugins once the machine's verify passes (the masters and mesh lists are written first).

**Masters on the build VM:** `stack.py masters` copies the 36 dependency plugins into `~/games/skyrimse/Data`,
44 mesh path lists into `Data/argonia-mesh-lists/`, and the load order into `Data/argonia-plugins.txt`. The
manifest's top-level `plugins` list (35, in load order, with their rows) is what `intermediate.load_order()`
reads. No textures are synced (the 2.W1 texture-by-file check needs the game machine).

## 2026-10-30: verify on the slimmed set, and the dodge that does not move (lane game-2)

**Verify:** `stack.py verify` reports **VERIFY OK**: 22,330 recorded files, 0 bad, 0 unrecorded, 30 Pandora
outputs. It took 54 s on the machine (9,394 files rehashed after the slimmed install) and 2 min 56 s end to end,
with a build-VM peak RSS of 100 MB. Defender was quiet (MsMpEng +0.22 CPU-s over 30 s).

**0.2 §c, first run** (`smoke.py launch`, `dodge`, `pad`; `~/.argonia/stack/smoke/20261030T00*`):
- **RT heavy: green.** `IsPowerAttacking` was seen, with tags `PowerAttack_Start_end`, `weaponSwing` and
  `AttackWinStart`, and stamina 300 to 271.6. One Click Power Attack NG's gamepad key works.
- **LB block: the block fires.** The tags were `blockStartOut`, `blockStop` and the shield-block sound. The
  probe misread the console's wording ("is blocking" / "is not blocking", not `>> 1`); `smoke.py` now reads it.
- **RS lock-on: not run.** The bandit form `0001E7D9` was refused as "Invalid object". The target is now a placed
  wolf (`00023ABE`).
- **The dodge: red, the owner's "rolls in place".** TK Dodge RE fires on B in every direction (`TKDR_DodgeStart`,
  `TKDodgeStop`, i-frame events, a stamina cost, about 730 ms). But rolls covered 55-157 units against a 75-95
  unit walk from the same stick time, and the **backstep moved 0.0** every time. A standing **power attack
  also moves 0.0**. Animation-driven motion is zeroed for every clip, not only the dodge.

**Bisect, each by a launch with the named files moved aside (`infra/gpu-box/aside.ps1`, restored after):**

| Variant | Backstep | Roll N | Power attack |
|---|---|---|---|
| everything laid | 0.0 | 157 | 0.0 |
| AMR's DLL off | 0.0 | 75 | - |
| Dynamic Dodge's OAR folder off (TK Dodge's own clips) | 0.0 | 85 | - |
| TDM, Precision, TrueHUD, FreeClimb, Svimex off | 0.0, 0.0 | 75 | 0.0 |
| Display Tweaks, Modern Stagger Lock, MaxsuIFrame, Elden Parry, OCPA NG, Animation Queue Fix off | 0.0, 0.0 | 79 | 0.0 |
| no teleport before the roll; after a walk; after `moveto` | 0.0 each | - | - |

Ruled out:
- **AMR.** It loads (1.5.4 for 1.7.104) and reads custom translations for DodgeBack, DodgeLeft and
  SneakRun_ForwardRoll, but the motion is zero with it off too.
- **Pandora's motion data.** `animationdatasinglefile.txt` holds the clips with their translation: DodgeBack
  (clip 643) 202 units back over 0.9 s, DodgeRight (645) 200 units, SneakRun ForwardRoll (1442) 349 units.
- **The test's teleport (SetPosition).**
- **The eleven DLLs above.**

Left: Engine Fixes, Behavior Data Injector, Payload Interpreter, OAR itself, SkySA, Custom Skills, the
behaviour files Pandora built, and Skyrim.ini or controlmap settings. Next: the same bisect over those, then a run
with the profile off (vanilla behaviours: a vanilla power attack's step is the control).

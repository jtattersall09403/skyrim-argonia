# Lane game-9: the Creation Kit, Papyrus, first-place's building blocks (2026-10-30, 07:45 to 09:00 UTC; hand-off)

## 1. The Creation Kit (owner #15): installed, closed
- The machine's Steam was not offline. It was logged on (connection_log: Logged On at 03:23, a JWT valid to May 2027)
  with `WantsOfflineMode 0`. Skyrim's manifest had AutoUpdateBehavior 1, buildid 24914197, and no pending update.
- App 1946180 was installed through Steam's own client: `steam://install/1946180` in the desktop session, then Install
  and the CK EULA accepted by clicks. The owner asked for it on #15. It downloaded 76.8 MB (buildid 24601472) and
  CreationKit.exe is 1.7.99.0.
- SkyrimSE.exe is unchanged after the install: 1.7.104.0, sha256 846EFCCF…F1402F before and after.
- Steam is now offline. It was shut down, `WantsOfflineMode` and `SkipOfflineModeWarning` were set to 1 in
  loginusers.vdf, and it was restarted `-silent`. The log reads "Logged Off" and the client does not log on.
- The game still launches offline: three deploys since (455 s, 323 s and 127 s) each reached the main menu and the
  base save.
- #15 is closed with e350a62.

## 2. Papyrus: 5 of 5 compile, laid by make deploy
- **Cause of rc 0x80131700:** PapyrusCompiler.exe and PCompiler.dll target CLR v2.0.50727 (.NET 3.5), and the machine
  has only .NET 4.8. records_jobs.ps1 now writes `PapyrusCompiler.exe.config`, which runs the compiler on CLR 4.
- The base sources unpack to `C:\argonia\records\base`, outside Data, because `stack.ps1 off` clears Data on every
  fresh launch. Unpacking takes about 200 s, once only.
- `scripts.zip` is added to vanilla-data-files.txt, so the CK's Scripts.zip survives `off`.
- **Deploy:** `make deploy` has a papyrus step (about 18 s warm; `--no-papyrus` lays the last compile). The .pex go to
  `C:\argonia\ours\scripts`, and `bridge.ps1 prepare` copies them into Data\Scripts. prepare reports `pex: 5`.
- **The .pex** (sha256, first 12):

  | File | sha256 |
  |---|---|
  | ArgoniaCore | 51823287c6176e15 |
  | ARG_PRKF_DialogueIntercept | bed10d0ff7af |
  | ARG_PRKF_RestIntercept | c15abd016da1 |
  | ARG_QF_LF83 | ea24bcccda7e |
  | ARG_StartQuestScript | 514aeb3fe43a |

  Compile: 0 errors, 0 warnings. Papyrus.0.log has no ARG_ bind error now. Before, it read "Cannot open store for
  class ARG_QF_LF83 / ARG_StartQuestScript".
- **0.3 §b:** `bridge.py core Version` returns `{"native":"Version","value":"0.3.0"}`. (The console has no `cgf` on
  this runtime.)

## 3. first-place: four record and staging faults found and fixed; steps 1-7 green twice
| Fault | Cause | Fix |
|---|---|---|
| make-camp: E ran nothing | at 150 units the bedroll is under the crosshair but out of activate reach (no prompt) | pose at 90 units, pitch 40 (both rest steps) |
| talk: E lost | the moveto to a speaker loads a cell; the key landed under the Fader Menu (events: Fader closes 0.7 s after the press) | wait 3 s after the pose; the walking speaker is moved back into the pose (`<speaker>.moveto player 0 110 0`) |
| learn-topic: "no line for topic.claywater-two-charges now" | the base save is Last Seed 17 (wet season); the hook greeting is dry-season only | the scene sets GameMonth 2, GameDay 15 (staging) |
| took-lf83: stage stays 0 | LF83's stage 0 (StartUpStage) had no log entry, so its fragment (WatchQuest) never ran; "quests: watching" never logged | QuestRecords.cs gives a fragment stage an empty log entry, as the CK writes; LF83 yaml regenerated (59a0c3c). **Built, not yet deployed or run in game.** |

- Also made the CK's shape, not proven necessary: perks list their fragment script under VMAD Scripts (eb839ed).
  ViewState lower-cases its view name, because BSFixedString pools strings case-insensitively (eb839ed). Dialogue
  opens through the intercept perk: the core log shows `view dialogue <- {dialogue.state ... Takes-The-Short-Weight}`.
- Last run (g9-fp6): steps 1-7 ok in both runs (arrived, walk-in, make-camp, talk-to-takes, learn-topic,
  goodbye-takes, ask-livia). took-lf83 failed on the stage-0 fault, which is now fixed at source.
- **Our view does not render** (1.2 §0, the gating item): ArgoniaCore pushes view state (`Push()` and `views`).
  There is no web-view host: no PrismaUI in the profile, no PrismaUI binding in ArgoniaCore (dialogue.cpp:6 "the
  web-view binding (PrismaUI) is 1.2 §0's"), and no view bundle laid. The journeys read state through `core`, so
  this does not block them.

## 4. The soak crash (loop 11): diagnosis started, not fixed
- Crash log 07:41:19 (SkyrimSE+100F207 `call [rax+0x10]`, rax 0):
  - The crash is on the main thread, in Main::Update (ID 36564) and a texture task (NiSourceTexture
    treepineforestbranchcomp_n.dds, TREE 0EF5A5).
  - Process memory: Private 9,803 MB, working set 683 MB.
- **Private bytes grow across the session.** Crash logs read 7,692 MB at 26 min (07:00) and 9,803 MB at 35 min
  (07:41). Fresh-launch crashes read 1.4-6 GB. The growth looks like about 230 MB per load or loop.
- **Commit exhaustion is not proved.** The pagefile is system-managed (AutomaticManagedPagefile True) and no
  Resource-Exhaustion event (2004) was found.
- **Next:** a load-only loop measuring private bytes per load, to separate the engine or a mod from ArgoniaCore
  (script ready in the hand-off below). Then the fix at source.

## Not done (hand-off)
The planner's rulings (bb7395f) re-cut the rest:
1. **Deploy 59a0c3c** (`make deploy --no-papyrus`), then re-cut first-place into component checks, read by state
   and events (no playthrough):
   - LF83's stages advance from facts set through the real paths;
   - a "journal updated" notice at each stage and clue;
   - topics granted and offered (`core KnowsTopic`, ViewState topics);
   - completion and fail-forwards;
   - each family round-trips.
   Steps 1-7 of tests/journeys/first-place.yaml are the green start.
2. **Livia's bed, the native way:** ownership on the bed ref and vanilla's sleep template targeting an owned bed.
   Check she reaches it at 23:00. nav-walk-2's door links (afdbae4) are in the deployed ESMs: Argonia.esm 299daa57,
   and the current build carries them too. Still owed: one still of a hut door at the play camera, for nav-walk-2.
3. **The crocodile:** fixes-1's den is deployed (deploy3 at 08:31, Argonia.esm with the den ref 000970). Verify it is
   placed, attacks and is killable, with no respawn after the kill.
4. **fixes-1's menus:** check that Tab, J and Map write no suspend save and the Journal stays open, and that the save
   is written on quit. The Map's FWMF chart needs the LOD run's terrain LOD first.
5. **The LOD run** (the 2.W4-lod sequence), then the map verification.
6. **The soak runs last,** once (planner ruling), after the per-load memory measure.
7. **The reader rule:** never Read stills in your own context; a `reader` agent judges them.

## Commits
- e350a62 CK and Papyrus;
- eb839ed perk VMAD, ViewState, forms.h;
- 59a0c3c quest-stage log entry, first-place staging.

`make check` green (334 pytest, plugin-check identical). The machine is left running with the game up (deploy at
08:31, Argonia.esm 4f5b30c6, which predates 59a0c3c).

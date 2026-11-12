# Engine facts for the quest form (walk 6, lane R3)

The measured facts the kit lane (K) needs for [walk-6-quests](../../phases/walk-6-quests.md): markers, a person who
speaks first, mortality, the death message, generic scripts, and "away from the player". Decision 0034: each answer
says how Bethesda did it, counted, and ends in **Do this:**.

**Sources and method (2026-11-12, build VM, read only).** Records: `~/games/skyrimse/Data/Skyrim.esm` and the DLC
masters, `Black Marsh.esm`, and our built `out/Argonia.esp` (built 2026-11-12 19:47), read with
`tools/argonia_world/esm.py`. Compiled scripts: all 14,026 `.pex` in `Skyrim - Misc.bsa` (Skyrim, Update and the DLC
scripts), unpacked and read with a throwaway reader of the compiled format (objects, properties, states, and every
`callmethod` instruction; no decompiler). Field and enum names (condition functions, alias, NPC, template, objective
target and message flags; the VMAD fragment shapes) were read from Mutagen 0.54.4 by reflection. Load order:
`Data/argonia-plugins.txt`. The helper scripts were not kept. Vanilla Papyrus *source* is not on this machine, so the
scripts' behaviour is read from their compiled instructions. **Not measurable here** (no game is run): anything about
what the engine does at run time but does not write in a file. Each such point is marked *(engine, not measured)*.

## 1. Why no quest marker could be followed

**Cause: our own game settings hide every quest marker.** `infra/gpu-box/stack.ps1:116` writes
`SkyrimPrefs.ini [GamePlay] bShowQuestMarkers=0; bShowFloatingQuestMarkers=0` on every stage of the play machine,
with the comment "quest markers stay off (below, Morrowind's way), so the compass shows places and directions but no
quest target" (lines 111-112, owner walk 2026-11-07, which asked for the compass). `bShowCompass=1` (line 113), so the
owner saw a compass with no quest target on it. `bShowQuestMarkers` is the game menu's "Quest Markers" option, which
covers the compass and the map. `bShowFloatingQuestMarkers` is the marker that floats over the target in the world.
The owner's ruling of 2026-11-12 (owner-rulings.md:470: "Quest markers on the map and in game for objectives and
things to pick up or use") overrides that setting.

Other candidates, each checked:

| Candidate | Finding |
|---|---|
| A HUD mod hides the compass or the markers | No. Of the stack's mods (`mods/dependencies.json`), only TrueHUD changes the HUD, and its staged settings change only the player's bars (`bPlayerWidgetHideVanillaBars=1` and the bar layout). Our only SKSE plugin is ArgoniaDodgeBuffer: `skse/` has no HUD hook (the old `hudElements` hook went with the pivot). SkyUI and FWMF (the map) hide no markers. |
| The quest is not the tracked (active) one | Possible as well; can be guarded cheaply. None of our 17 `papyrus/ARG_QF_*.psc` calls `SetActive`. Vanilla calls `SetActive()` from 18 of 880 QF scripts (25 calls, 24 of them on a quest). Nearly all of them are the main quest making the *next* main quest active as it starts it (`QF_MQ102` Fragment_45 `MQ103.SetActive()`, then MQ103 to MQ104, and so on up to MQ306), plus a few quests making themselves active (`QF_MQ105` Fragment_70). The other 860 vanilla quests rely on the engine making a quest active when it first shows an objective *(engine, not measured)*. |
| Target refs not persistent, not filled, or disabled | Our 11 built quests have 58 objective targets. Every one is a forced-reference alias to a **persistent** ref (58 of 58). 23 of the 58 hang on an enable parent (XESP) or start disabled (MQ03's objective 21: ref 000E3F starts disabled). The engine shows no marker for a disabled ref *(engine, not measured)*, so each of those 23 shows only once its parent is on at that stage. R2 (the post-mortem) owns the stage-by-stage check. |
| Objective target flags | No effect. QSTA's only flag is "Compass Marker Ignores Locks" (Mutagen `Quest.TargetFlag`). Vanilla sets it on 12 of 1,808 targets; we set it on none. It does not hide a marker. |

**How Bethesda marks each kind of target** (the 1,808 objective targets of Skyrim.esm, by the target alias's fill):

| Target | How | Count | Example |
|---|---|---|---|
| A person | forced ref to the actor (251) or unique actor (656) | 907 | MS10MiscObjPointer, objective 10 -> Orthus |
| A thing lying loose, to pick up | forced ref to the placed item: BOOK 35, MISC 22, WEAP 7, ALCH 6, ARMO 3, INGR 1, KEYM 1 | 75 | T01DegaineFavor, objective 10 -> Chalice (MISC) |
| A thing inside a container | created ref, "Create in" the container's alias (ALCO + ALCA with the In bit 0x8000): MISC 18, BOOK 17, WEAP 11, LVLI 7, ARMO 3, SLGM 1, KEYM 1. The marker shows on the container. Alternatively the container itself is the target (forced ref to the CONT, 37). | 58 (+37) | BardsCollegeDrum, objective 20 -> RjornsDrum (created inside its chest) |
| A door | forced ref to the DOOR | 89 | dunFrostmereCryptQST, objective 2 -> FrostmereDepthsDoor |
| A place | forced ref to a marker STAT (129), an activator (78), or a location alias's reference (ALFA+ALRT, 135) | 342 | TutorialEnchanting, objective 10 -> FarengarMarker |

A thing in a container cannot be a placed ref: a container's contents are base objects (CNTO), not refs. So a marker
on it needs Bethesda's "create in container" alias.

**Do this:** (1) Set `bShowQuestMarkers=1` and `bShowFloatingQuestMarkers=1` in `stack.ps1:116`, keep
`bShowCompass=1`, and rewrite the comment above them to the owner's ruling of 2026-11-12. The next stage of the play
machine writes them. (2) The kit makes the fragment that first shows an objective also call `SetActive()` on its
quest, as the main quest does. (3) Every target is a forced ref to a persistent ref, enabled at every stage where its
objective is shown; the form check fails a target whose ref (or its enable parent) is off at that stage. (4) Mark a
thing to pick up with a forced ref to the placed item, a thing in a container with a created-in-container alias
(ALCO + ALCA In) whose objective targets it, a door with a forced ref to the door, and a place with a forced ref to an
XMarker. (5) Leave "ignores locks" off, except for a target behind a door the player has the key to at that stage.

## 2. A person who speaks first (force-greet)

**Template.** `ForceGreet` (Skyrim.esm 03C1C4) is a package template. A force-greet package has type Package, and its
PKCU names the template. 302 packages in Skyrim.esm use it. 214 of them are alias packages (ALPC) in 124 quests (DA06
6, DA16 5, MQ201 5, MG03 5, ...), and 61 NPC_ carry one in their own package list. The template's 20 data inputs, with
the template's defaults:

| Input | Default | Vanilla use |
|---|---|---|
| Topic | subtype Hello | 291 of 302 name a specific topic (DIAL) instead; 8 keep Hello |
| NPC Wait Location (NPC hangs out here) | near the package start, radius 150 | |
| Trigger Location (player here causes forcegreet) | near the package start, radius 500 | |
| Forcegreet Distance | near the player (0x14), radius 300 | radii 150 to 1,500 seen |
| Player must be detected? | false | true in 18 |
| Greet Using Preferred Path? | true | |
| Player (single ref) | the player | the player in all 302 |
| ForceGreetLoc | near the player, radius 5,000 | |
| Forcegreet if player on horseback? | false | true in 27 |
| Sandbox While Waiting? and the Allow* sandbox switches, Energy 50 | off | AllowIdleMarkers on in 157 |

**Conditions** (on the package): 66 of the 302 have none. The others use GetStage 175, GetVMQuestVariable 95,
GetStageDone 81, GetDead 7, IsInCombat 7, GetInCell 7, GetInCurrentLoc 7, GetDistance 5,
IsPlayerMovingIntoNewSpace 4 and IsInInterior 3 (condition uses, by Mutagen's function index).

**How it ends.** The template's procedure tree is Travel (to the wait location) and ForceGreet, which runs when the
player enters the trigger location. A greet that has started does not end the package. The package ends when its
conditions fail, which in vanilla is a stage set by the greeting line's fragment (hence the 256 GetStage/GetStageDone
uses).

| Failure | Guard |
|---|---|
| The person's cell is not loaded: no AI runs, so no greet | The person stands placed at the wait location, with a marker on him. The player who walks up and speaks first gets the same line (below). |
| The player is in combat, in dialogue or in a menu, or moving through a load door, when they arrive | Condition the package on `IsInCombat == 0` (as 7 vanilla packages do) and `IsPlayerMovingIntoNewSpace == 0` (as 4 do). The ForceGreet procedure waits for the player to be free *(engine, not measured)*. |
| Distance: the player never comes within 500 of the package start, or there is no navmesh between the two | Place the person a few steps from where the player first appears (the plan's rule), on the same winning navmesh as that spot (blocks.md's E-package rule). Trigger radius 500, greet distance 300. |
| The greeting repeats, because the player left the talk before choosing | The greeting line's **begin** fragment sets the next stage, so the package's `GetStage == n` condition fails at once. |
| The person is made hostile or dies | Mortal by the plan. The quest's "who must live" row fails the quest (section 4). |

**A plain greeting plus a marker is a full fallback.** A force-greet only starts the conversation; the line it opens
is an ordinary INFO. If the same line, with the same conditions and the same result, is also on the person's
Greeting (HELO) topic, then the player who speaks first meets it, and the marker brings them to him.

**Do this:** one alias package on the person's quest alias, made from template `ForceGreet` (03C1C4). Its Topic is the
quest's own opening topic. Its conditions: `GetStage(quest) == n`, `IsInCombat == 0` on the subject, and
`IsPlayerMovingIntoNewSpace == 0`. Keep the template's radii (trigger 500, greet 300), "Player must be detected" off,
the wait location at his placement, and the objective marker on him. The same INFO text and result also sit under his
Greeting topic with the same condition. Both INFOs set stage n+10 in their **begin** fragment.

## 3. Nobody essential or protected

**Where the flag lives.** On the NPC_ record: ACBS flags Essential 0x2 and Protected 0x800. If the NPC_ has a
template (TPLT) with the "Use Base Data" template flag (0x80), the engine takes these flags from the template, so the
record to change is the end of that chain. On a quest alias: flags Essential 0x40 and Protected 0x400 make the ref
essential or protected while the alias holds it.

**Counts (by the engine's view: the winning record, through Use Base Data templates, in our load order):**

| Set | Essential | Protected | Of |
|---|---|---|---|
| Our NPC_ (Argonia.esp's own) | 9 (5 `ARG_Talker_*`, MQ04_PaysLate, MQ01_TiesTheLoosePlank, TG_BentSpine, TG_Tilts) | 26 (the MQ01, LQ25, LQ30, TG, MQ03, MQ04 and block-test casts) | 177 |
| People we place (Argonia.esp ACHR) | 10 refs (one is BM&V's BretonMaleMerchant) | 29 refs | 339 |
| BM&V's own NPC_ | 2: BretonMaleMerchant (089CD8), LuxHa (1454E2) | 0 | 103 |
| People placed by BM&V, on BM&V bases | 4 refs (BretonMaleMerchant 3, LuxHa 1) | 0 | 782 |
| People placed by BM&V, on vanilla or DLC bases | 8 refs: ArgonianFemalePreset01 (0B2E11, BM&V's override; a character-creation preset, essential) 7, DLC2DremoraMerchant (Dragonborn 01EEB1) 1 | 0 | 351 |
| Alias flags in our quests | 22 Essential/Protected alias flags in 8 of our quests (MQ01 6, BC02 5, BC01 3, MQ05 2, MQ03 2, BC03 2, LQ30 1, BlockTest 1) | | |
| Alias flags in BM&V's quests | 0 | | |

No NPC_ in the set carries a flag that its template then overrides (0 cases).

**What can bring it back.** (a) Alias flags in quests we do not own that fill freely, rather than by a forced ref:
start-game-enabled quests with such an alias are, in Skyrim.esm, DA04, DA08, DA16, **DialogueFollower**, MS12, T01,
T02, T03 and FreeformSkyhavenTempleA (24 aliases), plus DLC1NPCMentalModel, DLC2HirelingQuest and HearthFires'
RelationshipMarriageFIN. Of these, only DialogueFollower (anyone who becomes the player's follower) and marriage
can take a BM&V person. (b) Our overrides of vanilla quests (DA08, T01, MS11PreEssentializing and others) carry 47
such flags, all on vanilla people who do not stand in BM&V's worlds. (c) A script can call `SetEssential` *(no
vanilla count taken)*. The quest form has no such result.

**Do this:** at build, write an override in Argonia.esp that clears Essential and Protected on every NPC_ whose
winning, template-resolved flags carry either. Today that is our 35 NPC_ (cleared in our own records),
BretonMaleMerchant, LuxHa, ArgonianFemalePreset01 and DLC2DremoraMerchant. Clear the 22 alias flags in our quests.
Add a gate check that recomputes this table from the load order and fails on any essential or protected person
placed in BM&V's worlds, or any such alias flag in a quest we own. Being a follower or a spouse leaves a person
protected, as in vanilla; the form has no follower result, so nothing of ours triggers it.

## 4. A message box on a death

**The record.** MESG, with flag Message Box (0x1; Mutagen `Message.Flag`). Skyrim.esm has 571 MESG, 384 of them
message boxes. With no buttons (no ITXT), the box shows one OK. Vanilla's own quest-failure box is `DA06FailMessage`
(DNAM 0x1, FULL and DESC, no buttons), shown by `QF_DA06` Fragment_28.

**How vanilla shows one from a quest.** `Message.Show()` is called in 6 places across 5 QF scripts (DA06 Fragment_28
DA06FailMessage; MQ101 2; MQ104B 1; T02 1; TGBan 1) and from 3 TIF scripts. `ShowAsHelpMessage` (the tutorial pop-up)
appears 14 times in QF scripts.

**The alias death scripts, from their compiled instructions:**

| Script (extends) | Properties | What it does | Quests |
|---|---|---|---|
| `defaultSetStageOnDeathRefAlias` (ReferenceAlias) | `myQST` Quest (required: used directly, with no fallback to the owning quest), `StageToSet` Int, `preReqStage` Int (-1 = none) | in state `waiting`, `OnDeath`: if `preReqStage == -1` or `myQST.GetStageDone(preReqStage)`, then `myQST.SetStage(StageToSet)` and go to state `inactive`; otherwise nothing, **and the death is never seen again** | 20 |
| `DefaultAliasOnDeathScript` (ReferenceAlias) | `StageToSetOnDeath` Int, `PrerequisiteStage` Int | `OnDeath`: `GetOwningQuest()`, checks `GetStage` against the prerequisite, `SetStage` | 8 |
| `defaultSetStageOnDeath` (Actor, on the ref) | `myQST`, `StageToSet`, `preReqStage` | as the alias one, but on the actor | 4 refs |
| `defaultCounterIncrementOnDeath` (Actor) + `defaultCounter` | linked-ref keyword; `myQuest`, `myStage`, `TargetValue` | a group cleared | 47 |

(Quest counts from [quest-block-precedent](quest-block-precedent.md).)

**When they do not fire.** An alias script receives `OnDeath` only while its alias holds the actor. A death before
the quest starts, or before the alias fills, reaches no alias script. A death before the prerequisite stage is
dropped for good (above). A person can die while his cell is unloaded only by a script's `Kill()`. Whether `OnDeath`
reaches an alias then is *(engine, not measured)*; our results never kill anyone off screen.

**Do this:** one start-game-enabled, never-stopping quest, `ARG_MortalWatch`, holds every main-quest person. Each is a
forced-ref alias with no flags, filled at game start (every ref is persistent). Each alias carries the generic
`ARG_AliasEffects` (section 5) with two rows: ShowMessage (the main-quest MESG: a Message Box with no buttons, as
DA06FailMessage is) and SetStageIfRunning (the person's quest and its failure stage). The "if running" matters
because `SetStage` on a quest that is not running starts it (blocks.md, "A finished quest set going again"). The
failure stage's rows fail the shown objectives, write the failure journal entry and stop the quest. Outside the main
quest, a quest's "who must live" person carries vanilla `defaultSetStageOnDeathRefAlias` on that quest's alias
(`myQST` set, `preReqStage = -1`, `StageToSet` = the failure stage). Every quest's start-up stage holds a row
FailIfDead for each person who must live, so a death before the quest began fails it at its start.

## 5. Generic scripts: a quest that is data only

**(a) Stage fragments on one shared script.** A quest's VMAD names a fragment script (`FileName`), and each stage
row names a script and a function (Mutagen `QuestScriptFragment`: `Stage` UInt16, `StageIndex`, `ScriptName`,
`FragmentName`). Nothing in the format ties a script to one quest. Each quest that attaches the script gets its own
instance with its own property values. Vanilla never shares one: the Creation Kit writes one fragment script per
record (Skyrim.esm: 856 quests with fragments, 847 distinct fragment script names; the only name shared is the empty
one, on 10 quests). So a
shared stage script has **no vanilla precedent**. It rests on the format, plus the fact that we never open these
records in the Creation Kit (decision 0018), which would regenerate them.

**(b) One response script for every line.** Each INFO's VMAD holds its own script entry with its own property
values, plus `ScriptFragments` (`OnBegin` and `OnEnd`, each a script and a function name). Vanilla never shares one
(5,257 INFO fragment scripts, all distinct). **We already do**: `papyrus/TIF_ARG_BoatTravel.psc` is one compiled
`TopicInfo` script for every boatman's line, with each line's own `Destination` and `Fare` properties
(`tools/ArgoniaPlaces/Build/Boat.cs`). No in-game proof of it was found in the records (owner-walk-checks, PROGRESS).

**(c) Our tools.** Mutagen 0.54.4 has every array property type (`ScriptObjectListProperty`, `ScriptIntListProperty`,
`ScriptFloatListProperty`, `ScriptBoolListProperty`, `ScriptStringListProperty`). Our plugin already round-trips one
through Spriggit: `plugin/Argonia/Quests/ARG_MQ05 - 000DBE_Argonia.esp.yaml`, `Zones` (written by
`QuestKit.cs:413`), next to its `Fragments` list of (Stage, ScriptName, FragmentName). The quest fragment table and
the INFO `ScriptFragments` (OnEnd) are written by `QuestKit.cs:439,493,521` and round-trip in 175 response files.
Int and Float lists have not yet been written by us, but they use the same mechanism.

**(d) Which stage called.** The fragment table names a function per stage, and the function gets no argument. A
shared function reading `GetStage()` would read the *current* stage. When one fragment sets the next stage, the
fragments queue, so that read can be later than the caller *(engine, not measured)*. So: **one function per stage
number**, `Fragment_<n>()`, each with one line, `Run(n)`. A script with 256 such functions is sound by size: the
largest vanilla script has 309 functions (`FormArray`), and QF_MQ101 numbers fragments up to `Fragment_331`.
Mutagen's stage field is UInt16; the form limits stages to 0 to 255.

**(e) Vanilla data-in-properties scripts** (compiled properties, read here), the precedent for "effects in
properties":

| Trigger | Script (extends): properties |
|---|---|
| Take | `defaultSetStageOnPlayerAcquire` (ReferenceAlias): `myQST` (optional; falls back to the owning quest), `StageToSet`, `preReqStage` (-1 none); acts only when the new container is the player. `defaultSetStageOnPlayerAcquireItem` (ObjectReference): the same |
| Use / activate | `defaultSetStageAliasScript` (ReferenceAlias): `TriggerType`, `stage`, `prereqStageOPT` (activate, enter, read, open, equip, hit, death, by type; 119 quests). `defaultsetStageActRefAliasScript` (ReferenceAlias): `myQuest`, `stage`, `prereqStageOPT`, `requirePlayerActivation`, `delay`. `defaultsetStageActSCRIPT` (ObjectReference): the same |
| Read | `defaultSetStageOnCloseBook` (ReferenceAlias): `StageToSet`, `preReqStage`; `DefaultOnReadSetQuestStage` (ReferenceAlias): `myQuest`, `myStage` |
| Death | `defaultSetStageOnDeathRefAlias`, `DefaultAliasOnDeathScript`, `defaultSetStageOnDeath` (section 4) |
| Two stages | `defaultsetMultiStageAliasScript`: `TriggerType`, `prereqStage1/2`, `resultStage1/2` |

Array properties in vanilla data: 2 in Skyrim.esm (both Bool[] on CompanionsBladeFragmentTracking), 28 in Dawnguard,
52 in Dragonborn. A QF script holding a Form array is precedent: `DLC1_QF_DLC1LD_Bthalft` `ForgeDustFX`, 16 items. The
largest array is 35 items (DLC2dunNchardakTracking). None exceeds 128.

**(f) Risks.**
- **Array length.** Papyrus arrays made by `new` are capped at 128. No vanilla property array exceeds 35, and a
  VMAD-filled array over 128 is untested *(engine, not measured)*, so cap each array at 128 rows.
- **Properties.** The largest vanilla script has 599 (CWScript), and QF_CWSiege has 346. Ours needs about 6.
- **Fill order.** Property values bind when the instance is made, before any fragment runs. A changed value does not
  reach a save that already holds the instance *(engine, not measured)*, which the plan's "new game" ruling covers.
- **Saves.** Each quest's instance and arrays are saved. That is small: a few arrays of at most 128.
- **Instances.** One instance per quest, so two quests never share values.

**Do this:** four scripts, written once.
- `ARG_Effects` (a library): `Function Run(Int[] op, Form[] what, Int[] num, Int[] from, Int[] to, Quest q) Global`
  carries out the rows whose index lies in [from, to). The ops are a closed list matching the form's results:
  ShowObjective, CompleteObjective, FailObjective, SetActive, GiveItem, TakeItem, GiveGold, TakeGold, Enable, Disable,
  SetGlobal, ModGlobal, JoinFaction, SetRank, LeaveFaction, SetRegard, MovePlayerTo, ShowMessage, StartQuest,
  SetStageOf, SetStageIfRunning, FailIfDead, StopQuest, IncSideQuests.
- `ARG_QuestStages extends Quest`: properties `Int[] Op`, `Form[] What`, `Int[] Num`, and `Int[] StageFrom` and
  `Int[] StageTo` (indexed by stage number, giving each stage's row range). It holds `Fragment_0()` to
  `Fragment_255()`, each `ARG_Effects.Run(Op, What, Num, StageFrom[n], StageTo[n], Self)` and nothing else (generated
  once by a script, so not written by hand). Each built stage's fragment row names `ARG_QuestStages` and `Fragment_<n>`.
- `ARG_LineEffects extends TopicInfo`: properties `Op`, `What`, `Num`; `Fragment_Begin` and `Fragment_End` run all the
  rows (`Begin` for a line that opens a force-greet, `End` otherwise).
- `ARG_AliasEffects extends ReferenceAlias`: the same three arrays, run once on `OnDeath` (the main-quest message).

Take, use, read and death stay vanilla's own scripts above on the alias (no script of ours). The builder writes the
arrays from the form's rows.

## 6. "Away from the player": a checkable rule

**Facts.** An exterior cell is 4,096 units square (`tools/newworld/frame.py:33`). The loaded area is
`uGridsToLoad` by `uGridsToLoad` cells centred on the player's cell. The stack does not set it, and neither the
game's presets (`Low/Medium/High/Ultra.ini`, `Skyrim_Default.ini` on this VM) nor any staged mod ini names it, so it
is the engine default of 5 *(the default value is engine-compiled, not measured; the LOD plan relies on the same
value: [ck-lod-plan](ck-lod-plan.md):72)*. Actors and ordinary refs outside the loaded cells are not drawn. Refs with
distant LOD, and "large references" (SSE's own larger grid), can be seen beyond it *(engine, not measured)*. An
interior is one cell, and nothing outside it can be seen from inside, nor anything inside it from outside.

**The rule** (applied by the builder from positions, against the place where the result fires: the speaker of a line,
the thing taken or used, the person who died; for another quest's stage, that stage's own trigger):
1. The switched ref is in an **interior cell other than the trigger's cell**, or the trigger is in an interior and
   the ref is in the exterior (or the other way round): away.
2. Both are in the exterior: away only if the horizontal distance from trigger to ref is **at least 18,000 units**.
   Inside the 5 x 5 grid, a ref is at most 3 cells per axis from the player, so at most 3 x 4,096 x √2 = 17,378
   units away. The rest is margin for the player standing up to about 600 units from the trigger.
3. Never, whatever the distance: a ref with distant LOD (base STAT or MSTT flagged for distant LOD, or listed among
   the world's large refs), and a ref in the same interior as the trigger.
4. A result set by a trigger whose position the builder cannot know (none in the ceiling today) is refused.

**Do this:** the form check computes rule 1 to 3 from the placed refs' cells and positions, and refuses a switch
on or off that fails it, naming the distance.

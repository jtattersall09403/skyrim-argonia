# Phase 3: one test quest that proves the building blocks

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

**What it is for.** The story is built in Phase 4 from a small set of engine mechanics, the blocks, listed in
[blocks.md](../design/blocks.md) and derived from the Act I records in Phase 2: triggers (what moves a quest stage),
conditions (what gates a trigger or a line), effects (what a stage does) and the world edits under them. This phase
finds a broken block cheaply, in a throwaway test quest, before any story rests on it. If every block works, and the
blocks work wired together, any quest made only of them works (the induction note in blocks.md).

**Starts when** Phase 2's review is finished and blocks.md's stage table is regenerated from the final records; the
block list is then frozen for this phase. The design below is ready now; nothing is built into the plugin until then.
If the frozen list gains or loses a block, the step table changes by that block only.

**What gets built.** One test quest, `ARG_BlockTest`, and a second tiny quest it starts, `ARG_BlockTestEnd`, in our
plugin on top of BM&V. One console command starts it; it takes about ten minutes; it all happens on Lilmoth's dock,
beside our opening marker. Every trigger, condition and effect in blocks.md is used once, plus the five risk cases of
the induction note. Everything is removed from the plugin once the owner's walk has passed: the shapes stay, as the
templates every Phase 4 quest copies.

**How it is built.** Records added in `tools/ArgoniaPlugin/Generate.cs` beside the opening's, written to Spriggit YAML in
`plugin/`, built to the ESP on the build VM; Papyrus in `papyrus/`, compiled on the play machine; the Creation Kit only
for the compiler. Fixed allocation order (form ids stable), as the opening does.

## The place

BM&V's `BlackMarsh` worldspace, Lilmoth's dock: cell `005A21` (7,-1), navmesh 07EEF8 (Black Marsh North's winner).
`ARG_OpeningMarker` stands at 30901,-2903,3. The coast ship's door `0AA664` (base `SJailDoor02Load`, BM&V's) stands at
32176,-2430 in the same cell and leads into the ship interior `01Ship` (`0AA665`, navmesh 0AA666), which is unloaded
until entered: the test's "two cells away" place.

Nothing new is built on ground without navmesh; every actor we place stands on 07EEF8 or in `01Ship`. The test uses
only Argonians (BM&V's villager templates) and a mudcrab; no Nordic base reaches the player through what we add (the
ship door's vanilla base is BM&V's own placement, left as it is). No actor of ours has the PC-level-mult flag.

## What the test adds (records, by block shape)

All our records carry the prefix `ARG_BT_`. Positions are a start: the build agent snaps each to the nearest 07EEF8
triangle centre (as the opening marker was) and the read-back checks it.

| Record | Type | Block | What it is |
|---|---|---|---|
| `ARG_BlockTest` | QUST | E-stage | the test quest; not Start Game Enabled; stages 10 to 100 below; Run Once off (re-runnable for a re-test) |
| `ARG_BlockTestEnd` | QUST | TR-chain | the second quest: one start-up stage 10, journal "The second quest started from the first.", then completes |
| `ARG_BT_Keeper` | NPC_ | W-npc, W-fixed | "Dock Keeper", TPLT `00FF4D:Black Marsh.esm` (ArgonianMaleVillager), fixed level 5, not essential; our voice type none (topics are text with silent lines, as the act's will be until voiced) |
| `ARG_BT_Walker` | NPC_ | W-npc, W-fixed | "Dock Walker", TPLT `02A1EE:Black Marsh.esm` (ArgonianFemaleVillager), fixed level 5, protected |
| `ARG_BT_Crab` | NPC_ | W-fixed | "Mudcrab", TPLT `0E4011:Skyrim.esm` (EncMudcrabLarge), fixed level 4 (decision 0035: a fixed band, never the player's) |
| `ARG_BT_KeeperRef` | ACHR, persistent | W-npc | the keeper on the dock, 3 m north of the marker, enabled |
| `ARG_BT_WalkerRef` | ACHR, persistent, initially disabled | W-ref, alias guard | the walker inside `01Ship` (unloaded, disabled when the quest starts) |
| `ARG_BT_CrabRef` | ACHR, persistent | W-ref, E-enable | the crab on the dock 15 m east, enable parent `ARG_BT_CrabParent` |
| `ARG_BT_StartMarker`, `ARG_BT_WalkerMarker`, `ARG_BT_DoorMarker` | REFR XMarker (`00003B`), persistent | E-move, E-package | where the player lands (2 m from the keeper), where the walker appears (beside the keeper), where she walks to (in front of the ship door) |
| `ARG_BT_TokenParent`, `ARG_BT_CrabParent` | REFR XMarker, persistent, initially disabled | E-enable | enable parents |
| `ARG_BT_Token` | MISC "Test Token" (value 0, a vanilla shell model such as `Clutter\Common\...` picked by the build agent from BM&V's dock clutter) | TR-acquire | the thing to pick up |
| `ARG_BT_TokenRef` | REFR, persistent | TR-acquire, E-enable | the token on the dock planks 5 m west, enable parent `ARG_BT_TokenParent` |
| `ARG_BT_Key` | KEYM "Ship Door Key" | E-item (setDoorAccess) | the key the keeper hands over |
| `0AA664:Black Marsh.esm` override | REFR (W-override) | W-override, setDoorAccess | the ship door, XLOC level "requires key", key `ARG_BT_Key`; persistent flag set |
| `0AA665:Black Marsh.esm` override | CELL (W-name) | W-name | the ship's FULL "Test Ship" (BM&V's is "Ship") |
| `03E409`, `03E40A`, `03E40B`, `03E40C`, `03E40D` overrides | ACHR (W-ref removal) | W-ref | Black Marsh North's five Naga on and around the dock, each override flagged initially disabled (they are `we.clean.lilmoth` targets; the test builds them first) |
| `ARG_BT_ZoneA`, `ARG_BT_ZoneB` | REFR of ACTI `099312:Skyrim.esm` (defaultSetStageTRIGPlayerOnly), XPRM box 300 x 300 x 200, persistent | TR-zone, race guard | two boxes at the same spot on the planks before the ship door, so both fire in the same frame |
| `ARG_BT_Global` | GLOB short, 0 | E-global, C-global | the remembered "standing" |
| `ARG_BT_Faction` | FACT "Dock Hands", one rank "Hand" | E-faction, C-faction | the faction joined |
| `ARG_BT_Scene` | SCEN owned by `ARG_BlockTest`, actors the keeper and walker aliases | E-scene, TR-scene | two lines each, one phase, end fragment sets stage 60 |
| `ARG_BT_WalkPackage` | PACK Travel to `ARG_BT_DoorMarker`, condition GetStage ARG_BlockTest >= 60 | E-package | on the walker alias's package list (ALPC) |
| `ARG_BT_Topics` | DIAL branch in `ARG_BlockTest`, INFOs below | TR-topic, every condition | the keeper's lines |

**Aliases of `ARG_BlockTest`** (all forced references, never find-matching; blocks.md's rule): Keeper
(`ARG_BT_KeeperRef`), Walker (`ARG_BT_WalkerRef`, flags Allow Disabled, Optional; package list `ARG_BT_WalkPackage`;
Protected), Crab (`ARG_BT_CrabRef`, Allow Disabled; script `defaultSetStageOnDeathRefAlias`: `myQST` this quest,
`preReqStage` 60, `StageToSet` 65), Token (`ARG_BT_TokenRef`, Allow Disabled; script `defaultSetStageOnPlayerAcquire`:
`myQST`, `preReqStage` 20, `StageToSet` 30), ShipDoor (`0AA664`; script `defaultSetStageAliasScript`: `stage` 80,
`prereqStageOPT` 75, `TriggerType` as vanilla's activate uses, copied from a vanilla alias that sets a stage on
activate), ZoneA and ZoneB (the two boxes). Each zone box's own `defaultSetStageTrigScript` properties: `myQuest`
this quest, `prereqStageOPT` 65, `stage` 71 (A) or 72 (B). Property names are as Skyrim.esm writes them
(measured 2026-11-06: 88 refs use `prereqStageOPT`/`myQuest`/`stage`; 8 acquire aliases `myQST`/`preReqStage`/`StageToSet`).

**The keeper's lines** (INFO conditions are CTDA run on the keeper unless said; each fragment is the TR-topic shape,
`GetOwningQuest().SetStage(n)`):

| Line (player's choice / keeper's reply) | Conditions | Sets |
|---|---|---|
| "I am ready for the test." / "Then take this key, and find the token on the planks." | GetIsID Keeper; **C-stage** GetStage ARG_BlockTest == 10 | 20 |
| "Here is the token." / "Good. You are one of the dock hands now." | **C-item** GetItemCount ARG_BT_Token >= 1 (run on player); **C-global** GetGlobalValue ARG_BT_Global >= 1; GetStage == 30 | 40 |
| "Talk me into it." / "You talk well enough. Watch the walker." | **C-faction** GetInFaction ARG_BT_Faction == 1 (player); **C-skill** GetActorValue Speech >= 15 (player); GetStage == 40 | 50 |
| "Talk me into it, master." (should never show) | GetActorValue Speech >= 100 (player); GetStage == 40 | none |
| "The crab is dead." / "By day, too. Done." | **C-alive** GetDead (run on the Crab alias) == 1; **C-time** GetCurrentTime >= 6 and < 20; GetStageDone 80 == 1 | 90 |
| "The crab is dead." / "At this hour. Done." | GetDead (Crab) == 1; GetCurrentTime < 6 or >= 20; GetStageDone 80 == 1 | 90 |

## The steps (the owner's walk)

About ten minutes. Each line is one thing to look at; the stage is what the console shows with `sqs ARG_BlockTest`.

| Step | Stage | Block(s) proved | What the owner does | What should happen |
|---|---|---|---|---|
| 1 | 10 | console start; alias filling at start (walker disabled and in the unloaded ship); persistent refs; E-move (the player); E-stage | Anywhere in the game, open the console and type `startquest ARG_BlockTest` | You are moved to Lilmoth's dock beside the Dock Keeper. The journal has "Block Test" with an objective "Speak to the Dock Keeper". No Naga anywhere on the dock (W-ref removal). |
| 2 | 20 | TR-topic; C-stage; E-item (setDoorAccess: the key given); E-enable (the token appears); E-regard | Talk to the keeper, pick "I am ready for the test." | "Ship Door Key" in your inventory. A Test Token is now on the planks to the west. Click the keeper in the console and type `getrelationshiprank player`: it says 1. |
| 3 | 30 | TR-acquire; E-global | Pick up the Test Token | The objective moves to "Bring the token to the Dock Keeper". `getglobalvalue ARG_BT_Global` says 1. |
| 4 | 40 | TR-topic; C-item; C-global; E-item (taken); E-faction | Talk to the keeper, pick "Here is the token." | The token leaves your inventory. `player.getinfaction ARG_BT_Faction` says 1. |
| 5 | 50 | C-faction; C-skill (both sides); E-move (an actor from an unloaded cell); E-enable; E-scene | Talk to the keeper again | "Talk me into it." shows; "Talk me into it, master." does not. Pick the first: the Dock Walker appears beside the keeper and the two of them speak two lines each. |
| 6 | 60 | TR-scene; E-package; E-enable (a hostile); AI package priority | Watch | When the talk ends, the walker walks to the ship door. A mudcrab appears 15 m east and comes for you. The walker keeps to her walk (or flees and goes back to it); she does not stand still. |
| 7 | 60 | C-detected (GetDetected, `detectedBy`) | Crouch behind the dock clutter while the walker walks, then step into her view; each time type `player.getdetected ARG_BT_WalkerRef` in the console | Hidden it says 0 (the walker's package also checks it as a PACK condition); in her view it says 1. |
| 8 | 60 | save and reload mid-quest | Save, then load that save | The walker carries on to the ship door; the crab is still there; the journal is as before. |
| 9 | 65 | TR-death; W-fixed | Kill the mudcrab | Objective "Walk to the ship door". The crab was the same strength as on any other day (level 4; `getlevel` on it says 4). |
| 10 | 71 or 72, then 75 | TR-zone; two triggers racing for one stage | Walk onto the planks in front of the ship door | `sqs ARG_BlockTest` shows exactly one of 71 or 72 done, never both, and 75 done. Objective "Open the ship door". |
| 11 | 75 | save and reload; a trigger refiring | Save, load, walk off the planks and back on | Nothing changes: still exactly one of 71 or 72. |
| 12 | 80 | TR-activate; W-override (the lock); setDoorAccess (the key opens it) | Open the ship door | It opens with the key (no lockpick prompt) and you are inside "Test Ship" (W-name, on the loading screen and the map). Objective "Tell the Dock Keeper". |
| 13 | 90, 100 | C-alive; C-time; TR-topic; E-item (gold); TR-chain | Go back out, talk to the keeper, pick "The crab is dead." | His reply says "By day" between six in the morning and eight at night, "At this hour" otherwise (tell us the game hour). 10 gold in your inventory. The journal shows "Block Test" complete and a second entry, "Block Test, the end": "The second quest started from the first." |

Every trigger (7), condition (7) and effect (9) in blocks.md is in the table; of the world edits, W-npc, W-fixed,
W-ref (placement, enable parent and removal), W-name and W-override are; W-navmesh is not (risk 1). The two blocks
whose precedent blocks.md leaves uncounted, E-move and E-regard, each have a step that shows them on their own (steps
1 and 5; step 2).

## The Papyrus (by block shape)

Two scripts, both short and idempotent (enable what should be enabled, give only what is missing, never toggle), as
the save-and-reload guard asks. Everything else is vanilla's own scripts with properties.

`papyrus/ARG_QF_BlockTest.psc`, the stage fragments of `ARG_BlockTest` (each stage holds one empty or written log
entry, as the opening's do, so its fragment binds):

```papyrus
Scriptname ARG_QF_BlockTest extends Quest Hidden
{Phase 3's test quest: every effect block once, in its own shape. Throwaway; the shapes are the templates.}

ReferenceAlias Property Keeper Auto
ReferenceAlias Property Walker Auto
ReferenceAlias Property ZoneA Auto
ReferenceAlias Property ZoneB Auto
ObjectReference Property StartMarker Auto
ObjectReference Property WalkerMarker Auto
ObjectReference Property TokenParent Auto
ObjectReference Property CrabParent Auto
Key Property ShipKey Auto
MiscObject Property Token Auto
MiscObject Property Gold001 Auto
GlobalVariable Property Standing Auto
Faction Property DockHands Auto
Scene Property TalkScene Auto
Quest Property EndQuest Auto

Function Fragment_10() ; start-up stage: E-move (the player), E-stage
	Game.GetPlayer().MoveTo(StartMarker)
	SetObjectiveDisplayed(10)
EndFunction

Function Fragment_20() ; E-item (setDoorAccess), E-enable, E-regard
	Actor player = Game.GetPlayer()
	SetObjectiveCompleted(10)
	If player.GetItemCount(ShipKey) == 0
		player.AddItem(ShipKey, 1)
	EndIf
	TokenParent.Enable()
	Keeper.GetActorRef().SetRelationshipRank(player, 1)
	SetObjectiveDisplayed(20)
EndFunction

Function Fragment_30() ; E-global
	Standing.SetValue(1)
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(30)
EndFunction

Function Fragment_40() ; E-item (taken), E-faction
	Actor player = Game.GetPlayer()
	player.RemoveItem(Token, player.GetItemCount(Token))
	player.SetFactionRank(DockHands, 0)
	SetObjectiveCompleted(30)
EndFunction

Function Fragment_50() ; E-move (an actor out of an unloaded cell), E-enable, E-scene
	ObjectReference w = Walker.GetRef()
	w.MoveTo(WalkerMarker)
	w.Enable()
	TalkScene.Start()
EndFunction

Function Fragment_60() ; E-package (by the alias's package list, gated on this stage), E-enable (a hostile)
	Walker.GetActorRef().EvaluatePackage()
	CrabParent.Enable()
	SetObjectiveDisplayed(60)
EndFunction

Function Fragment_65() ; E-stage
	SetObjectiveCompleted(60)
	SetObjectiveDisplayed(65)
EndFunction

Function Fragment_71() ; the race: disable the other trigger first
	ZoneB.GetRef().Disable()
	SetStage(75)
EndFunction

Function Fragment_72()
	ZoneA.GetRef().Disable()
	SetStage(75)
EndFunction

Function Fragment_75()
	SetObjectiveCompleted(65)
	SetObjectiveDisplayed(75)
EndFunction

Function Fragment_80()
	SetObjectiveCompleted(75)
	SetObjectiveDisplayed(80)
EndFunction

Function Fragment_90() ; E-item (gold), TR-chain
	Game.GetPlayer().AddItem(Gold001, 10)
	SetObjectiveCompleted(80)
	EndQuest.Start()
	SetStage(100)
EndFunction

Function Fragment_100()
	CompleteQuest()
	Stop()
EndFunction
```

Dialogue fragments, one per line that sets a stage, the TR-topic shape (`TIF_ARG_BT_<stage>.psc`, Hidden, extends
TopicInfo): `GetOwningQuest().SetStage(n)` in `Fragment_0` (end). The scene's end fragment
(`SF_ARG_BT_Scene.psc`, extends Scene): `GetOwningQuest().SetStage(60)`. `ARG_BlockTestEnd`'s stage 10 needs no
script: its log entry is the proof, and its stage carries the Complete Quest flag.

## Agent check, before the owner

Read the built plugin and scripts (not the game): every step's stage, condition, alias, property and fragment is
present and points at the right records; every ref a block names is persistent; no NPC_ of ours has PC-level-mult;
every placed actor stands within a 07EEF8 triangle or in `01Ship`; the five Naga overrides are initially disabled.
Loop until it does.

## As built (2026-11-06)

Built by `tools/ArgoniaPlugin/BlockTest.cs` (called from `Generate.cs` after the opening's records), YAML in
`plugin/Argonia`, scripts `papyrus/ARG_QF_BlockTest.psc`, `TIF_ARG_BT_20/40/50/90.psc`, `SF_ARG_BT_Scene.psc` (8 of 8
compiled, 0 errors). The agent check is `bash tools/ArgoniaPlugin/plugin.sh blocktest` (BlockTestCheck.cs: the ESP,
the .pex strings, the compile log); all 13 steps pass. Where the build differs from the design above, and why:

- **One branch per keeper line.** A topic shows one menu choice (its first passing INFO), so "Talk me into it." and
  its "master" twin must be two topics for step 5 to show one and hide the other. Each line is its own top-level
  DLBR and DIAL (`ARG_BT_Topic20`, `40`, `50`, `50Never`, `90`); the two "crab is dead" replies are two INFOs of
  `ARG_BT_Topic90`, the first that passes wins. Every INFO also carries GetIsID Keeper.
- **The scene's lines** are four Scene-category topics (`ARG_BT_Scene1` to `4`), one INFO each.
- **The ship door is off 07EEF8.** 07EEF8's east edge is about 17 m short of door 0AA664; the navmesh under the door
  (0FE9A3) belongs to another worldspace, and BlackMarsh has none at dock height there. So `ARG_BT_DoorMarker` (the
  walk's end) is 07EEF8's nearest triangle, and the two zone boxes (the player's, not an actor's) sit on the door,
  1.5 m toward the dock (32087,-2475). The crab's "15 m east" snaps to 07EEF8's nearest, 15 m south-east.
- **C-detected on the package** is `GetDetected Player >= 0`: the condition is read on the PACK, the walk never gated.
- **TriggerType 0** (on activate) for the door's alias script, from vanilla's activate aliases (SolitudeFreeform07's
  HornActivator, TutorialEnchanting's FarengarEnchanter).
- **Stats are ours**: the three bases inherit everything from their templates but Stats and Base Data (name,
  Protected), with fixed levels 5, 5 and 4 and AutoCalcStats on the template's class.

Positions (07EEF8 triangle): start marker 30535,-2646 (29), keeper 30757,-2589 (32), walker marker 30714,-2461 (31),
door marker 30981,-3029 (22), crab 31351,-3506 (189), token 30603,-2893 (25); the walker in `01Ship` at 2907,5107,7046
(0AA666 triangle 28).

## Owner test

One issue: the console command, where it puts you, and the step table's last two columns. You play it once and reply
with any step that did not happen. A broken block is fixed and only that step re-posted; if it cannot be made reliable
it is dropped, and the Phase 2 records that used it are re-authored before Phase 4. A step that passes is never
re-tested.

## Block W-talk: a BM&V person's own topics (added 2026-11-07)

A new kind of change (owner, 2026-11-07): BM&V's people open no dialogue, because Skyrim opens the menu only on a
topic gated to that speaker and BM&V ships none ([talk.md](../design/talk.md), measured). Built in
`tools/ArgoniaPlugin/Talk.cs` from the story data's talk tables: quest `ARG_Talk` (Start Game Enabled), one
top-level topic per topic kind, one INFO per person gated GetIsReference to their placed ref; Flaa Heet (no voice
type) gets our silent voice type `ARG_TalkSilentVoice` by a base override. Lines are subtitles (Fuz Ro D'oh).

As built: all 12 talkable Lilmoth people (`bmv_talker`, settlement Lilmoth), 9 topics, 53 responses; the read-back
of out/Argonia.esp finds every person's topics gated to their ref (12 of 12), ARG_Talk start-game-enabled, the
voice override in place. Not this block: Lilmoth's five Naga (hostile) and the three Dunmer corpses. The rest of
BM&V is [Phase 4a](4a-talk-to-everyone.md). Owner check: docs/owner-walk-checks.md, Phase 3 section.

## Risks

1. **W-navmesh is not on this route.** The dock and the ship both have navmesh, and navmesh is made only in the
   Creation Kit, so the test cannot prove it. It is proved on its own, once, in the first slice room without navmesh
   (BC02's cells) when that is built, with the same agent read-back (NAVM in the cell's group) and one owner look.
2. **The ship door is MQ05's route.** The lock override on `0AA664` and the "Test Ship" name sit on MQ05's door and
   room; both go when the test records are removed after the walk, before MQ05 is built. The build check fails if any
   `ARG_BT_` record or these two overrides remain once Phase 3 is done.
3. **Five hostile Naga stand on the dock today** (`we.clean.lilmoth` is ledgered, not yet built). The test builds
   their five disables first; without them step 1 is a fight.
4. **SCEN, PACK and DIAL by Mutagen are new to our generator** (it has written only QUST, GLOB, worldspace refs and
   story-manager records so far). The first build may need a round of read-back in xEdit; the shapes then stand.
5. **The race (step 9) may not race.** Two boxes in the same place fire in the same frame only if the engine handles
   both enter events before either fragment runs; if one always wins first, the guard is shown to hold but the race is
   not proven. A pass is "exactly one of 71 and 72", whichever way it comes.
6. **Package priority is judged by eye.** A mudcrab may draw the walker into combat (she is a villager and will flee);
   the pass is that she returns to her walk once it ends, not that she ignores the crab.
7. **C-skill's line depends on the start's Speech.** Every race starts at Speech 15 or more, so ">= 15" shows and
   ">= 100" does not; a character built with a perk or a mod that changes the base would need the threshold moved.
8. **TriggerType for the door's activate alias script** is copied from a vanilla use, not read from source (pex
   bodies are compiled); if the door's activation is consumed by the load, the alias script may not fire before the
   teleport. The fallback is the same script on a trigger box inside the ship's entry (TR-zone), and TR-activate is
   then proved on the token itself (`defaultSetStageAliasScript` on activate) instead.
9. **Silent lines.** With no voice type the lines show as subtitles for a moment; the owner reads the choice text.

**Done when** every step has passed in the owner's walk, and the test records are removed.

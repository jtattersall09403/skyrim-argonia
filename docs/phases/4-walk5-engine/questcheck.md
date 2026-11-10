# Brief: `plugin.sh questcheck`, one read-back over every quest of ours in the built plugin

Repo: /home/ubuntu/skyrim-argonia (read CLAUDE.md). You work in an isolated git worktree of it (another agent is
refactoring the quest builders in the main tree at the same time; do not edit any existing *.cs except Program.cs,
plugin.sh and, if needed, a small extraction from Inspect.cs's navpath code into a shared static). Never run the game.
Background: /tmp/claude-1000/-home-ubuntu-skyrim-argonia/076ab6a8-7438-4fd6-9a59-df6ba0cf5c1a/scratchpad/review/engine.md
sections A, B, C, D (read them: they are the faults this check must catch, with the record evidence).

## What to build
`tools/ArgoniaPlugin/QuestCheck.cs` + `case "questcheck"` in Program.cs + `questcheck) build; tool questcheck "$esp" papyrus "${lo[@]}" ;;`
in plugin.sh (and its line in the usage comment). Generic over every quest in Argonia.esp whose EditorID starts `ARG_`
except ARG_BlockTest*, ARG_Opening (no per-quest tables). It reads the ESP, the load order (navmeshes, base records)
and the Papyrus SOURCE (papyrus/*.psc and papyrus/generated/*.psc: .pex are compiled elsewhere, so the source is the
truth here). Prints one `FAIL <quest> <rule>: <what, with form ids/editor ids>` line per fault and a summary
`questcheck: <n> quests, <m> failed checks`; exit 1 on any failure.
Structure: a loader that builds a plain model (quests, stages with log text and flags, objectives with targets,
aliases with flags/forced ref/packages/scripts, zones = placed refs with defaultSetStageTrigScript, packages,
INFOs with conditions and fragment script names, quest-script functions parsed from .psc), and one pure function per
rule over that model, so each rule is unit-testable on a hand-made model.

Papyrus parsing (enough, not a compiler): per script, functions/fragments -> list of calls; `SetStage(<int>)` and
`<Prop>.SetStage(<int>)` (Prop resolved through the quest's VMAD properties to another quest), `GetOwningQuest().SetStage(n)`,
calls of the quest script's own functions (resolve transitively, with int literal arguments bound to a parameter used
in `SetStage(param)`), `<Prop>.Enable()/.Disable()`, `<Alias>.GetRef()/GetActorRef().Disable()`, `.Lock(False)`,
`AddItem(<Prop>`, `Stop()`, `Is3DLoaded`, `EvaluatePackage`. TIF scripts: the INFO's fragment script name -> its file.

## Rules (each fails the build)
1. route: every alias package with a location (Travel/sandbox/sleep: the LocationTarget ref) or a follow target
   (PlayerRef): start = the alias's forced ref's placed spot; destination = the target ref's spot, or for a follow every
   zone of the quest whose prerequisite stage is a stage the package is gated on (== S or >= S). Both must lie within
   150 units (x,y; and within 200 in z) of a triangle of ONE winning navmesh (last plugin in the load order that has the
   NAVM; a winner with no data is DELETED: fail naming it), and a breadth-first walk over that mesh's triangle
   adjacency must join them (reuse Inspect.cs navpath's walk: lines ~102-140). An interior with no navmesh under the
   spot fails. Exception: a destination over water (no navmesh) for a follow is not an exception: fail.
2. start: every Travel (location, no ScheduleHour >= 0, no GetCurrentTime condition) alias package gated on GetStage
   >= S or == S: every setter of S must be (a) a zone, door alias or INFO whose spot (zone/door position; the INFO
   speaker's ref spot) is in the same cell (interior) or within 4096 units in the same worldspace of the walker's
   start, or (b) a quest-script function that calls `Is3DLoaded` before its `SetStage(S)`. A schedule or clock-gated
   package passes (it may start unseen by design). Follow packages pass this rule (started by the person's own line).
3. shape: every alias package is `Type == Package` (never PackageTemplate) and has a non-null PackageTemplate link.
4. stages: every stage of the quest except the start-up stage has at least one setter that is reachable (setters:
   zones (prereq stage must itself be reachable), alias scripts defaultSetStageOnDeathRefAlias / OnPlayerAcquire /
   defaultSetStageAliasScript (prereq), INFO fragments, quest-script functions and fragments of this or another quest
   (NextQuest.SetStage), Start Game Enabled's stage 0); a death setter on an alias flagged Essential, or whose forced
   ref's base has the Essential flag, does not count and is itself a failure. Every stage with log text that is not
   an ending (no CompleteQuest/FailQuest flag) must display at least one objective (SetObjectiveDisplayed(n) in its
   fragment or a function it calls) and every objective must have at least one target (QuestObjectiveTarget). A
   non-ending stage with no way out (no stage above it reachable from it) fails.
5. endings: every quest has the RunOnce flag; every ending stage's fragment (with the functions it calls) calls
   `Stop()` and disables every zone of the quest (each zone ref reached by a `.Disable()` on its property or alias, or
   one call to a function that disables a `ObjectReference[] Zones` property holding them all, which the quest's VMAD
   must fill with exactly the quest's zones).
6. zones: no two zones of one quest overlap when one's stage is the other's prerequisite.
7. people: no two of our placed NPC refs with the same displayed name (base Name) are enabled at once at any point of
   a simulated run of the quest's fragments in ascending stage order (initial state from the record flag 0x800 and the
   enable parent chain, incl. SetEnableStateToOppositeOfParent; Enable()/Disable() calls on refs and parents) when
   they stand in one cell, in two cells joined by a door pair, or within 8192 units in one worldspace.
8. offers: every INFO of a quest Topic (not Hello) whose conditions name the quest's own GetStage must have an upper
   bound (== s, < s or <= s) below the quest's first ending stage; `>= s` alone fails.
9. doors: every door ref our plugin overrides with `LockLevel.RequiresKey` and a key: on every ending of the quest whose
   script holds that key (or door) as a property, the key is given (AddItem) or the door unlocked (.Lock(False));
   else fail ("locked out on ending 91").
10. objectives: every objective has a target (also counted in 4; report once).

## Tests
Put the rules' fixtures in code: `ArgoniaPlugin questcheck --selftest` builds small hand-made models (one passing and
one failing case per rule) and exits 1 if any rule misjudges; add `tools/tests/test_questcheck.py` that runs
`dotnet <built dll> questcheck --selftest` (build with `dotnet build -c Release -o out/tools/ArgoniaPlugin tools/ArgoniaPlugin`
first; skip the test if ~/.dotnet is absent) so `make check` runs it.

## Prove
`tools/ArgoniaPlugin/plugin.sh questcheck` on today's plugin (run under `tooling/job_guard.sh run <name> -- ...`, then
`job_guard.sh wait <name>`; never sleep or poll): it must FAIL on today's records with at least these (from the review):
ARG_MQ01 start (MarchOff gated on 30, set by the hold's door), ARG_BC01 route (PatronAtLanding from an interior with no
navmesh), ARG_BC01/BC02 shape (template-type follows), ARG_MQ04 route (deleted navmesh: it may pass if the spot is on
0C7102; report what it says), ARG_MQ05 endings (no Stop()), ARG_MQ01 endings (zones not disabled), death setters on
Essential aliases (MQ03, BC01, BC02, BC03), offers (BC01 TheEstate >= 10, ...), doors (MQ03 key only on 90), people
(MQ01 Wuleen-Sei twice), objectives without targets. Paste the summary and the FAIL lines grouped by rule.
`--selftest` passes; `make check` green for what you touched (ruff on the .py test).
Commit in the worktree branch with `git commit -- <paths>` (only QuestCheck.cs, Program.cs, plugin.sh, Inspect.cs if
touched, tools/tests/test_questcheck.py), message ending with "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>".
Do not push. Return at most 20 lines: the branch and commit, the selftest result, the FAIL summary per rule on today's
plugin, and any rule you simplified and how.

# Brief: the quest recipe's engine sections as a clean recipe

Repo: /home/ubuntu/skyrim-argonia (read CLAUDE.md, and its rule: docs read as the current recipe, never as history or
feedback; no dates, no "walk 5", no "was", no review ids). Other lanes edit other parts of these files at the same
time: change ONLY docs/design/blocks.md (the rows named below and its "Where the argument fails on this engine" table)
and docs/design/quests-on-a-world.md sections 4, 5 and 8 (lines from "## 4." up to "## 6." and from "## 8." up to
"## 9."). Use targeted Edit replacements, never rewrite a whole file, and commit promptly.

Source text: /tmp/claude-1000/-home-ubuntu-skyrim-argonia/076ab6a8-7438-4fd6-9a59-df6ba0cf5c1a/scratchpad/review/engine.md
section F (paste-ready text), adjusted to these decided facts (the engine lane is building them now):
- One navmesh island per walk: every walk a quest asks of a person (travel, follow to an end zone, sandbox) lies on one
  winning navmesh, proven off game (`plugin.sh inspect navpath`, and `plugin.sh questcheck`). We author no navmesh and no
  edge links in BM&V's worlds. A quest whose people would have to cross islands is hosted where they need not, or the
  person is moved by a stage's fragment while the player can see neither spot (an unloaded cell or another cell),
  never in view.
- Start circumstance: no walk becomes eligible while its people are unloaded if the player is meant to see it start:
  the walk is gated on a hidden stage that the quest script sets once every walker's 3D is loaded (a once-a-second
  update in game mode, bounded at 60 checks), and that stage's fragment calls `GetActorRef().EvaluatePackage()` on each
  walker. A schedule or clock-gated package may start unseen and says so. A follow starts from the person's own line.
- A guide never ends in nothing: the walk ends inside the zone (or within the distance) that sets the next stage; the
  objective marker sits on that place; if the player arrives first, the stage's fragment puts the walkers there.
- Run Once and endings: every quest is Run Once; every ending stage's fragment completes the shown objectives, disarms
  every trigger zone of the quest (the kit fills the quest script's `Zones` array; `DisarmZones()`), counts a side
  quest, and calls `Stop()` last; every stage two triggers can set is guarded by a variable read and set with no call
  between.
- Objective targets: every objective has at least one target alias (person, door, zone marker or thing); the kit
  refuses an objective without one.
- Death triggers: a person whose death moves the quest is Protected on the alias with a death trigger; a person who
  must live is Essential and has none; the kit refuses a death trigger on an Essential alias or base.
- One person, one ref enabled at a time: where two refs stand for one person, the fragment that enables one disables
  the other while the player sees neither.
- Doors: a door a quest sends the player through is openable on every path (its key or its unlock on each path).
- Offers: every quest topic INFO has a last stage below the quest's first ending; nobody offers a task after its end.
- The one quest kit (tools/ArgoniaPlugin/QuestKit.cs): every builder uses its helpers (conditions, stages and
  objectives from the story rows, forced aliases, topics and choices with their wording bands, Travel / Follow /
  Schedule packages copied from vanilla packages of type Package with the owner quest set, zones, doors, objective
  targets, endings, `Snap` to the winning undeleted navmesh); a builder never copies a helper or builds one of these
  by hand; a condition that needs another builder's quest is added in a finish step after both exist and the build
  fails if it cannot be; builders run in a fixed order so form ids never move.
- The quest check `plugin.sh questcheck`, generic over every quest of ours in the built plugin, fails the build on:
  a package route not on one island (or on a deleted navmesh), a walk that can start unseen, a template-type package
  on an alias, a stage with no reachable setter or (non-ending) no way out, a visible stage with no objective or an
  objective with no target, a death trigger on an Essential alias, a quest not Run Once or an ending that does not stop
  it and disarm its zones, overlapping consecutive zones, two refs of one person enabled at once, an opening INFO with
  no upper stage bound, a key-locked door not opened on every ending path. It runs beside the per-quest read-backs
  (mainquestcheck, mqcheck, bccheck, nightreedcheck, localcheck) and placecheck; 0 failures before deploy.
- blocks.md: replace the TR-zone, E-package and E-stage rows and the failures table rows with F's text adjusted to the
  above; merge E-target into E-stage ("objective with a target alias") if blocks.md has a separate E-target or says
  "objective, no target". Do not touch blocks.md's generated stage tables (another lane owns them).
- quests-on-a-world.md: section 4's "Walking" bullet and the new bullets from F; section 5's table rows from F (people
  who lead, an escort, a person at a place by the clock, a person moved elsewhere, a quest that is over, a zone, a
  death, a thing needed back) and its "Engine rules" and "Code" bullets; section 8 the quest check bullet. Keep each
  section's existing correct content; remove anything these replace or contradict (e.g. "the alias filling applies it",
  "an escort reaching a place: a follow package" without the island rule, "0 edge links": the measured figure is 5 link
  entries in 17,591 navmeshes, none on any route a quest uses).
Acceptance: `git diff docs/design/blocks.md docs/design/quests-on-a-world.md` touches only the named parts; no sentence
reads as history (grep for "walk 5", "review", "was ", "used to", "now " finds none you added); commit with
`LANE_COAUTHOR="Claude Opus 5.5 <noreply@anthropic.com>" tooling/lane_commit.sh -m "docs: the quest recipe's engine rules (one island per walk, start in view, Run Once and endings, targets, death triggers, the one kit, questcheck)" -- docs/design/blocks.md docs/design/quests-on-a-world.md`.
Return at most 8 lines: the commit and the parts changed.

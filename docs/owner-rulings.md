# Owner rulings that still bind

The owner's rulings from 2026-10-27 to 2026-11-05 that survive the pivot ([0038](decisions/0038-the-pivot-bmv-is-the-world.md)),
in the owner's terms. Everything else the owner said before the pivot is in git history
(`docs/owner-brief.md`, `docs/inherited-rulings.md` before this commit) and no longer binds. New rulings are
added here the day they are made, with the date and the issue.

## The goal (2026-11-05)

- Vanilla Skyrim + Black Marsh & Valenwood + the collection xyf1u3 for soulslike combat, out of the box +
  FreeClimb + Morrowind magic (Magic Expanded). BM&V is the default world: a start mod puts the player in Black
  Marsh; the main quest, dragon attacks, the civil war, the Thieves Guild couriers and Skyrim's radiant quests are
  stopped.
- A new game takes the player straight into our own authored opening, nothing via Helgen and no alternate-start
  menu, as Enderal does it (2026-11-05).
- No owner test in Phase 0; the first walk is after Phase 1, with a Vanilla Skyrim card and the Argonia card
  on the play page to try both at once (2026-11-05).
- Agents verify by reading the files the game will consume (the ESP, the scripts, the DLLs, the profile) and
  loop until that read meets the bar; they never run the game themselves (2026-11-05).
- The BM&V census into the relational story data runs in Phase 1, beside the stack (2026-11-05).
- Write and review the first act before building any block, so the blocks are the ones the story needs; aim for
  a small set of blocks that combine into many quest dynamics, so proving each once (and their connectors once)
  proves every quest built from them, like a proof by induction; if a block is too hard, re-author the quests
  around the blocks that work (2026-11-05).
- An offline interactive 2D map of BM&V's world, linked to the mined place records, for the owner and agents
  (2026-11-05).
- Decided by the agents under the owner's hand-over (2026-11-05, "gate nothing on me; full permission"): the four
  free Creation Club files' self-starting quests are stopped like vanilla's; our plugin ships `Argonia.ini` to blank
  the race-menu bound-hands pose, as Live Another Life does; the opening marker stands on Lilmoth's pier, a dock
  arrival; the Creation Kit EULA was accepted with the owner's OK.
- Phase 2 adapts the entire quest system and every faction line to BM&V's world (minor world edits allowed), keeping
  each line's spirit, designed once as a consistent whole with no clashes; minor lines adapted or dropped; a wider
  minor-quest build-out is a Phase 5 placeholder (2026-11-05).
- BM&V is used whole, all four plugins and every file of both ModDB parts; all of it goes through the census and the
  map (2026-11-05).
- The first story slice (owner, 2026-11-06): BM&V's world stays as it is (separate worldspaces, not stitched into one
  walkable land), with only the allowed minor edits; fitted to it first are (a) the opening act of the main quest,
  including the new-game flow and the opening scene (our Helgen), and (b) a sensible subset of non-clashing factions
  and questlines. Get that working in the modded world for the owner to try, then decide what else to change. The
  world-option analyses (joining the worldspaces, extending the land, interiors and places) are still posted as calls,
  but nothing waits on them.
- The play machine signs the Administrator in automatically at boot (Sysinternals Autologon, the password stored
  encrypted), so Sunshine's cards can start after any reboot (owner, 2026-11-06).
- An agent may launch the game to warm Community Shaders' shader cache before the owner plays (owner, 2026-11-06);
  it tests nothing that way.
- The quest review loop (owner, 2026-11-06): the planner judges which findings matter and when the loop ends, not
  a reviewer finding nothing; one shared bar for "blocking" (an unfinishable path, a contradiction with the record,
  the world or the lore, a 0006 or 0035 breach); settled findings stay settled; fixes subtract before they add;
  a branching budget keeps quests simple (some branching for interest); agents write only what the lore and data
  give, so no unsourced claims are made in the first place; quests lean on action, danger and discovery, not on
  law and custom; no long hand-overs (small fixer agents, the loop's state in a file). Blocking also covers a quest
  that does not use the player's in-game skills (not fun) and one harder to script than an average Skyrim quest.
  Within a questline, earlier choices and endings do not change later quests' stages (no multiplying branches);
  only planned finale choices carry forward. The whole main quest is reviewed against these rules: keep the
  treasure hunt, the spies and its spirit, make it more Black Marsh, more exciting, less bureaucratic.
- Then our storyline, quests and factions on top of BM&V's world, with minimal tweaks (NPCs, items, bosses,
  creatures added, removed, changed). This is the main work, in phases.
- Process as light as possible. Agents avoid in-game testing if at all possible; the owner tests. Test a small
  number of building blocks once, then build everything from them.
- Delete as much as possible; this was a throwaway repo. Keep the build machine and the Paris g6.xlarge play
  machine; keep the rule that build-machine agents assume frequent interruption.

## Machines and money

- AWS London; the $100 a month cap is for AWS infrastructure only and binds from November 2026.
- The build VM is on demand (the owner's change, 2026-11-05) and runs only about 8 to 10 hours a day; the play
  machine stays spot. Every job resumes from where it got to after an interruption (decision 0037).
- Agents may always start and stop the game machines; a stop is never a reason to wait (2026-10-30).
- The game machine runs Windows (the licence cost is approved); the build VM stays Linux.
- Tidy up: delete temporary files, captures and anything we will never need, on the VM and in the bucket; never
  archive rubbish "to be safe" (2026-11-02). Claude usage is reported as a percentage of the weekly allowance
  (about 1% per $19), never in dollars.
- Stale machine images are deleted (2026-11-02, "explicit permission"); the owner deleted the last ones and the
  play machine itself on 2026-11-05.
- The play machine must not be interrupted often; the owner will pay a bit more, but not on-demand (2026-10-31).
  A g6.xlarge is comfortably strong enough; use whichever region is expected to interrupt less at a similar
  price (2026-11-05); Paris has been the machine since 2026-10-31.
- Changes to the owner's live services (the play-switch Worker, the play page, the stream config) get an owner
  call first (2026-10-30).

## Playing

- The owner plays entirely in third person (2026-10-29).
- Controls: keyboard and mouse on the Mac; on the phone the GameSir X2s or on-screen touch; the whole game must
  be playable by touch (2026-10-28). Moonlight's Android app is an option.
- The gamepad follows DS1 Remastered on Switch by button position: roll on the right button, R1/R2 light and
  heavy, L1 block, L2 parry (2026-10-29). The collection's own bindings are the starting point now.
- Latency and stream health are logged automatically; the owner never records anything by hand (2026-10-28).
- Cheats and shortcuts (god mode, item grants, teleports, setstage) are allowed whenever they make something
  easier to test (2026-10-28).

## Working with the owner

- One GitHub issue per owner check or owner call (`tooling/owner_inbox.py`), assigned to the owner, closed when
  answered; an owner comment wakes the build VM (wake.yml). Only the owner's own GitHub text counts; the repo
  is public (2026-10-31).
- Owner check-ins are plain English: one check per bullet, places named, how to reply, costs.
- Hand over nothing partially finished; "known issues" only for what truly cannot be fixed, each with why
  (2026-10-30, 2026-11-03, 2026-11-04).
- Method changes are applied and recorded without asking; a goal change is an owner call (2026-10-28).
- The owner judges look; agents check for Nordic tells, never feel (2026-10-30, #43).
- Agents stop only when the work is complete, a blocker needs the owner, or at a handover the owner asked for.

## The game

- Set in Argonia (Black Marsh), 4E 201; no Nordic element reaches the player through what we add (0006);
  Skyrim's own voiced barks stay, filtered of lines naming Skyrim places, people or events (2026-10-31, #22).
- Dialogue is unvoiced text, Morrowind-like in structure and style; the writing rules live in the
  `dialogue-write` skill and `story/design/text/` (2026-10-27, 0024).
- Nothing is ever levelled against the player: creatures, enemies, loot, chests; danger bands are fixed and the
  player grows into them (2026-11-01, 0035).
- Quests have "action" (the player's skills used, varied), no talk-to-X-then-Y quests; the old main quest,
  factions and quest designs are the foundation, improved not replaced (2026-10-28).
- A detectives' faction, rival to the assassins and thieves (0025).
- A creature from a mod is used as its mod designed it (2026-10-30).
- Magic is mostly covered by Magic Expanded; reuse it rather than build magic (2026-10-30).
- Interiors may look Nordic where a borrowed interior is all there is (2026-10-30); exteriors are BM&V's.
- Armour pieces stay as base Skyrim has them (2026-10-31, #21).
- Climb anything big enough, Breath of the Wild style, through FreeClimb (2026-11-01).
- Parry, riposte and backstab are what the owner called souls-like (2026-10-29); the collection is used out of
  the box first, and that ruling is revisited only if the owner misses them.

## Writing

- Lines read as if they were Morrowind's, adapted to Black Marsh; the old written lines are not models.
- No personification, no verbless fragments, no dangling modifiers, nothing opaque to the player; British
  punctuation; held-back information says so; banned constructions live in `dialogue-write/bans.yaml`.
- Speakers and players may be any of the ten races; address and manner vary by player race, faction and rank.
- Quests, places, dialogue, characters and facts are consistent first time, by how they are written.
- Every world, people and quest call cites the lore dossiers (`story/lore/`) or the extrapolation (0032).
- 2026-11-06: the whole of the soulslike collection xyf1u3 is in the stack, Nordic-themed parts included ("I want
  the full mod stack from that collection in, even if there are some nordic themed elements"); decision 0006 item 4.
- 2026-11-06: reviewers return every finding they need, no cap in any round; the 3NF story database is the single
  source of truth.
- 2026-11-06: owner-facing writing assumes no context: every name explained, full sentences, no shorthand.
- 2026-11-06 (#51): TrueHUD's player bars on. Add Rim Parry And Execution and Elden Parry. GameSir layout like Dark
  Souls: B dodge/sprint, LB block, RB light attack, RT (R2) heavy/power attack, LB+RB parry then RB riposte (Rim
  Parry And Execution), the Tween menu on d-pad left/right, LT shouts; RB pressed during a dodge queues the attack
  for straight after the dodge.
- 2026-11-06 (#51): TrueHUD's player bars on (done, fbdff408). Add Rim Parry And Execution and Elden Parry.
  GameSir layout like Dark Souls: B dodge and sprint, LB block, RB light attack, RT heavy or power attack, LB+RB
  parry then RB riposte (Rim Parry And Execution), LT shouts, the Tween menu on d-pad left or right; RB pressed
  during a dodge queues the attack for straight after it.
- 2026-11-06 (#51): Precision (Nexus 72347) goes into the stack. On the attack queued after a dodge the owner wrote
  "*make* the dodge mod support it" and "Writing our own skse code absolutely should not be ruled out by our build
  rules, I want to rule that in, make that change now". Our own SKSE plugin is allowed where no mod, record or
  script does the job (CLAUDE.md and PLAN §6 changed the same day).
- 2026-11-06 (#50): every quest uses named Skyrim skills (One-Handed, Two-Handed, Archery, Block, Destruction,
  Alteration, Illusion, Conjuration, Restoration, Alchemy, Sneak, Lockpicking, Pickpocket, Speech, Mysticism, plus
  climbing and swimming), and names which. Every main quest offers at least two ways through, each with different
  named skills, so different builds can finish it. Faction quests are tied to the faction's own skills ("for
  consistency and immersion"). The opening is too slow. Every stage must make plain what to do (e.g. the dive for
  the bronze thing). MQ05's tree climb is pointless (and tree climbing is buggy): replace it. Update the slice quests.
- 2026-11-06 (#53): you can run with a weapon drawn (Arena Movement's faster variant). Explicit permission to
  override the safety check to install the attack-queue plugin. Swimming and climbing are not skills: they do not
  count as skills in quest writing.
- 2026-11-07 (walk feedback): never disable, rewrite or toggle the build VM's CloudWatch idle-stop alarm (the owner's
  `idle-stop-build-machine`: CPU at or under 3% for 6 periods of 5 minutes); for longer waits keep the CPU above 3%
  instead. The g4dn on-demand machine is the play machine from now on; retire the g6 spot and every snapshot, image
  and volume no longer needed. Every BM&V person must be talkable: a light backstory grounded in their place,
  profession and spot, their own set of topics (some shared) that are all true in the world (places and how to get
  there, nearby danger, rumours that lead to quests, loot spots, local ingredients, and more), written with the
  dialogue writer. Enemies and the player must stagger when hit: use the stack's poise mod if it has one, else add
  Nexus SSE mods 74032 and 72653 with all their requirements. Standing still, a dodge tap is a backstep (hop back),
  not a backward roll. An attack pressed during a roll fires when the roll ends.
- 2026-11-07: the g4dn's $0.80 an hour is fine: play is about 20 hours a month at most, not 50; the play machine
  must stop itself when the owner is not playing (its 15-minute idle stop stays on).
- 2026-11-07: every BM&V person must be talkable, with a light backstory grounded in their place, trade and spot, and their own topics (directions, dangers, rumours that lead to quests, loot spots, ingredients, more), every fact real and true in the loaded world; do all of Lilmoth's people now, and put a phase in the plan for the rest (Phase 4a, docs/design/talk.md).
- 2026-11-08 (walk-2 feedback, tmp/walk-2-feedback.md): TrueHUD's new-game defaults are the mod's own except display
  criteria "dynamic" for all three player bars, hide vanilla bars on, bar width 150 (minimum 50, maximum 500), scale
  bars on, player widget anchor X 0.045 and Y 0.105. The player's health does not regenerate; magicka and stamina do.
  The compass is back on (the owner needs it to follow directions). A weapon drawn runs at the normal run speed, not a
  fast walk. Elden Parry's window is widened again (hard, not impossible, over the stream). A standing dodge is one
  backstep, not two (unless that is the mod's own clip). Magistrate's Levitate (Nexus SSE 24695) goes into the stack
  and its Levitate spell into the starting Magic menu. Talk: each person needs their own personality and their own
  knowledge, written into the speaker brief so the dialogue writer flavours their lines; every Lilmoth person is
  talkable and named; the Looks-At-Books trader gets topics and a stock that fits a small trader. Lilmoth's walk-in
  shell buildings count as rooms for quests and homes. Fix the windows that render as flat blue panes in Lilmoth.
  The next walk re-tests only the blocks still unproved, not the whole test quest. The world map: investigate and
  plan (native or 2d parchment with fog of war, whichever is easiest and most reliable); do not build it yet.
- 2026-11-08 (after walk-2 fixes): build the world map fix now (it is small). Walk-in shells need a census of every
  place in the story data (done: `bmv_shell`). Backstab must actually work, not be explained. The standing backstep
  goes about half as far: the first of its two pushes, by trimming Dynamic Dodge's clip (the owner checked its
  permissions: customising is allowed) or by a shorter backstep clip, whichever is better. A lore fact said by two
  or three people is fine. The "New Order" soldiers' lines must be consistent with our lore, as everything must.
  Skyrim ingredient names are fine where BM&V places those ingredients.
- 2026-11-08 (walk-3 feedback, tmp/walk-3-feedback.md; ticks in docs/owner-walk-checks.md, e570c531): passed: no
  health regen, compass, drawn-weapon run, Levitate, the parry window, Lilmoth's windows, the world map in all three
  worlds, block checks A to D. The standing backstep: cut the clip itself at the end of the first push (holding the
  keys while the clip plays whole "looks stupid"). TrueHUD: start from the Player Widget's "Combined" preset, then
  apply the owner's tweaks (Dynamic for the three bars, hide vanilla bars, width 150, min 50, max 500, scale bars,
  anchor X 0.045, Y 0.105). "Block Test, the end" shows "completed" but is missing from the journal's completed
  list (Block Test is there; Stats count 2). Directions are Morrowind's: a route by real landmarks taken from the
  world (follow the shore, swim to the island, take the path north, on your left a ...), varied by person and
  context; paces and a compass point only where the place is close. "My friend" at most once or twice a person, and
  friendly address only where the person's standing with the player warrants it. Every topic fact is true of BM&V's
  world (not the old place records: Lilmoth's "lighters, no big ships" is false, a big ship docks); the old repo's
  naming rules apply to these people; the recipe for naming people, personality and topics becomes a skill. The
  backstab is Dark Souls': stand behind someone, locked on or not, and a normal attack does Rim Parry's backstab and
  execution. Skyrim's normal game music is on for now (Argonia music later). Walk-in shells: the owner dropped the
  walk check. Walk checks: ticked checks stay where they are as the record; add the fewest checks that prove the
  change; the owner reports problems in the session. Goal for the session: resolve the walk, then deliver Phase 4
  with names, topics and dialogue for everyone in the places the opening act visits.
- 2026-11-08 (new worldspace, nw-01, in session): the new worldspace runs in parallel with the BM&V work
  (docs/phases/new-worldspace-plan/). Project Tamriel's Black Marsh map, its regions map and the Hammerfell/High Rock
  key are public domain and are kept in the repo (newworld/sources/maps/), since they are the base the world is built
  from.
- 2026-11-08 (new worldspace, nw-02, in session): the phase is delivered including the LOD (the brief had it after
  the owner's walk; the owner changed this the same day). The goal is reached when the world, its LOD and the
  in-game world map are deployed and the owner's walk check is posted. The owner's edits to the plan (nw-02's brief,
  the README's lessons and the permission to use every mod named in the new-worldspace plan, nw-03's additions, the
  CLAUDE.md rule on updating skills after verified feedback) are committed as written.
- 2026-11-08 (walk-4 feedback, tmp/walk-4-feedback.md, in session): personification is banned in all dialogue (an
  inanimate thing doing a person's act: "the roll adds months", "the hold heard you"); every line we have is swept for
  it. The opening needs more quest stages with journal entries: talk to Wuleen-Sei, go out of the hold's door, then
  what to do next. Everyone in every place the slice quests touch talks, the opening barge's people included.
  Buys-the-Months must let the player give a name. Mee-Tuja's height is wrong (about 12 feet). Audit every door we
  have changed: one did nothing, another showed a room but teleported out. Many people near Lilmoth's docks lost
  their dialogue: a regression to fix. The standing backstep becomes Skyrim's own vanilla backstep, not the truncated
  Dynamic Dodge clip. TrueHUD's Combined preset did not reach the game: apply it. The backstab gave the stagger but
  not the execution or its damage: make the execution play.
- 2026-11-08 (nw-02, in session): the old pipeline never fully fixed hard texture edges (it did fix the bare pebble
  swathes), so the new world's texturing proves edges gone by measurement and by looking at close crops. Water
  classification faults: closed little bodies classed as stream must be swamp, marsh or pond; a closed larger body
  is one congruent marsh, not part marsh and part stream; river stretches are never blackwater swamp. Fixed at the
  method's root and checked by a visual loop over the map in chunks until it reads sensibly.

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
  is one congruent marsh, not part marsh and part stream; river stretches are never blackwater swamp; flow directions were mostly wrong (downstream along each channel to its
  outlet, from the channel graph, never across a channel or reversing mid-channel; a flowing channel may run into a still body, where its flow stops, and
  flow starts again where a channel leaves it). Fixed at the
  method's root and checked by a visual loop over the map in chunks until it reads sensibly.
- 2026-11-08 (nw-02, in session): King of the Murkmire, Tropical Skyrim, Depths of Skyrim and the other world-asset
  mods are asset dependencies of the new world's plugin, not active plugins: their meshes and textures are laid,
  their plugins stay off, and ArgoniaNewWorld.esm carries its own copies of the base records it uses (never mastering
  them).
- 2026-11-08 (in session): the personification ban goes into the dialogue skills now, without waiting for the owner's
  next walk; the owner is changing CLAUDE.md's rule on when skills are updated.
- 2026-11-09 (new-world feedback, tmp/new-world-feedback-2026-11-09.md, in session): every place promises only
  what Skyrim's own systems can deliver (a "strong current" is not something the game does), and every place gets a
  field for what it gives the player: hard gameplay, not local colour, drawn from the full range Skyrim's places
  give (fast travel, traders and specialist traders, smithing, crafting, cooking, enchanting, alchemy, spells,
  trainers, combat always paired with a reward in proportion to its difficulty, shrine blessings, rare ingredients
  and materials, treasure and so on; quests and factions left out for now). A place can give several kinds, and
  several of each. No purely invented place: every AGENT_INVENTED place is re-derived from the lore by logical
  extrapolation (neighbouring provinces may be drawn on, e.g. wrecks from Morrowind, Cyrodiil, Elsweyr or Valenwood,
  with a reason), and all extrapolation is one consistent story and timeline. Ledgers, rolls, tallies and the like
  are cut to a few, in vocabulary Black Marsh's own lore uses; all place data is reviewed and edited.
  Water: streams in the north that flow inland are reversed; flow follows each channel's curved course downstream
  toward the sea (even where it ends in a still body); a channel with no continuous water surface to the sea cannot
  be a stream or river and is a still kind. The owner's atlas edits (saved 2026-11-09, "update-2026-11-09b") are kept;
  the small stream fringes on the edges of bodies the owner made swamp or marsh become that body's kind; round
  Helstrom only the widest river courses stay river and the rest become green marsh. The terrain honours each
  place's terrain needs (islets for places in lakes). Then the terrain, the plants and the LOD are rebuilt and
  deployed for the owner's first walk or fly, posted as an update to issue #56, and the atlas updated.
  Six mods are asset and source-place dependencies only (never active plugins), for Dunmer, shanty and Ashlander
  places in the new world: Dunmer Settlements of Solstheim (Nexus 33751), Dawn of Grey Quarter expansion
  overhaul (71162), Project AHO (15996), Nexus 180133 (a Dunmer village), Ashlander camp New Zainab (14229), and
  Journey to Baan Mular and Morrowind (114518). Updating skills from feedback gets one consistent system, written
  into CLAUDE.md. On the desktop keyboard, dodge and sprint move from Alt to Space, and jump moves to Shift, on both
  cards (BM&V and New World).
- 2026-11-09 (in session): the atlas's water layer may look blobby, but in the game all water is one continuous
  connected surface at one level, and the seams between water areas, kinds and colours are smooth and gradual, never
  hard edges or gaps (a cell's water type changes only through a blend of neighbouring types, measured off game).
- 2026-11-09 (in session): on ledgers, tallies and the like it is the theme as well as the word: Black Marsh is not
  a bureaucratic place, and the player's play should not revolve round ledgers and documents. Concepts built on
  records, registers, counts and papers are reworked into Argonian life (the Hist, eggs, trade by water, raiding,
  ruins, beasts, kin, memory carried in speech and carving), keeping a few where a document is natural (an outsider's
  papers). The rework stays faithful to canon and to the one extrapolation spine, history and faith above all: a fact other places rely on is kept and only the way it is carried changes.
- 2026-11-09 (in session, the nw-03 interview): the place builder and the studio.
  **Scope.** The whole of nw-03 is built in one overnight run, with no core-first trial: the studio at a URL, the
  first draft of Helstrom loaded beside BM&V's Helstrom, the place-builder skill, the edits-to-lessons agent, and
  both interim save-and-load and save-and-finalise proven end to end. Everything is delivered; nothing is left
  for a later pass. Nothing is deployed to the play machine until after the owner's nw-02 walk.
  **Built for every place.** The tooling is built from the ground up for any place seeded on any source place;
  Helstrom on BM&V's Helstrom is only the first.
  **Real ground and plants.** The draft and the studio use the real current in-game world: heights, water level,
  trees, plants, ground cover and scatter are read from the built game file, checked identical to the deployed
  one. The draft seats every placed thing correctly in or on the terrain. The agent clears vegetation as
  appropriate while drafting; the owner can clear more and un-clear in the studio. The owner's terrain edits
  finalise into the land records that are then deployed.
  **Extent.** All of BM&V's Helstrom at its true size, landing included, the landing on our real riverbank. The
  layout is adapted to fit our terrain wherever possible; a land patch is the last resort. Our record's radius
  is corrected to what was built.
  **People.** Every service person our place record promises, working, with a bed and a routine; guards and a
  crime faction; residents only up to the bed count of the copied homes; each of the nine houses its own
  interior; placeholder names until nw-05; no talk beyond services.
  **Hosting.** The studio is drawn in the tablet's browser and served from the build machine behind the owner's
  Cloudflare login; the machine stays awake while a studio tab is open. AWS going over $100 in November 2026 is
  accepted for this (estimate $130 to $160).
  **Interiors.** Open in the studio from the first night with the same tools; routines run unbroken from street
  to room.
  **Finalise.** One tap runs record, build, learn and report unattended. Lessons from fault edits land in the
  skill as their own revertible commit; taste edits never become rules.
  **The phase file.** The owner's wording in a phase plan is preserved; agents add below it, never rewrite it.
- 2026-11-10 (in session): the commit guard. When `tooling/lane_commit.sh` refuses a commit as undoing recent work
  and the change is deliberate (a redraft's own output, files of a room the drafter dropped, the owner's finalised
  edits), the agent uses `LANE_ALLOW_REVERT=1` or commits the deletion itself; the owner is not asked to run it.
- 2026-11-10 (in session): the studio and the review. No "worth a look" list: the fault is fixed instead. No timing
  or frame-rate measurements on the build machine. Nothing already proven is tested again, and a test that is
  itself wrong or tests nothing the owner needs is fixed or removed, not satisfied. The lead reviews the code of
  the drafter, the builder and the studio itself, not through subagents, and keeps the skills current with what
  the review finds. A session with a goal never idles waiting on the owner.
- 2026-11-10 (in session, later): lanes and models. The lead plans and orchestrates; work goes to lanes and
  subagents again. Delivery lanes run on Opus 5.5 at medium effort; code-review lanes are forced to Fable 5.2 at
  medium effort.
- 2026-11-10 (in session, later): the studio draws exactly what will be in the game. People's routes are found on
  the built place's own walking mesh; streets, patrols and door arrivals lie on the built walkable network; nothing
  the game does not draw (editor markers, effect shells) is drawn; everything placed shows at any zoom; the owner
  leaves notes for the agent in the studio, about the place or about selected things; the Atlas opens inside the
  studio from the built page, with no copied code.
- 2026-11-10 (in session, later): stocking is part of nw-03 (building Helstrom "in its entirety"), as its own
  skill `place-stock`. Set dressing stays as the source has it; anything more significant is authored on purpose
  from who owns it, what and where the container is, and the place's record; no random loot, nothing levelled.
  Value, level and strength are derived on one fixed scale (danger of the ground, the place's facts, the owner,
  security, effort, provenance; cities are safe ground with costly things hard to steal). Every promise of the
  place record is delivered, or the record is edited case by case with a reason, never as a way out. Contents are
  editable in the studio, optionally. The full text is in the nw-03 phase file.
- 2026-11-10 (in session, later): light identities (name, household, trade, wealth, a line or two of backstory; no
  dialogue) are brought forward into nw-03 for Helstrom's people, before stocking; nw-05 may recast anyone. The
  stocking lane is delivered now.
- 2026-11-10 (in session, evening): the owner's own text ranks above agent text. A note or reason the owner writes
  in the studio is stored at an owner statement tier above anything an agent wrote, and an agent's later pass
  never overwrites it. World facts of people, economy and stock live in the database in third normal form from
  the start, populated more fully later (nw-05). The landing's walkability lane moves to Fable 5.2 at medium
  effort. The skills are brought up to date with every outstanding improvement.
- 2026-11-10 (in session, evening): travel. Fast travel from the map will be removed in time (not yet), so no
  place promises it. The place records' fast-travel promises are rewritten as promises about the travel network
  (boat, coach, rootworm), authored sensibly place by place, and delivered by the place build as a service.
- 2026-11-10 (in session, evening): Helstrom's stock and record. (1) The drowned Third Era villages and their
  boat-robbers come out of Helstrom's record. A city has no hostile occupants unless it has dungeon-like interiors
  (a dangerous cellar, a sewer); no extra place, such as a whole village, sits inside a city's own extent. (2) The
  levy wears BM&V's Argonian guard armour. (3) The smith carries and sells Argonian sword and armour: Helstrom is
  the capital city and has good things. (4) The owner's statement tier ranks top, above canon.
- 2026-11-10 (walk 5, `tmp/walk-5-feedback-2026-11-10.md`, quests in BM&V): (1) the opening is good up to leaving
  the hold, and the skills are to be updated from it; the gang never starts moving after that: root cause and fix,
  and the same fix everywhere the same building blocks are used or affected in the first act's quests. (2) Too
  many people early on repeat each other (everyone in the hold, and Buys-The-Months, on months added for food): the
  dialogue writer skill must be context aware, so that several conversations in one space are written first time
  without repeating each other, the opening act's flow above all. (3) A Fable 5.2 agent at medium effort reviews
  everything about how the opening act and the slice's factions and quests are implemented; bugs are fixed, the
  approach optimised, and the skills and building blocks improved until a future agent implementing a new quest
  gets it right first time; Phases 4 and 4a are what was aimed at. Passed in walk 5: checks 8.1, 8.2, 9.1, 9.3 to
  9.7; 8.3 (backstab) not yet checked.
- 2026-11-10 (in session, evening): Nordic pieces. "don't worry so much about the nordic elements, e.g. the
  sconces. as long as our source places are the mods + tropical skyrim we should be OK." A piece a source place
  itself uses, from its own mods or Tropical Skyrim, is accepted as it comes; it is not reviewed by look or
  replaced. (The lead's reading: decision 0006 still governs what we add from elsewhere.)
- 2026-11-10 (in session, evening): the studio. A day and night view that approximates the game's lighting in
  both states, without shadows, so the owner can judge whether a place is lit enough and add or remove lights and
  see the effect. Notes are part of editing: the owner changes one thing or several and leaves one note for the
  agent about them, smoothly, without a separate step.
- 2026-11-10 (in session, walk 5 follow-up): (1) confirmed in game: the gang was already standing at the dock's
  landward end when the owner came out of the hold, and nothing happened there; the gang starts its walk only once
  the player is outside, so the player can follow. (2) The opening is re-authored and rebuilt so its spirit is
  kept but it happens at the place the player reaches straight after stepping off the dock: no long march to
  Hereguard Plantation, so a new player cannot wander off before the opening completes. (3) The walking limit of
  BM&V's ground (its navmeshes are not joined to each other) is fixed anyway where the slice's routes need it.
- 2026-11-10 (in session): navmesh in BM&V is the agent's call, not a question for the owner: choose the most
  sensible approach that enables the quest system generally (joining existing navmesh, or adding it where the
  quests need ground that has none).
- 2026-11-10 (in session, night): redrafts. A whole place is never redrafted to change one part of it. What needs
  changing is changed and the rest is kept; a whole redraft only when a narrow change truly cannot be correct.
- 2026-11-10 (in session, night): the narrow-change rule stands for all future work, and the owner's edits made
  in the studio are applied the same way: only what the edit touches changes, and no later draft step regenerates
  over a place the owner has edited. The rule is a line in CLAUDE.md.
- 2026-11-10 (in session, night): the AWS limit is $150 a month, up from $100 (decision 0008 amended).
- 2026-11-10 (issue #60, the owner's reply): A, the fights removed from small settlements are restored as
  encounters near the place. B, a friendly place's goods are capped by its wealth as well as by the land round it.
  C, Helstrom stays in wealth band 4. D, the studio needs no shadows; in the game there is no cap on
  shadow-casting lights: each room keeps the source's own. E, vanilla Nordic pieces a source place's own room
  uses are accepted. F, the travel network stands as built.
- 2026-11-10 (in session, night): law. A native Argonian place has no jail (the lore: the Owing, no cell). The
  Owing is the playable sentence: the game's jail mechanism re-dressed as a season of work, no cell. Capital
  punishment is part of native law: a person who resists arrest is fought to the death by the guards. The studio
  shows a kept invisible wall as a faint box when selecting, as it shows lights.
- 2026-11-10 (in session, night): the walk 5 feedback on the built world is delivered by a fresh orchestrator
  session, started unattended by the nw-03 session when its own lanes have landed, from the hand-over
  (docs/phases/new-worldspace-plan/nw-02-walk-5-handover.md).
- 2026-11-11 (in session, morning): the LOD is built for our worldspace only (ArgoniaBlackMarsh), never for any
  other world in the load order. Each LOD run is checked for it: xLODGen's world list, DynDOLOD's preset and the
  folders and logs each tool writes.
- 2026-11-11 (in session, morning, before leaving the session unattended): (1) Far-off shapes (LOD models) for the
  placed things that have none and are too heavy to draw far off as they are (fallen logs, stumps, boulders): "how
  simple would it be to just make these too, in whatever is the most Skyrim native way that you can do? ... If
  there's a known simple and reliable way then just do it please." So a lighter far-off model derived from a
  placed model is allowed where a known, simple and reliable way exists (the lead's reading: this is a derived
  build output like the rest of the LOD, generated on the machines and never committed; it is the one exception to
  "we make no art"). (2) Parallelism wherever sensible. (3) Everything rerunnable must be right first time: clean
  recipe skills are written and maintained for whatever of this work agents will need again (the object and tree
  LOD will be rebuilt after places are built). (4) Long jobs run once: every check that can be made before a long
  job is made before it, and what it finds is fixed and checked again first; checks are not a formality. (5) Break
  bad patterns and going round in circles when found.
- 2026-11-11 (in session, morning): the skills for rebuilding the world and its LOD say plainly to run only what
  needs to be run: nothing that has not changed, or is already right, is regenerated. Each recipe names, for each
  kind of change, the stages it makes stale and the stages it leaves alone.
- 2026-11-11 (in session): tidying is automatic. The build machine's disk and the bucket are cleared of what is
  no longer needed periodically and whenever appropriate, in every session, without the owner asking; no worktree
  is left abandoned or orphaned when its lane has ended.
- 2026-11-11 (in session): reviews are weighed by what the player would notice. A review ranks each fault by its
  effect in game; a fault that breaks the game or is plainly noticeable is fixed; a tiny fault, or one that would
  not really be noticed in game, is not worth hours of fixing and rebuilding (fix it only where the fix is cheap
  and needs no long job; otherwise note it in one line and move on). And for any long-running tool or job there
  is always a fast way to find faults and test fixes (for the LOD, a small world first): it is built before the
  long job is relied on.
- 2026-11-11 (in session, evening): the owner edits placed plants and rocks one at a time. "I will also want to be
  able to edit plants without having to regenerate/re-place all of them (e.g. if I remove a tree or move a rock in
  the studio it would be madness to re-place everything else)." An owner's edit of a placed thing in the world
  (remove, move, add) is its own record applied over the placement; it never re-places anything else, and a
  rebuild after it redoes only what that thing touches.
- 2026-11-12 (in session, nw-03b and nw-04): (a) the owner needs a way into the new world from a phone with the
  game pad alone, "whatever is simplest/easiest to deliver"; (b) a delivery must not leave the owner sitting
  through Community Shaders' "compiling shaders" again: the cache is kept per card, archived, and proved complete
  at the end of a deploy; (c) the grey untextured grass at ArgoniaNWStart: "find all cases (could be others beyond
  this type) and fix"; groundcover changes are allowed for that fix ("I can rule back in groundcover changes for
  dealing with that issue"); terrain, trees, scatter placement and LOD stay untouched in nw-03b; (d) hostile NPC
  bands are "widely varied (in a lore consistent way) in terms of appearance and gear", gear quality and value by
  danger band and by who they are (the owner's edit of the phase file).
- 2026-11-12 (in session, nw-04 check #64): (a) "yes happy with nordic layouts as the base (they get adapted to
  our land anyway)": Skyrim's towns stay layout sources for our places; the call is dropped from the sources page;
  (b) "yes please source more ruin mods to mine. please do the same for any other bad gaps as well (e.g. the
  villages that got mapped to shrines)": every kind whose allocated sources are of another kind or culture, or
  score low, gets more sources, first by mining what we hold more finely, then by new mods taken as layout
  sources and asset dependencies the player downloads (never redistributed).
- 2026-11-12 (in session, nw-04 calls, issue #64): Skyrim's Nordic towns are accepted as layout sources ("they
  get adapted to our land anyway"); more mods are sourced and mined for ruins and "any other bad gaps as well (e.g.
  the villages that got mapped to shrines)". Sourcing mods is the lane's own job: "I do not want to be just
  presented with a list of mods to download at the end"; a gap is reported only after a proper search ("Improve
  your search ability").
- 2026-11-12 (in session, regional distinctiveness): after the walk of the new world the regions "still don't feel
  that different to each other". The owner asked for all of the lead's levers (sound, music, a wider air, water
  look, ground-cover colour, small signature things, creatures), planned in nw-03b's "Regional distinctiveness"
  section and delivered. Music: "our own versions of every Morrowind track, using Suno to adapt them to our Black
  Marsh game theme", consistent as one soundtrack yet distinct. Unmet creatures: "do a loop of reauthoring &
  searching & sourcing until you have a broad enough set of creatures meeting all the requirements".
- 2026-11-12 (in session, music, issue #65): the owner wants the actual Morrowind tracks as the base ("use the
  actual track as the base ... recreate the same motifs/harmonies/etc but with new instruments"). The agent
  declined to generate music that recreates Morrowind's compositions; it delivers an original soundtrack to the
  same roles, and a music system with one named slot per role and a drop-in folder, so any file the owner makes
  himself replaces a piece without a code change.
- 2026-11-12 (in session, creature mods of lanes C and D3): "I have checked and we have permission to use them in
  this way if we don't ship their assets directly and we make their mods dependencies for ours." Recorded on each of
  the eighteen creature mods' rows in mods/sourcing-register.json (`permission`, `permission_condition`). Before
  release the creature mods' plugins become real masters of our world file rather than record copies (owed in
  docs/phases/5-scale.md).
- 2026-11-12 (in session, nw-03b music and lanterns): (a) discovery sting: "Let's just use Skyrim's for now": in the
  new world discovering a place plays Skyrim's own discovery music (our discovery override removed from
  NewWorldMusic.cs and music/records.json; the slot stays in the pack unused); the death sting is ours and approved;
  the level-up sting is recut from the owner's own Overture. (b) Wild Hist lanterns stay only near places ("they are
  presumably placed there by people"): within 2 cells of a place in Murkwood, as built.
- 2026-11-12 (in session, evening): stings: the death sting is approved; discovering a place plays Skyrim's own
  sting for now; the level-up sting is cut from the owner's own Overture, at about the length of Skyrim's level-up
  sting (measured, not guessed). Hist lanterns hang only near places ("they are presumably placed there by
  people"); Helstrom gets its lanterns now, and Helstrom is deployed only "after I have done my editing and feedback
  on the draft in the studio". The flagged dialogue of the BM&V version is rewritten with the updated dialogue
  skill (directions in words, the Morrowind find step on every run).
- 2026-11-12 (evening, nw-03b music): the discovery sting is ours again (slot sting-discovery, recut to its first 4 s
  with a fade ending near 7 s), reversing (a) above: our override of the four discovery music types is restored. The
  level-up follows Skyrim's two parts: the UI sound UILevelUp plays our 8 s sting (sting-levelup), the level-up music
  type a 19 s cut of the Overture (music-levelup).
- 2026-11-12 (evening, nw-04 sense check, issue #64): "I think it looks good. Make the population match the source
  population though don't cut it down like we have done so far, that will just make them feel weirdly empty." A lived
  place's population is now its source's residents, with no blend or clamp (empty places stay 0; never under the
  people the record names; a source counting nobody keeps the estimate).
- 2026-11-12 (in session, dialogue): "please rewrite all the flagged dialogue in the BM&V version of our mod with the
  new updated skill." Every line the B13 lint and talk_check flag (a count of paces, yards or metres) is rewritten whole
  through the dialogue skills with the Morrowind find step: directions by landmarks, compass words and distance
  words, never a number.
- 2026-11-12 (walk 6, the quests; tmp/walk-6-quests-feedback.md, kept whole in docs/phases/walk-6-quests-handover.md):
  the opening and the start of the main quest were "a complete mess". "Let's have nothing more complicated than
  Morrowind-level scripting for all of our quests, and do much less world-editing for each quest." The barge is
  kept; outside its door the man starts the talk himself: the player is not on his list, owes nobody, and is sent
  to a named place and person who inducts them into the main quest's faction. Everything authored so far is
  reviewed and rowed back, keeping the spirit. Quest markers on the map and in game for objectives and things to
  pick up or use. "Anyone in our game can die", with a message like Morrowind's when a main-quest person dies. An
  off-game paper playtest played by a fresh agent, on the game's own built version, part of authoring, never a
  gate, with a broad brief and an artifact to explore the runs. The plan: docs/phases/walk-6-quests.md, issue #68.
- 2026-11-12 (in session, walk 6, anyone can die): "only people who are essential for *major* quests get our version
  of the 'thread of prophecy' message if they die. Main quest and factions, not just any old minor side quest. If
  you kill someone necessary for a minor side quest it should just close the quest as failed or something with a
  journal update." The message shows for a person the main quest or a faction's quest line cannot go on without;
  a minor side quest whose person dies ends as failed with a journal entry and no message.
- 2026-11-12 (in session, walk 6, what follows it): "Once you have delivered everything from your original goal,
  learned all the lessons along the way, and updated all the relevant skills - please *then* also own and deliver
  the new world phase that is about the first pass of fitting our authored quests to the new world (using
  everything you've learned and the newly updated skills). The brief for it is very minimal from me currently so
  you'll need to build it out in the phase plan." The walk 6 planner session owns that phase after walk 6 is
  delivered: it builds out the phase's plan (the owner's own words in the phase file are kept as written, detail
  appended below them) and delivers it.
- 2026-11-12 (in session, the new world's first pass of fitting quests, nw-05): "I don't want the quests and story
  to feel like they're patched or shoehorned into that world, I want them to feel really naturally and deeply
  integrated with it, whilst keeping the overall factions and spirit of the original. You have creative license to
  rewrite and reauthor, I want it to flow like a really nicely written exciting story throughout that any elder
  scrolls fan would fall in love with and have a lot of fun playing through. (The 'using in game skills' for every
  quest is really key to the fun as well btw)". For nw-05: the factions and the spirit are kept; everything else
  may be rewritten so the story grows out of the new world's places, people and regions; every quest is played
  with the game's own skills.
- 2026-11-12 (in session, who writes the story, nw-05): "The overall story for the main quest and each major
  faction should be written by Fable by the way, it's comfortably the best writer. It should be aware of our
  various quest rules though and Morrowind level scripting so it doesn't write an overall story that is
  undeliverable. The art really is in achieving what Morrowind achieved: beautiful storytelling, deep world
  building, compelling narrative lines, moral ambiguity, genuinely interesting conflict (of various kinds) all
  within the constraints of minimal scripting". The main quest's and each major faction's overall story is written
  by Fable (the lead, or a lane forced to Fable 5.2), with the quest rules and the Morrowind-level ceiling in its
  brief; delivery lanes on Opus build quests from that story.
- 2026-11-12 (in session, walk 6, the skills learn from the paper players): "the feedback from these agent players
  should be used to improve the skills as we go along (obeying the other rules about always having them simply as
  clean recipes for how to deliver high quality output). Especially after agent players give good feedback on
  something that was previously poor, that shows we figured something out and properly fixed it. With the quest
  skill toolkit, you can create new skills if you think sensible (e.g. having different types of quest skills more
  specifically tailored to different types of task), and/or restructure the whole set of skills however you see
  fit (I'm imagining a sort of skill graph making up an overall system for creating our high quality quest system
  or something)". A paper player's finding that a fix then clears (a later player is no longer confused or bored
  there) is generalised into the recipe that produced the fault, as owner-verified fixes are; the lead may add,
  split and restructure the quest skills into one connected set.
- 2026-11-12 (in session, nw-05, a reader loop for the story itself): the owner proposed "something like the 'agent
  player' loop" for the story and factions rewrite: "You author an overall story, then you take a fresh agent
  through it chapter by chapter or quest by quest without it knowing the context or what the ending will be, and it
  does the same sorts of things ... thinking aloud and giving its feedback. You use that feedback to improve your
  story, and loop until you decide you've reached the Morrowind level quality bar. For the main quest and each of
  the factions." Adopted by the lead for nw-05 (the owner asked "what do you think?"; no objection is recorded yet):
  the story is told to fresh readers one quest at a time as a player would meet it; at each step they say what they
  think is going on, whom they trust, what they expect and what they would choose; fresh readers every round; a
  separate reader checks each chapter can be built at the ceiling; readers are evidence, not votes; it stops when a
  round can retell it, wants the next chapter, splits on the conflicts meant to be ambiguous and raises nothing new
  the author agrees with.
- 2026-11-12 (in session, review loops must not go in circles): "with your overlapping checks (e.g. the separate
  deliverability check) ... you must not create circular issues - e.g. the player readers giving some feedback
  that leads to a change that the deliverability reader then says is undeliverable that leads to a change that
  then the player reader doesn't like... I think you need to get the feedback from all of them and make coherent
  sets of changes that resolve everything together and leaves the output in a state that resolved all of their
  issues without creating any new ones." And on fresh agents being agreeable: "you should consider this in the
  persona that you prompt them with (don't make them *too* harsh though or we'll never pass)." Every round gathers
  all readers' findings first (players and the deliverability reader), the author makes one set of changes that
  answers them together inside the ceiling, and the next round checks that set whole; a reader's persona is honest
  and a little hard to please, never hostile.
- 2026-11-12 (in session, nw-05, the story rewrite's vibe): "remember our golden rule about the vibe of Argonia,
  about minimising bureaucracy, and avoiding 'tallies' and 'rolls' and ledgers and paperwork and bureaucracy and
  process generally. Lean towards activity and action (of various kinds, I don't just mean combat, use your
  imagination and anchor on the variety of in game skills) over processes and procedures and records. And remember
  about different builds being able to complete main; factions have their own build leanings". For the rewrite: no
  quest turns on a document, a count, a hearing or a procedure; each turns on something the player does with a
  skill; the main quest can be finished by any build (each main quest offers ways through for different skills);
  each faction's line leans on that faction's own skills.
- 2026-11-13 (in session, the vibe ruling softened): "Doesn't have to be absolutely *no* records or ledgers or
  whatever, should just be at most a very small amount across the board. Might be some particular people or
  factions or contexts where it's appropriate. Use your judgment". Records, rolls and paperwork are rare, kept for
  the people, factions and places they truly belong to; the lead judges case by case.
- 2026-11-13 (in session, factions must be exciting): "The chainbreakers main thing being about buying people out
  sounds kind of boring by itself ... that's basically just chores. 'Chainbreakers' sounds like an exciting faction.
  Make them exciting. I'm not saying you have to get rid of the concept of buying people out entirely, but the
  quests themselves need some drama to them - do you have to pickpocket somebody to get a key to break into their
  house to change something on a record about owed months, for example. Use your imagination, make them fun. Same
  goes for all the factions. They should be fun and intriguing and exciting and have drama and tension, all of
  their own". Every faction's line has drama, tension and intrigue of its own kind; a faction's premise (buying
  people out) may stay as background, but each quest is something daring the player does.
- 2026-11-13 (in session, lines true of the built world): "quests and dialogue must be consistent with the actual
  world and the context in which they are spoken. There's no point someone talking about tides when our province
  has none. We can't have someone saying 'there's a spear in the grass next to us' at a time of day when they are in
  a different part of their routine and they're not next to the spear (so the dialogue should instead say the
  spear's location relative to things that don't move). We can't have people talking about a house that's on fire
  if there's no house on fire; we can't have people talking about 'hatching sheds' if there is no building that
  clearly reads as a hatching shed; or talking about how their job is lifting crates if they don't actually do any
  crate lifting ... The actual game world and built places and dialogue and quests all need to be completely
  consistent with each other. This is super important". Every line, journal entry and record is true of what is
  built: what exists and reads as what it is called, where things are relative to things that do not move, what
  the world's systems do (no tides), and what the speaker is actually seen to do. It is built into the skills and
  checked, and kept to.
- 2026-11-13 (in session, truth of the world built into how quests are made): "behind quests I never play needs to
  be the thing about quests and dialogue consistent with the real game world. Not just as a check but somehow built
  into how quests are created in the first place. The built places aren't in yet though so bear that in mind (see
  the nw phase plan for the proposed sequencing regarding story authoring, place building and quest implementing)".
  The method (quest-system): a story names places by what the world's data says they are and lists anything
  physical it needs as a need of that place; the place's record carries the needs as promises and the place is
  built to them; a quest's record and its words are written only on a built place, from measured spots and the
  speaker's surroundings sheet; the truth reader is the last check, not the method. This follows the new world
  plan's order: story (nw-05), places (nw-06, nw-08, nw-09), quests on them (nw-07, nw-08, nw-10, nw-12).
- 2026-11-13 (in session, what the player can know): "agents will be like 'ok we'll use this house for the hatching
  shed that the quest needs', but then to the player there's no way to know it's supposed to be a hatching shed, it
  just looks like a house ... the agent doesn't think about what the player will know or how they'll know. That
  creates major issues". Whether a place or thing is what a quest calls it is judged only from the player's side:
  its look, the names the game shows on doors, rooms, markers and things, what stands there, what a person has told
  them. Every promised place and thing carries how the player will know it, and that is tested by a fresh reader
  given only what the player would see.
- 2026-11-13 (in session, nw-05): (a) the story hooks in each place's data: "I hadn't checked whether [they] were
  any good or not. They were kind of rough I think and not based on that much. You can and should review and change
  them wherever you think it's a good idea to, in order to make our story better." The hooks are raw material, not
  canon: a writer may take, change or drop one, and the place's notes are then brought into line with the story.
  (b) "Echo deep instead of lost city sounds good to me." (c) On the deliverability reader finding none of Act I's
  outlines buildable: "if it's easy for a reader to tell this, it should be easy for the writer to know it as well,
  and therefore to write buildable output in the first place. Make it so. Agents follow instructions, its
  instructions should clearly say how to design something buildable." The story-line skill tells the writer how to
  design a buildable quest and gives a mechanical check to run before any reader sees it; a reader finding an
  outline unbuildable is then a fault in the skill, fixed there.
- 2026-11-13 (in session, the place studio and the story): "stuff about the story may affect decisions I make about
  whether and how to edit places. It must always be mindful of the fact that I won't have the story in my head or
  know who people are etc, generally won't have much context for any of it." And: "I'm going to be editing and
  building Helstrom now as the first place before the slices so surely we need something now?" The studio shows, for
  any place and first for Helstrom, what the stories need of it in plain words that assume no knowledge of the
  story, who each person is to a player, and a warning (never a block) when an edit touches something a quest
  needs; the owner's edit stands and the story is changed to fit the place. Built now, in nw-05, not left to nw-06.
- 2026-11-13 (in session): (a) on every paper player making the same choice: it "might just be because they're all
  the same AI model right, they're not actually different people, so you probably need to give them personalities
  that are more different in order for that to be a fair test." A choice is tested by readers who are given
  different things to value, on different models where possible, each also arguing the options they did not take.
  (b) Helstrom is not redrafted for the stories ("It's a bit of a faff"): the stories and quests are fitted to what
  is already drafted; only small narrow additions (a lock, a named door, a thing placed) are made where a story
  cannot do without, and nothing larger without asking. (c) The owner does not open the studio until told it is
  ready.
- 2026-11-13 (in session, what a choice or ending means in play): "what matters here is what the different endings
  mean for the player. Beyond just description and text I mean. Like, what are the actual gameplay impacts? In terms
  of powers, rewards, abilities, unlocking fun stuff, etc. there must be some more we can research online about how
  to make this shape of thing good. Do that and think all of this through and bake it in wherever multiple
  outcomes/choices are concerned (again, aiming to instruct writers & builders to get it right first time
  primarily)". Every choice and every ending says what it gives and costs the player in play (a power, a thing, a
  service or place opened or closed, standing), researched and written into the skills as instructions, with the
  tools able to build it.

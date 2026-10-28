# P7: The vertical slice: the opening region, played end to end

**Goal.** A new player can start Argonia, make a character, play the opening and the first questline in one
region, and meet every system (soul, combat, traversal, boats, world) at shipping quality, with no Nordic element
in reach. The owner plays it through the stream from start to finish.

**Starting state.** P3 (at least the slice region), P4, P5 and P6 exit gates passed. The immersion inventory has
verdicts for every system those phases touched.

**Read first.** Imported `docs/design/quests/00-overview.md`, `30-main-quest.md` (the opening), the old phase
2 slice docs (`docs/design/phases/2-slice/`), old decisions 0026 (main quest), 0134 (systems whole, content
thin), 0149 (play the shipped path, no modes or flags), 0155 (journeys as staged scenes), 0156 (cheapest test
level).

## Work packages

### WP7.1 Choose and scope the slice (owner call O-10)
- Default: the old opening, "a prisoner on a work detail near Stormhold / Alten Corimont, attacked by Sithis
  radicals, recorded dead, recruited by the Veiled Reed" (main quest "The Eye and the Root"), in the
  pirate-freeholds / dunmer-north border with the Opening Work Camp (an already-built place), the route to the
  first town, and enough of the region to hold 2–3 hours of play.
- **The vastei tutorial scene** (owner requirement, 76 ~563–569): vastei is taught in fiction in the opening hours
  by a Nisswo character ("the change you have earned"), with the first death and pile retrieval staged safely.
- Scope list: places (built and new), NPCs, quests (the opening + 1 faction line start + 3 local quests), every
  system's first rungs (one climbable cliff route, one dive, one boat trip, one boss), crafting stations, a
  merchant of each type, a trainer, a travel service.
- **Acceptance:** owner approves the scope list.

### WP7.2 Build the slice content
- New places for the slice through the `world-builder` skill (P3-WP3.9 recipe), with Morrowind density targets
  for the region (18–22 named places per km² in low-danger land, something named within 300 m along every road,
  a landmark about every minute of walking; old 0027), every building enterable (old 0103), every NPC named.
- NPCs with schedules, faces, dialogue (dialogue-write rounds on Sonnet), quests with stages, directions and
  journal text; loot and encounters by danger band.
- **Acceptance:** data checks green (L1); every quest runs in an L4 scenario; the direction validator passes.

### WP7.3 Journeys
- The old journey set reborn as in-game scenarios (`tests/journeys/*.yaml`): the vastei tutorial, combat, magic, crafting, stealth,
  quests, climb and swim, boats, persistence (rest, die, recover vastei, save/load), chargen, travel service.
- Each journey plays the shipped path only (old 0149: no debug mode stands in for a game action).
- **Acceptance:** all journeys green on two consecutive runs.

### WP7.4 Immersion pass for the slice (T-IMM)
- From now on the gate fails on any reachable `unreviewed` inventory row. Close every row the slice can reach:
  menus, HUD, items, NPC looks, sounds, music types, text, loading screens.
- Reader panels on a capture sweep of the slice (every place, every menu) with the Nordic-tells checklist.
- **Acceptance:** zero reachable unreviewed rows; reader panels' "obvious" findings fixed.

### WP7.5 Owner playthrough
- A packet: start a new game and play to the end of the slice; a checklist of systems to try; how to report
  (GitHub issue per finding with a screenshot, or a voice note summarised by the planner).
- Findings are triaged by the blocker rule (ways-of-working): blockers fixed before P7 closes; polish to the
  backlog with one quick-fix attempt each.
- **Acceptance:** the owner completes the slice and calls it the game they want, or lists what must change.

### WP7.5b Triage the old polish backlog
- Read the old project's polish backlog (`docs/design/phases/P-polish/backlog.md`, ~470 rows): each row is
  carried into `docs/phases/backlog.md` (if it describes a design intent still true here), or dropped as
  three.js-specific, with a one-word reason column.
- **Acceptance:** every old row has a verdict; carried rows are tagged to a phase.

### WP7.6 Re-plan
- Measure: time per place, per quest, per dialogue round, per GPU check; costs per week; the owner's turnaround.
  Re-estimate P8–P10 and set P9's packet size and lane count (and O-2: when to move to the 20x plan).
- Write `docs/phases/P9-packet-template.md` from what the slice taught; its quest and dialogue steps follow
  decision 0017's order.
- **Detectives' faction (decision 0018):** the lore pass (its place in 4E 201 Black Marsh, from the lore
  dossiers and extrapolation, written as an extrapolation entry) and its line record through `quest-write`
  (ranks, cases per rank, recurring cast and rival, the finale and the clues seeded for it), reviewed by
  `quest-review`, so every P9 packet plans the cases it hosts.
- **Acceptance:** PLAN §5 table updated with measured estimates; the packet template exists; O-2 asked in the
  P7 check-in with the measured numbers.

## Exit gate
Slice complete; journeys green; zero reachable unreviewed inventory rows; owner playthrough with no open
blocker; P9 packet template written from what the slice taught.

## Risks and fallbacks
- **Integration surprises between phases** (combat × dialogue interception, boats × save, climbing × navmesh):
  the journeys exist to catch them; fix at source, once.
- **Owner finds the streamed feel poor in long sessions**: revisit 0007 options (bitrate, codec, a local PC).

## Deliberately out of scope
Regions beyond the slice (P9); the immersion sweep of anything the slice cannot reach (P8); release packaging
(P10).

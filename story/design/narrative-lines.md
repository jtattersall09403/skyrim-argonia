# 4.3: Narrative lines

**Goal.** The main quest, the faction lines and the endings, built as narrative packets in story order, each quest
staged when the region packet holding its places has landed. The bosses are on the 2.7 engine.

**Starting state.** Written by the agent that closes the region packet the line first needs.

**Read first.** Decisions 0024 and 0025; imported `docs/design/quests/30-main-quest.md`, `40-factions.md`,
`36-cast-roster.md`; old 0026, 0028, 0030 (inherited-rulings); 2.7 §k (the boss engine); the `quest-write`
(`questlines.md` first) and `quest-review` skills.

## How a line is written
Every line runs decision 0024's order on its old design (the foundation, kept and improved):
- a **line record** first (`questlines.md`: ranks, the arc, recurring cast and rival, seeding, the finale),
  reviewed by `quest-reviewer` before any of its quests;
- each quest's record through `quest-write`, its action plan weighted by the line's profile and away from what
  the line already uses; then `quest-review`, `brief.py`, `dialogue-write` and `lint.py`, as in 4.2 steps 5 and 6;
- a quest set in a city or in the opening is hands-on with the owner (0024 §10).
- **Acceptance:** every line record and quest record `reviewed` with no open finding; every line lint clean.

## The lines

- The main quest "The Eye and the Root" (23–24 core quests, 25–35 hours, stakes legible in the first two hours,
  three endings CUT / CLAIM / MEND; old 0026/0028) is built across packets in story order, each quest staged when
  its region packet lands; tier protection (main > faction > side; old 0030).
- The 8 major faction lines (Shadowscales, Night-Reed, Nisswo, Many-Root; Marsh Charter, Sunken Archive,
  Reed-Sail Compact, League of Open Water) and the compact lines, with allegiance reward tracks (old 0028).
- **The detectives' line** (decision 0025), rival to the Shadowscales and the Night-Reed: its cases are built in
  the 4.2 packets that host them, from petty crime up; the grand murder-mystery finale when its region's packet
  lands, with the clues 4.1's line record seeded.
- The climax expedition Helstrom → Lost City with the Wamasu guardian (a boss on the 2.7 engine) and the named antagonist (duel
  or words).

## The bosses
- On the 2.7 engine, each with phases, an arena, the HUD boss bar, and a DS1 reference boss of similar shape for
  pacing, measured the same way:
  - the swamp leviathan;
  - the Wamasu guardian of the main quest;
  - Xal-Krona;
  - the main antagonist (a duel, or words).
- **Acceptance:** each boss has L4 checks (phase transitions fire; punish windows match its spec) and an owner feel
  packet.

## Loops (docs/loops.md)
- **Per line:**
  - every line and quest record: `quest-review`, then `brief.py` (L1);
  - every quest's stage graph: L1 validator, plus an L2 walk of every branch on a unit test over the record;
  - the main path and one fail-forward per quest: L4 on the game runner;
  - directions: L1;
  - journal text: text-review.
- **Joins owned:**
  - tier protection, main > faction > side (old 0030; L2);
  - a dead NPC → fail-forward (L2);
  - endings → world state (L2, L4).
- **Journeys:** each act end to end, and each ending.

## Owner check
Each act and each ending, played in the real game from a save at the act's start.

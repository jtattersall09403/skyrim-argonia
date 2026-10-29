<!-- imported unchanged from elder-souls-argonia docs/decisions/0147-early-levels-come-fast.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0147 Early levels come fast: a ranks-per-level curve to a ceiling of eight

**Decision (owner, 2.9x owner calls).** The owner's words, verbatim:
"level 2 after 15–30 minutes; early level-ups closer together than later
ones; never ages between levels later on".

1. **The counter asks a curve, not a flat ten.** The counted ranks from
   level *n* to *n* + 1 are `curves.levelUp.ranksPerLevel[n − 1]` =
   1, 2, 3, 4, 5, 6, 7, 8; every level from 8 on asks the last entry, the
   ceiling of 8 ([world/76](../world/76-stats-progression.md) §120.5).
   Use values, rank costs, the 1 : 3 credit, attribute prices and the enemy
   bands are unchanged. Morrowind's own rule set keeps its flat ten, so
   the known-answer test still runs Morrowind as Morrowind.
2. **Why.** The level-up is the hook moment. A first level-up after one to
   two hours, and later gaps of three to four hours, leave a new player
   with nothing to mark the first sessions and a veteran waiting through
   long stretches. The curve gives level 2 at 20–30 minutes and level 10
   at four to six hours.
3. **The numbers it holds** (measured by the campaign harness, asserted
   in `stats/balance.test.ts`): level 2 earned within 15–30 minutes;
   mean hours per level rising across hours 2–10, 10–40 and 40–100; the
   late gap (hours 40–100) at most 2.5 h, measured 2.1–2.4 h against
   2.5–2.9 h under a flat ten. A whole campaign ends at level 69–90
   (it was 53–69); this replaces the 150-hour target of 50–70 in
   [0037](0037-workstream-s-round4-qa-rulings.md) item 6.
4. **The ceiling is set by the attribute economy.** A sitting's vastei comes
   from that level's ranks. At a ceiling of 7 or below, a level-20 to
   level-30 sitting buys one attribute point, under the 2–8 points of
   §120.4. A late gap well under two hours (a ceiling of 5 gives 1.3–1.5 h)
   needs the sitting's price keyed to something other than the level
   counter. That is an owner call, not taken here.
5. **One level per sitting stays.** A rest banks one pending level. Early
   levels now come faster than rests (about 1.3 an hour), so the first
   levels queue: level 2 is earned at 20–30 minutes and banked at the
   first rest, about 35 minutes in; level 5 is earned at 1.4–1.9 h and
   banked at about 3 h. Whether a rest should bank every pending level is
   an owner call, not taken here.

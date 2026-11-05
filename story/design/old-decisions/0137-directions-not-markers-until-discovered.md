<!-- imported unchanged from elder-souls-argonia docs/decisions/0137-directions-not-markers-until-discovered.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0137 Directions, not markers, until the player has been there

**Decision (owner).** Morrowind's rule is kept: nothing in the
journal, dialogue or map points the player at a place they have not
reached on foot. A journal entry or a line of dialogue gives
**directions**, written against the real world (the road and river
network, the named geography of
`world/sources/hydrology/names.json`, the place records' real positions
and landmarks), so a player can follow them; it never carries a map
link or a marker for an undiscovered place. Once the player has
discovered the place (2.2 § b, the per-place `discovered` state), the
entry gains its map link and the map its pin. Grantable markers (2.11)
are the only exception and are granted by a deliberate in-world act
(a map bought, a mark drawn by an NPC), never by a quest stage.

**Why.** The owner names it as one of the things people loved about
Morrowind: finding a place is the play. A marker turns a journey into a
waypoint.

**Consequences.**
- 2.2: the journal's entry links resolve only for discovered places; the
  component takes the discovery state; the fixture shows one entry each
  way. Map pins only once discovered (already the rule).
- 2.5 and 2.11: every direction in dialogue and journal text is authored
  from the real world and gated by a test that walks it: the route
  described must exist in the route network and end within the place's
  extent, and every landmark named must be a real record within sight
  of that route. The content-format spec in 2.11 gets a Directions
  section (how far, which bank, which turning, what you see).
- World provisions (quests/20): a place that quests send the player to
  must be findable by its directions, so it carries the landmarks the
  directions name.

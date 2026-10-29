<!-- imported unchanged from elder-souls-argonia docs/decisions/0138-people-and-creatures-live-by-the-place-record-and-the-lamp-clock.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0138 People and creatures live by the place record and the lamp clock

**Decision (owner).** The life of a place, its people and its creatures, is
whatever its place record says, at the depth the cast ladder allows, every
one named and visually unique across the province.

- **Skyrim-style days.** People walk their routes on the path network when a
  player can see them and are swapped between spots when nobody can, in two
  to four coarse blocks on one village clock pinned to the lamp and sleeping
  hours already in the game (rise 05:30, at work by 06:30, home when the
  lamps come on at 17:30, candles out and bed at 22:00).
- **Per-person jitter on the clock.** Each person's block edges carry their
  own small offset, so nobody stops for lunch at the same instant; shops,
  inns and watches keep their hours.
- **People sit to eat on furniture already in the place.** At midday and in
  the evening a person takes the nearest free chair or bench the place
  already has. Seats are added only as sockets in a layer
  ([0140](0140-layers-on-a-built-place-never-rebuild-it.md)), chosen by the
  furniture's geometry; nothing is republished or rebuilt for them.
- **Role exceptions** (inn, watch, fishers and divers, a tended camp fire,
  more as places are authored) are the only per-person authoring.
- **Houses and shops lock as Skyrim does**, by the common day and the role
  exceptions, in the studio and the game alike. A shop shuts by its keeper
  going home and the door locking; someone who loiters inside is never
  thrown out, and trading is refused until morning.
- **Creatures and ecology are one system with people**: same shape, same
  clock, same loops, a province-wide researched table, properly sourced
  models and clips per creature type, variety and difficulty by the fixed
  danger band, placed in the slice's places, routes and crossings only.
- **Packs spawn as packs and behave as packs.** Every member of an authored
  pack is spawned and drawn, never one animal a day; a pack moves by its
  group kind (formation, cohesion, follower lag, alarm), varied and sensible,
  following a leader's route.
- **Hostile places attack from the day they are placed.**
- **Factions at Morrowind's size.** The registry is merged down to about
  Morrowind's 32 real factions; a local group is merged into the faction it
  answers to, with a written reason, or becomes a label on its place, never
  a faction of its own. A villager's default faction is none.
- **"Essential" means the doom-warning tier**; nobody is unkillable. There
  are no followers.

**Why.** The owner wants places to feel as alive as in any Elder Scrolls
game, and which Elder Scrolls feeling depends on the place: a Hist village,
a deserter camp and a voriplasm chamber promise different things, and the
place record already says what. A full timetable per person is more than
the feeling is worth; Skyrim's own trick, walk when seen and swap when not,
costs one walk routine and a stuck-people loop on a path network combat and
sneaking need anyway. A whole village changing task on one instant, a pack
arriving one animal at a time, or a meal eaten standing beside a bench all
read as machinery. Eighty placeholder factions is not a design.

**Consequences.**
- [2.4](../phases/2-slice/2.4-people.md) carries the plan: the record, the
  day, the ecology table and assets, the loops and the owner check. 2.7
  takes brains, movesets, loot and death from it.
- [world/72](../world/72-navigation-ai.md) is "walk when seen, swap when
  not".
- Exterior window glow follows the bedtime rule of
  [0123](0123-interiors-are-lit-by-their-sources-windows-and-beams.md).
- `docs/world/74-ecology.md` is the home of every creature row; group kinds
  for packs are data beside it. Part 4 extends both and never re-invents.
- The seat height is one shared value (`socket.seatHeightM`) read by the
  people layer and the player's sit.
- Helstrom's people are 4.1b; nothing built in 2.4 may need a different
  approach for three hundred.

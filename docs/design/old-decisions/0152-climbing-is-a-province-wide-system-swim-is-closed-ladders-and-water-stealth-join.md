<!-- imported unchanged from elder-souls-argonia docs/decisions/0152-climbing-is-a-province-wide-system-swim-is-closed-ladders-and-water-stealth-join.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0152 Climbing is a province-wide system; swim is closed; ladders and water stealth join 2.12

**Decision (owner, 2.12 plan review).**

1. **The climb is Breath of the Wild's, as a generalised system, never
   tailored to the slice.** What is climbable is derived from the rules
   (solid-mesh size, slope bands for walk, scramble and climb, surface
   classes, the exclusions) and holds for the whole province on the day
   the phase closes: every surface the rules call climbable is climbable,
   everywhere, measured by a province-wide survey, not proved on four
   slice surfaces. The set is BotW's only: free climb in any direction
   with corners, hang, shimmy, leap catch up and sideways, climb-down over
   an edge, mantle, drop, slip when wet, a fall at zero stamina. No wall
   running or overhang traversal; those clips stay in the vault for a
   later depth round.
2. **The clips come from FreeClimb** (Nexus 193552, with EVG Animated
   Traversal and SkyParkour for the one-shots: mantles, ledge catch,
   slip, water exit). The mod scene does hold the continuous loops; the
   earlier audit that said otherwise was wrong. The licence reading on
   download is waived: the build is private, personal use, undistributed.
   Credits still land in the root README with every download.
3. **Ladders are 2.12's**: the placed ladder objects, sourced as meshes
   and placed where lore puts them, and the climb up and down them with
   mount and dismount.
4. **Swim is closed as built.** The owner has played it and it stands;
   2.12 runs no swim loop. It delivers only the small swim pieces other
   phases wait on (drowning damage, the water-exit climb, the water rows
   of detection), each with a test. Owner feedback later opens a fix
   round, not this phase.
5. **Climbing out of the water gets its own eyes loop**: onto a ledge, a
   plank landing and a moored hull, proved on the lighter flotilla's
   hulls. Player control of boats stays 2.15's.
6. **Water stealth rides 2.10's per-observer detection.** There is no
   sneak stance in water, yet water is a stealth medium: a submerged
   player breaks sight from an observer above the surface; slow surface
   swimming at night is low and quiet; sprint-swim is loud. These are data
   rows on the detection service, not a mode.
7. **2.12 runs after 2.11**, in the plan's order, as its own phase, never
   as a side lane: it shares the combat runtime, the input bindings, the
   HUD and the touch controls with 2.10.

**Why.** The brief had aged: swim was built and played, the clip audit had
missed FreeClimb, and a climb proved on four hand-picked surfaces would
have been rebuilt the first time a Part 4 packet placed a cliff the rules
never saw. A system that answers "is this climbable?" from geometry alone
scales with the province for free.

**Consequences.** The 2.12 brief is rewritten around these rules; the
research record's clip audit and world/90 §74.3 are corrected;
[loops.md](../phases/loops.md) carries the 2.12 row; 2.10's crouch-to-swim
seam closes in 2.12.

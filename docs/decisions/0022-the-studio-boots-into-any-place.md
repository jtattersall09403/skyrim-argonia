# 0022: The studio is the real game booted into any place by a saved game and a scene file; SkyLink and the console are its hands

**Status:** decided 2026-10-28; rewritten 2026-10-29 by [0029](0029-part-0-is-one-sequence-not-spikes.md) §3
(owner: the studio "may be stale: didn't I subsequently decide we can just use the SkyLink AI tools for things
that we had intended to build 'the studio' for?"; reuse existing tools rather than build redundant harness).
The owner's original ask stands: "some studio mode… designed for agents to be able to easily drive headless and
that is playable for me so we can drop in and teleport around the world to see and test things", without the
new-game flow.

## Context

Skyrim modders already work this way by hand: from the main menu they open the console and `coc` into a cell,
skipping the new game; they use console commands for time, weather, items and quest stages; they keep test saves
and **batch files** (`bat <file>` runs a text file of console commands). SkyLink AI (an SKSE plugin and an MCP
server; owner ruling 2026-10-28) gives an agent the same console with its output, plus teleport, time, weather,
quests, inventory, events, screenshots, save and load. So the studio is those things, not a panel of ours.

## Decision

1. **The studio is the dev profile of the real game** on the game machine: same Skyrim, same pinned stack, same
   `Argonia.esm`, plugins and views, plus the dev-only bridge (SkyLink, and `ArgoniaBridge` for what it lacks;
   0.3 §a), which never ships (0003's release guard checks the DLL list). There is no `ArgoniaStudio` DLL and no
   dev panel.
2. **Boot to a scene, never through the new game.** After each deploy the profile makes the **base save**: a new
   game through the quarantine start (0.4 §b), the **studio character** (built from real records: a race, class,
   birthsign and start kit) standing in a holding cell. A **scene** is `tests/scenes/<id>.txt`, a console batch
   file applied from that save with `bat <id>`: place and marker or coordinates, hour, weather, the character's
   sheet and carried items, quest stages, standing, Owing, who stands where. Every setting goes through what the
   game itself does.
3. **The owner's studio is the console on the stream.** `bat <scene>` for any chunk's owner-check scene; `coc`
   and the map for anywhere else; `tfc` for a free camera; `set gamehour to`, `fw` for time and weather; the
   console's own reads (`getstage`, `getav`, `sqv`) to observe. "Report here" is a note in the check-in issue
   naming the place and the scene; a still the owner wants kept is a screenshot through the stream page.
   Cheats are fine for setup (owner, 2026-10-28); what is tested is still reached by play.
4. **What never happens (old 0149 carried).** No mode, flag or switch stands in for a game action: a scene may
   *start* with items or a stage, because that is staging; drawing a weapon, trading, resting and sailing are
   reached as the player reaches them. A scene never sets what its check tests (loops rule 4).
5. **Agents drive the same studio** through `tools/bridge.py` (0.3): apply a scene, teleport, time, weather,
   short real inputs, activate, read state, events with timestamps, a still from a fixed vantage, the booth,
   frame time. `console` is the scene tool and the setup tool, never the action under test.
6. **The fixtures.** Two studio-only places, never reachable in the game: the **proving ground** (a flat arena
   with walls of each climb class, water of each depth, doors, a ladder, targets, a duel ring) and the **booth**
   (a lit neutral cell for contact sheets). Everything else is tested on real places.
7. **Part 3 builds the real front door** (main menu, character creation, the opening). Until then a player's new
   game lands in the holding cell and nothing depends on it.

## Consequences

- Chunk 0.3 builds the bridge client, the base save, the scenes and the journey runner; every L4 row and owner
  check after Part 0 starts from a scene.
- One base save per build is a build output on the game machine, never committed; it is rebuilt by every deploy,
  so scenes never carry stale state.
- The owner reaches the studio through the same browser stream as the game (0007); the console is opened by the
  stream page's keyboard.
- Scene-to-scene and launch-to-scene times are measured in 0.3 and read by the planner; they are not targets.

# 0022: The studio: a dev build of the game that boots into any place, for agents and the owner

**Status:** decided 2026-10-28. Owner: "Presumably we will need some kind of 'world studio' equivalent so we
don't have to literally go through the new game flow in Skyrim every time we want to test something! … some
studio mode or whatever designed for agents to be able to easily drive headless and that is playable for me so
we can drop in and teleport around the world to see and test things."

## Context

The old project tested everything in `apps/world-studio` and built the real new-game flow only in its Part 3.
Its rule 0149 held: the studio plays the game's own systems the way the player reaches them, and debug UI only
observes or moves the tester.

Skyrim modders work the same way by hand. From the main menu they open the console and `coc` into a cell,
skipping the new game. Bethesda's own test hall `qasmoke` holds one of everything. Then they use console
commands for time, weather, items and quest stages, and keep test saves and batch files. STEP's smoke test is
"`coc riverwood` from the main menu". AutoTest automates the same thing, but reports a crash as "still
running" (research `skyrim-tooling`). The studio is that practice turned into a tool agents can drive.

## Decision

1. **The studio is a dev profile of the real game on the GPU box.** Same Skyrim, same pinned stack, same
   `Argonia.esm`, plugins and views, plus two dev-only parts that never ship (decision 0003; the release guard
   checks the DLL list):
   - **ArgoniaBridge**, the agent API (127.0.0.1, token, SSH tunnel);
   - **ArgoniaStudio**, the owner's panel and the boot. It is a PrismaUI view on our design system, marked
     DEV, calling the same functions as the bridge (one implementation, two front ends).
2. **Boot to a scene, never through the new game.** At the main menu the studio loads the **studio base
   save**. That save is made by the studio itself once per plugin build: the quarantine start is done, and the
   **studio character** stands in a holding cell. The character is built from real records (a race, class and
   birthsign, plus a start-kit record of the kind classes carry).
   The studio then applies a **scene** (`tests/scenes/*.yaml`): a place id and marker, or worldspace
   coordinates; hour; weather; the character's sheet and carried items; quest stages; standing; Owing; who
   stands where. Everything is set at step 0 through the setters the game itself calls, never by a
   stand-in.
   Targets, measured in chunk 0.4: game start to scene ≤ 90 s; scene to scene in a running game ≤ 20 s
   (reload the base save, apply the scene).
3. **What the owner can do in the studio** (the panel, on a dev hotkey and a pad chord):
   - **Places:** every built place from the world record, with its markers.
   - **Map:** click anywhere to teleport.
   - **Scenes:** every chunk's owner-check scenes.
   - **Time and weather.**
   - **Free camera.**
   - **Overlays:** navmesh, sockets, encounter zones and danger bands, water bodies, region, cell borders,
     LOD tier, frame time.
   - **Observe** (read only): quest stages, Owing, the disposition of the person under the crosshair, any
     co-save value.
   - **Report here:** writes the position, a still and a note to the owner's findings file on the box. The
     planner collects it privately and nothing goes into a public issue. Owner check-ins name scenes and
     places, not URLs or machines.
4. **What the studio never does (0149 carried).** No mode, flag or switch stands in for a game action: no god
   mode, no "give me a sword", no "start fight". Drawing a weapon, trading, resting and sailing are reached as
   the player reaches them. A scene may *start* with items or a quest stage, because that is staging, not
   play. A capability that changes what the player can do is a game feature that ships, or it does not exist.
5. **Agents drive the same studio.** The bridge exposes the following, so an L4 check or a journey's game
   runner starts in seconds from a known state:
   - `scene` (apply a scene file), `teleport`, `time`, `weather`;
   - `input` (short real inputs), `activate`;
   - `read` (state), `events` (subscribe with timestamps), `still` (a fixed-vantage screenshot), `booth`.
6. **The fixtures.** Two studio-only places carry no lore and are never reachable in the game:
   - the **proving ground**, adapted from the old repo's `place.fixture.proving-ground` (a flat arena with
     walls of each climb class, water of each depth, doors, a ladder, targets);
   - the **booth**, a lit neutral cell for contact sheets.
   Everything else is tested on real places.
7. **Part 3 builds the real front door** (main menu, character creation, the opening). Until then a player's
   new game lands in a placeholder and nothing depends on it.

## Consequences

- Chunk 0.4 builds the studio with the bridge and both journey runners. Part 1's walks, every Part 2 owner
  check and every L4 row start from it.
- One studio base save per build is a build output on the GPU box, never committed. It is rebuilt when the
  plugin changes, so scenes never carry stale state.
- The owner reaches the studio through the same browser stream as the game (decision 0007).

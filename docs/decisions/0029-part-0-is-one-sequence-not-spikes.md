# 0029: Part 0 is one sequence, not spikes: our stack, the agent's hands on the game, the pipeline and the first block; SkyLink is the bridge; scenes are save plus batch files; journeys read state and keep stills; no installer until release; no time budgets

**Status:** decided 2026-10-29. The owner, reviewing 0.2–0.5 before an unattended overnight run: delete the
time budgets ("not really based on anything"); 0.2's "UI approach chosen with the owner" is stale after the
two-stage UI; "0.2 seems to be proving a load of stuff in spikes that looks like it's now planned in
1-core-loop… review the whole lot and sort it out so we end up with a flow that actually makes sense
sequentially"; no player installer now ("let's just get ourselves up to work"); a brief's Starting state is its
state *now*; the studio may be stale since "we can just use the SkyLink AI tools"; "why is the game runner
'eyeless', that sounds kind of dumb, don't we need eyes?"; "reuse existing tools (like SkyLink AI) wherever
possible rather than reinventing the wheel".

## What was wrong

1. **Spikes duplicated Part 1.** The plan's rule is "final-shaped from the first line" (0023 §4), yet 0.2 had a
   spike for the bridge (then 0.4 built the bridge), for Claywater (then 0.5 regenerated it), for dialogue (then
   1.3 built it), for the native map (then 1.1 used it), for the UI approach (then 1.2 built it). With that rule
   a spike is just the first step of the chunk that builds the thing. Separate spike chunks meant two briefs,
   two contexts and a `spikes/` folder of code to throw away.
2. **Three pieces of harness were about to be built that existing things already do.** The bridge (SkyLink AI
   ships an SKSE plugin and an MCP server with teleport, time, weather, console with output, Papyrus calls,
   state, events, screenshots, save and load: the owner's 2026-10-28 ruling named it); the studio panel (the
   console's `coc`, `bat <file>`, `set gamehour`, `fw` and a saved game already boot into any place and apply a
   scene, for an agent and for the owner alike); the core runner (a second runner replaying journeys against our
   rules with a world model is a harness for its own sake; unit tests prove rules).
3. **"Eyeless" overstated the 2026-10-28 ruling.** The owner banned agents *piloting* the game by looking,
   because that produced harness bugs, not findings. It never banned evidence. A journey's pass or fail is read
   from state and events; a still at each step is kept as evidence and read when a step fails or a reader is
   asked. That is "eyes on", not "eyes off".
4. **The installer for strangers belongs to release** (3.4). Now the stack must install on our own game machine
   by script, nothing more.
5. **Time budgets** ("budget 6 days", "6–10 wk") were guesses dressed as plans. Cycle times are measured
   (0.3's loop), never budgeted.

## Decision

1. **Part 0 is four chunks in sequence, each a real deliverable that Part 1 builds on, and no spike:**
   - **0.0** can it be played (done, closing);
   - **0.1** bootstrap (done);
   - **0.2 our stack on the game machine:** the pinned runtime, every dependency the plan names installed by
     script as a profile (the 0.0 overlay generalised), Pandora run, the smoke scene passed (walk, swing, dodge,
     climb, swim, sail, open each menu), the frame-time and latency record with the full stack, Crash Logger,
     saves backed up; permission requests drafted for the owner to send (not gating);
   - **0.3 the agent's hands:** SkyLink AI as the bridge if it loads on the pin (our own dev plugin only for
     what it lacks, by its method), our SKSE build on the game machine proved with the first ArgoniaCore stub,
     scenes as a base save plus console batch files, the journey runner (state and events, stills as evidence),
     the deploy, and the edit → deploy → verdict cycle timed once unattended;
   - **0.4 the pipeline and the first block:** world JSON → ArgoniaGen → Spriggit → `Argonia.esm`,
     deterministic; the quarantine start; the immersion inventory; and the Claywater Station block built the
     native way (LAND and LTEX paint from the pulled heightfield, one region through the CK's generator with
     Tropical Skyrim loaded, the place as REFRs on its own ground, three people with whole-body templates,
     navmesh by our job with the CK as check), walked in game.

   Part 1 then builds the systems on that block. The world track starts after 0.4.
2. **What the spikes asked is answered inside the chunks that build the thing**, as their first step and with a
   gate that can fail: the native map in 1.1 §a; the dialogue engine's route (MorrowindRuntime model-half fork
   or our own store) in 1.3 §b; the UI technology for our four screens in 1.2 §0; DSR measurement and timing in
   2.7; the stepped river in 2.W2; perf with the stack in 0.2; the loop timing in 0.3. The `spikes/` folder goes.
3. **The studio is a base save, scene batch files and SkyLink.** No dev panel, no `ArgoniaStudio` DLL. A scene is
   `tests/scenes/<id>.txt`, a console batch file (`bat <id>` in the console; the same file applied by the agent
   through SkyLink's console tool), starting from the dev profile's base save made after each deploy. The owner
   opens the console on the stream and types `bat <scene>`; cheats are fine for setup (owner, 2026-10-28). What
   stays from 0022: every in-game check starts from a scene, never the new-game flow; no scene sets what it
   tests; the fixtures (the proving ground, the booth). 0022 is rewritten.
4. **Journeys read state and keep stills.** A journey is a script of short steps with expectations on state and
   events, played in the game through the bridge; the runner takes a still at every step and attaches it to the
   run; a failing step's stills go to a reader; no agent pilots by looking and no step is judged by pixels unless
   its brief says so (L5). There is one runner. 0021 §3 and §5 are rewritten; the ladder stands.
5. **No installer for players until 3.4.** 0.2 installs our stack on our machine by script; the same script is
   the seed of 3.4's installer.
6. **No time budgets anywhere.** Chunks have gates, not days; PLAN §5 loses its estimate column; 0.3 measures the
   cycle time and the planner reads it, never a guess.
7. **A Starting state is the state now.** Every brief's Starting state describes the tree on the date written
   and is rewritten by the chunk before it when that chunk closes; "Expected:" lines are what the previous chunk
   has promised, named as such.
8. **Reuse before harness, always.** Before any dev tool is written, the brief names the existing tool tried
   (SkyLink, the console, the CK's own tools, houseCARL, xEdit scripts) and why it fell short.

## Consequences

- 0.2–0.5 rewritten as 0.2–0.4; 0.5 merged into 0.4; `spikes/` removed; decisions 0021, 0022, 0023 and 0001 §3
  updated; 1.1, 1.2 and 1.3 gain the first steps the spikes held; every G-gate reference outside Part 0 now
  names the chunk and section that answers it.
- The overnight run's order: 0.2 (game machine) with 0.4 §a–§c (build VM) in parallel; 0.3 after 0.2's stack;
  0.4 §d (the block in game) after 0.3's hands; then Part 1's 1.1 and the world track's 2.W1 in parallel.
- Owner involvement in Part 0 after this: none that blocks (permission requests are sent in the owner's time;
  O-1 is theirs).

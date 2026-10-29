# Loops and the ladder: how a chunk checks its own work

Carried from elder-souls-argonia (its `docs/phases/loops.md`, decisions 0155 and 0156) and rebuilt for this
project's machines and engine ([0021](decisions/0021-fast-focused-loops-and-the-ladder.md)). Every chunk brief
names its loops in a **Loops** section. A loop nobody planned means the acceptance list was incomplete: fix the
list.

## 1. The ladder: each block at its cheapest level, composed once

A feature is a composition of **blocks**. Each block is checked **once, at the cheapest level that can reliably
prove it**, and the composition is checked only for what composition can break.

| Level | Harness here | Proves | Where | Cost |
|---|---|---|---|---|
| **L1 data** | schema and integrity checks, generated-record checks, Spriggit round trip, the direction validator, the CK load log | ids, references, counts, every socket filled, every promise met | build VM | seconds |
| **L2 logic** | unit tests of the pure C++ core and the Python tools | the numbers and the rules | build VM | seconds |
| **L3 still, off-game** | PrismaUI views in headless Chrome against mock JSON at the four viewports, read by readers | a screen, its states, focus order, readability | build VM | a minute |
| **L4 in game, from a scene** | a scene applied on the base save (decision [0022](decisions/0022-the-studio-boots-into-any-place.md)), then the **journey runner**: state reads, event timestamps (hits, animation events, stages, music), a still per step, and **fixed-vantage stills** read by readers | that blocks join inside Skyrim (the engine, the frameworks and our plugins agree); a placed thing looks right | GPU box | seconds per check, batched |
| **L5 short clip** | a 3–8 s clip from a fixed vantage (or side by side with a DSR reference), read frame by frame | only what no still or timestamp can show: a transition, the near-to-distance hand-off, feel | GPU box | minutes per pass |
| **L6 the owner** | the owner plays from a scene (Parts 0–2) or the real game (Parts 3–4) through the stream | the whole, as a player | owner | the owner's time |

**What changed from the old ladder.** The old project could run its game headless in Node; Skyrim needs a GPU.
- The old "headless play" level becomes the **journey runner** (L4, the script in Skyrim through the bridge,
  state and events with a still per step); our own rules are unit tests (L2), not a second runner (0029).
- The old "motion" level becomes L4 event timestamps for timing, with L5 clips only for how motion *looks*.
- RunPod pods are replaced by the AWS GPU box (decision 0008), one game at a time.

## 2. Rules

1. **A check lives at the lowest level that proves it, never higher.**
   - A damage number is L1 or L2, never a filmed swing.
   - A HUD icon's states are L3 stills.
   - A roll's i-frame window is an L4 timestamp check, never a clip.
2. **One lane owns a feature and its joins.** The lane that builds a subset tests the subset and its joins to
   what is already built, in the same loop. The later system owns the join with the earlier one. The brief
   lists the joins. There are no separate seam lanes.
3. **Scenes stage every block proved below them** and play only the join they test: the attacker at reach, the
   arrow through the game's own hit path, the witness in view. Replaying a proved block is a defect in the
   check.
4. **State is set at step 0 only, and a scene never sets what it tests.**
   - Staging an observer's suspicion and then expecting the sneak eye proves nothing.
   - Every later state is reached by play: an input, or the activation call the input makes.
   - Scenes use the shipped plugins, data and systems through the setters the game itself calls. No stub
     stands in for a system.
5. **Journeys read state and keep stills** (decision 0021 §3).
   - **The script.** A journey is a script as data (`tests/journeys/<id>.yaml`).
   - **The runner.** `tools/run_journey.py` plays it in the game through the bridge (0.3 §d).
   - **What it does.** It moves the player between steps by teleport. Each step is a short action; it reads
     state and events, and takes a still it keeps with the run.
   - **What decides.** State and events. A failing step's stills go to a reader; no agent pilots by looking;
     no step is judged by pixels unless the brief names an L5 reason.
   - **When it runs.** After its chunk's loops are green, until it passes; then the owner plays it from the
     same scene (L6).
   - **The deployed build.** Nothing plays on a real place's long-lived state, or on the owner's save, as an
     agent gate.
6. **A clip (L5) needs a reason no lower level can give**, written in the brief. A feature with no such join
   films nothing.
7. **Measure everything, diagnose all, fix once, re-measure.**
   - One survey of every deliverable, kept as a script or checklist file in the chunk's loop folder, so the
     re-measure is the same survey.
   - Every finding gets a root cause before any edit.
   - Fixes go as one batch, each with the test that would have caught it.
   - Re-measure. A surviving finding gets one more pass with its diagnosis corrected, never a third without a
     written reason.
   - One finding at a time is the anti-pattern.
8. **Eyes live in the lane that builds the thing.** Stills and clips go to `reader` agents, never the planner.
   A builder may look at its own stills. Every reader carries the **feel question** beside its checklist:
   "does this feel like the game; what jars?" **Numbers alone never close a visual change.**
9. **The harness is tested before a lane uses it.**
   - A change to the bridge, a runner, a scene or the reader brief carries its own test, plus a dry run on a
     known-green scene.
   - A harness defect found in a lane is fixed at source, with that test, before the lane continues.
   - The screenshot oracle is proved live (two frames differ).
   - Three identical failures stop the loop for diagnosis.
   - A crash is a failure.
10. **GPU-box batching.**
    - A lane holds the GPU-box lock for its whole loop pass: start once, apply each scene, run every L4 and L5
      row of the pass, stop. Other lanes queue.
    - If the queue is measured to be the bottleneck and the budget allows, the planner adds a second GPU box
      (decision 0008).
11. **The planner watches the loops run.**
    - At every check-in it reads each lane's timeline and judges elapsed time against what the step should
      cost.
    - When a step is slow it diagnoses and fixes the method first: pause, optimise, resume. Examples: a survey
      that re-reads what it measured, a check that restarts the game instead of applying a scene, a sweep that
      could be batched.
12. **The owner never does QA.** Owner checks are play (L6) of work that is already green. A red the owner
    finds returns to the lane that owns it.

## 3. Harnesses (cheap first)

| What is measured | Harness | Level |
|---|---|---|
| data shape, ids, references, counts, sockets, promises | integrity gate, record checks, Spriggit round trip, CK load log | L1 |
| a rule or formula (stats, vastei, barter, detection, damage, poise) | C++ core and Python unit tests; the stats sim (every archetype × five builds) | L2 |
| a fight, an AI choice, a combat window by time | the combat core driven by a time stream (no game) | L2 |
| a quest's rules, a dialogue walk's conditions, a crime response, a co-save round trip | unit tests of the core and the tools | L2 |
| a UI screen on every viewport, focus order, readability | the `ui/` harness: Playwright at 1920×1080, 1280×720, the Magic V5 folded (~21:9) and unfolded; readers | L3 |
| that our plugin, the frameworks and Skyrim agree (a hit lands, a window opens on time, a stage fires, an NPC paths) | a studio scene and the game runner: state reads and event timestamps | L4 |
| a journey inside the game | the journey runner: state, events, a still per step | L4 |
| a place, a kit piece, an item or creature up close | bridge vantage stills and booth sheets, read by readers | L4 |
| a transition, the LOD hand-off, feel (including side by side with DSR) | short clips, read frame by frame | L5 |
| frame cost on the composed world | bridge frame-time probes on the chosen GPU instance | L4 |
| prose | the `text-review` skill (one reader, then the prose linter) | L1 |

## 4. Where the chunks use loops

Each chunk brief's **Loops** section lists:
- its subsets, each with its level;
- the joins its lane owns;
- its journeys;
- for any L5 row, the reason.

Chunks that build tooling (Part 0) run their acceptance commands and the gate, and prove each harness on a
known-green case. They do not loop.

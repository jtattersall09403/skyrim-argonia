# Loops and the ladder: how a phase checks its own work

Carried from elder-souls-argonia (old `docs/phases/loops.md`, decisions 0155 and 0156; owner: "I liked it as a
conceptual way of working") and rebuilt for this project's machines and engine (decision
[0021](decisions/0021-fast-focused-loops-and-the-ladder.md)). Every phase file names its loops in a **Loops**
section; a loop nobody planned means the acceptance list was incomplete.

## 1. The ladder: each block at its cheapest level, composed once

A feature is a composition of **blocks**. Each block is checked **once, at the cheapest level that can reliably
prove it**, and the composition is checked only for what composition can break.

| Level | Harness here | Proves | Where | Cost |
|---|---|---|---|---|
| **L1 data** | schema and integrity checks, generated-record checks, Spriggit round trip, direction validator, CK load-log check | ids, references, counts, every socket filled, every promise met | build VM | seconds |
| **L2 logic and simulation** | unit tests of the pure C++ core and Python tools; **core simulations**: scripted sessions that drive ArgoniaCore/ArgoniaCombat's rules with no game (a duel by time stream, a quest walked stage by stage, a dialogue tree walked, a barter, a crime → Owing → custody, a save round trip of the co-save) | the numbers, the rules, and joins *between our own systems* | build VM | seconds |
| **L3 still (off-game)** | PrismaUI views in headless Chrome against mock JSON at the four viewports; reader agents on the stills | a screen, its states, focus order, readability | build VM | a minute |
| **L4 in game, staged** | a staged scene on the GPU box through ArgoniaBridge: state reads, event timestamps (hits, animation events, music), and **in-game stills** (bridge screenshots, booth sheets) read by readers | that blocks join inside Skyrim: the engine, the frameworks and our plugins agree; a placed thing looks right | GPU box | minutes per batch |
| **L5 filmed seam** | a 3–8 s clip recorded in game (or side by side with a DSR reference clip), read frame by frame | only what no lower level can show: motion, a transition, feel | GPU box | minutes and dollars per pass |
| **L6 the owner** | the owner plays a packet through the stream | the whole, as a player | owner | the owner's time |

**What changed from the old ladder.** The old project could run its game headless in Node; Skyrim cannot run
without a GPU. So:
- the old "headless play" level splits in two: **joins between our own systems** move down to L2 core
  simulations (seconds, no GPU), and **joins that need the engine** are L4 staged scenes on the GPU box;
- the old "motion" level (a sandbox animation check) becomes L4 event-timestamp checks for timing (cheap, no
  film) and L5 clips only for how motion *looks*;
- RunPod pods are replaced by the AWS GPU box (decision 0008), one game at a time.

## 2. Rules

1. **A check lives at the lowest level that proves it, never higher.** A damage number is L1/L2, never a filmed
   swing. A HUD icon's states are L3 stills. A roll's i-frame window is an L4 timestamp check, never a clip.
2. **Staged scenes stage every block proved below them** and play only the join they test (the attacker at reach,
   the arrow through the game's own hit path, the witness in view), so they can fail only on that join. Replaying
   a proved block is a defect in the check.
3. **State is set at step 0 only, and a scene never sets what it tests.** Staging an observer's suspicion and then
   expecting the sneak eye proves nothing; every later state is reached by play (bridge inputs). Scenes use the
   shipped plugins, data and systems through the setters the game itself calls; no stub stands in for a system.
4. **A filmed seam (L5) needs a reason no lower level can give**, written in the brief. A feature with no such join
   films nothing.
5. **Feature loops and seam loops, in parallel, then compose once.** A phase runs many small loops, each on one
   subset (a system, a place, a creature, a screen) with disjoint files, each pairing its measurement with its own
   eyes at the level that proves it. Every **seam** between two systems is its own loop row and **names two owners**
   (the system on each side). Entry into and exit from a feature (the prompt that opens it, the screen closing back
   to play) are blocks of its loop where a player would notice them.
6. **Journeys come last.** A phase names a few end-to-end journeys (staged scenes as data); they run only after
   every feature and seam loop is green, loop until they pass, and then the owner plays them (L6). Nothing plays on
   a real place's live state as an agent gate.
7. **Measure everything, diagnose all, fix once, re-measure.** One survey of every deliverable (a script or
   checklist file in the phase's loop folder, so the re-measure is the same survey); every finding gets a root cause
   before any edit; fixes go as one batch, each with the test that would have caught it; re-measure; a surviving
   finding gets one more pass with its diagnosis corrected, never a third without a written reason. One finding at
   a time is the anti-pattern.
8. **Eyes live in the lane that builds the thing.** Images and clips go to `reader` agents (never the planner); a
   builder may look at its own renders. Every reader carries the **feel question** beside its checklist: "does
   this feel like the game; what jars?" **Numbers alone never close a visual change.**
9. **The harness is tested before a lane uses it.** A change to the bridge, a scenario runner, the capture or the
   reader brief carries its own test and a dry run on a known-green scene; a harness defect found in a lane is fixed
   at source, with that test, before the lane continues. The screenshot oracle is proved live (two frames differ);
   three identical failures stop the loop for diagnosis; a crash is a failure.
10. **GPU-box batching.** A lane holds the GPU-box lock for its whole loop pass (start once, run every L4/L5 row of
    the pass, stop), queuing other lanes; if the queue is measured to be the bottleneck and the budget allows, the
    planner adds a second GPU box (decision 0008).
11. **The planner watches the loops run.** At every check-in it reads each lane's timeline, judges elapsed time
    against what the step should cost, and when a step is slow it diagnoses and fixes the method first (a survey that
    re-reads what it measured, a scene that boots the game per check, a sweep that could be batched): pause,
    optimise, resume.
12. **The owner never does QA.** Owner packets are play (L6) of work that is already green; a red the owner finds
    returns to a focused loop.

## 3. Harnesses (cheap first)

| What is measured | Harness | Level |
|---|---|---|
| data shape, ids, references, counts, sockets, promises | integrity gate, record checks, Spriggit round trip, CK load-log | L1 |
| a rule or formula (stats, vastei, barter, detection, damage, poise) | C++ core and Python unit tests; the stats sim (every archetype × five builds) | L2 |
| a fight, an AI choice, a combat window by time | core combat simulation by time stream (ArgoniaCombat core, no game) | L2 |
| a quest, a dialogue walk, a crime response, a co-save round trip | ArgoniaCore simulations by script | L2 |
| a UI screen on every viewport, focus order, readability | `ui/` harness: Playwright at 1920×1080, 1280×720, Magic V5 folded (~21:9) and unfolded; readers | L3 |
| that our plugin, the frameworks and Skyrim agree (a hit lands, a window opens on time, a quest stage fires, an NPC paths) | bridge scenarios with state reads and event timestamps on the GPU box | L4 |
| a place, a kit piece, an item or creature up close | bridge booth sheets and vantage stills, read by readers | L4 |
| motion, a transition, feel (incl. side by side with DSR) | recorded clips, read frame by frame | L5 |
| frame cost on the composed world | bridge frame-time probes on the chosen GPU instance | L4 |
| prose | `text-review` skill (one reader, then the prose linter) | L1 |

## 4. Where the phases use loops

Each phase file's **Loops** section lists its feature loops, seam loops (with their two owners) and journeys, each
with its level and, for L5 rows, the reason.

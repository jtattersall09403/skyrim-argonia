# 0036 — In-game checks are driven by an agent, kept simple and smart

**Date:** 2026-11-01 · **Status:** accepted (owner rulings in the 1.15 session; amends 0021 §3's journey runner)

## Decision

1. **An agent drives the in-game check**, through the bridge and the console, and judges as it goes: it looks at
   each result (a still's content, a state read, an event) before the next step, waits longer when a load has not
   settled, retakes a blank or unchanged capture, moves the camera when the subject is out of frame, and stops when
   it has the evidence the brief asks for. A scripted journey (`tests/journeys/<id>.yaml`, `tools/run_journey.py`)
   remains the record of the steps and a way to replay a check that is already known to work; it is not the only
   way, and a script that fails on timing is the driver's to fix on the spot, not a verdict on the game.
2. **Simple and smart.** The lightest check that gives confidence: teleport, settle, still, state read. No walks,
   no fights, no long sequences of inputs. A mod's own behaviour is not retested (0010): what we check is our
   placement and our joins.
3. **Stills first, clips when a still cannot show it.** A short clip or a temporal strip (frames every N seconds,
   side by side) is taken when the question is motion, transition, burn-off, drift or timing (0021's L5 reason),
   and the brief says why.
4. **A capture is evidence only when the driver has confirmed it:** two frames differ (the oracle is live), the
   subject is in frame, the load has finished. A blank or stale still is a harness failure, never a finding.
5. The **driver agent** (`.claude/agents/driver.md`) is the one that runs a batch on the game machine: it starts
   from the batch file, runs each item, confirms each capture, adapts, and hands the confirmed stills to a `reader`
   with the brief's checklist. It never diagnoses the game from a capture it has not confirmed.

## Why

- The owner, 2026-11-01: "agents might be better, if a little slower, as they can look at the results of their
  actions and adjust accordingly; we had lots of times where captures came back blank because they just didn't wait
  long enough for something to load; an agent acting intelligently can reason about things like that." And: "I am
  very loath to have lots of complicated journeys; agents struggle to actually do them and then draw incorrect
  conclusions about the game that are the result of a capture failure or bad controls."
- 1.12's look 1 (2026-11-01) passed scripted checks the owner then found broken; the blank and stale captures of
  2026-10-30 and 2026-10-31 cost a day each.

## Consequences

- `docs/loops.md` §2 rule 5 and the scene-author skill carry this; every brief that names an in-game check names
  the driver, the evidence wanted (still, clip or strip) and the lightest steps that give it.
- The planner's one-batch-per-round rule (loops rule 10) stands: the driver runs the whole round's batch in one
  session on one deploy.

## Amendment, 2026-11-04 (owner, 19:05, #41)

- A wrongly framed capture is fixed inside the run: the run's reader judges each still as it lands and the driver retakes at once with a changed heading or pitch; nothing waits for the round's end and a laborious redo.
- Every look stop takes a scan: captures at several headings from the stand (the runner's `scan:` on a still step, six headings by default), so the reader picks the frame that shows the subject and the stand's aim is never the single point of failure.
- Creature and spawn checks are state reads, never stills: the spawn records loaded and the actors within range read by kind through the bridge ("lining up the stills will be very buggy").

# Part 0: Foundation

**Goal.** First, prove the game can be played at all through the stream on the owner's phone and Mac (0.0, gate
G0); then put everything in place that Part 1 builds on, each piece real and kept (decision
[0029](../../decisions/0029-part-0-is-one-sequence-not-spikes.md): no spikes):
- the repo, the ways of working, the toolchain and the imported world (0.1);
- our dependency stack installed on our game machine by script, smoke-tested, with the frame-time and latency
  record (0.2);
- the agent's hands on the running game: the bridge (SkyLink AI first), our SKSE build, scenes, the journey
  runner, the deploy and the timed loop (0.3);
- the record pipeline, the quarantine, the immersion inventory, and the Claywater Station block built the
  native way and walked in game (0.4).

**What this part is not.** It builds no game system (Part 1), no installer for other players (3.4), and no tool
before the chunk that uses it (decision 0027 §7). It builds no harness an existing tool already provides (0029 §8).

## Starting state (2026-10-29)

0.0 is closing in its own session (the owner's play sessions passed; the hand-off is in its brief). 0.1 is done
(its Outcome). The game machine is a Windows spot GPU instance with Skyrim 1.7.104 pinned offline, the 0.0
souls-like overlay and the stream; the build VM holds the toolchain, the imported world, the pulled heightfield
and hydrology arrays in `$ARGONIA_DATA`, the corpus in `$ARGONIA_PRIVATE`, and the Nexus key.

## Chunk table

| Id | Chunk | Depends on | Runs beside |
|---|---|---|---|
| 0.0 | [Can it be played? Vanilla Skyrim streamed, touch and GameSir controls, a feel probe (G0)](0.0-can-it-be-played.md) | — | — |
| 0.1 | [Bootstrap: repo, ways of working, lean toolchain, import](0.1-bootstrap.md) | 0.0 | 0.0 |
| 0.2 | [Our stack on the game machine](0.2-the-stack.md) | 0.1 | 0.4 §a–§c (build VM) |
| 0.3 | [The agent's hands: bridge, SKSE build, scenes, runner, deploy, the timed loop](0.3-the-agents-hands.md) | 0.2 | 0.4 §a–§c |
| 0.4 | [The pipeline, the quarantine, the inventory and the first block](0.4-pipeline-and-first-block.md) | §a–§c: 0.1; §d: 0.2, 0.3 | 0.2, 0.3 |

**The overnight order.** 0.2 on the game machine and 0.4 §a–§c on the build VM at once; 0.3 when 0.2's stack
passes its smoke scene; 0.4 §d when 0.3's hands work; then Part 1's 1.1 and the world track's 2.W1 at once.
Only one lane drives the game machine at a time (`job_guard.sh run --gpu`).

## Part 0 exit (the owner signs)

- 0.2's smoke scene passes on the installed stack; the frame-time bar and the latency record are written.
- 0.3: the bridge answers every call the journey runner needs; our SKSE stub loads; ten scenes apply; a broken
  journey fails at its step with a readable reason and its stills; one unattended edit → deploy → verdict cycle
  is timed and recorded.
- 0.4: `make plugin && make check` green with the Spriggit round trip and no diff on a second run; the
  quarantine journey green at 1, 10 and 50 days; the inventory written; the Claywater block walked in game by
  the journey runner and by the owner.
- **Owner check:** on the phone and the Mac, open the console, `bat claywater`, walk the road into the place and
  into a house, `bat proving-ground`, climb a wall, swim, board the boat. Reply with what jarred. The check-in
  carries the gate evidence and the costs; no estimate.

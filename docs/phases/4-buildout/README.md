# Part 4: Build out sideways

**Goal.** Go from the slice to the whole province and every quest, with the systems Part 2 proved and the shell
Part 3 shipped. The work runs in region packets, each landing in studio and game at once. Nothing here is a new
risk: it is leg-work run as sprints, with the measure–diagnose–fix loop, an owner walk per region, and polish at
the three moments the master plan fixes.

## Shape
1. **4.1 Before scale** runs once:
   - the `P1 before-scale` queue;
   - `world-builder` proved per place type, unattended;
   - Helstrom and the cities by hand with the owner;
   - the immersion method at scale;
   - the packet template;
   - the re-plan, and O-2 (when to move to 20x).
2. **4.2 Region packets** repeat until the province is full. A packet holds one region's worth of places,
   population, dialogue, quests, encounters, sound and books, with its `P2` polish inside it. Each is walked and
   frozen.
3. **4.3 Narrative lines** run as narrative packets interleaved with 4.2, by what each needs built:
   - the main quest's acts beyond the opening;
   - the faction lines;
   - the Lost City and the endings;
   - the bosses.
4. **4.4 Assembled interiors** and **4.5 Systems depth** are pulled when a packet or a line first needs them, never
   ahead.
5. **4.6 Final look, polish and release** runs once at the end.

**Agile, concretely.** A packet is a sprint with a brief, a survey script, one owner walk per region and a
retrospective line in the packet ledger. The next packet's brief takes the retrospective. Velocity is measured
from the ledgers (agent time, GPU time and rounds per place), never estimated.

## Starting state

Written by the agent that closes 3.5.

## Chunk table

| Id | Chunk | Depends on |
|---|---|---|
| 4.1 | [Before scale](4.1-before-scale.md) | 3.5 |
| 4.2 | [Region packets](4.2-region-packets.md) (one chunk per packet, `4.2-<region>-<n>`) | 4.1 |
| 4.3 | [Narrative lines](4.3-narrative-lines.md) (one chunk per line, `4.3-<line>`) | the packets a line needs |
| 4.4 | [Assembled interiors](4.4-assembled-interiors.md) | the first packet that needs one |
| 4.5 | [Systems depth](4.5-systems-depth.md) (one chunk per system, `4.5-<system>`) | the packet or line that needs it |
| 4.6 | [Final look, polish and release](4.6-final-polish-release.md) | the last packet |

## Milestones
- **M1, the first complete playthrough:**
  - the main quest end to end with all three endings;
  - 170–210 journaled quests;
  - every region at least at slice density along the main quest's route.

  The owner plays it through, and a release follows (4.6, or an early-access update).
- **M2, maturity:** every active catalogue place built, 450–550 quests (O-18), all factions complete. Owner
  sign-off.

## Part 4 exit
- M2 is reached, or the owner declares the content complete.
- Every region walk is closed. Every quest's branches pass at L2 against the record, and its main path in game.
- The `P3` queue is done, or marked `optional` by the owner.
- The release is published.

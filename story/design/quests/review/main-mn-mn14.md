# Paper runs: MN14 to MN19 (lane D)

Each run's folder is `story/playtests/quest.main.<quest>/<time>-designed/`, and its `grade.md` grades every milestone.
From 17:15 on, every run is played after MN01 to MN13 (`--after`, MN13 at 91), with the earlier quests of this lane
after them.

| Quest | Runs | Passing runs (way or ending) |
|---|---|---|
| MN14 | 9 since `--after` (2 before, plus 2 stuck and 3 steered ones before that) | 172637 pick, 172753 unseen, 172548 force (duel, then killed him), 172405 buy; 173527 guest with lane C's real MN13 notes |
| MN15 | 6 (3 before `--after`) | 172829 fight, 172853 sneak, 172919 turn |
| MN16 | 9 (2 before `--after`) | 172949 lift, 173021 force, 173056 sneak, 173129 turn |
| MN17 | 9 (1 stuck before `--after`) | 173353 believed, 173432 fought her |
| MN18 | 4 | 172837 believed, 172909 she is dead |
| MN19 | 5 | 173251 Use, 173054 Take, 173333 Give |

## Classes of miss that a change cleared

- **A room behind a door was not a place.** The hall and the vaults are rooms of their places (`anchor.room`), and
  their chests are containers.
- **A thing the objective points at had no placement.** The marker led nowhere: the Kings' Gate in MN17, and
  Never-Writes-Twice in MN19. Both are now placed.
- **A term the line relies on was not glossed in the quest's first entry.** The player could name the Eye, the Root
  and the order but not say what they are. Each quest's first entry now glosses them once: the order as the
  Xeech-Leel's secret warriors, the Eye as an amber jewel at the Root, and the gate and its stones.
- **A report step with no reason given.** At MN16 the player asked why the stones go to Helstrom and not to the gate;
  the end entry now says Never-Writes-Twice ordered all three brought to her first.
- **The twist's choice did not state everything it relies on.** MN17's stage 30 entry now states:
  - what the order is, and Umbriel;
  - what the dreamers are;
  - what the Eye does used and lifted;
  - what fighting her and believing her each give and cost.
- **A person dead in an earlier quest still stood in the hall.** In MN18, Cuts-the-Old-Knot's placement in the hall
  is now off until the believing branch switches it on.

## Left open

- The Unbound's top rank shows to the player as "top": the rank still needs a name.
- In MN19 the Use ending kills Cuts-the-Old-Knot's reference at the gate, not her reference in the hall. The build
  must treat her as one person with one reference.

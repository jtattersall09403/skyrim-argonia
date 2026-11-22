# Paper playtests: main quest MN01 to MN05 (lane A)

Moment 1: the designed records. One line per run.

| Quest | Run | Result |
|---|---|---|
| MN01 | quest.main.mn01/20261117T170035Z-designed (thief) | pass |
| MN01 | quest.main.mn01/20261117T170035Z-designed~2 (own five) | pass |
| MN02 | quest.main.mn02/20261117T165848Z-designed (--know: a stand-in from MN01's design) | pass; replaced by runs on MN01's real notes |
| MN02 | quest.main.mn02/20261117T170200Z-designed | miss: what a Hist is, and who Weeltul is, at stage 20; where to ask for the second task at 90 |
| MN02 | quest.main.mn02/20261117T170313Z-designed | pass |
| MN03 | quest.main.mn03/20261117T165941Z-designed (truth; stand-in MN02 notes) | miss: what each answer gives at 60; the next step at the ending |
| MN03 | quest.main.mn03/20261117T165941Z-designed~2 (comfort; stand-in) | miss: the same, and a false belief that Heem-Jasa would still trade |
| MN03 | quest.main.mn03/20261117T170353Z-designed (truth) | miss: "Unbound" had no gloss or topic |
| MN03 | quest.main.mn03/20261117T170353Z-designed~2 (comfort) | miss: the same |
| MN03 | quest.main.mn03/20261117T170516Z-designed (truth) | pass |
| MN03 | quest.main.mn03/20261117T170516Z-designed~2 (comfort) | pass |
| MN02 | quest.main.mn02/20261117T170740Z-designed (--way fight) | pass |
| MN02 | quest.main.mn02/20261117T170740Z-designed~2 (--way shoot) | pass |
| MN03 | quest.main.mn03/20261117T170740Z-designed (--way fight, truth) | pass |
| MN03 | quest.main.mn03/20261117T170741Z-designed (--way shoot, comfort) | pass |
| MN04 | quest.main.mn04/20261117T171435Z-designed, ~2, 20261117T171436Z-designed | miss: Vosh-Leera in a room no MN04 door reached (stopped at 30) |
| MN04 | quest.main.mn04/20261117T171601Z-designed, ~2 (pickpocket, pick) | harness error: the cage door had no placeName |
| MN04 | quest.main.mn04/20261117T171601Z-designed~3 (fight) | pass |
| MN04 | quest.main.mn04/20261117T171711Z-designed (pick) | pass |
| MN04 | quest.main.mn04/20261117T171712Z-designed (pickpocket) | pass |
| MN05 | quest.main.mn05/20261117T171712Z-designed (pickpocket) | pass; its notes are MN06's --know |
| MN05 | quest.main.mn05/20261117T171712Z-designed~2 (fight) | pass |
| MN05 | quest.main.mn05/20261117T171712Z-designed~3 (buy) | pass |
| MN01 | quest.main.mn01/20261117T171828Z-designed (rooms) | pass |
| MN02 | quest.main.mn02/20261117T171828Z-designed (--after MN01) | pass |
| MN03 | quest.main.mn03/20261117T171829Z-designed, ~2 (--after; truth, comfort) | pass |

A further class cleared: **a person in a room with no door to it** (record: placements). Every quest that names
a person standing in a room places the door whose `placeName` is that room.

Classes of miss that a change cleared:

- **Did not know what to do next** (record: journal). An ending's journal must name the next quest's first step and
  its place, even when the next quest's objective carries the marker. MN03's endings and MN04's ending were fixed.
- **Did not see a choice's stakes** (record: journal). Before a choice, the journal says what each answer gives and
  costs (MN03 stage 60).
- **Believed something false** (record: ending journal). An ending says plainly what is now closed (MN03 stage 91).
- **A word with no gloss** (record: terms and the line on the path). A name the game shows on people ("Unbound
  Sap-Taker") is glossed on the path where it is first seen (MN03 stage 50).
- **Did not know a central thing or a person on sight** (record: journal). The journal names the person the
  objective marks, and says what the central thing is at the step that sends the player to it (MN02 stage 20).

Harness note for the lead: the paper game puts the barge's hold and the landing in one place, so MN01's player
lists Dralin as present in the hold.

## Dralin's offer of gear (2026-11-22)

The owner's ruling of 2026-11-22 replaced the hold's starter kit with Dralin's offer on the landing: his
speaks-first line now ends with the offer and sets stage 50; four pick topics (stages 51 to 54, each giving its
pieces and setting 90) and a decline (to 90) close it, and Dralin's death at stage 50 moves the quest on to 90, so
MN02 still starts on stage 90. The pieces are Cipactli's Naga warhammer, sword, flint arrows and knife and bamboo
bow at Skyrim's iron tier, and Skyrim's tome of Sparks. The kit is gone from main-plot.md and the place's needs.

| Quest | Run | Grade |
|---|---|---|
| MN01 | quest.main.mn01/20261122T053302Z-designed (hunter, took the bow) | pass |

Harness fix in the same change: a stage whose own results set the next stage now shows its journal entry first, as
Skyrim does (tools/playtest/record.py, with its test).
| MN01 | quest.main.mn01/20261122T054214Z-designed (after review: the bow) | pass |

Review round (fresh quest-reviewer): fixed, Naga glossed in Dralin's line; the Naga item names credited to the dead
cutters who carried them, not to a Naga tongue; stage 90 entry no longer says Dralin has nothing more (untrue if he
was killed at 50); e-freed covers his death; the walk-off case stated in the foundation. Stands: the decline stays
(the lead's brief asks for it; it costs the player the gear and nothing else, a plain refusal as in Morrowind). The
hold's kit rows in the place's stock are the place agent's to remove (not this lane's files).

# Paper playtests: MN11 to MN13 (moment 1, the designed records)

| Quest | Run | Result |
|---|---|---|
| MN11 | story/playtests/quest.main.mn11/20261117T165703Z-designed | stopped at 20: the ballast crate was placed as a carriable thing, so the stone could not be taken from it |
| MN11 | story/playtests/quest.main.mn11/20261117T165846Z-designed | pass |
| MN13 | story/playtests/quest.main.mn13/20261117T170002Z-designed | pass (the ghost now also glosses the Root) |
| MN12 | story/playtests/quest.main.mn12/20261117T170101Z-designed | stopped at 20; 3 miss: a locked door fires no use trigger, so trying the cellar door set nothing |
| MN12 | story/playtests/quest.main.mn12/20261117T170240Z-designed | stopped at 20; 3 miss: the store's jar was anchored in the yard, so the store looked empty |
| MN12 | story/playtests/quest.main.mn12/20261117T170448Z-designed | pass |

Classes of miss cleared:
- A fixed thing the player must open or use (a crate, a gate) is placed `kind: container`, never `thing`, or the player picks it up.
- A step that is "try a locked door" needs a usable or readable thing at the door that carries what the player learns there (here a barred window with the moaning); a locked door alone gives nothing.
- Every room the quest uses inside a place is a place of its own, with doors between them, and each person and thing is anchored in the room they stand in.
| MN11 | story/playtests/quest.main.mn11/20261117T170701Z-designed (way fight) | pass |
| MN11 | story/playtests/quest.main.mn11/20261117T170701Z-designed~2 (way sneak) | pass |

With --after (the whole line from MN01, each at 90):

| Quest | Run | Result |
|---|---|---|
| MN11 | story/playtests/quest.main.mn11/20261117T171620Z-designed (way fight, after MN01 to MN10) | pass |
| MN11 | story/playtests/quest.main.mn11/20261117T171622Z-designed (way sneak, after MN01 to MN10) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171632Z-designed (way captain, after MN01 to MN11) | stopped; the working stage ended only on the gaoler's first line and a jar taken |
| MN12 | story/playtests/quest.main.mn12/20261117T171634Z-designed (way trapdoor, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171636Z-designed (way lockpick, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171639Z-designed (way pickpocket, after MN01 to MN11) | stopped; the working stage ended only on the gaoler's first line and a jar taken |
| MN12 | story/playtests/quest.main.mn12/20261117T171640Z-designed (way speech, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171642Z-designed (way illusion, after MN01 to MN11) | stopped; the working stage ended only on the gaoler's first line and a jar taken |
| MN12 | story/playtests/quest.main.mn12/20261117T171645Z-designed (way trapdoor, after MN01 to MN13) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171908Z-designed (way captain, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171910Z-designed (way trapdoor, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171912Z-designed (way lockpick, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171914Z-designed (way pickpocket, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171916Z-designed (way speech, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171918Z-designed (way illusion, after MN01 to MN11) | pass |
| MN12 | story/playtests/quest.main.mn12/20261117T171920Z-designed (way trapdoor, after MN01 to MN13) | pass |
| MN13 | story/playtests/quest.main.mn13/20261117T171624Z-designed (way fight, after MN01 to MN11) | pass |
| MN13 | story/playtests/quest.main.mn13/20261117T171626Z-designed (way sneak, after MN01 to MN11) | pass |
| MN13 | story/playtests/quest.main.mn13/20261117T171628Z-designed (way turn, after MN01 to MN11) | pass |
| MN13 | story/playtests/quest.main.mn13/20261117T171630Z-designed (way sneak, after MN01 to MN12) | pass |

Cleared with --after: a working stage that waits on several parts counts every line the person can give (and their death), never one line; a thing the player is meant to notice is a container or a readable they look at, never only a take.

Regraded milestone by milestone (a run that completes is not a pass). Each run's grade.md has one line per milestone. MN11 know: lane B's real MN10 notes; MN12 and MN13 know: MN11's passing notes (20261117T172437Z-designed).

- MN11 20261117T171620Z-designed (fight): PASS
- MN11 20261117T171622Z-designed (sneak): PASS
- MN11 20261117T172311Z-designed (fight): MISS: miss (terms): cannot place the Collector or the Unbound; journal 10 named neither plainly
- MN11 20261117T172313Z-designed (sneak): MISS: miss (terms): cannot place the Collector or the Unbound; miss (going): cannot say what the Root and the Eye are; miss (terms): unsure the Toh-Reel-Ka is their order; miss (going): cannot say what the Root and the Eye are; the report line did not gloss them
- MN11 20261117T172437Z-designed (fight): PASS
- MN11 20261117T172439Z-designed (sneak): PASS
- MN12 20261117T171632Z-designed (captain): 1 pass; 2 pass; 3 miss (next). Stopped at stage 20. The working stage ended only on the gaoler's speaks-first topic and on a jar taken: a player who heard only his persuade or Illusion line, or looked at the jars without taking one, could not end it. Change: any of the gaoler's lines (or his death) counts; a stack of sap jars by the stair, looked at, sets the flag.: ass; 2 pass; 3 miss (next). Stopped at stage 20. The working stage ended only on the gaoler's speaks-first topic and on a jar taken: a player who heard only his persuade or Illusion line, or looked at the jars without taking one, could not end it. Change: any of the gaoler's lines (or his death) counts; a stack of sap jars by the stair, looked at, sets the flag.
- MN12 20261117T171634Z-designed (trapdoor): 1 pass; 2 pass; 3 pass; 4 pass. PASS. The open questions (what moans in the cellar, why the order feeds it sap) are the plan's own.
- MN12 20261117T171636Z-designed (lockpick): 1 pass; 2 pass; 3 pass; 4 pass. PASS. The open questions (what moans in the cellar, why the order feeds it sap) are the plan's own.
- MN12 20261117T171639Z-designed (pickpocket): 1 pass; 2 miss (next). Stopped at stage 25. The working stage ended only on the gaoler's speaks-first topic and on a jar taken: a player who heard only his persuade or Illusion line, or looked at the jars without taking one, could not end it. Change: any of the gaoler's lines (or his death) counts; a stack of sap jars by the stair, looked at, sets the flag.: ass; 2 miss (next). Stopped at stage 25. The working stage ended only on the gaoler's speaks-first topic and on a jar taken: a player who heard only his persuade or Illusion line, or looked at the jars without taking one, could not end it. Change: any of the gaoler's lines (or his death) counts; a stack of sap jars by the stair, looked at, sets the flag.
- MN12 20261117T171640Z-designed (speech): 1 pass; 2 pass; 3 pass; 4 pass. PASS. The open questions (what moans in the cellar, why the order feeds it sap) are the plan's own.
- MN12 20261117T171642Z-designed (illusion): 1 pass; 2 pass; 3 miss (next). Stopped at stage 20. The working stage ended only on the gaoler's speaks-first topic and on a jar taken: a player who heard only his persuade or Illusion line, or looked at the jars without taking one, could not end it. Change: any of the gaoler's lines (or his death) counts; a stack of sap jars by the stair, looked at, sets the flag.: ass; 2 pass; 3 miss (next). Stopped at stage 20. The working stage ended only on the gaoler's speaks-first topic and on a jar taken: a player who heard only his persuade or Illusion line, or looked at the jars without taking one, could not end it. Change: any of the gaoler's lines (or his death) counts; a stack of sap jars by the stair, looked at, sets the flag.
- MN12 20261117T171645Z-designed (trapdoor): 1 pass; 2 pass; 3 pass; 4 pass. PASS. The open questions (what moans in the cellar, why the order feeds it sap) are the plan's own.
- MN12 20261117T171908Z-designed (captain): MISS: miss (going): believes Jal-Veesa is a person or at Noota Nara; the journal does not say it is the town whose sick Hist they first saw
- MN12 20261117T171910Z-designed (trapdoor): MISS: miss (going): calls the hunt 'the seven towers for the Seal' or 'the Unbound business'; it does not hold that the order's hunt is for the Eye and waits at Bell Station
- MN12 20261117T171912Z-designed (lockpick): MISS: miss (ways): believes the keep door can be picked; it opens only with the captain's key; miss (ways): believes the keep door can be picked; it opens only with the captain's key
- MN12 20261117T171914Z-designed (pickpocket): PASS
- MN12 20261117T171916Z-designed (speech): MISS: miss (going): calls the hunt 'the seven towers for the Seal' or 'the Unbound business'; it does not hold that the order's hunt is for the Eye and waits at Bell Station; miss (going): believes Jal-Veesa is a person or at Noota Nara; the journal does not say it is the town whose sick Hist they first saw
- MN12 20261117T171918Z-designed (illusion): MISS: miss (going): calls the hunt 'the seven towers for the Seal' or 'the Unbound business'; it does not hold that the order's hunt is for the Eye and waits at Bell Station
- MN12 20261117T171920Z-designed (trapdoor): MISS: miss (going): calls the hunt 'the seven towers for the Seal' or 'the Unbound business'; it does not hold that the order's hunt is for the Eye and waits at Bell Station; miss (next): sends themself to Bell Station though MN13 is done; ending 91 does not name the three stones' places
- MN12 20261117T172608Z-designed (captain): MISS: miss (ways): means to pick the keep door, which opens only with the wall captain's key
- MN12 20261117T172611Z-designed (trapdoor): PASS
- MN12 20261117T172613Z-designed (lockpick): MISS: miss (ways): means to pick the keep door, which opens only with the wall captain's key
- MN12 20261117T172614Z-designed (captain-pickpocket): MISS: miss (ways): means to pick the keep door, which opens only with the wall captain's key
- MN12 20261117T172616Z-designed (speech): PASS
- MN12 20261117T172619Z-designed (illusion): PASS
- MN12 20261117T172620Z-designed (trapdoor): MISS: miss (going): believes the order is the Unbound; journal 10 says 'the order' and never names the Toh-Reel-Ka; miss (going): believes the order is the Unbound; journal 10 says 'the order' and never names the Toh-Reel-Ka
- MN12 20261117T172853Z-designed (captain): PASS
- MN12 20261117T172855Z-designed (trapdoor): PASS
- MN12 20261117T172857Z-designed (lockpick): PASS
- MN12 20261117T172859Z-designed (captain-pickpocket): PASS
- MN12 20261117T172901Z-designed (speech): PASS
- MN12 20261117T172903Z-designed (illusion): MISS: miss (going): names only the errand; does not hold that the order's hunt for the Eye waits at Bell Station
- MN12 20261117T172905Z-designed (trapdoor): PASS
- MN12 20261117T173140Z-designed (captain-pickpocket): PASS
- MN12 20261117T173142Z-designed (captain-pickpocket): PASS
- MN12 20261117T173144Z-designed (illusion): PASS
- MN12 20261117T173146Z-designed (illusion): PASS
- MN13 20261117T171624Z-designed (fight): MISS: miss (next): cannot tell which of Meer-Tasi and Sees-Below is the steward; the journal and objective name no one; miss (terms): does not know what the Eye is; nothing at the gate offers it
- MN13 20261117T171626Z-designed (sneak): MISS: miss (next): cannot tell which of Meer-Tasi and Sees-Below is the steward; miss (terms): does not know what the Eye is; nothing at the gate offers it
- MN13 20261117T171628Z-designed (turn): MISS: miss (next): cannot tell which of Meer-Tasi and Sees-Below is the steward; miss (terms): does not know what the Eye is; nothing at the gate offers it
- MN13 20261117T171630Z-designed (sneak): MISS: miss (next): cannot tell which of Meer-Tasi and Sees-Below is the steward; miss (terms): does not know what the Eye is; nothing at the gate offers it
- MN13 20261117T172600Z-designed (fight): MISS: miss (going): believes the order is the Unbound; journal 10 says 'the order' and never names the Toh-Reel-Ka
- MN13 20261117T172602Z-designed (sneak): MISS: miss (going): believes the order is the Unbound; journal 10 says 'the order' and never names the Toh-Reel-Ka
- MN13 20261117T172604Z-designed (turn): MISS: miss (going): believes the order is the Unbound; journal 10 says 'the order' and never names the Toh-Reel-Ka
- MN13 20261117T172606Z-designed (sneak): MISS: miss (going): believes the order is the Unbound; journal 10 says 'the order' and never names the Toh-Reel-Ka
- MN13 20261117T172845Z-designed (fight): PASS
- MN13 20261117T172847Z-designed (sneak): PASS
- MN13 20261117T172849Z-designed (turn): PASS
- MN13 20261117T172851Z-designed (sneak): PASS

Classes of miss cleared in the regrade: a person the player must find is named in the journal and objective (the steward); the order is named as the Toh-Reel-Ka, never 'the order' alone, where the player may confuse it with the Unbound; the Eye and the Root are glossed in each quest's first entry and each report line; a door only a key opens says so where the ways are given; an ending reached in either order names the next places, never a step already done.

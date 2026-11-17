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

# Paper runs: MN14 to MN19 (lane D)

| Quest | Run folder | Result |
|---|---|---|
| MN14 | story/playtests/quest.main.mn14/20261117T165818Z-designed | stuck: the Warden's Chest could be carried off and the vault door led to an empty room |
| MN14 | story/playtests/quest.main.mn14/20261117T170049Z-designed | pass (as a guest: toll, then pickpocket) |
| MN14 | story/playtests/quest.main.mn14/20261117T170146Z-designed | pass (unseen) |
| MN14 | story/playtests/quest.main.mn14/20261117T170220Z-designed | pass (by force: duel, then killed him) |
| MN15 | story/playtests/quest.main.mn15/20261117T170305Z-designed | pass; the end stage said two stones were still out, because the paper game cannot see MN14 done |
| MN16 | story/playtests/quest.main.mn16/20261117T170337Z-designed | pass; the same mismatch at the end stage |
| MN17 | story/playtests/quest.main.mn17/20261117T170412Z-designed | stuck: a fresh session holds none of the three stones, so the report line is never open |

Faults the changes cleared:
- A room behind a door was not a place: the hall and the vaults are now places, named with `placeName`.
- A chest placed as a `thing` could be carried off: it is now a `container`.
- MN13's markers needed a `name`.
- The Collector's ring and offer are now in the guest-stage journal.

# 0039: The play machine is a g4dn.xlarge on demand

**Status:** decided 2026-11-07 (owner ruling, walk feedback, in [owner-rulings](../owner-rulings.md)).

## Decision

1. `argonia-play` is a **g4dn.xlarge on demand** in Paris (eu-west-3b), Windows Server 2022: the Argonia card on
   Moonlight, the play page and agents' game-machine jobs all use it. Owner: "The g4dn on-demand machine frame
   rates are perfect. Let's always use this for the play machine going forward."
2. `create.sh` defaults to g4dn on demand. No image or snapshot of the machine is kept.
3. On demand costs about $0.80 an hour, so the machine's own idle-stop (15 minutes) and the Worker's backstops
   (8-hour cap, stale heartbeat, night stop) matter, and play hours count against the limit in
   [0008](0008-infrastructure-aws-under-150-a-month.md).

## Why

The owner judged the g4dn's frame rates perfect and wants no reclaims mid-play; he has chosen the price.

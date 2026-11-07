# 0039 — The play machine is a g4dn.xlarge on demand

**Date:** 2026-11-07 · **Status:** accepted (owner ruling, walk feedback 2026-11-07, in
[owner-rulings](../owner-rulings.md)). Supersedes the play-machine line of [0008](0008-infrastructure-aws-london-under-100-a-month.md).

## Decision

1. `argonia-play` is a **g4dn.xlarge on demand** in Paris (eu-west-3b), Windows Server 2022: the Argonia card on
   Moonlight, the play page and agents' game-machine jobs all use it. Owner: "The g4dn on-demand machine frame
   rates are perfect. Let's always use this for the play machine going forward."
2. The g6.xlarge persistent spot is retired, with its image and snapshot
   ([retire-g6](../research/machines/retire-g6.md)). `create.sh` now defaults to g4dn on demand.
3. On demand costs ~$0.80 an hour against the spot's ~$0.33, so the machine's own idle-stop (15 minutes) and the
   Worker's backstops (8-hour cap, stale heartbeat, night stop) matter more, and play hours count against
   0008's $100.

## Why

The owner judged the g4dn's frame rates perfect and wants no reclaims mid-play; the earlier "not on demand"
ruling (2026-10-31) was about price, and the owner has now chosen the price.

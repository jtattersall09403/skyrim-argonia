# Retiring the g6 spot play machine (owner ruling 2026-11-07)

The ruling: the g4dn.xlarge on-demand machine is the play machine from now on; retire the g6 spot and every
snapshot, image and volume no longer needed ([decision 0039](../../decisions/0039-the-play-machine-is-a-g4dn-on-demand.md)).

## Inventory, 2026-11-07 ~15:10 UTC (eu-west-2 and eu-west-3, the regions machines.conf and the build VM use)

| Item | Region | What | Referenced by | Call |
|---|---|---|---|---|
| i-0aec57899356eb8bc | eu-west-2 | m7i-flex.xlarge on demand, `argonia-build`, running | everything | keep (not in scope) |
| vol-0bb0d876067d6de46 | eu-west-2 | 120 GiB gp3, the build VM's root | the build VM | keep |
| i-003a8d8e08142cc5b | eu-west-3b | g4dn.xlarge on demand, `argonia-play`, running, launched 2026-11-06 | machines.conf (by name), run.sh, the Worker (by Name tag in eu-west-3) | keep: the play machine |
| vol-05e7c96872ff95078 | eu-west-3 | 150 GiB gp3, the g4dn's root (DeleteOnTermination) | the g4dn | keep |
| i-06511c8d8e2f1f1bf | eu-west-3 | the g6.xlarge persistent spot | docs/PROGRESS.md only | already gone: no instance, no spot request, no volume left in either region |
| ami-0dae75bada92b9713 | eu-west-3 | `argonia-play-g6-2026-11-05`, an image of the g6 | no script or doc names it (grep) | delete: the g4dn was launched from it and has moved on (BM&V, the stack since); it is not a documented recovery path, and the documented path is create.sh + setup + stack.py, with saves in S3 |
| snap-04996e7a172ed70ac | eu-west-3 | 150 GiB, the AMI's snapshot | the AMI only | delete with the AMI |
| Elastic IPs | both | none | | nothing to do |

## Saving

- The snapshot: 150 GiB at most (snapshots bill stored blocks; $0.05 per GB-month standard tier): up to about
  $7.50 a month. No EBS volume was left over from the g6 (its disk went with the instance), so no gp3 GB-months
  are saved beyond that.
- The g4dn.xlarge on demand, Windows, Paris: **$0.799 an hour** (AWS Price List, 2026-11-07), against the g6 spot's
  ~$0.33. At ~50 hours a month that is ~$40 instead of ~$17.

## The g4dn's idle-stop (checked 2026-11-07)

Scheduled task `argonia-idle-stop` is present and runs every 5 minutes (`idle-stop.ps1`, 15 minutes idle);
the instance's shutdown behaviour is `stop`; the System log shows the script's WMI shutdown at 18:30 on
2026-11-06, so a Windows shutdown stops (not terminates) the instance. The Worker's 8-hour cap, stale-heartbeat
stop and night stop are the backstops.

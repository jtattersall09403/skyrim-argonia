# Lane play-2: the clone image, kept; no machine (2026-10-30)

## Outcome

- **Image:** `ami-0e0653a8c139a7441` (snapshot `snap-04e7baf1f99932f82`, 150 GB), tagged `argonia-image=argonia-play`,
  `project=argonia`. Taken `--no-reboot` at 16:1x UTC while holding argonia-play's lock (`job_guard.sh run --gpu
  clone-src`, queued behind g13-e2e, released as soon as `create-image` returned; the snapshot is point-in-time from
  that call). It was still `pending` at 16:41 UTC and completes on its own.
- **No play-2 instance.** The owner cancelled the CK LOD run (xLODGen's result stays) mid-lane; the clone job was
  killed while it waited for the image, before `run-instances`. No instance, volume or alarm exists for play-2.
- **Unproven still** (the owner moment from lane-infra-play2 stands for the next creation): Steam starting offline
  on a clone with no egress, and Steam's sign-in surviving the Windows rename.

## Cost

- Image while kept: the EBS snapshot, at most 150 GB x $0.053/GB-month ~ $8/month (incremental, so likely less).
- A clone while running: g4dn.xlarge Windows spot in eu-west-2 at $0.2455/h (2026-10-30), plus its 150 GB gp3 volume
  (~$0.017/h) = about **$0.26/h**. Stopped: the volume only, ~$12/month; so terminate, not stop, when the job ends.

## Idle auto-stop (owner requirement for any extra machine)

Two layers, both keyed to the clone's own instance:
1. Inside Windows: scheduled task `argonia-idle-stop` runs `C:\argonia\infra\idle-stop.ps1` every 5 min and shuts
   down after 15 idle min (no stream, no SSH session, `state\busy` older than 15 min). It is in the image, so every
   clone has it; a Windows shutdown stops the instance (run-instances default behaviour `stop`).
2. AWS backstop (argonia-play's is the tunnel heartbeat, which a clone lacks): `infra/gpu-box/alarm.sh
   argonia-play-N` sets CloudWatch alarm `argonia-play-N-idle`, CPU < 3 % average for 9 x 5 min, action `ec2:stop`.
   `clone.sh` now calls it after launch. Not yet proved in game: the first clone must show it stops itself.

## Re-create recipe (when a job truly needs a second machine)

```
tooling/job_guard.sh run --gpu=argonia-play-2 clone-2 -- infra/gpu-box/clone.sh argonia-play-2   # reuses the image above; sets the alarm
infra/gpu-box/run.sh --machine argonia-play-2 ip; infra/gpu-box/run.sh --machine argonia-play-2 ps hostname
infra/gpu-box/run.sh --machine argonia-play-2 ps "Get-ScheduledTask argonia-idle-stop | select State"
infra/gpu-box/run.sh --machine argonia-play-2 ps "Stop-Service *sunshine* -Force; Set-Service *sunshine* -StartupType Disabled"  # headless
python3 infra/gpu-box/stack.py --machine argonia-play-2 menu        # MAIN-MENU OK; Steam offline, no login prompt
# idle proof: no SSH, no job; within ~20 min the state reads stopped:
aws ec2 describe-instances --region eu-west-2 --filters Name=tag:Name,Values=argonia-play-2 --query 'Reservations[].Instances[].State.Name'
# when the job ends: terminate (the volume deletes with it), and drop the alarm
aws ec2 terminate-instances --region eu-west-2 --instance-ids <id>; aws cloudwatch delete-alarms --region eu-west-2 --alarm-names argonia-play-2-idle
```

Headless: the clone's security group (`argonia-play-clone`) allows SSH from the build VM only and egress inside
the VPC only, so its copy of Sunshine cannot reach Moonlight hosts even before it is disabled; the cloudflared
tunnel is disabled by clone.sh's first boot. A persistent spot request must be cancelled with the instance
(`cancel-spot-instance-requests`) or it relaunches.

## Docs

ways-of-working §3, phases/README (two places) and 0-foundation README now say: one lane per game machine; extra
machines only for a substantial gain, created per job and stopped after.

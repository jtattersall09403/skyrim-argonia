# Play machine infrastructure: evidence, options, recommendation (2026-11-02, read-only)

Asked by the owner after the Paris g6.xlarge was reclaimed seven times on a Sunday: find the Windows spot GPU pools most
likely to run two hours uninterrupted, able to hold 50+ fps with Community Shaders, under $0.70/h, with one setup that
always has the latest build and saves and pays for no idle disks. Nothing was built or changed. The Paris machine's
spot request was fulfilled again at 18:19:55 UTC (the owner's walk).

Sources: Spot Instance Advisor data (spot-bid-advisor.s3.amazonaws.com, fetched 18:13 UTC), `describe-spot-price-history`
(30 days, Windows, time-weighted), `get-spot-placement-scores` (18:2x UTC), the Price List API, `describe-instance-types`,
service quotas, our own logs and research (1.8-machine-evidence.md, round-3.md, owner-brief.md), AWS docs
(spot-best-practices, interruption-behavior, replace-root, ebs-initialize, ebs-fast-snapshot-restore, ebs-copy-snapshot,
hibernating-prerequisites, ec2-capacity-blocks), and three web sweeps (Community Shaders performance, spot GPU interruption
reports, cloud-gaming-on-spot practice). The web sweeps were thin: nobody publishes Community Shaders benchmarks on
datacentre GPUs, and nobody publishes time-of-day interruption data for GPU spot; where a number below is an estimate it
says so.

## 1. Which instance types can run the game

- Measured: g4dn.xlarge (T4) at Riverwood, shaders on, 45 fps median / 32-35 fps 1% low; shaders off 53/40
  (lane-game-3). Below the bar (median 60 best, 50 acceptable, 95% of frames >= 45). The owner found the Paris
  g6.xlarge (L4) fast (#30). The L4 is RTX 3060-4060 class, the A10G (g5) RTX 3060 Ti-3070 class, both with 24 GB; the
  game is partly CPU-bound (2-4 threads), so 1% lows gain less than the medians. Estimate: g6.xlarge 60-75 median,
  g5.xlarge 70-90, both meeting the bar; the g6 numbers are still owed by 1.17.
- Ruled out: g6f fractional L4s: g6f.xlarge is 1/8 of an L4 with 2.8 GB of GPU memory, g6f.2xlarge 1/4 with 5.6 GB (too
  small for our textures), g6f.4xlarge 1/2 with 11 GB costs $0.86/h spot on Windows (16 vCPU: Windows adds $0.046 per
  vCPU-hour, so $0.74/h of licence). g4ad (AMD V520): priced in the Price List but `describe-instance-types` says the type
  does not exist in any region for this account, so it cannot be launched. g6e (L40S) $0.60-1.0 and only in Frankfurt
  and Stockholm; gr6 over $0.90. On-demand under $0.70 on Windows: none usable (g6.xlarge $1.21, g5.xlarge $1.46,
  g4dn.xlarge $0.80; the on-demand G quota is 0 in every region anyway). Capacity Blocks cover only p/trn types, Linux
  only. Hibernate: no G type supports it.
- So the choice is spot g6.xlarge, g6.2xlarge, g5.xlarge, g5.2xlarge, with g4dn.xlarge as a degraded last resort.

## 2. Pools: price, interruption band, availability now

Windows spot, USD/h, 30-day time-weighted median (p95 where it differs). Band = Spot Instance Advisor "frequency of
interruption" over the trailing month, Windows | Linux. The Linux band matters: Windows and Linux share one capacity
pool, the Windows sample is small, and a Linux band of >20% says the pool is hot whatever the Windows figure says.

| region (RTT from London) | g6.xlarge | g6.2xlarge | g5.xlarge | g5.2xlarge | g4dn.xlarge |
|---|---|---|---|---|---|
| London eu-west-2 (0 ms; G spot quota 16) | 0.29 (2a,2b), 0.44 (2c); 5-10% \| >20% | 0.50 (2c p95 0.61); 5-10% \| 10-15% | 0.31 flat (2a), 0.37 (2b, max 0.44); <5% \| >20% | 0.53 (2a,2b); >20% \| >20% | 0.25; 10-15% \| 5-10% |
| Paris eu-west-3 (8 ms; quota 8) | 0.33 (3b,3c only); 15-20% \| 15-20% | 0.55; >20% \| 10-15% | 0.36-0.74, max 1.12; no band | 0.58-0.75; no band | 0.25; <5% \| <5% |
| Frankfurt eu-central-1 (13 ms; quota 0) | 0.36; 5-10% \| <5% | 0.59-0.65 (p95 0.70-0.79); <5% \| <5% | 0.41-0.47; 5-10% \| 15-20% | 0.64-0.74; <5% \| >20% | 0.30; >20% \| 15-20% |
| Stockholm eu-north-1 (28 ms; quota 8) | 0.27; 5-10% \| >20% | 0.47; >20% \| 15-20% | 0.29 flat; <5% \| >20% | 0.50 flat; >20% \| >20% | 0.24; 10-15% \| 15-20% |
| Ireland eu-west-1 (10 ms; quota 8) | not offered | not offered | 0.64; >20% \| 10-15% | 0.73; >20% \| 10-15% | 0.43; >20% \| 5-10% |

Readings:
- Paris g6 is the worst L4/A10G pool in the table (15-20% on both OSes, >20% for the 2xlarge, only two AZs). Today's seven
  reclaims are what that band looks like on a bad day. Ireland is bad and dear on everything. Stockholm's Windows bands
  are good but its Linux bands say hot pools, and it is 28 ms away.
- The calmest pools at or above L4 class are Frankfurt g6.2xlarge (<5% both OSes) and Frankfurt g6.xlarge (5-10% | <5%),
  then London g6.2xlarge and g6.xlarge. Frankfurt needs the owner to request the G spot quota (it is 0; the build role
  cannot). Frankfurt g6.2xlarge's p95 price touches the $0.70 line.
- The calmest pool of all is Paris g4dn.xlarge (<5% | <5%, score 9 in all three AZs, $0.25): a T4 at 45 fps, the right
  last resort, not the machine.
- Placement scores at 18:2x UTC (Sunday): single types score 1 almost everywhere (g6.xlarge Paris 3b = 9, g4dn.xlarge 9
  in most AZs). The diversified L4/A10G set (g6.xlarge, g6.2xlarge, g5.xlarge, g5.2xlarge) per AZ: Paris 3b 9, Frankfurt
  3-4, London 1, Stockholm 1; with g4dn added, regionally London 9, Paris 9, Ireland 9, Frankfurt 8. Paris 3b scored 9
  today while reclaiming the machine seven times: the score says "a launch would succeed now", nothing about staying up
  (AWS says the same in writing).
- The honest reliability statement: with a quiet pool (band <5%) and interruptions spread evenly, a two-hour session
  survives well over 99% of the time; in a hot pool (today's Paris) it is a coin toss. Interruptions come in bursts on
  one pool, bands are monthly averages and cannot show the bursts, and no public source gives hour-of-day or weekday
  numbers (one vendor blog claims weekends are 40% quieter, unsourced). Reliability therefore comes from being able to
  leave a pool in minutes, not from picking the one right pool.

## 3. Our own interruption record

- 10-28: reclaimed during the owner's play. 10-31: 24/24 London launches failed 05:41-06:21 (no capacity); Paris and
  London g6 reclaimed together at 12:03; the London g6.2xlarge pair reclaimed 35 min after launch at 14:05.
- 11-02 (Sunday): Paris g6.xlarge reclaimed seven times from 10:57; Ireland g5 without capacity all afternoon; the build
  VM (m7i-flex spot, London) reclaimed twelve times.
- Every stop was a pool staying hot for hours while the persistent request kept restarting into it.

## 4. The disk questions, answered

- Different instance types in the same AZ can use one disk, one at a time: a gp3 root volume is detached from one
  instance and attached as the root device of another type (or swapped into a running instance with the replace-root
  task, one reboot). An EBS volume never leaves its AZ. Another AZ or region needs a snapshot and a new volume from it.
  Multi-Attach (several instances at once) is io1/io2 only, not a boot volume, not for NTFS: irrelevant.
- A persistent spot request with stop-on-interrupt restarts only the same type in the same AZ; a stopped spot instance
  cannot change type; detaching its root volume terminates it. That is exactly today's trap: the machine is pinned to the
  one pool that is reclaiming it.
- A volume made from a snapshot is lazy (each block fetched from S3 on first read: a slow Windows boot and a very slow
  first game load). Two remedies: the volume initialization rate (100-300 MiB/s, set at launch; 150 GB fully loaded in
  ~9 min; about $0.0036/GB, so roughly $0.50 per launch, EU rate to confirm), or Fast Snapshot Restore ($0.75 per
  snapshot per AZ per hour, one-hour minimum: not worth it).
- Snapshot copies between regions: the first copy is full (our 150 GB took ~25 min), later copies incremental, plus
  $0.02/GB transfer; a time-based copy of up to 500 MiB/s is available for a fee.
- One image works across T4, L4 and A10G with the NVIDIA GRID or gaming driver installed; the L4 needed a one-off
  pnputil rebind on new hardware (play_move.sh step 3); the A10G is unproven.
- Storage prices (London and Paris): gp3 $0.0928/GB-month, so an idle 150 GB volume is $13.9/month whether the machine
  runs or not; a snapshot $0.053/GB-month for used blocks only, at most $8/month for our image. What we pay today for
  idle storage: the Paris volume $14, the Ireland volume $14, an orphan 150 GB `old-london-restore` volume in London
  $14 (vol-004941a8732affa76, available since the London retirement), two Paris AMI snapshots up to $16: about $58 a
  month, more than the GPU hours at 50 h.

## 5. Options

A. **One disk, one AZ, many types.** Home AZ London 2a (euw2-az2): g6.xlarge $0.29, g5.xlarge $0.31, g6.2xlarge
$0.50, g5.2xlarge $0.53, g4dn.xlarge/2xlarge as the floor: six pools on one volume. A session launches the type with the
best score (EC2 Fleet, instant, capacity-optimized, one subnet) and swaps the volume in (replace-root, one reboot, ~3-5
min); an interruption moves to the next type the same way, saves already in S3. Deploys go to the volume over the
private route as today. Idle storage: one volume $14 + one AMI $8. Weak point: one AZ; London was dry one morning
(10-31); a second region needs B's mechanism anyway. Needs: the volume-swap launch path, the A10G driver proof.

B. **The machine is a snapshot.** Each deploy ends by imaging the machine (incremental, minutes to measure); the image is
copied to the second region incrementally. Any session launches the newest image into the best pool across London (3
AZs, 6 pools) and Frankfurt (3 AZs, once the owner's quota lands), Paris g4dn.xlarge the floor: ~15 pools, no volume kept
anywhere. The launch sets the initialization rate so the disk is at full speed in ~9 min (~$0.50); the instance's volume
dies with it. Saves round-trip through S3 (built: push every 5 min and on the spot notice, pull at boot). Idle storage:
snapshots only, ~$8 per region. Weak points: a start is a fresh launch (Windows first boot, tunnel, GPU bind: 5-8 min
against ~3 min for a stopped machine's start; the play page's "starting…" grows), a deploy is followed by an image step
before the owner's next start sees it, and the image-after-deploy time is unmeasured (the first full image took ~1 h,
incrementals should be minutes). Needs: image step in deploy, launch-from-image start path, the pool picker, the
quota request.

C. **Minimal: move the standbys, keep the model.** Stopped standbys in better pools: London 2a (g6.xlarge or g5.xlarge)
and Frankfurt g6.2xlarge after the quota; Paris g6 and Ireland retired. No new code beyond machines.conf and the
images. Still two idle volumes, still two pinned pools, still the same failure when both run hot.

D. **Leave AWS for a flat-rate cloud PC** (Shadow PC $38-55/month, persistent disk, no interruptions). Would mean
rebuilding the play page, tunnel, bridge, deploy and saves tooling around their client; agents could not drive it. Not
now.

## 6. Recommendation

B, with London first and Frankfurt second, Paris g4dn.xlarge as the floor, Ireland retired and Paris g6 retired once
the owner's walk is done. It is the only option that answers every ask at once: the latest build on whatever machine
appears at the stream URL (the image is made by the deploy), saves current (S3, already built), no idle disks, and the
widest set of pools to flee to. Expected monthly storage ~$16 against ~$58 today; GPU hours $15-25 at 50 h.

Before building, four measurements (one day, on the existing machines, nothing moved):
1. Incremental image time after a deploy on the Paris machine (expect minutes; the design dies if it is an hour).
2. Launch from that image with the initialization rate at 300 MiB/s: time to main menu, first ArgoniaWalk load time,
   the EU price of the rate.
3. One image on a g5.xlarge (A10G) in London 2a: does the GPU bind without hand work; Riverwood frame rate with
   shaders on (the g6 numbers 1.17 owes, measured at the same time).
4. Placement scores for our pools logged hourly for a week from the build VM, to choose the home AZ on evidence rather
   than on one Sunday.
And one owner action: request the G spot quota (16) in eu-central-1.

If B's start time proves too slow for the owner, A is the fallback: the same London pools, one kept volume, swap on
interruption; B's image path then serves only Frankfurt.

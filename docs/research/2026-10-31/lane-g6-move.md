# Lane g6-move: argonia-play to a g6.xlarge (owner #16, 2026-10-31): not cut over

## Measured

- **Image:** `ami-0b28d03211e7d92d2` (`argonia-play-20261031-g6move`), taken 05:3x UTC from i-0a3a6d5d93f8dfcb2 while
  stopped (consistent), tagged project=argonia, argonia-image=argonia-play. It is the source for the move and the way back.
- **#25 (Paris copy permission):** not answered, so London only.
- **Spot $/h, Windows, 05:25 UTC:** g6.xlarge 2a 0.2866, 2b 0.2864, 2c 0.4713; g5.xlarge 2a 0.3117, 2b 0.4122.
- **Capacity 05:41-06:21 UTC:** 24 launch attempts (g6 and g5 in 2a/2b/2c, every 10 min, job g6-try / g6-try2):
  every one InsufficientInstanceCapacity. The build VM restarted at 06:29 and killed the retry job.
- **09:16 UTC:** one-time spot g6.xlarge in eu-west-2a **launched** (probe i-0e2865746a1412bcc, terminated at once;
  one-time request sir-ggpqm43k ends with it). London 2a has g6 capacity again.
- The old g4dn was renamed argonia-play-g4dn for the 05:41 attempt and renamed back to argonia-play at 05:42. It stays
  the play machine; game-21 started it this morning.
- Deleted the 16:19 image ami-0e0653a8c139a7441 and its snapshot snap-04e7baf1f99932f82 (argonia-play-2 is gone).

## Not done (needs the machine from game-21)

Cut-over (lane-g6.md steps 2-4), the proofs, the frame measurements and retiring the g4dn. With capacity back, the
next run takes the slot between game-21's jobs and launches from ami-0b28d03211e7d92d2 as lane-g6.md says:
rename the old one argonia-play-g4dn first, then a persistent spot g6.xlarge in 2a (subnet-19b56a63, sg-0c73f686853568ced,
profile argonia-play-ssm), tag it Name=argonia-play, run alarm.sh, and prove it. Capacity changes hour to hour, so
launch first (as argonia-play-new) and retag at handover. Note: the new image holds tonight's state up to 05:3x, so any
deploy game-21 makes after that is pushed again to the new machine (stack.py push).

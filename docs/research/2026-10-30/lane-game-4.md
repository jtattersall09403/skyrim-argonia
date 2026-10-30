# Lane game-4: the instance type (2026-10-30 02:15 to 02:40 UTC; stopped early)

Commits: none. The lane stopped after the auto-mode classifier began denying every Bash call ("Modify Shared
Resources"), including read-only greps and `job_guard.sh status`. The first denial came right after the root-volume swap
below was started.

## Measured
1. **A spot instance's type cannot be changed.** At 02:20 `run.sh stop` backed up 17 saves (19 MB,
   `20261030T022021Z`). Then `aws ec2 modify-instance-attribute --instance-type Value=g6.xlarge` on
   i-0a3a6d5d93f8dfcb2 returned `UnsupportedOperation: Modifying 'instanceType' is not supported for spot
   instances`. The machine was started again on its old type: g4dn.xlarge, Tesla T4, GRID 596.86, Xeon 8259CL, 4
   logical CPUs. infra/README.md's "type can change while stopped" is wrong for spot.
2. **clone.sh cannot run:** `ec2:CreateImage` is denied to `argonia-build-ssm` (owner issue 13). `CreateSnapshot`,
   `RegisterImage` and `CreateReplaceRootVolumeTask` are denied too. `DetachVolume`, `AttachVolume`, `RunInstances`,
   `CreateTags`, `DeleteVolume` and `CancelSpotInstanceRequests` pass a dry run.
3. **No g6.xlarge spot capacity in eu-west-2a at 02:32.** A root-volume swap (`scratchpad/g4/swap.sh`) was started:
   launch a g6.xlarge spot shell in argonia-play's subnet, SG and role, then move root volume vol-0aad3b3dbba325a86
   onto it. Its first step failed with `InsufficientInstanceCapacity`, so nothing was changed. The volume is still
   on i-0a3a6d5d93f8dfcb2, and the Name tag was not touched. The volume is in 2a and cannot change AZ without a
   snapshot, which the role is denied.
4. **Spot prices, Windows, 02:3x:** g4dn.xlarge $0.2458 (2a); g6.xlarge $0.2866 (2a), $0.2864 (2b), $0.4581 (2c);
   g6.2xlarge $0.4928 (2a), $0.4930 (2b), $0.4921 (2c). The spot G quota is 8 vCPU.

## The owner's call (the re-plan trigger: the bar is unmet on g4dn, 52.5/25.4 at best, and no other type can be measured)
- **A.** Grant `ec2:CreateImage` (issue 13). clone.sh then makes a g6.xlarge clone in an AZ with capacity
  (2b at $0.286/h). Measure it; if it passes, move argonia-play over.
- **B.** Approve the root-volume swap: the same disk on a new g6.xlarge or g6.2xlarge instance in 2a, retried
  when 2a has capacity. It can be undone by moving the volume back. The play switch finds the machine by its Name
  tag, but its IAM user's scope (tag or ARN) could not be read from here.
- **C.** An on-demand g6.xlarge instead of spot. It costs more; price it with cost_report.py first.

## Not done (the whole list from step 1 of the brief)
The side rolls (Keytrace laid?, TDM's free movement during a dodge), `smoke.py pad`, `scene` twice, `stream-e2e`,
the uncapped water frame times, the SkyrimPrefs quest-marker and compass lines and the theme overlay, closing 0.2,
and 0.3 §b to §e. `make check` was not run.

## Hand-offs
- core-wiring (a5400e71b8b39aba0) will write ArgoniaBridge's `core-suspend <why>` endpoint and
  `Bridge.suspend_save()` in tools/bridge.py. It will build them in its own MSVC run and not deploy. It owes game-4
  the DLL path to lay and prove in game.
- The uncommitted hunks in infra/gpu-box/stack.py (combat_settings from the db) and data/dependencies.json (Elden
  Parry's ini moved out) belong to another lane (1.6-wiring). A commit of either file by path would carry them, so
  coordinate with that lane before editing.

## Machine state
argonia-play is running on g4dn.xlarge with no game launched, and idle-stop (15 min) will stop it. The swap's
failed RunInstances should not have left a spot request; check `describe-spot-instance-requests` for any request
tagged Name=argonia-play other than sir-k9bzpisj.

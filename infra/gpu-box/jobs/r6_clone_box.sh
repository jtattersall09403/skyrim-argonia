#!/usr/bin/env bash
# Round 6's in-game batch on a SPOT clone of Paris of a type that has capacity (owner call #42, 2026-11-04 19:1x:
# Paris's g6.xlarge scored 1 of 10 for spot placement in every Paris zone from 18:10; g4dn.xlarge scored 9).
# An image of Paris's stopped disk (the current build deployed: "DEPLOY held") launches as argonia-play-4, a persistent
# spot request that stops on interrupt (so run.sh up/stop and job_guard's resume work as on Paris); its tunnel
# connector is stopped so the play page never routes the owner to it; the running chain on Paris is stopped and the
# same chain relaunched at HEAD against the clone. The planner terminates the clone and deletes the image when the
# round's batch is read (`r6_clone_box.sh cleanup`). Under job_guard: tooling/job_guard.sh run r6-clone -- infra/gpu-box/jobs/r6_clone_box.sh
# Waits are `read -t` (no sleep: shell_guard); every step reuses what exists (image, instance), so a resume is cheap.
set -u; cd "$(dirname "$0")/../../.."
R=eu-west-3; SRC=i-06e8da597eb5fceab; NAME=argonia-play-4; TYPE=${CLONE_TYPE:-g4dn.xlarge}
q() { aws ec2 --region $R --output text "$@"; }
pause() { read -t "$1" < /dev/zero 2>/dev/null || true; }
fail() { echo "CLONE: $1 $(date -u +%H:%M)"; infra/build-vm/agent-wake.sh "round 6 clone box FAILED: $1. Read ~/.argonia/jobs/r6-clone.log."; exit 3; }
if [ "${1:-}" = cleanup ]; then
  ID=$(q describe-instances --filters Name=tag:Name,Values=$NAME Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[0].Instances[0].InstanceId')
  [ -n "$ID" ] && [ "$ID" != None ] && { q terminate-instances --instance-ids "$ID" --query 'TerminatingInstances[0].CurrentState.Name'; echo "$NAME $ID terminating"; }
  for a in $(q describe-images --owners self --filters Name=tag:temporary,Values=clone-box-2026-11-04 --query 'Images[].ImageId'); do
    snaps=$(q describe-images --image-ids $a --query 'Images[0].BlockDeviceMappings[].Ebs.SnapshotId'); q deregister-image --image-id $a && for sn in $snaps; do q delete-snapshot --snapshot-id $sn && echo "deleted $a $sn"; done
  done
  for sr in $(q describe-spot-instance-requests --filters Name=tag:Name,Values=$NAME Name=state,Values=open,active,disabled --query 'SpotInstanceRequests[].SpotInstanceRequestId'); do q cancel-spot-instance-requests --spot-instance-request-ids $sr >/dev/null && echo "spot request $sr cancelled"; done
  exit 0
fi
echo "== wait for Paris stopped $(date -u +%H:%M)"
for i in $(seq 1 60); do s=$(q describe-instances --instance-ids $SRC --query 'Reservations[0].Instances[0].State.Name'); [ "$s" = stopped ] && break; pause 15; done
[ "$s" = stopped ] || fail "Paris never stopped ($s)"
AMI=$(q describe-images --owners self --filters Name=tag:temporary,Values=clone-box-2026-11-04 Name=state,Values=available,pending --query 'Images[0].ImageId')
if [ -z "$AMI" ] || [ "$AMI" = None ]; then
  AMI=$(q create-image --instance-id $SRC --name "argonia-play-r6-$(date -u +%Y%m%dT%H%M)" --description "argonia-play with the round-6 build deployed (2026-11-04), for the spot clone" \
    --tag-specifications "ResourceType=image,Tags=[{Key=project,Value=argonia},{Key=argonia-image,Value=argonia-play},{Key=temporary,Value=clone-box-2026-11-04}]" --query ImageId) || fail "create-image"
  echo "== image $AMI creating $(date -u +%H:%M)"
else echo "== image $AMI reused"; fi
for i in $(seq 1 160); do s=$(q describe-images --image-ids $AMI --query 'Images[0].State'); [ "$s" = available ] && break; [ "$s" = failed ] && fail "image failed"; pause 30; done
[ "$s" = available ] || fail "image not available after 80 min"
echo "== image available $(date -u +%H:%M)"
ID=$(q describe-instances --filters Name=tag:Name,Values=$NAME Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[0].Instances[0].InstanceId')
if [ "$ID" = None ] || [ -z "$ID" ]; then
  TAGS="{Key=Name,Value=$NAME},{Key=project,Value=argonia},{Key=argonia-clone-of,Value=argonia-play},{Key=temporary,Value=clone-box-2026-11-04}"
  for sub in subnet-0bfc8c0a0d4b464ed subnet-0fd095fbc67f08b40 subnet-077a9641bc87135e0; do  # 3c, 3a, 3b: the clone's zone need not be Paris's
    ID=$(q run-instances --image-id $AMI --instance-type $TYPE --subnet-id $sub --security-group-ids sg-0617ac75f5e8c5e92 \
      --iam-instance-profile Name=argonia-play-ssm --metadata-options HttpTokens=required \
      --instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=persistent,InstanceInterruptionBehavior=stop}' \
      --tag-specifications "ResourceType=instance,Tags=[$TAGS]" "ResourceType=volume,Tags=[$TAGS]" "ResourceType=spot-instances-request,Tags=[$TAGS]" --query 'Instances[0].InstanceId' 2>&1) && break
    echo "run-instances in $sub: $(echo "$ID" | tail -1)"; ID=
  done
  [ -n "$ID" ] || fail "run-instances ($TYPE spot) in every zone"
  echo "launched $NAME $ID (spot $TYPE) $(date -u +%H:%M)"
else echo "reusing $NAME $ID"; q start-instances --instance-ids "$ID" >/dev/null 2>&1 || true; fi
echo "$ID" > ~/.argonia/jobs/r6-clone.id
aws ec2 wait instance-running --region $R --instance-ids "$ID" && echo "running $ID $(date -u +%H:%M)"
export ARGONIA_PLAY=$NAME
infra/gpu-box/run.sh up || fail "clone never answered"
infra/gpu-box/run.sh ps 'if (Get-Service cloudflared -EA SilentlyContinue) { Stop-Service cloudflared -Force -EA SilentlyContinue; Set-Service cloudflared -StartupType Disabled }; Get-Process SkyrimSE,skse64_loader -EA SilentlyContinue | Stop-Process -Force; "tunnel off, game clean"'
echo "== clone ready $(date -u +%H:%M): stopping the Paris chain, relaunching at HEAD against $NAME"
tooling/job_guard.sh stop r6-chain13 --keep-machine >/dev/null 2>&1 || true
rm -f ~/.argonia/round/chain.1.15-round-6.sha
ARGONIA_PLAY=$NAME tooling/job_guard.sh run --gpu=$NAME r6-chain14 -- infra/gpu-box/jobs/chain.sh tests/journeys/batches/1.15-round-6.yaml docs/research/2026-11-04/round-6.md 'r6-chain*'
echo "CLONE DONE $(date -u +%H:%M): r6-chain14 queued on $NAME"
